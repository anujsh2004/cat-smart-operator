from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import TelemetryPoint


def recent_points(db: Session, machine_id: str, minutes: int) -> list[TelemetryPoint]:
    t = models.TelemetryReading
    since = datetime.now() - timedelta(minutes=minutes)
    rows = db.scalars(select(t).where(t.machine_id == machine_id, t.timestamp >= since).order_by(t.timestamp))
    return [
        TelemetryPoint(
            timestamp=r.timestamp,
            fuel_rate_lph=r.fuel_rate_lph,
            idle_pct=round(r.idle_time_min / r.operating_time_min * 100, 1) if r.operating_time_min else 0.0,
            load_cycles=r.load_cycles,
            proximity_m=r.proximity_m,
        )
        for r in rows
    ]
