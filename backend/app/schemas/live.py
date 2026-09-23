from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import Health, Scenario, SeatbeltStatus, TaskType


class TaskMetric(BaseModel):
    key: str
    label: str
    value: float
    unit: str


class LiveState(BaseModel):
    timestamp: datetime
    machine_id: str
    operator_id: str
    task_id: str | None = None
    task_type: TaskType | None = None
    engine_on: bool
    engine_hours: float
    fuel_used_l: float
    fuel_rate_lph: float
    idle_time_min: float
    operating_time_min: float
    idle_pct: float
    load_cycles: int
    avg_payload_kg: float
    seatbelt_status: SeatbeltStatus
    proximity_m: float
    people_in_zone: int
    speed_kmh: float
    health: Health
    active_scenario: Scenario
    task_metrics: list[TaskMetric] = []


class TelemetryPoint(BaseModel):
    timestamp: datetime
    fuel_rate_lph: float
    idle_pct: float
    load_cycles: int
    proximity_m: float
