from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Anomaly, LiveState, Module, SafetyStatus, TaskTimePrediction, TaskTimeRequest
from app.services.ml import interface as ml


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "db": True, "ml_mode": "stub"}


def _state(**overrides) -> LiveState:
    base = dict(
        timestamp=datetime(2026, 9, 23, 10, 32, 14), machine_id="EXC001", operator_id="OP1001",
        task_id="T001", task_type="Earth Excavation", engine_on=True, engine_hours=1524.8,
        fuel_used_l=38.2, fuel_rate_lph=14.1, idle_time_min=22.0, operating_time_min=95.0,
        idle_pct=23.2, load_cycles=118, avg_payload_kg=1450, seatbelt_status="Fastened",
        proximity_m=18.5, people_in_zone=0, speed_kmh=2.1, health="Good", active_scenario="normal",
    )
    return LiveState(**(base | overrides))


def test_stub_predict_task_time():
    req = TaskTimeRequest(
        task_type="Trenching", operator_id="OP1001", operator_skill="Intermediate",
        operator_experience_yrs=4, machine_age_yrs=4, weather="Rainy",
        ground_condition="Wet", temperature_c=27,
    )
    pred = ml.predict_task_time(req)
    assert isinstance(pred, TaskTimePrediction)
    assert pred.lower_min < pred.predicted_time_min < pred.upper_min


def test_stub_safety_levels():
    assert ml.assess_safety(_state(), "Sunny").risk_level == "LOW"
    hazard = ml.assess_safety(
        _state(seatbelt_status="Unfastened", proximity_m=4.2, people_in_zone=1), "Rainy"
    )
    assert isinstance(hazard, SafetyStatus)
    assert hazard.risk_level == "HIGH" and hazard.alert and hazard.risk_score == 100
    assert all(f.label for f in hazard.factors)


def test_stub_anomalies_and_training():
    baseline = {"idle_time_min": 24.0, "fuel_rate_lph": 14.0, "cycle_time_s": 21.0}
    found = ml.detect_anomalies(_state(idle_time_min=75.0), baseline)
    assert [a.anomaly_type for a in found] == ["excessive_idling"]

    module = Module(
        module_id="TM03", title="Fuel-Efficient Operation", category="efficiency", format="video",
        duration_min=12, description="...", trigger_anomaly_type="excessive_idling",
    )
    anomalies = [a.model_dump() | {"anomaly_id": "ANM0001"} for a in found]
    recs = ml.recommend_training([Anomaly(**a) for a in anomalies], [], [module])
    assert recs and recs[0][0] == "TM03"
