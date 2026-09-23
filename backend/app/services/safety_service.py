from sqlalchemy.orm import Session

from app.schemas import SafetyStatus
from app.services import live_service, task_service
from app.services.ml import interface as ml


def safety_status(db: Session, machine_id: str) -> SafetyStatus | None:
    """Assess the machine's current state. B4 swaps the static LiveState for the sim engine's."""
    state = live_service.initial_state(db, machine_id)
    if state is None:
        return None
    task = task_service.current_task(db, machine_id=machine_id)
    weather = task.weather if task else "Sunny"
    return ml.assess_safety(state, weather)
