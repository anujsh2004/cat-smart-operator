from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.routers.deps import get_or_404
from app.schemas import Incident, IncidentCreate, IncidentResolve, IncidentStatus
from app.services import incident_service

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[Incident])
def list_incidents(machine_id: str | None = None, operator_id: str | None = None,
                   status: IncidentStatus | None = None, limit: int = Query(20, ge=1, le=200),
                   db: Session = Depends(get_db)):
    return incident_service.list_incidents(db, machine_id=machine_id, operator_id=operator_id,
                                           status=status, limit=limit)


@router.post("", response_model=Incident, status_code=201)
def report_incident(body: IncidentCreate, db: Session = Depends(get_db)):
    get_or_404(db, models.Machine, body.machine_id, "Machine")
    get_or_404(db, models.Operator, body.operator_id, "Operator")
    return incident_service.create_manual(db, body)


@router.patch("/{incident_id}/resolve", response_model=Incident)
def resolve_incident(incident_id: str, body: IncidentResolve, db: Session = Depends(get_db)):
    incident = get_or_404(db, models.Incident, incident_id, "Incident")
    return incident_service.resolve(db, incident, body.resolution)
