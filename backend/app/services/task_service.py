from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def _today_bounds() -> tuple[datetime, datetime]:
    today = date.today()
    return datetime.combine(today, time.min), datetime.combine(today, time.max)


def list_today(db: Session, operator_id: str) -> list[models.Task]:
    start, end = _today_bounds()
    stmt = (
        select(models.Task)
        .where(models.Task.operator_id == operator_id, models.Task.scheduled_start.between(start, end))
        .order_by(models.Task.scheduled_start)
    )
    return list(db.scalars(stmt))


def current_task(db: Session, *, operator_id: str | None = None, machine_id: str | None = None) -> models.Task | None:
    """The in-progress task today, else the first not-completed one, else the first one."""
    start, end = _today_bounds()
    stmt = select(models.Task).where(models.Task.scheduled_start.between(start, end))
    if operator_id:
        stmt = stmt.where(models.Task.operator_id == operator_id)
    if machine_id:
        stmt = stmt.where(models.Task.machine_id == machine_id)
    tasks = list(db.scalars(stmt.order_by(models.Task.scheduled_start)))
    for status in ("in_progress", "scheduled"):
        for task in tasks:
            if task.status == status:
                return task
    return tasks[0] if tasks else None


def in_progress_task(db: Session, machine_id: str) -> models.Task | None:
    start, end = _today_bounds()
    return db.scalars(select(models.Task).where(
        models.Task.machine_id == machine_id,
        models.Task.status == "in_progress",
        models.Task.scheduled_start.between(start, end),
    ).order_by(models.Task.scheduled_start)).first()


def set_progress(db: Session, task_id: str, progress_pct: int) -> None:
    task = db.get(models.Task, task_id)
    if task is not None and task.status == "in_progress" and task.progress_pct != progress_pct:
        task.progress_pct = progress_pct
        db.commit()


def start_task(db: Session, task: models.Task) -> models.Task:
    # Only one task per machine runs at a time: pause any other in-progress one
    others = db.scalars(select(models.Task).where(
        models.Task.machine_id == task.machine_id,
        models.Task.status == "in_progress",
        models.Task.task_id != task.task_id,
    ))
    for other in others:
        other.status = "scheduled"
    task.status = "in_progress"
    task.started_at = task.started_at or datetime.now()
    db.commit()
    return task


def complete_task(db: Session, task: models.Task) -> models.Task:
    now = datetime.now()
    task.status = "completed"
    task.completed_at = now
    task.progress_pct = 100
    if task.started_at:
        task.actual_time_min = round((now - task.started_at).total_seconds() / 60, 1)
    db.commit()
    return task
