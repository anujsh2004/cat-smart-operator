from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models


def operator_baseline(db: Session, operator_id: str) -> dict[str, float]:
    """Operator's normal behaviour from historical (non-anomalous) sessions.

    Shape matches the ML interface: {"idle_time_min", "fuel_rate_lph", "cycle_time_s"}.
    """
    s = models.SessionRecord
    idle, fuel_rate, cycle = db.execute(
        select(
            func.avg(s.idle_time_min),
            func.avg(s.fuel_used_l / func.nullif(s.operating_time_min / 60.0, 0)),
            func.avg(s.operating_time_min * 60.0 / func.nullif(s.load_cycles, 0)),
        ).where(s.operator_id == operator_id, s.anomaly_flag.is_(False))
    ).one()
    return {
        "idle_time_min": round(float(idle or 0), 1),
        "fuel_rate_lph": round(float(fuel_rate or 0), 2),
        "cycle_time_s": round(float(cycle or 0), 1),
    }


# Only used if the sessions table has no usable rows at all
DEFAULT_PROFILE = {"fuel_rate_lph": 13.0, "cycle_time_s": 22.0, "avg_payload_kg": 1450.0, "idle_frac": 0.25}


def task_profile(db: Session, operator_id: str, task_type: str | None) -> dict[str, float]:
    """Typical fuel rate, cycle time, payload and idle share for a task type, from normal sessions.

    Prefers this operator's history for the task type, then all operators, then DEFAULT_PROFILE.
    The sim engine drives live values around these numbers.
    """
    s = models.SessionRecord
    columns = (
        func.avg(s.fuel_used_l / func.nullif(s.operating_time_min / 60.0, 0)),
        func.avg(s.operating_time_min * 60.0 / func.nullif(s.load_cycles, 0)),
        func.avg(s.avg_payload_kg),
        func.avg(s.idle_time_min / func.nullif(s.operating_time_min, 0)),
    )
    filters = [s.anomaly_flag.is_(False)]
    if task_type:
        filters.append(s.task_type == task_type)
    for extra in ([s.operator_id == operator_id], []):
        row = db.execute(select(*columns).where(*filters, *extra)).one()
        if row[0] is not None:
            keys = ("fuel_rate_lph", "cycle_time_s", "avg_payload_kg", "idle_frac")
            return {k: round(float(v if v is not None else DEFAULT_PROFILE[k]), 3) for k, v in zip(keys, row)}
    return dict(DEFAULT_PROFILE)
