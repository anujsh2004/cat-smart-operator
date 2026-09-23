"""Task-specific KPIs (docs/ARCHITECTURE.md §5.3), derived from load cycles, payload and time."""
from app.schemas import TaskMetric

TARGET_DEPTH_M = {"Earth Excavation": 3.0, "Trenching": 1.8}
RATED_PAYLOAD_KG = 2000.0   # bucket rating used for payload utilisation
CYCLES_PER_GRADING_PASS = 6


def _m(key: str, label: str, value: float, unit: str) -> TaskMetric:
    return TaskMetric(key=key, label=label, value=round(value, 1), unit=unit)


def task_metrics(task_type: str | None, values: dict, *, cycle_time_s: float, base_cycle_time_s: float,
                 progress_pct: int, weather: str, alerts: int) -> list[TaskMetric]:
    cycles = values["load_cycles"]
    payload_t = values["avg_payload_kg"] / 1000

    if task_type in ("Earth Excavation", "Trenching"):
        return [
            _m("bucket_cycles", "Bucket cycles", cycles, ""),
            _m("avg_bucket_load", "Avg bucket load", payload_t, "t"),
            _m("dig_depth", "Excavation depth" if task_type == "Earth Excavation" else "Trench depth",
               TARGET_DEPTH_M[task_type] * progress_pct / 100, "m"),
            _m("cycle_time", "Cycle time", cycle_time_s, "s"),
        ]
    if task_type == "Material Loading":
        return [
            _m("load_cycles", "Load cycles", cycles, ""),
            _m("avg_payload", "Avg payload", payload_t, "t"),
            _m("payload_utilisation", "Payload utilisation", values["avg_payload_kg"] / RATED_PAYLOAD_KG * 100, "%"),
            _m("loading_cycle_time", "Loading cycle time", cycle_time_s, "s"),
        ]
    if task_type == "Grading":
        # Slower-than-usual cycles and poor weather both cost grade accuracy
        slowdown = abs(cycle_time_s / base_cycle_time_s - 1) if base_cycle_time_s else 0
        accuracy = max(80.0, 98.0 - 25 * slowdown - (3.0 if weather in ("Rainy", "Foggy") else 0.0))
        return [
            _m("passes_completed", "Passes completed", cycles // CYCLES_PER_GRADING_PASS, ""),
            _m("grade_accuracy", "Grade accuracy", accuracy, "%"),
            _m("surface_deviation", "Surface deviation", (100 - accuracy) * 0.8, "cm"),
            _m("travel_speed", "Travel speed", values["speed_kmh"], "km/h"),
        ]
    if task_type == "Demolition":
        return [
            _m("impact_cycles", "Impact cycles", cycles, ""),
            _m("material_removed", "Material removed", cycles * payload_t, "t"),
            _m("proximity_risk", "Proximity risk", max(0.0, min(100.0, (10 - values["proximity_m"]) * 10)), "%"),
            _m("structural_alerts", "Structural alerts", alerts, ""),
        ]
    return []
