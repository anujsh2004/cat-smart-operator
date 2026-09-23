import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import engine, get_db
from app.schemas import Context, HealthResponse
from app.services import context_service
from app.services.ml import interface as ml

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


def _db_ok() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # health must report, not crash
        logger.warning("DB health check failed: %s", exc)
        return False


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db = _db_ok()
    return HealthResponse(status="ok" if db else "degraded", db=db, ml_mode=ml.ml_mode())


@router.get("/context", response_model=Context)
def get_context(operator_id: str = settings.DEFAULT_OPERATOR_ID, db: Session = Depends(get_db)) -> Context:
    context = context_service.get_context(db, operator_id)
    if context is None:
        raise HTTPException(status_code=404, detail=f"Operator {operator_id} not found")
    return context
