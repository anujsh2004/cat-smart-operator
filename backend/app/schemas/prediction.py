from pydantic import BaseModel

from app.schemas.common import GroundCondition, SkillLevel, TaskType, Weather


class TaskTimeRequest(BaseModel):
    task_type: TaskType
    operator_id: str
    operator_skill: SkillLevel
    operator_experience_yrs: int
    machine_age_yrs: int
    weather: Weather
    ground_condition: GroundCondition
    temperature_c: float


class PredictionFactor(BaseModel):
    feature: str
    label: str
    impact_min: float


class TaskTimePrediction(BaseModel):
    predicted_time_min: float
    lower_min: float
    upper_min: float
    historical_avg_min: float
    model: str
    top_factors: list[PredictionFactor]
