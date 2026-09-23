import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    analytics,
    anomalies,
    incidents,
    machines,
    predict,
    safety,
    sim,
    system,
    tasks,
    training,
)
from app.services.ml import interface as ml
from app.sim import engine as sim_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml.load_models()
    logger.info("ML mode: %s", ml.ml_mode())
    await asyncio.to_thread(sim_engine.init_all)
    stop = asyncio.Event()
    sim_task = asyncio.create_task(sim_engine.run(stop))
    yield
    stop.set()
    await sim_task


app = FastAPI(title="Smart Operator Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (system, tasks, machines, safety, incidents, predict, anomalies, analytics, training, sim):
    app.include_router(module.router, prefix="/api")
