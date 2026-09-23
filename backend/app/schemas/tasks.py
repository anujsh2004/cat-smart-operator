from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import GroundCondition, TaskStatus, TaskType, Weather


class Task(BaseModel):
    task_id: str
    task_type: TaskType
    machine_id: str
    operator_id: str
    site_zone: str
    scheduled_start: datetime
    status: TaskStatus
    progress_pct: int
    weather: Weather
    ground_condition: GroundCondition
    estimated_time_min: float
    predicted_time_min: float | None = None
    actual_time_min: float | None = None
