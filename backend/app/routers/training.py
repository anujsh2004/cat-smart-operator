from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.session import get_db
from app.routers.deps import get_or_404
from app.schemas import Module, Quiz, Recommendation, TrainingProgress, TrainingProgressCreate
from app.services import training_service

router = APIRouter(prefix="/training", tags=["training"])


@router.get("/modules", response_model=list[Module])
def list_modules(db: Session = Depends(get_db)):
    return training_service.list_modules(db)


@router.get("/modules/{module_id}/quiz", response_model=Quiz)
def get_quiz(module_id: str, db: Session = Depends(get_db)):
    get_or_404(db, models.TrainingModule, module_id, "Module")
    quiz = training_service.get_quiz(module_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail=f"Module {module_id} has no quiz")
    return quiz


@router.get("/recommendations", response_model=list[Recommendation])
def recommendations(operator_id: str = settings.DEFAULT_OPERATOR_ID, db: Session = Depends(get_db)):
    return training_service.recommendations(db, operator_id)


@router.get("/progress", response_model=list[TrainingProgress])
def list_progress(operator_id: str = settings.DEFAULT_OPERATOR_ID, db: Session = Depends(get_db)):
    return training_service.list_progress(db, operator_id)


@router.post("/progress", response_model=TrainingProgress)
def save_progress(body: TrainingProgressCreate, db: Session = Depends(get_db)):
    get_or_404(db, models.Operator, body.operator_id, "Operator")
    get_or_404(db, models.TrainingModule, body.module_id, "Module")
    return training_service.save_progress(db, body)
