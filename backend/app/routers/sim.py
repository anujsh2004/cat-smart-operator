from fastapi import APIRouter, HTTPException

from app.schemas import LiveState, ResetRequest, ScenarioRequest

router = APIRouter(prefix="/sim", tags=["sim"])

NOT_READY = "Simulation engine arrives in phase B4"


@router.post("/scenario", response_model=LiveState)
def set_scenario(body: ScenarioRequest) -> LiveState:
    raise HTTPException(status_code=501, detail=NOT_READY)


@router.post("/reset", response_model=LiveState)
def reset(body: ResetRequest) -> LiveState:
    raise HTTPException(status_code=501, detail=NOT_READY)
