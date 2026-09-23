"""Unusual behaviour detection (port of ml/anomaly.py + the shared definitions in ml/common.py).

IsolationForest gives an overall "how unusual" score (0-1); ratio rules against the operator's
own baseline decide the type and message. Report if a rule fires, or if the IF score is high
AND some ratio is elevated. Unsafe operation is a pure rule (behaviour features can't see it).
"""
from typing import Any, Mapping

import numpy as np
import pandas as pd

TASK_TYPES = ["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
BASELINE_KEYS = ["idle_time_min", "idle_pct", "fuel_rate_lph", "cycle_time_s"]


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def features(state: Mapping[str, Any]) -> dict[str, float]:
    """Shared definitions (docs/TRACK_A.md). The live fuel_rate_lph is used when present so a
    spike shows up immediately instead of slowly in the session average."""
    op, idle = float(state["operating_time_min"]), float(state["idle_time_min"])
    fuel, cycles = float(state["fuel_used_l"]), float(state.get("load_cycles") or 0)
    engine_on = op + idle
    rate = state.get("fuel_rate_lph")
    return {
        "idle_pct": _safe_div(idle, engine_on) * 100,
        "fuel_rate_lph": float(rate) if rate is not None else _safe_div(fuel, engine_on / 60),
        "cycle_time_s": _safe_div(op * 60, cycles),
        "fuel_per_cycle_l": _safe_div(fuel, cycles),
    }


def model_score(model: Any, meta: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    """IsolationForest score normalised to 0-1 with the training percentiles in anomaly_meta."""
    row = features(state)
    for t in TASK_TYPES:
        row[f"task_type={t}"] = 1.0 if state.get("task_type") == t else 0.0
    X = pd.DataFrame([row])[meta["feature_columns"]]
    raw = float(-model.score_samples(X)[0])
    s = meta["score_scaling"]
    return float(np.clip((raw - s["lo"]) / (s["hi"] - s["lo"]), 0.0, 1.0))


def resolve_baseline(meta: Mapping[str, Any], operator_id: str, task_type: str | None,
                     fallback: Mapping[str, float] | None) -> dict[str, tuple[float, str]]:
    """Per key: (value, whose). Order: operator+task, operator, backend fallback, fleet per task."""
    b = meta["baselines"]
    layers = [
        (b["operator_task"].get(f"{operator_id}|{task_type}"), "your usual"),
        (b["operator"].get(operator_id), "your usual"),
        (fallback, "your usual"),
        (b["task_type"].get(task_type or ""), "the fleet usual"),
    ]
    out: dict[str, tuple[float, str]] = {}
    for key in BASELINE_KEYS:
        for layer, whose in layers:
            if layer and layer.get(key):
                out[key] = (float(layer[key]), whose)
                break
    return out


def _severity(excess: float) -> str:
    """excess = ratio / threshold (>= 1 means the rule fired)."""
    if excess >= 1.5:
        return "high"
    if excess >= 1.2:
        return "medium"
    return "low"


def detect(meta: Mapping[str, Any], state: Mapping[str, Any], if_score: float,
           fallback_baseline: Mapping[str, float] | None) -> list[dict]:
    """state: LiveState as a dict. Returns AnomalyCreate-shaped dicts (recommended_module_id unset)."""
    th = meta["thresholds"]
    operator_id = state["operator_id"]
    task_type = state.get("task_type")
    feats = features(state)
    base = resolve_baseline(meta, operator_id, task_type, fallback_baseline)
    engine_on = float(state["operating_time_min"]) + float(state["idle_time_min"])

    def ratio(obs: float, key: str) -> float:
        return obs / base[key][0] if key in base and base[key][0] > 0 else 0.0

    candidates: list[dict] = []
    if engine_on >= th["min_engine_on_min"]:
        idle_min = float(state["idle_time_min"])
        r_min, r_pct = ratio(idle_min, "idle_time_min"), ratio(feats["idle_pct"], "idle_pct")
        if r_min / th["idle_time_ratio"] >= r_pct / th["idle_pct_ratio"]:
            b, whose = base.get("idle_time_min", (0.0, ""))
            candidates.append({"type": "excessive_idling", "obs": idle_min, "base": b, "unit": "min",
                               "ratio": r_min, "th": th["idle_time_ratio"],
                               "msg": f"Idle time {idle_min:.0f} min vs {whose} {b:.0f} min this session"})
        else:
            b, whose = base.get("idle_pct", (0.0, ""))
            candidates.append({"type": "excessive_idling", "obs": feats["idle_pct"], "base": b, "unit": "%",
                               "ratio": r_pct, "th": th["idle_pct_ratio"],
                               "msg": f"Idling {feats['idle_pct']:.0f}% of engine time vs {whose} {b:.0f}%"})

        b, whose = base.get("fuel_rate_lph", (0.0, ""))
        candidates.append({"type": "fuel_spike", "obs": feats["fuel_rate_lph"], "base": b, "unit": "L/h",
                           "ratio": ratio(feats["fuel_rate_lph"], "fuel_rate_lph"), "th": th["fuel_rate_ratio"],
                           "msg": f"Fuel burn {feats['fuel_rate_lph']:.1f} L/h vs {whose} {b:.1f} L/h"})

        if float(state.get("load_cycles") or 0) > 0:
            b, whose = base.get("cycle_time_s", (0.0, ""))
            candidates.append({"type": "abnormal_cycle_time", "obs": feats["cycle_time_s"], "base": b, "unit": "s",
                               "ratio": ratio(feats["cycle_time_s"], "cycle_time_s"), "th": th["cycle_time_ratio"],
                               "msg": f"Cycle time {feats['cycle_time_s']:.0f} s vs {whose} {b:.0f} s"
                                      + (f" for {task_type}" if task_type else "")})

    out: list[dict] = []

    def emit(anomaly_type: str, observed: float, baseline: float, unit: str, severity: str,
             score: float, message: str) -> None:
        out.append({
            "timestamp": state["timestamp"],
            "machine_id": state["machine_id"],
            "operator_id": operator_id,
            "anomaly_type": anomaly_type,
            "observed_value": round(float(observed), 1),
            "baseline_value": round(float(baseline), 1),
            "unit": unit,
            "severity": severity,
            "anomaly_score": round(float(score), 2),
            "message": message,
        })

    fired = [c for c in candidates if c["ratio"] >= c["th"]]
    for c in fired:
        excess = c["ratio"] / c["th"]
        rule_strength = min(1.0, 0.5 + 0.5 * (excess - 1))
        emit(c["type"], c["obs"], c["base"], c["unit"], _severity(excess),
             max(if_score, rule_strength), c["msg"])
    if not fired and if_score >= meta["score_scaling"]["threshold"]:
        elevated = [c for c in candidates if c["ratio"] >= th["elevated_ratio"]]
        if elevated:
            c = max(elevated, key=lambda c: c["ratio"] / c["th"])
            emit(c["type"], c["obs"], c["base"], c["unit"], "low", if_score,
                 f"Unusual operating pattern. {c['msg']}")

    prox = float(state.get("proximity_m", 99.0))
    if (state.get("seatbelt_status") == "Unfastened" and int(state.get("people_in_zone", 0)) > 0
            and prox < th["unsafe_proximity_m"]):
        emit("unsafe_operation", prox, th["unsafe_proximity_m"], "m", "high", max(if_score, 0.9),
             f"Operating unbelted with a person {prox:.1f} m away (limit {th['unsafe_proximity_m']:g} m)")
    return out
