from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import LiveState
from app.services import baseline_service, task_service


def initial_state(db: Session, machine_id: str) -> LiveState | None:
    """Starting LiveState for a machine: latest telemetry reading if any, else shift-start defaults."""
    machine = db.get(models.Machine, machine_id)
    if machine is None:
        return None
    task = task_service.current_task(db, machine_id=machine_id)
    operator_id = task.operator_id if task else ""
    baseline = baseline_service.operator_baseline(db, operator_id) if operator_id else {}

    t = models.TelemetryReading
    last = db.scalars(select(t).where(t.machine_id == machine_id).order_by(t.timestamp.desc()).limit(1)).first()
    if last is not None:
        values = dict(
            engine_hours=last.engine_hours, fuel_used_l=last.fuel_used_l, fuel_rate_lph=last.fuel_rate_lph,
            idle_time_min=last.idle_time_min, operating_time_min=last.operating_time_min,
            load_cycles=last.load_cycles, avg_payload_kg=last.avg_payload_kg,
            seatbelt_status=last.seatbelt_status, proximity_m=last.proximity_m,
            people_in_zone=last.people_in_zone, speed_kmh=last.speed_kmh,
        )
    else:
        values = dict(
            engine_hours=machine.engine_hours, fuel_used_l=0.0,
            fuel_rate_lph=baseline.get("fuel_rate_lph") or 13.0,
            idle_time_min=0.0, operating_time_min=0.0, load_cycles=0, avg_payload_kg=1450.0,
            seatbelt_status="Fastened", proximity_m=25.0, people_in_zone=0, speed_kmh=0.0,
        )

    operating = values["operating_time_min"]
    return LiveState(
        timestamp=datetime.now(),
        machine_id=machine_id,
        operator_id=operator_id,
        task_id=task.task_id if task else None,
        task_type=task.task_type if task else None,
        engine_on=True,
        idle_pct=round(values["idle_time_min"] / operating * 100, 1) if operating else 0.0,
        health="Good",
        active_scenario="normal",
        task_metrics=[],
        **values,
    )
