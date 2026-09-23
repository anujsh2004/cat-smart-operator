"""Smoke test: every GET endpoint once against the seeded DB, validated against the contract schemas."""
import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import app
from app.schemas import (
    AnalyticsSummary,
    Anomaly,
    Context,
    HealthResponse,
    Incident,
    LiveState,
    Module,
    Quiz,
    Recommendation,
    SafetyStatus,
    Task,
    TaskTimePrediction,
    TelemetryPoint,
    TrainingProgress,
)

GET_ENDPOINTS = [
    ("/api/health", HealthResponse),
    ("/api/context?operator_id=OP1001", Context),
    ("/api/tasks/today?operator_id=OP1001", list[Task]),
    ("/api/machines/EXC001/live", LiveState),
    ("/api/machines/EXC001/telemetry?minutes=60", list[TelemetryPoint]),
    ("/api/safety/status?machine_id=EXC001", SafetyStatus),
    ("/api/incidents?machine_id=EXC001&limit=20", list[Incident]),
    ("/api/anomalies?operator_id=OP1001&limit=20", list[Anomaly]),
    ("/api/analytics/summary?operator_id=OP1001&days=7", AnalyticsSummary),
    ("/api/training/modules", list[Module]),
    ("/api/training/modules/TM01/quiz", Quiz),
    ("/api/training/recommendations?operator_id=OP1001", list[Recommendation]),
    ("/api/training/progress?operator_id=OP1001", list[TrainingProgress]),
]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("path,schema", GET_ENDPOINTS)
def test_get_endpoint(client: TestClient, path: str, schema: type):
    res = client.get(path)
    assert res.status_code == 200, res.text
    TypeAdapter(schema).validate_python(res.json())


def test_tasks_today_seeded(client: TestClient):
    tasks = client.get("/api/tasks/today?operator_id=OP1001").json()
    assert [t["task_id"] for t in tasks][:1] == ["T001"]


def test_predict_task_time(client: TestClient):
    body = {
        "task_type": "Trenching", "operator_id": "OP1001", "operator_skill": "Intermediate",
        "operator_experience_yrs": 4, "machine_age_yrs": 4,
        "weather": "Rainy", "ground_condition": "Wet", "temperature_c": 27,
    }
    res = client.post("/api/predict/task-time", json=body)
    assert res.status_code == 200, res.text
    TaskTimePrediction.model_validate(res.json())


def test_unknown_id_404(client: TestClient):
    res = client.get("/api/machines/NOPE/live")
    assert res.status_code == 404
    assert "detail" in res.json()


def test_sim_not_ready(client: TestClient):
    res = client.post("/api/sim/scenario", json={"machine_id": "EXC001", "scenario": "normal"})
    assert res.status_code == 501
