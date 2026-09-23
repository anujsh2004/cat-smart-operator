from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.routers.deps import get_or_404
from app.schemas import LiveState, TelemetryPoint
from app.services import live_service, telemetry_service

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("/{machine_id}/live", response_model=LiveState)
def live_state(machine_id: str, db: Session = Depends(get_db)):
    get_or_404(db, models.Machine, machine_id, "Machine")
    # Static snapshot until the B4 sim engine owns live state
    return live_service.initial_state(db, machine_id)


@router.get("/{machine_id}/telemetry", response_model=list[TelemetryPoint])
def telemetry(machine_id: str, minutes: int = Query(60, ge=1, le=1440), db: Session = Depends(get_db)):
    get_or_404(db, models.Machine, machine_id, "Machine")
    return telemetry_service.recent_points(db, machine_id, minutes)
