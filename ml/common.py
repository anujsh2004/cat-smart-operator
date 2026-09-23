"""Shared definitions for Track A (docs/TRACK_A.md "Shared definitions", docs/ARCHITECTURE.md §4.3).

Every metric function accepts either a pandas DataFrame (vectorised, returns a Series)
or a dict such as a sessions.csv row or a live LiveState (returns a float), so the same
feature code runs in training and in live inference.
"""

from __future__ import annotations

from typing import Any, Mapping, Union

import numpy as np
import pandas as pd

# --- Enums (ARCHITECTURE.md §4.3, exact strings) ---
TASK_TYPES = ["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
WEATHER = ["Sunny", "Cloudy", "Windy", "Rainy", "Foggy"]
GROUND_CONDITIONS = ["Firm", "Loose", "Wet", "Rocky"]
SKILL_LEVELS = ["Beginner", "Intermediate", "Expert"]
SEATBELT_STATUSES = ["Fastened", "Unfastened"]
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]  # LOW < 40, MEDIUM 40-69, HIGH >= 70
SEVERITIES = ["low", "medium", "high"]
EVENT_TYPES = [
    "proximity_hazard",
    "seatbelt_unfastened",
    "excessive_idling",
    "fuel_spike",
    "abnormal_cycle_time",
    "unsafe_operation",
    "manual_report",
]
ANOMALY_TYPES = ["excessive_idling", "fuel_spike", "abnormal_cycle_time", "unsafe_operation"]
HEALTH_STATES = ["Good", "Attention", "Critical"]
SCENARIOS = ["normal", "seatbelt_off", "proximity_hazard", "excessive_idle", "fuel_spike", "rain"]

Data = Union[pd.DataFrame, Mapping[str, Any]]
Result = Union[pd.Series, float]


def _safe_div(num: Any, den: Any) -> Any:
    """num / den, returning 0.0 where den <= 0 (works for scalars and Series)."""
    if isinstance(den, pd.Series):
        return (num / den.where(den > 0)).fillna(0.0)
    den = float(den)
    return float(num) / den if den > 0 else 0.0


def engine_on_min(data: Data) -> Result:
    """Engine-on minutes = operating_time_min + idle_time_min."""
    total = data["operating_time_min"] + data["idle_time_min"]
    return total if isinstance(total, pd.Series) else float(total)


def idle_pct(data: Data) -> Result:
    """Idle share of engine-on time, in percent."""
    return _safe_div(data["idle_time_min"], engine_on_min(data)) * 100


def fuel_rate_lph(data: Data) -> Result:
    """Fuel used per engine-on hour (L/h)."""
    return _safe_div(data["fuel_used_l"], engine_on_min(data) / 60)


def cycle_time_s(data: Data) -> Result:
    """Seconds of productive work per load cycle (0 if no cycles)."""
    return _safe_div(data["operating_time_min"] * 60, data["load_cycles"])


def fuel_per_cycle_l(data: Data) -> Result:
    """Litres of fuel per load cycle (0 if no cycles)."""
    return _safe_div(data["fuel_used_l"], data["load_cycles"])


def risk_level(score: float) -> str:
    """Map a 0-100 safety risk score to LOW / MEDIUM / HIGH."""
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


if __name__ == "__main__":
    row = {"operating_time_min": 45.0, "idle_time_min": 15.0, "fuel_used_l": 12.0, "load_cycles": 90}
    df = pd.DataFrame([row, {**row, "load_cycles": 0, "operating_time_min": 0.0, "idle_time_min": 0.0}])
    for fn in (engine_on_min, idle_pct, fuel_rate_lph, cycle_time_s, fuel_per_cycle_l):
        print(f"{fn.__name__:18} dict={fn(row):8.3f}  df={np.round(fn(df).to_list(), 3).tolist()}")
