from pydantic import BaseModel

from app.schemas.common import GroundCondition, MachineType, MLMode, ShiftName, SkillLevel, Weather


class HealthResponse(BaseModel):
    status: str
    db: bool
    ml_mode: MLMode


class Operator(BaseModel):
    operator_id: str
    name: str
    skill_level: SkillLevel
    experience_yrs: int
    shift: ShiftName


class Machine(BaseModel):
    machine_id: str
    model: str
    machine_type: MachineType
    age_yrs: int
    engine_hours: float


class WeatherInfo(BaseModel):
    condition: Weather
    temperature_c: float
    visibility: str


class ShiftInfo(BaseModel):
    name: ShiftName
    start: str  # "HH:MM"
    end: str


class Context(BaseModel):
    operator: Operator
    machine: Machine
    weather: WeatherInfo
    ground_condition: GroundCondition
    shift: ShiftInfo
