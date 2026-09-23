import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.session import engine
from app.schemas import HealthResponse
from app.services.ml import interface as ml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml.load_models()
    logger.info("ML mode: %s", ml.ml_mode())
    yield


app = FastAPI(title="Smart Operator Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _db_ok() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # health must report, not crash
        logger.warning("DB health check failed: %s", exc)
        return False


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    db = _db_ok()
    return HealthResponse(status="ok" if db else "degraded", db=db, ml_mode=ml.ml_mode())
