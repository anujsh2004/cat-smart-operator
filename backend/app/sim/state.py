"""In-memory live state, one entry per machine. Only the engine mutates it, always under `lock`."""
import threading
from dataclasses import dataclass, field
from typing import Any

from app.schemas import LiveState, SafetyStatus


@dataclass
class SimTask:
    task_id: str
    task_type: str
    estimated_time_min: float


@dataclass
class MachineSim:
    machine_id: str
    operator_id: str
    task: SimTask | None
    task_weather: str
    task_ground: str
    profile: dict[str, float]      # typical fuel rate / cycle time / payload / idle share for the task type
    baseline: dict[str, float]     # operator baseline passed to detect_anomalies()
    values: dict[str, Any]         # raw (unrounded) LiveState values the engine advances each tick
    live: LiveState                # rounded snapshot served by the API
    overlays: set[str] = field(default_factory=set)   # hazard scenarios currently applied (they stack)
    active_scenario: str = "normal"                   # most recently requested scenario
    safety: SafetyStatus | None = None
    tick: int = 0
    cycle_acc: float = 0.0          # fractional load cycles carried between ticks
    cycle_time_s: float = 0.0       # latest simulated cycle time
    cycles_at_start: int = 0        # load_cycles when this task (re)started, for progress
    progress_offset: int = 0        # task progress_pct when the sim picked it up
    progress_pct: int = 0
    open_incidents: dict[str, str] = field(default_factory=dict)  # event_type -> incident_id
    alerts: int = 0                 # HIGH-risk incidents raised this session

    @property
    def weather(self) -> str:
        return "Rainy" if "rain" in self.overlays else self.task_weather

    @property
    def ground(self) -> str:
        return "Wet" if "rain" in self.overlays else self.task_ground


machines: dict[str, MachineSim] = {}
lock = threading.RLock()
