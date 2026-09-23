"""Explainable safety risk engine (Phase A4). Output matches SafetyStatus in ARCHITECTURE.md §5.4
minus machine_id / evaluated_at, which the backend adds.

Weighted rules are the runtime source of truth because every point of the score can be
explained to an operator. ml/train_safety.py checks the weights against the historical data.
"""

from __future__ import annotations

from typing import Any, Mapping

from common import risk_level

BASE_SCORE = 10
WEIGHTS = {
    "seatbelt": 30,           # seatbelt unfastened while engine on
    "people_in_zone": 40,     # person in operating zone
    "proximity_warning": 20,  # proximity < 5 m
    "proximity_danger": 30,   # proximity < 3 m (replaces the warning weight)
    "interaction": 10,        # unfastened AND person in zone
    "weather_bad": 12,        # Rainy / Foggy
    "weather_windy": 6,
    "speed_near_people": 10,  # > 8 km/h with a person in zone
}
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


def assess(state: Mapping[str, Any], weather: str) -> dict:
    """state: LiveState-shaped dict (seatbelt_status, proximity_m, people_in_zone, speed_kmh, engine_on)."""
    seatbelt = state.get("seatbelt_status", "Fastened")
    proximity = float(state.get("proximity_m", 99.0))
    people = int(state.get("people_in_zone", 0))
    speed = float(state.get("speed_kmh", 0.0))
    engine_on = bool(state.get("engine_on", True))
    unbelted = seatbelt == "Unfastened" and engine_on

    factors: list[dict] = []

    def add(factor: str, label: str, weight_key: str) -> None:
        factors.append({"factor": factor, "label": label, "contribution": WEIGHTS[weight_key]})

    if people > 0:
        who = "Person" if people == 1 else f"{people} people"
        add("people_in_zone", f"{who} detected within {proximity:.1f} m of operating zone", "people_in_zone")
    if proximity < PROXIMITY_DANGER_M:
        add("proximity", f"Obstacle at {proximity:.1f} m, inside the {PROXIMITY_DANGER_M:g} m danger radius", "proximity_danger")
    elif proximity < PROXIMITY_WARNING_M:
        add("proximity", f"Obstacle at {proximity:.1f} m, inside the {PROXIMITY_WARNING_M:g} m warning radius", "proximity_warning")
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
    score = int(round(min(100, max(0, BASE_SCORE + sum(f["contribution"] for f in factors)))))
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


if __name__ == "__main__":
    import json

    cases = {
        "all clear": ({"seatbelt_status": "Fastened", "proximity_m": 18.5, "people_in_zone": 0, "speed_kmh": 2.1}, "Sunny"),
        "seatbelt only": ({"seatbelt_status": "Unfastened", "proximity_m": 18.5, "people_in_zone": 0, "speed_kmh": 2.1}, "Sunny"),
        "person at 4 m": ({"seatbelt_status": "Fastened", "proximity_m": 4.0, "people_in_zone": 1, "speed_kmh": 1.5}, "Sunny"),
        "person at 2 m + unfastened + rain": ({"seatbelt_status": "Unfastened", "proximity_m": 2.0, "people_in_zone": 1, "speed_kmh": 1.0}, "Rainy"),
        "high speed near person": ({"seatbelt_status": "Fastened", "proximity_m": 6.5, "people_in_zone": 1, "speed_kmh": 12.0}, "Cloudy"),
    }
    for name, (state, weather) in cases.items():
        r = assess(state, weather)
        print(f"\n== {name}: {r['risk_score']} {r['risk_level']} alert={r['alert']}")
        for f in r["factors"]:
            print(f"   +{f['contribution']:<3} {f['label']}")
        print(f"   -> {r['recommended_action']}")
    print("\n" + json.dumps(assess(*cases["person at 2 m + unfastened + rain"]), indent=2))
