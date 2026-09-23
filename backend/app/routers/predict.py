from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import TaskTimePrediction, TaskTimeRequest
from app.services import prediction_service

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("/task-time", response_model=TaskTimePrediction)
def predict_task_time(body: TaskTimeRequest, db: Session = Depends(get_db)):
    return prediction_service.predict_task_time(db, body)
