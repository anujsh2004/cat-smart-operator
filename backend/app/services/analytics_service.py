from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import AnalyticsDay, AnalyticsSummary, AnalyticsTotals, FleetAvg


def _pct(part: float, whole: float) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def summary(db: Session, operator_id: str, days: int) -> AnalyticsSummary:
    """Per-day usage from historical sessions, plus today's latest (cumulative) telemetry reading."""
    first_day = date.today() - timedelta(days=days - 1)
    since = datetime.combine(first_day, time.min)
    buckets: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    s = models.SessionRecord
    for row in db.scalars(select(s).where(s.operator_id == operator_id, s.timestamp >= since)):
        b = buckets[row.timestamp.date()]
        b["fuel_l"] += row.fuel_used_l
        b["idle_min"] += row.idle_time_min
        b["operating_min"] += row.operating_time_min
        b["load_cycles"] += row.load_cycles

    t = models.TelemetryReading
    latest = db.scalars(
        select(t).where(t.operator_id == operator_id, t.timestamp >= datetime.combine(date.today(), time.min))
        .order_by(t.timestamp.desc()).limit(1)
    ).first()
    if latest is not None:
        b = buckets[date.today()]
        b["fuel_l"] += latest.fuel_used_l
        b["idle_min"] += latest.idle_time_min
        b["operating_min"] += latest.operating_time_min
        b["load_cycles"] += latest.load_cycles

    i = models.Incident
    for ts in db.scalars(select(i.timestamp).where(i.operator_id == operator_id, i.timestamp >= since)):
        buckets[ts.date()]["incidents"] += 1

    day_rows = []
    for n in range(days):
        d = first_day + timedelta(days=n)
        b = buckets.get(d, {})
        day_rows.append(AnalyticsDay(
            date=d,
            fuel_l=round(b.get("fuel_l", 0.0), 1),
            idle_pct=_pct(b.get("idle_min", 0.0), b.get("operating_min", 0.0)),
            load_cycles=int(b.get("load_cycles", 0)),
            operating_min=round(b.get("operating_min", 0.0), 1),
            incidents=int(b.get("incidents", 0)),
        ))

    total_idle = sum(b.get("idle_min", 0.0) for b in buckets.values())
    total_operating = sum(b.get("operating_min", 0.0) for b in buckets.values())
    totals = AnalyticsTotals(
        fuel_l=round(sum(d.fuel_l for d in day_rows), 1),
        idle_pct=_pct(total_idle, total_operating),
        load_cycles=sum(d.load_cycles for d in day_rows),
        incidents=sum(d.incidents for d in day_rows),
    )

    fleet_idle, fleet_operating, fleet_fuel, fleet_cycles = db.execute(
        select(func.sum(s.idle_time_min), func.sum(s.operating_time_min), func.sum(s.fuel_used_l), func.sum(s.load_cycles))
    ).one()
    fleet = FleetAvg(
        idle_pct=_pct(float(fleet_idle or 0), float(fleet_operating or 0)),
        fuel_per_cycle_l=round(float(fleet_fuel or 0) / float(fleet_cycles), 3) if fleet_cycles else 0.0,
    )
    return AnalyticsSummary(days=day_rows, totals=totals, fleet_avg=fleet)
