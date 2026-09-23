from fastapi import APIRouter, HTTPException

from app.schemas import LiveState, ResetRequest, ScenarioRequest
from app.sim import engine

router = APIRouter(prefix="/sim", tags=["sim"])


def _found(live: LiveState | None, machine_id: str) -> LiveState:
    if live is None:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return live


@router.post("/scenario", response_model=LiveState)
def set_scenario(body: ScenarioRequest) -> LiveState:
    return _found(engine.set_scenario(body.machine_id, body.scenario), body.machine_id)


@router.post("/reset", response_model=LiveState)
def reset(body: ResetRequest) -> LiveState:
    return _found(engine.reset(body.machine_id), body.machine_id)
