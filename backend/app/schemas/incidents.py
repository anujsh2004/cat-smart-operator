from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import EventType, IncidentStatus, Severity


class Incident(BaseModel):
    incident_id: str
    timestamp: datetime
    machine_id: str
    operator_id: str
    event_type: EventType
    severity: Severity
    risk_score: int | None = None
    details: dict[str, Any] = {}
    action_taken: str | None = None
    status: IncidentStatus
    resolved_at: datetime | None = None
    duration_s: int | None = None


class IncidentCreate(BaseModel):
    machine_id: str
    operator_id: str
    event_type: EventType = "manual_report"
    severity: Severity
    description: str


class IncidentResolve(BaseModel):
    resolution: str
