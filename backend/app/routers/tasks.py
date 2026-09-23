from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.session import get_db
from app.routers.deps import get_or_404
from app.schemas import Task
from app.services import task_service
from app.sim import engine

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/today", response_model=list[Task])
def tasks_today(operator_id: str = settings.DEFAULT_OPERATOR_ID, db: Session = Depends(get_db)):
    return task_service.list_today(db, operator_id)


@router.post("/{task_id}/start", response_model=Task)
def start_task(task_id: str, db: Session = Depends(get_db)):
    task = task_service.start_task(db, get_or_404(db, models.Task, task_id, "Task"))
    engine.reload_task(task.machine_id)  # point the sim at this task
    return task


@router.post("/{task_id}/complete", response_model=Task)
def complete_task(task_id: str, db: Session = Depends(get_db)):
    task = task_service.complete_task(db, get_or_404(db, models.Task, task_id, "Task"))
    engine.reload_task(task.machine_id)
    return task
