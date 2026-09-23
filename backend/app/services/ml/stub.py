"""Deterministic rule-based stand-ins for the ML models (docs/ARCHITECTURE.md §6 "Stub behaviour").

Track A replaces these with services/ml/live.py; interface.py picks which one to call.
"""
from app.schemas import (
    Anomaly,
    AnomalyCreate,
    Incident,
    LiveState,
    Module,
    PredictionFactor,
    SafetyFactor,
    SafetyStatus,
    TaskTimePrediction,
    TaskTimeRequest,
)

# --- Task-time prediction ---------------------------------------------------

BASE_TIME_MIN = {
    "Earth Excavation": 60.0,
    "Trenching": 45.0,
    "Material Loading": 30.0,
    "Grading": 35.0,
    "Demolition": 90.0,
}
SKILL_FACTOR = {"Beginner": 1.2, "Intermediate": 1.0, "Expert": 0.85}
WEATHER_FACTOR = {"Sunny": 1.0, "Cloudy": 1.0, "Windy": 1.05, "Foggy": 1.1, "Rainy": 1.15}


def predict_task_time(req: TaskTimeRequest) -> TaskTimePrediction:
    base = BASE_TIME_MIN[req.task_type]
    skill = SKILL_FACTOR[req.operator_skill]
    weather = WEATHER_FACTOR[req.weather]
    predicted = base * skill * weather

    factors = [
        PredictionFactor(
            feature="weather",
            label=f"{req.weather} weather",
            impact_min=round(base * skill * (weather - 1), 1),
        ),
        PredictionFactor(
            feature="operator_skill",
            label=f"{req.operator_skill} operator",
            impact_min=round(base * (skill - 1), 1),
        ),
    ]
    factors.sort(key=lambda f: abs(f.impact_min), reverse=True)

    return TaskTimePrediction(
        predicted_time_min=round(predicted, 1),
        lower_min=round(predicted * 0.9, 1),
        upper_min=round(predicted * 1.1, 1),
        historical_avg_min=base,
        model="stub_task_time_v0",
        top_factors=factors,
    )


# --- Safety -------------------------------------------------------------------

BAD_WEATHER_LABELS = {
    "Rainy": "Rain reduces traction and visibility",
    "Foggy": "Fog reduces visibility",
}


def _risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def assess_safety(state: LiveState, weather: str) -> SafetyStatus:
    factors: list[SafetyFactor] = []
    actions: list[str] = []

    if state.people_in_zone > 0:
        factors.append(SafetyFactor(
            factor="people_in_zone",
            label=f"Person detected within {state.proximity_m:.1f} m of operating zone",
            contribution=40,
        ))
        actions.append("stop swing movement and sound horn")
    if state.proximity_m < 5:
        factors.append(SafetyFactor(
            factor="proximity",
            label=f"Obstacle closer than 5 m ({state.proximity_m:.1f} m)",
            contribution=20,
        ))
        if not actions:
            actions.append("stop and check surroundings")
    if state.seatbelt_status == "Unfastened" and state.engine_on:
        factors.append(SafetyFactor(
            factor="seatbelt",
            label="Seatbelt unfastened while engine running",
            contribution=30,
        ))
        actions.append("fasten seatbelt")
    if weather in BAD_WEATHER_LABELS:
        factors.append(SafetyFactor(factor="weather", label=BAD_WEATHER_LABELS[weather], contribution=12))
        actions.append("reduce speed for conditions")

    factors.sort(key=lambda f: f.contribution, reverse=True)
    score = min(100, sum(f.contribution for f in factors))
    level = _risk_level(score)

    if actions:
        text = ", ".join(actions)
        recommended = text[0].upper() + text[1:] + " before resuming."
    else:
        recommended = "No action needed. Continue operating safely."

    return SafetyStatus(
        machine_id=state.machine_id,
        evaluated_at=state.timestamp,
        risk_score=score,
        risk_level=level,
        alert=level == "HIGH",
        seatbelt_status=state.seatbelt_status,
        proximity_m=state.proximity_m,
        people_in_zone=state.people_in_zone,
        factors=factors,
        recommended_action=recommended,
    )


# --- Anomaly detection -------------------------------------------------------

ANOMALY_MODULE = {"excessive_idling": "TM03", "fuel_spike": "TM03", "abnormal_cycle_time": "TM04"}


def _anomaly(state: LiveState, anomaly_type: str, observed: float, baseline: float,
             unit: str, message: str) -> AnomalyCreate:
    ratio = observed / baseline
    return AnomalyCreate(
        timestamp=state.timestamp,
        machine_id=state.machine_id,
        operator_id=state.operator_id,
        anomaly_type=anomaly_type,
        observed_value=round(observed, 1),
        baseline_value=round(baseline, 1),
        unit=unit,
        severity="high" if ratio >= 3 else "medium",
        anomaly_score=round(min(1.0, (ratio - 1) / 3), 2),
        message=message,
        recommended_module_id=ANOMALY_MODULE.get(anomaly_type),
    )


def detect_anomalies(state: LiveState, operator_baseline: dict) -> list[AnomalyCreate]:
    found: list[AnomalyCreate] = []

    idle_base = operator_baseline.get("idle_time_min") or 0
    if idle_base > 0 and state.idle_time_min > 2 * idle_base:
        found.append(_anomaly(
            state, "excessive_idling", state.idle_time_min, idle_base, "min",
            f"Idle time {state.idle_time_min:.0f} min vs your usual {idle_base:.0f} min this session",
        ))

    fuel_base = operator_baseline.get("fuel_rate_lph") or 0
    if fuel_base > 0 and state.fuel_rate_lph > 1.8 * fuel_base:
        found.append(_anomaly(
            state, "fuel_spike", state.fuel_rate_lph, fuel_base, "L/h",
            f"Fuel rate {state.fuel_rate_lph:.1f} L/h vs your usual {fuel_base:.1f} L/h",
        ))

    return found


# --- Training recommendations -----------------------------------------------

def recommend_training(anomalies: list[Anomaly], incidents: list[Incident],
                       modules: list[Module]) -> list[tuple[str, str, str]]:
    by_trigger = {m.trigger_anomaly_type: m for m in modules if m.trigger_anomaly_type}
    events = [(a.anomaly_type, a.timestamp, a.severity) for a in anomalies]
    events += [(i.event_type, i.timestamp, i.severity) for i in incidents]
    events.sort(key=lambda e: e[1], reverse=True)  # newest first

    results: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for event_type, ts, severity in events:
        module = by_trigger.get(event_type)
        if module is None or module.module_id in seen:
            continue
        seen.add(module.module_id)
        reason = f"Triggered by {event_type.replace('_', ' ')} on {ts:%d %b}"
        results.append((module.module_id, reason, "high" if severity == "high" else "medium"))
    return results
