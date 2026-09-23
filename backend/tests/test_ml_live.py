"""Live ML mode: each interface function with the trained artifacts, plus per-function stub fallback.

Calls the interface directly (no TestClient), so it needs the artifacts but not the database.
"""
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from app.config import settings
from app.schemas import AnomalyCreate, LiveState, Module, SafetyStatus, TaskTimePrediction, TaskTimeRequest
from app.services.ml import interface as ml
from app.services.ml import live


@pytest.fixture(autouse=True)
def live_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "ML_MODE", "live")
    ml.load_models()
    yield
    monkeypatch.undo()
    live.load_models()  # restore state from the real MODEL_DIR for other tests


def _request(**overrides) -> TaskTimeRequest:
    base = dict(task_type="Trenching", operator_id="OP1001", operator_skill="Intermediate",
                operator_experience_yrs=4, machine_age_yrs=4, weather="Rainy",
                ground_condition="Wet", temperature_c=27)
    return TaskTimeRequest(**(base | overrides))


def _state(**overrides) -> LiveState:
    base = dict(
        timestamp=datetime(2026, 9, 23, 10, 32, 14), machine_id="EXC001", operator_id="OP1001",
        task_id="T001", task_type="Earth Excavation", engine_on=True, engine_hours=1524.8,
        fuel_used_l=18.0, fuel_rate_lph=12.0, idle_time_min=30.0, operating_time_min=60.0,
        idle_pct=33.3, load_cycles=175, avg_payload_kg=1450, seatbelt_status="Fastened",
        proximity_m=18.5, people_in_zone=0, speed_kmh=2.1, health="Good", active_scenario="normal",
    )
    return LiveState(**(base | overrides))


BASELINE = {"idle_time_min": 34.0, "fuel_rate_lph": 12.0, "cycle_time_s": 24.0}


def test_mode_is_live():
    assert ml.ml_mode() == "live"


def test_predict_task_time_uses_model():
    rainy = ml.predict_task_time(_request())
    sunny = ml.predict_task_time(_request(weather="Sunny", ground_condition="Firm"))
    assert isinstance(rainy, TaskTimePrediction)
    assert rainy.model == "xgb_task_time_v1"
    assert rainy.lower_min < rainy.predicted_time_min < rainy.upper_min
    assert rainy.predicted_time_min > sunny.predicted_time_min + 5
    features = {f.feature for f in rainy.top_factors}
    assert {"weather", "ground_condition"} <= features
    assert 1 <= len(rainy.top_factors) <= 3


def test_assess_safety_levels():
    clear = ml.assess_safety(_state(), "Sunny")
    assert isinstance(clear, SafetyStatus)
    assert clear.risk_level == "LOW" and not clear.alert and clear.factors == []

    hazard = ml.assess_safety(_state(seatbelt_status="Unfastened", proximity_m=2.0, people_in_zone=1), "Rainy")
    assert hazard.risk_level == "HIGH" and hazard.alert and hazard.risk_score == 100
    assert hazard.machine_id == "EXC001" and hazard.evaluated_at == datetime(2026, 9, 23, 10, 32, 14)
    assert hazard.factors[0].label == "Person detected within 2.0 m of operating zone"
    assert "Fasten seatbelt" in hazard.recommended_action


@pytest.mark.parametrize("overrides,expected", [
    ({}, []),
    ({"operating_time_min": 30.0, "idle_time_min": 130.0, "load_cycles": 88,
      "fuel_used_l": 14.5, "fuel_rate_lph": 5.4}, ["excessive_idling"]),
    ({"fuel_used_l": 40.0, "fuel_rate_lph": 28.5}, ["fuel_spike"]),
    ({"seatbelt_status": "Unfastened", "people_in_zone": 1, "proximity_m": 2.2}, ["unsafe_operation"]),
])
def test_detect_anomalies(overrides: dict, expected: list[str]):
    found = ml.detect_anomalies(_state(**overrides), BASELINE)
    assert all(isinstance(a, AnomalyCreate) for a in found)
    assert [a.anomaly_type for a in found] == expected
    for a in found:
        assert a.message and 0 <= a.anomaly_score <= 1 and a.operator_id == "OP1001"


def test_recommend_training_returns_tuples():
    module = Module(module_id="TM03", title="Fuel-Efficient Operation", category="efficiency",
                    format="video", duration_min=12, description="...",
                    trigger_anomaly_type="excessive_idling")
    recs = ml.recommend_training([], [], [module])
    assert isinstance(recs, list)


def test_missing_artifact_falls_back_to_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    real = Path(settings.MODEL_DIR)
    for name in ("safety_meta.json", "anomaly_model.joblib", "anomaly_meta.json"):
        shutil.copy(real / name, tmp_path / name)  # task-time artifacts deliberately missing
    monkeypatch.setattr(settings, "MODEL_DIR", str(tmp_path))
    ml.load_models()

    pred = ml.predict_task_time(_request())
    assert isinstance(pred, TaskTimePrediction) and pred.model == "stub_task_time_v0"
    # the other functions keep using their live artifacts
    hazard = ml.assess_safety(_state(seatbelt_status="Unfastened", proximity_m=2.0, people_in_zone=1), "Rainy")
    assert "danger radius" in " ".join(f.label for f in hazard.factors)
    assert [a.anomaly_type for a in ml.detect_anomalies(_state(fuel_rate_lph=28.5), BASELINE)] == ["fuel_spike"]
