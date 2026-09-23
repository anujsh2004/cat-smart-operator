from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import AnomalyCreate


def list_anomalies(db: Session, *, operator_id: str | None = None, machine_id: str | None = None,
                   limit: int = 20, since: datetime | None = None) -> list[models.Anomaly]:
    stmt = select(models.Anomaly)
    if operator_id:
        stmt = stmt.where(models.Anomaly.operator_id == operator_id)
    if machine_id:
        stmt = stmt.where(models.Anomaly.machine_id == machine_id)
    if since:
        stmt = stmt.where(models.Anomaly.timestamp >= since)
    return list(db.scalars(stmt.order_by(models.Anomaly.timestamp.desc()).limit(limit)))


def _next_id(db: Session) -> str:
    ids = db.scalars(select(models.Anomaly.anomaly_id)).all()
    nums = [int(i[3:]) for i in ids if i.startswith("ANM") and i[3:].isdigit()]
    return f"ANM{max(nums, default=0) + 1:04d}"


def save_if_new(db: Session, anomaly: AnomalyCreate, dedupe_minutes: int = 10) -> models.Anomaly | None:
    """Persist unless the same type was recorded for this machine within dedupe_minutes."""
    recent = db.scalar(select(models.Anomaly).where(
        models.Anomaly.machine_id == anomaly.machine_id,
        models.Anomaly.anomaly_type == anomaly.anomaly_type,
        models.Anomaly.timestamp >= anomaly.timestamp - timedelta(minutes=dedupe_minutes),
    ))
    if recent is not None:
        return None
    row = models.Anomaly(anomaly_id=_next_id(db), **anomaly.model_dump())
    db.add(row)
    db.commit()
    return row
