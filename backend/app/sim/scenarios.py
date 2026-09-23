"""Demo scenarios. Hazard scenarios stack (proximity_hazard + seatbelt_off is the HIGH-risk demo);
"normal" clears them and values drift back to baseline over ~3 ticks."""
import random

from app.sim.state import MachineSim

BASE_PROXIMITY_M = 20.0
DRIFT = 0.5                 # share of the gap to baseline closed per tick
IDLE_FUEL_FACTOR = 0.35     # idling burns about a third of working fuel
FUEL_SPIKE_FACTOR = 2.2
BASE_SPEED_KMH = {"Grading": 5.0}


def _drift(current: float, target: float, noise: float, rng: random.Random) -> float:
    return max(0.0, current + (target - current) * DRIFT + rng.gauss(0, noise))


def apply(m: MachineSim, v: dict, rng: random.Random) -> None:
    """Set the instantaneous values (fuel rate, speed, payload, proximity, seatbelt) for this tick."""
    running = v["engine_on"]
    idling = "excessive_idle" in m.overlays
    base_rate = m.profile["fuel_rate_lph"]

    if running and "fuel_spike" in m.overlays:
        v["fuel_rate_lph"] = base_rate * FUEL_SPIKE_FACTOR * rng.gauss(1, 0.03)
    else:
        target = 0.0 if not running else base_rate * (IDLE_FUEL_FACTOR if idling else 1.0)
        v["fuel_rate_lph"] = _drift(v["fuel_rate_lph"], target, 0.15 if running else 0, rng)

    working = running and not idling
    task_type = m.task.task_type if m.task else ""
    v["speed_kmh"] = max(0.0, rng.gauss(BASE_SPEED_KMH.get(task_type, 1.5), 0.3)) if working else 0.0
    if working:
        v["avg_payload_kg"] = m.profile["avg_payload_kg"] * rng.gauss(1, 0.04)

    if "proximity_hazard" in m.overlays:
        v["people_in_zone"] = 1
        v["proximity_m"] = rng.uniform(3.0, 4.8)
    else:
        v["people_in_zone"] = 0  # the person has walked clear; distance recovers gradually
        v["proximity_m"] = _drift(v["proximity_m"], BASE_PROXIMITY_M, 0.8, rng)

    v["seatbelt_status"] = "Unfastened" if "seatbelt_off" in m.overlays else "Fastened"
