import json
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import Anomaly, Incident, Module, Quiz, Recommendation, TrainingProgressCreate
from app.services import anomaly_service, incident_service
from app.services.ml import interface as ml

TRAINING_JSON = Path(__file__).resolve().parent.parent / "db" / "seed_training.json"


@lru_cache
def _quizzes() -> dict[str, dict]:
    modules = json.loads(TRAINING_JSON.read_text(encoding="utf-8"))
    return {m["module_id"]: {"questions": m.get("quiz", [])} for m in modules}


def list_modules(db: Session) -> list[models.TrainingModule]:
    return list(db.scalars(select(models.TrainingModule).order_by(models.TrainingModule.module_id)))


def get_quiz(module_id: str) -> Quiz | None:
    quiz = _quizzes().get(module_id)
    return Quiz.model_validate(quiz) if quiz else None


def list_progress(db: Session, operator_id: str) -> list[models.OperatorTraining]:
    stmt = select(models.OperatorTraining).where(models.OperatorTraining.operator_id == operator_id)
    return list(db.scalars(stmt.order_by(models.OperatorTraining.module_id)))


def save_progress(db: Session, body: TrainingProgressCreate) -> models.OperatorTraining:
    row = db.scalar(select(models.OperatorTraining).where(
        models.OperatorTraining.operator_id == body.operator_id,
        models.OperatorTraining.module_id == body.module_id,
    ))
    if row is None:
        row = models.OperatorTraining(operator_id=body.operator_id, module_id=body.module_id)
        db.add(row)
    pct = max(0, min(100, body.progress_pct))
    row.progress_pct = pct
    row.status = "completed" if pct >= 100 else "in_progress" if pct > 0 else "not_started"
    if body.score is not None:
        row.score = body.score
    row.updated_at = datetime.now()
    db.commit()
    return row


def recommendations(db: Session, operator_id: str, days: int = 7) -> list[Recommendation]:
    since = datetime.now() - timedelta(days=days)
    anomalies = [Anomaly.model_validate(a, from_attributes=True)
                 for a in anomaly_service.list_anomalies(db, operator_id=operator_id, since=since)]
    incidents = [Incident.model_validate(i, from_attributes=True)
                 for i in incident_service.list_incidents(db, operator_id=operator_id)
                 if i.timestamp >= since]
    modules = [Module.model_validate(m, from_attributes=True) for m in list_modules(db)]
    by_id = {m.module_id: m for m in modules}

    recs = ml.recommend_training(anomalies, incidents, modules)
    return [
        Recommendation(module=by_id[module_id], reason=reason, priority=priority)
        for module_id, reason, priority in recs
        if module_id in by_id
    ]
