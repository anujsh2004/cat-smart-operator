"""ML interface: the only entry point routers and the sim engine use for intelligence.

Signatures are FROZEN (docs/ARCHITECTURE.md §6). Implementations live in stub.py (rules)
and live.py (Track A, trained models); this module dispatches on ML_MODE.
"""
import logging
from types import ModuleType

from app.config import settings
from app.schemas import (
    Anomaly,
    AnomalyCreate,
    Incident,
    LiveState,
    Module,
    SafetyStatus,
    TaskTimePrediction,
    TaskTimeRequest,
)
from app.services.ml import stub

logger = logging.getLogger(__name__)


def ml_mode() -> str:
    return settings.ML_MODE


def _impl() -> ModuleType:
    if ml_mode() == "live":
        try:
            from app.services.ml import live
            return live
        except ImportError:
            logger.warning("ML_MODE=live but services/ml/live.py is missing; using stub")
    return stub


def load_models() -> None:
    impl = _impl()
    if impl is not stub:
        impl.load_models()


def predict_task_time(req: TaskTimeRequest) -> TaskTimePrediction:
    return _impl().predict_task_time(req)


def assess_safety(state: LiveState, weather: str) -> SafetyStatus:
    return _impl().assess_safety(state, weather)


def detect_anomalies(state: LiveState, operator_baseline: dict) -> list[AnomalyCreate]:
    # operator_baseline: {"idle_time_min": float, "fuel_rate_lph": float, "cycle_time_s": float}
    return _impl().detect_anomalies(state, operator_baseline)


def recommend_training(anomalies: list[Anomaly], incidents: list[Incident],
                       modules: list[Module]) -> list[tuple[str, str, str]]:
    # returns [(module_id, reason, priority)]
    return _impl().recommend_training(anomalies, incidents, modules)
