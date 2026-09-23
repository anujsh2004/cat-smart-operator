"""Live ML implementation (Track A): trained models from settings.MODEL_DIR.

Each function falls back to stub.py on its own when its artifact is missing or a call fails,
so the app and the sim loop never crash because of ML.
"""
import json
import logging
from pathlib import Path
from typing import Any, Callable, TypeVar

import joblib

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
from app.services.ml import live_anomaly, live_safety, live_task_time, live_training, stub

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Module-level state, filled once by load_models(). None = not available -> stub.
_task_time: tuple[Any, dict] | None = None
_safety: dict | None = None
_anomaly: tuple[Any, dict] | None = None
_loaded = False
_warned: set[str] = set()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _try_load(name: str, loader: Callable[[], T], files: list[Path]) -> T | None:
    try:
        value = loader()
        logger.info("ML live: loaded %s (%s)", name, ", ".join(f.name for f in files))
        return value
    except Exception as exc:
        logger.warning("ML live: could not load %s from %s (%s); %s will use the stub",
                       name, files[0].parent, exc, name)
        return None


def load_models() -> None:
    """Load every artifact independently; a missing one only disables its own function."""
    global _task_time, _safety, _anomaly, _loaded
    model_dir = Path(settings.MODEL_DIR)

    tt_model, tt_meta = model_dir / "task_time_model.joblib", model_dir / "task_time_meta.json"
    _task_time = _try_load("predict_task_time",
                           lambda: (joblib.load(tt_model), _read_json(tt_meta)), [tt_model, tt_meta])

    sf_meta = model_dir / "safety_meta.json"
    _safety = _try_load("assess_safety", lambda: _read_json(sf_meta), [sf_meta])

    an_model, an_meta = model_dir / "anomaly_model.joblib", model_dir / "anomaly_meta.json"
    _anomaly = _try_load("detect_anomalies",
                         lambda: (joblib.load(an_model), _read_json(an_meta)), [an_model, an_meta])
    _loaded = True


def _ensure_loaded() -> None:
    if not _loaded:
        load_models()


def _fallback(name: str, exc: Exception | None = None) -> None:
    """Log once per function so the sim loop doesn't flood the log."""
    if name not in _warned:
        _warned.add(name)
        if exc is not None:
            logger.exception("ML live: %s failed; using stub", name, exc_info=exc)
        else:
            logger.warning("ML live: %s has no artifact; using stub", name)


def predict_task_time(req: TaskTimeRequest) -> TaskTimePrediction:
    _ensure_loaded()
    if _task_time is None:
        _fallback("predict_task_time")
        return stub.predict_task_time(req)
    try:
        model, meta = _task_time
        return TaskTimePrediction(**live_task_time.predict(model, meta, req.model_dump()))
    except Exception as exc:
        _fallback("predict_task_time", exc)
        return stub.predict_task_time(req)


def assess_safety(state: LiveState, weather: str) -> SafetyStatus:
    _ensure_loaded()
    if _safety is None:
        _fallback("assess_safety")
        return stub.assess_safety(state, weather)
    try:
        result = live_safety.assess(state.model_dump(), weather,
                                    _safety["rule_weights"], _safety.get("base_score", 10))
        return SafetyStatus(machine_id=state.machine_id, evaluated_at=state.timestamp, **result)
    except Exception as exc:
        _fallback("assess_safety", exc)
        return stub.assess_safety(state, weather)


def detect_anomalies(state: LiveState, operator_baseline: dict) -> list[AnomalyCreate]:
    # operator_baseline (from the backend) is only a fallback; the A5 per-operator,
    # per-task baselines in anomaly_meta.json are preferred.
    _ensure_loaded()
    if _anomaly is None:
        _fallback("detect_anomalies")
        return stub.detect_anomalies(state, operator_baseline)
    try:
        model, meta = _anomaly
        data = state.model_dump()
        score = live_anomaly.model_score(model, meta, data)
        found = live_anomaly.detect(meta, data, score, operator_baseline)
        return [
            AnomalyCreate(**a, recommended_module_id=stub.ANOMALY_MODULE.get(a["anomaly_type"]))
            for a in found
        ]
    except Exception as exc:
        _fallback("detect_anomalies", exc)
        return stub.detect_anomalies(state, operator_baseline)


def recommend_training(anomalies: list[Anomaly], incidents: list[Incident],
                       modules: list[Module]) -> list[tuple[str, str, str]]:
    # Works without artifacts; anomaly_meta (if loaded) adds the "weakest area" upskilling picks.
    _ensure_loaded()
    try:
        meta = _anomaly[1] if _anomaly is not None else None
        return live_training.recommend(anomalies, incidents, modules, meta)
    except Exception as exc:
        _fallback("recommend_training", exc)
        return stub.recommend_training(anomalies, incidents, modules)
