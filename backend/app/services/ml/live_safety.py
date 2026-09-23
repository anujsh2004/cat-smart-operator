"""Explainable safety risk rules (port of ml/safety.py).

Weights come from ml/artifacts/safety_meta.json ("rule_weights"), so the runtime and the
deck evidence (logistic-regression check in ml/train_safety.py) share one source.
"""
from typing import Any, Mapping

PROXIMITY_WARNING_M = 5.0
PROXIMITY_DANGER_M = 3.0
SPEED_LIMIT_NEAR_PEOPLE_KMH = 8.0

ACTIONS = {
    "proximity": "Stop swing movement, sound horn and wait for the zone to clear.",
    "people_in_zone": "Stop swing movement, sound horn and wait for the zone to clear.",
    "seatbelt": "Fasten seatbelt before continuing operation.",
    "interaction": "Stop, fasten seatbelt and wait for the person to leave the zone.",
    "speed": "Slow below 8 km/h and give way to people in the zone.",
    "weather": "Reduce speed and swing rate; allow extra stopping distance.",
}
ALL_CLEAR_ACTION = "No action needed. Continue safe operation."


def risk_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def assess(state: Mapping[str, Any], weather: str, weights: Mapping[str, int], base_score: int) -> dict:
    """state: LiveState as a dict. Returns SafetyStatus fields minus machine_id / evaluated_at."""
    seatbelt = state.get("seatbelt_status", "Fastened")
    proximity = float(state.get("proximity_m", 99.0))
    people = int(state.get("people_in_zone", 0))
    speed = float(state.get("speed_kmh", 0.0))
    unbelted = seatbelt == "Unfastened" and bool(state.get("engine_on", True))

    factors: list[dict] = []

    def add(factor: str, label: str, weight_key: str) -> None:
        factors.append({"factor": factor, "label": label, "contribution": int(weights[weight_key])})

    if people > 0:
        who = "Person" if people == 1 else f"{people} people"
        add("people_in_zone", f"{who} detected within {proximity:.1f} m of operating zone", "people_in_zone")
    if proximity < PROXIMITY_DANGER_M:
        add("proximity", f"Obstacle at {proximity:.1f} m, inside the {PROXIMITY_DANGER_M:g} m danger radius",
            "proximity_danger")
    elif proximity < PROXIMITY_WARNING_M:
        add("proximity", f"Obstacle at {proximity:.1f} m, inside the {PROXIMITY_WARNING_M:g} m warning radius",
            "proximity_warning")
    if unbelted:
        add("seatbelt", "Seatbelt unfastened while engine running", "seatbelt")
    if unbelted and people > 0:
        add("interaction", "Unbelted operator with a person in the zone", "interaction")
    if weather == "Rainy":
        add("weather", "Rain reduces traction and visibility", "weather_bad")
    elif weather == "Foggy":
        add("weather", "Fog reduces visibility", "weather_bad")
    elif weather == "Windy":
        add("weather", "Wind affects load and boom stability", "weather_windy")
    if people > 0 and speed > SPEED_LIMIT_NEAR_PEOPLE_KMH:
        add("speed", f"Travelling at {speed:.1f} km/h with people nearby", "speed_near_people")

    factors.sort(key=lambda f: f["contribution"], reverse=True)
    score = int(round(min(100, max(0, base_score + sum(f["contribution"] for f in factors)))))
    level = risk_level(score)

    action = ACTIONS[factors[0]["factor"]] if factors else ALL_CLEAR_ACTION
    if unbelted and factors and factors[0]["factor"] != "seatbelt":
        action += " Fasten seatbelt before resuming."

    return {
        "risk_score": score,
        "risk_level": level,
        "alert": level == "HIGH",
        "seatbelt_status": seatbelt,
        "proximity_m": round(proximity, 1),
        "people_in_zone": people,
        "factors": factors,
        "recommended_action": action,
    }
