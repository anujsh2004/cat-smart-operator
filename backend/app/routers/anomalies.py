from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import Anomaly
from app.services import anomaly_service

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[Anomaly])
def list_anomalies(operator_id: str | None = None, machine_id: str | None = None,
                   limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    return anomaly_service.list_anomalies(db, operator_id=operator_id, machine_id=machine_id, limit=limit)
