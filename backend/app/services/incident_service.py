from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import IncidentCreate


def _next_id(db: Session) -> str:
    ids = db.scalars(select(models.Incident.incident_id)).all()
    nums = [int(i[3:]) for i in ids if i.startswith("INC") and i[3:].isdigit()]
    return f"INC{max(nums, default=1000) + 1}"


def list_incidents(db: Session, *, machine_id: str | None = None, operator_id: str | None = None,
                   status: str | None = None, limit: int = 20) -> list[models.Incident]:
    stmt = select(models.Incident)
    if machine_id:
        stmt = stmt.where(models.Incident.machine_id == machine_id)
    if operator_id:
        stmt = stmt.where(models.Incident.operator_id == operator_id)
    if status:
        stmt = stmt.where(models.Incident.status == status)
    return list(db.scalars(stmt.order_by(models.Incident.timestamp.desc()).limit(limit)))


def create_manual(db: Session, body: IncidentCreate) -> models.Incident:
    return create(
        db,
        machine_id=body.machine_id,
        operator_id=body.operator_id,
        event_type=body.event_type,
        severity=body.severity,
        details={"description": body.description},
        action_taken="Reported by operator",
    )


def create(db: Session, *, machine_id: str, operator_id: str, event_type: str, severity: str,
           details: dict[str, Any], action_taken: str, risk_score: int | None = None) -> models.Incident:
    incident = models.Incident(
        incident_id=_next_id(db),
        timestamp=datetime.now(),
        machine_id=machine_id,
        operator_id=operator_id,
        event_type=event_type,
        severity=severity,
        risk_score=risk_score,
        details=details,
        action_taken=action_taken,
        status="open",
    )
    db.add(incident)
    db.commit()
    return incident


def resolve(db: Session, incident: models.Incident, resolution: str) -> models.Incident:
    if incident.status != "resolved":
        now = datetime.now()
        incident.status = "resolved"
        incident.resolved_at = now
        incident.duration_s = int((now - incident.timestamp).total_seconds())
        incident.action_taken = resolution
        db.commit()
    return incident
