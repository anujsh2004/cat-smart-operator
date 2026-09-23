from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import RiskLevel, SeatbeltStatus


class SafetyFactor(BaseModel):
    factor: str
    label: str
    contribution: int


class SafetyStatus(BaseModel):
    machine_id: str
    evaluated_at: datetime
    risk_score: int
    risk_level: RiskLevel
    alert: bool
    seatbelt_status: SeatbeltStatus
    proximity_m: float
    people_in_zone: int
    factors: list[SafetyFactor]
    recommended_action: str
