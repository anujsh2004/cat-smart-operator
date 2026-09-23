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
