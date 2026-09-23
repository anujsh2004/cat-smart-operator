from datetime import datetime

from sqlalchemy.orm import Session

from app.db import models
from app.schemas import TaskTimePrediction, TaskTimeRequest
from app.services.ml import interface as ml


def predict_task_time(db: Session, req: TaskTimeRequest) -> TaskTimePrediction:
    """Run the task-time model and keep an audit row in predictions."""
    prediction = ml.predict_task_time(req)
    db.add(models.Prediction(
        task_id=None,
        model_name=prediction.model,
        predicted_value=prediction.predicted_time_min,
        features=req.model_dump(),
        created_at=datetime.now(),
    ))
    db.commit()
    return prediction
