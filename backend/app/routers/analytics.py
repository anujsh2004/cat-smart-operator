from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.session import get_db
from app.routers.deps import get_or_404
from app.schemas import AnalyticsSummary
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def summary(operator_id: str = settings.DEFAULT_OPERATOR_ID, days: int = Query(7, ge=1, le=90),
            db: Session = Depends(get_db)):
    get_or_404(db, models.Operator, operator_id, "Operator")
    return analytics_service.summary(db, operator_id, days)
