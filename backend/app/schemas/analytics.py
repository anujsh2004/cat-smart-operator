import datetime as dt

from pydantic import BaseModel


class AnalyticsDay(BaseModel):
    date: dt.date
    fuel_l: float
    idle_pct: float
    load_cycles: int
    operating_min: float
    incidents: int


class AnalyticsTotals(BaseModel):
    fuel_l: float
    idle_pct: float
    load_cycles: int
    incidents: int


class FleetAvg(BaseModel):
    idle_pct: float
    fuel_per_cycle_l: float


class AnalyticsSummary(BaseModel):
    days: list[AnalyticsDay]
    totals: AnalyticsTotals
    fleet_avg: FleetAvg
