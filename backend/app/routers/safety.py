from fastapi import APIRouter, HTTPException

from app.schemas import SafetyStatus
from app.sim import engine

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("/status", response_model=SafetyStatus)
def safety_status(machine_id: str):
    status = engine.get_safety(machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return status
