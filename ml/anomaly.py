"""Unusual behaviour detection (Phase A5). Output items match AnomalyCreate (the Anomaly shape in
ARCHITECTURE.md §5.7 without anomaly_id; recommended_module_id is left None for the recommender).

Hybrid, explainable logic:
- IsolationForest gives an overall "how unusual" score (0-1).
- Ratio rules against the operator's OWN baseline decide the type and the message.
- Report if a ratio rule fires (always), or if the IF score is high AND some ratio is elevated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Union

import joblib
import numpy as np
import pandas as pd

from common import TASK_TYPES, cycle_time_s, fuel_per_cycle_l, fuel_rate_lph, idle_pct

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
MODEL_NAME = "iforest_anomaly_v1"

NUMERIC_FEATURES = ["idle_pct", "fuel_rate_lph", "cycle_time_s", "fuel_per_cycle_l"]
FEATURE_COLUMNS = NUMERIC_FEATURES + [f"task_type={t}" for t in TASK_TYPES]
BASELINE_KEYS = ["idle_time_min", "idle_pct", "fuel_rate_lph", "cycle_time_s"]

THRESHOLDS = {
    "idle_pct_ratio": 1.8,
    "idle_time_ratio": 2.0,
    "fuel_rate_ratio": 1.6,
    "cycle_time_ratio": 2.0,
    "elevated_ratio": 1.3,     # "somewhat high": only reported together with a high IF score
    "unsafe_proximity_m": 3.0,
    "min_engine_on_min": 5.0,  # ratios are too noisy before this in a live session
}

Data = Union[pd.DataFrame, Mapping[str, Any]]


def feature_frame(data: Data) -> pd.DataFrame:
    """Model features from sessions.csv rows or a single live-state dict (shared definitions)."""
    df = data if isinstance(data, pd.DataFrame) else pd.DataFrame([dict(data)])
    out = pd.DataFrame({
        "idle_pct": idle_pct(df),
        "fuel_rate_lph": df["fuel_rate_lph"] if "fuel_rate_lph" in df else fuel_rate_lph(df),
        "cycle_time_s": cycle_time_s(df),
        "fuel_per_cycle_l": fuel_per_cycle_l(df),
    }, index=df.index)
    for t in TASK_TYPES:
        out[f"task_type={t}"] = (df["task_type"] == t).astype(float)
    return out[FEATURE_COLUMNS].astype(float)


def normalise_score(raw: np.ndarray, scaling: Mapping[str, float]) -> np.ndarray:
    """-score_samples (higher = more unusual) mapped to 0-1 with training percentiles."""
    return np.clip((raw - scaling["lo"]) / (scaling["hi"] - scaling["lo"]), 0.0, 1.0)


_cache: dict[str, Any] = {}


def load(artifacts: Path = ARTIFACTS) -> tuple[Any, dict]:
    key = str(artifacts)
    if key not in _cache:
        model = joblib.load(artifacts / "anomaly_model.joblib")
        meta = json.loads((artifacts / "anomaly_meta.json").read_text(encoding="utf-8"))
        _cache[key] = (model, meta)
    return _cache[key]


def model_score(state: Data, artifacts: Path = ARTIFACTS) -> np.ndarray:
    model, meta = load(artifacts)
    raw = -model.score_samples(feature_frame(state))
    return normalise_score(raw, meta["score_scaling"])


def resolve_baseline(
    meta: Mapping[str, Any], operator_id: str, task_type: str, fallback: Mapping[str, float] | None
) -> dict[str, tuple[float, str]]:
    """Per key: (value, whose). Order: operator+task, operator, backend fallback, fleet per task."""
    layers = [
        (meta["baselines"]["operator_task"].get(f"{operator_id}|{task_type}"), "your usual"),
        (meta["baselines"]["operator"].get(operator_id), "your usual"),
        (fallback, "your usual"),
        (meta["baselines"]["task_type"].get(task_type), "the fleet usual"),
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


def detect_with_score(
    state: Mapping[str, Any], operator_id: str, fallback_baseline: Mapping[str, float] | None,
    if_score: float, meta: Mapping[str, Any],
) -> list[dict]:
    """Rule layer given a precomputed IsolationForest score (lets training evaluate in bulk)."""
    th = meta.get("thresholds", THRESHOLDS)
    task_type = state.get("task_type", "")
    feats = feature_frame(state).iloc[0]
    base = resolve_baseline(meta, operator_id, task_type, fallback_baseline)
    engine_on = float(state["operating_time_min"]) + float(state["idle_time_min"])

    candidates: list[dict] = []  # each: type, observed, baseline, unit, ratio, threshold, message

    def ratio(obs: float, key: str) -> float:
        return obs / base[key][0] if key in base and base[key][0] > 0 else 0.0

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

        if float(state.get("load_cycles", 0)) > 0:
            b, whose = base.get("cycle_time_s", (0.0, ""))
            candidates.append({"type": "abnormal_cycle_time", "obs": feats["cycle_time_s"], "base": b, "unit": "s",
                               "ratio": ratio(feats["cycle_time_s"], "cycle_time_s"), "th": th["cycle_time_ratio"],
                               "msg": f"Cycle time {feats['cycle_time_s']:.0f} s vs {whose} {b:.0f} s for {task_type}"})

    out: list[dict] = []

    def emit(anomaly_type: str, observed: float, baseline: float, unit: str, severity: str,
             score: float, message: str) -> None:
        out.append({
            "timestamp": state.get("timestamp"),
            "machine_id": state.get("machine_id"),
            "operator_id": operator_id,
            "anomaly_type": anomaly_type,
            "observed_value": round(float(observed), 1),
            "baseline_value": round(float(baseline), 1),
            "unit": unit,
            "severity": severity,
            "anomaly_score": round(float(score), 2),
            "message": message,
            "recommended_module_id": None,
        })

    if_high = if_score >= meta["score_scaling"]["threshold"]
    fired = [c for c in candidates if c["ratio"] >= c["th"]]
    for c in fired:
        excess = c["ratio"] / c["th"]
        rule_strength = min(1.0, 0.5 + 0.5 * (excess - 1))
        emit(c["type"], c["obs"], c["base"], c["unit"], _severity(excess),
             max(if_score, rule_strength), c["msg"])
    if not fired and if_high:
        elevated = [c for c in candidates if c["ratio"] >= th["elevated_ratio"]]
        if elevated:
            c = max(elevated, key=lambda c: c["ratio"] / c["th"])
            emit(c["type"], c["obs"], c["base"], c["unit"], "low", if_score,
                 f"Unusual operating pattern. {c['msg']}")

    prox = float(state.get("proximity_m", state.get("proximity_min_m", 99.0)))
    if (state.get("seatbelt_status") == "Unfastened" and int(state.get("people_in_zone", 0)) > 0
            and prox < th["unsafe_proximity_m"]):
        emit("unsafe_operation", prox, th["unsafe_proximity_m"], "m", "high", max(if_score, 0.9),
             f"Operating unbelted with a person {prox:.1f} m away (limit {th['unsafe_proximity_m']:g} m)")
    return out


def detect(
    state: Mapping[str, Any], operator_id: str, fallback_baseline: Mapping[str, float] | None = None,
    artifacts: Path = ARTIFACTS,
) -> list[dict]:
    """state: LiveState-shaped dict (idle_time_min, operating_time_min, fuel_used_l, fuel_rate_lph,
    load_cycles, task_type, seatbelt_status, people_in_zone, proximity_m). The live fuel_rate_lph
    is used when present so a fuel spike shows up immediately rather than in the session average."""
    _, meta = load(artifacts)
    score = float(model_score(state, artifacts)[0])
    return detect_with_score(state, operator_id, fallback_baseline, score, meta)


if __name__ == "__main__":
    normal = {
        "timestamp": "2026-09-23T10:32:14", "machine_id": "EXC001", "task_type": "Earth Excavation",
        "operating_time_min": 60.0, "idle_time_min": 30.0, "fuel_used_l": 18.0, "fuel_rate_lph": 12.0,
        "load_cycles": 175, "seatbelt_status": "Fastened", "people_in_zone": 0, "proximity_m": 18.5,
    }
    cases = {
        "normal OP1001": normal,
        "idle-heavy": {**normal, "operating_time_min": 30.0, "idle_time_min": 130.0, "load_cycles": 88,
                       "fuel_used_l": 14.5, "fuel_rate_lph": 5.4},
        "fuel spike": {**normal, "fuel_used_l": 40.0, "fuel_rate_lph": 28.5},
        "unsafe": {**normal, "seatbelt_status": "Unfastened", "people_in_zone": 1, "proximity_m": 2.2},
    }
    for name, state in cases.items():
        found = detect(state, "OP1001")
        print(f"\n== {name}: IF score {model_score(state)[0]:.2f}, {len(found)} anomaly(ies)")
        for a in found:
            print(f"   [{a['severity']:6}] {a['anomaly_type']:20} score {a['anomaly_score']:.2f}  {a['message']}")
