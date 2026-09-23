"""Small helpers shared by routers."""
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Base

M = TypeVar("M", bound=Base)


def get_or_404(db: Session, model: type[M], key: str, label: str) -> M:
    row = db.get(model, key)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{label} {key} not found")
    return row
