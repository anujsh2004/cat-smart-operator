from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import SafetyStatus
from app.services import safety_service

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("/status", response_model=SafetyStatus)
def safety_status(machine_id: str, db: Session = Depends(get_db)):
    status = safety_service.safety_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return status
