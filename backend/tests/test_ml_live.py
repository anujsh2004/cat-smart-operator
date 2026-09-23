"""Live ML mode: each interface function with the trained artifacts, plus per-function stub fallback.

Calls the interface directly (no TestClient), so it needs the artifacts but not the database.
"""
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.config import settings
from app.schemas import (
    Anomaly, AnomalyCreate, Incident, LiveState, Module, SafetyStatus, TaskTimePrediction, TaskTimeRequest,
)
from app.services.ml import interface as ml
from app.services.ml import live, live_training


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


def test_normal_sim_state_raises_nothing():
    # Real sim values: cumulative operating time includes idle, so cycles look slow; the live fuel
    # rate is a working rate. The instantaneous cycle metric and backend baseline keep this quiet.
    state = _state(operating_time_min=25.2, idle_time_min=15.6, fuel_used_l=8.2, fuel_rate_lph=19.6,
                   load_cycles=28, task_metrics=[{"key": "cycle_time", "label": "Cycle time", "value": 21, "unit": "s"}])
    assert ml.detect_anomalies(state, {"idle_time_min": 38.0, "fuel_rate_lph": 18.6, "cycle_time_s": 21.0}) == []
    spike = state.model_copy(update={"fuel_rate_lph": 19.6 * 2.2})
    assert [a.anomaly_type for a in ml.detect_anomalies(spike, {"fuel_rate_lph": 18.6})] == ["fuel_spike"]


SEED_TRAINING = Path(__file__).resolve().parents[1] / "app" / "db" / "seed_training.json"
MODULES = [Module.model_validate(m) for m in json.loads(SEED_TRAINING.read_text(encoding="utf-8"))]


def _anomaly(anomaly_type: str, minutes_ago: int, severity: str = "medium", n: int = 1) -> Anomaly:
    return Anomaly(
        anomaly_id=f"ANM{n:04d}", timestamp=datetime.now().replace(microsecond=0) - timedelta(minutes=minutes_ago),
        machine_id="EXC001", operator_id="OP1001", anomaly_type=anomaly_type, observed_value=75,
        baseline_value=24, unit="min", severity=severity, anomaly_score=0.7, message="...",
    )


def _incident(event_type: str, ts: datetime, weather: str = "Sunny", severity: str = "high") -> Incident:
    return Incident(
        incident_id="INC1042", timestamp=ts, machine_id="EXC001", operator_id="OP1001",
        event_type=event_type, severity=severity, risk_score=82,
        details={"proximity_m": 4.2, "people_in_zone": 1, "weather": weather}, status="resolved",
    )


def test_recommend_excessive_idle_gives_fuel_efficiency():
    recs = ml.recommend_training([_anomaly("excessive_idling", 5)], [], MODULES)
    assert recs[0][0] == "TM03" and recs[0][2] == "medium"
    assert recs[0][1].startswith("Excessive idling at ") and recs[0][1].endswith("on EXC001")


def test_recommend_reason_leads_with_today():
    recent = _anomaly("excessive_idling", 1)
    older = [_anomaly("excessive_idling", 60 * 24 * d, n=d + 1) for d in (1, 2)]
    reason = ml.recommend_training([recent, *older], [], MODULES)[0][1]
    assert reason == f"Excessive idling at {recent.timestamp:%H:%M} on EXC001 (3 in the last 3 days)"


def test_recommend_repeats_and_high_severity_are_high_priority():
    today = datetime.now().replace(hour=10, minute=32, second=0, microsecond=0)
    recs = ml.recommend_training(
        [_anomaly("excessive_idling", 5, n=1), _anomaly("excessive_idling", 20, n=2)],
        [_incident("proximity_hazard", today)],
        MODULES,
    )
    by_id = {m: (reason, p) for m, reason, p in recs}
    assert by_id["TM03"] == ("Triggered by 2 excessive-idling alerts today", "high")
    assert by_id["TM02"] == ("Proximity hazard at 10:32 on EXC001", "high")
    assert [p for _, _, p in recs] == sorted((p for _, _, p in recs), key=["high", "medium", "low"].index)


def test_recommend_mapping_table_weather_dedupe_and_cap():
    now = datetime.now().replace(microsecond=0)
    recs = ml.recommend_training(
        [_anomaly("fuel_spike", 3), _anomaly("excessive_idling", 4, n=2), _anomaly("abnormal_cycle_time", 6, n=3)],
        [_incident("manual_report", now, severity="low"),
         _incident("seatbelt_unfastened", now - timedelta(minutes=1), weather="Rainy")],
        MODULES,
    )
    ids = [m for m, _, _ in recs]
    assert len(ids) == len(set(ids)) <= 4                   # de-duplicated, capped
    assert ids.count("TM03") == 1                           # idling + fuel spike share one module
    all_recs = live_training.recommend(
        [], [_incident("manual_report", now, severity="low"),
             _incident("proximity_hazard", now, weather="Rainy")], MODULES)
    titles = {m: r for m, r, _ in all_recs}
    assert "TM05" in titles                                 # manual_report -> Incident Response Basics
    assert "TM06" in titles and "in rain" in titles["TM06"]  # Rainy incident -> Wet-Weather Operation


def test_recommend_fills_with_low_priority_weakest_area():
    recs = ml.recommend_training([_anomaly("unsafe_operation", 5, severity="high")], [], MODULES)
    assert recs[0][0] == "TM05" and recs[0][2] == "high"
    low = [r for r in recs if r[2] == "low"]
    assert 1 <= len(recs) <= 3
    assert all("above the fleet" in reason for _, reason, _ in low)
    assert low, "OP1001 idles more than the fleet, so an upskilling pick is expected"


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
