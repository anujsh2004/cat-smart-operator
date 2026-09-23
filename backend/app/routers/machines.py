from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.routers.deps import get_or_404
from app.schemas import LiveState, TelemetryPoint
from app.services import telemetry_service
from app.sim import engine

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("/{machine_id}/live", response_model=LiveState)
def live_state(machine_id: str):
    live = engine.get_live(machine_id)
    if live is None:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return live


@router.get("/{machine_id}/telemetry", response_model=list[TelemetryPoint])
def telemetry(machine_id: str, minutes: int = Query(60, ge=1, le=1440), db: Session = Depends(get_db)):
    get_or_404(db, models.Machine, machine_id, "Machine")
    points = telemetry_service.recent_points(db, machine_id, minutes)
    live = engine.get_live(machine_id)
    if live is not None and (not points or live.timestamp > points[-1].timestamp):
        points.append(telemetry_service.point_from_live(live))  # newest value, not yet persisted
    return points
