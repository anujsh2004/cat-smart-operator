from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import LiveState, TelemetryPoint


def record(db: Session, live: LiveState) -> None:
    db.add(models.TelemetryReading(
        timestamp=live.timestamp, machine_id=live.machine_id, operator_id=live.operator_id,
        task_id=live.task_id, engine_hours=live.engine_hours, fuel_used_l=live.fuel_used_l,
        fuel_rate_lph=live.fuel_rate_lph, load_cycles=live.load_cycles, idle_time_min=live.idle_time_min,
        operating_time_min=live.operating_time_min, avg_payload_kg=live.avg_payload_kg,
        seatbelt_status=live.seatbelt_status, proximity_m=live.proximity_m,
        people_in_zone=live.people_in_zone, speed_kmh=live.speed_kmh,
    ))
    db.commit()


def point_from_live(live: LiveState) -> TelemetryPoint:
    return TelemetryPoint(
        timestamp=live.timestamp, fuel_rate_lph=live.fuel_rate_lph, idle_pct=live.idle_pct,
        load_cycles=live.load_cycles, proximity_m=live.proximity_m,
    )


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
