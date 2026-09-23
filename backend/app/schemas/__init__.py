"""Pydantic models mirroring the frozen API contract (docs/ARCHITECTURE.md §5)."""
from app.schemas.analytics import AnalyticsDay, AnalyticsSummary, AnalyticsTotals, FleetAvg
from app.schemas.anomalies import Anomaly, AnomalyCreate
from app.schemas.common import (
    AnomalyType,
    EventType,
    GroundCondition,
    Health,
    IncidentStatus,
    MachineType,
    MLMode,
    ModuleCategory,
    ModuleFormat,
    Priority,
    RiskLevel,
    Scenario,
    SeatbeltStatus,
    Severity,
    ShiftName,
    SkillLevel,
    TaskStatus,
    TaskType,
    TrainingStatus,
    Weather,
)
from app.schemas.context import Context, HealthResponse, Machine, Operator, ShiftInfo, WeatherInfo
from app.schemas.incidents import Incident, IncidentCreate, IncidentResolve
from app.schemas.live import LiveState, TaskMetric, TelemetryPoint
from app.schemas.prediction import PredictionFactor, TaskTimePrediction, TaskTimeRequest
from app.schemas.safety import SafetyFactor, SafetyStatus
from app.schemas.sim import ResetRequest, ScenarioRequest
from app.schemas.tasks import Task
from app.schemas.training import (
    Module,
    Quiz,
    QuizQuestion,
    Recommendation,
    TrainingProgress,
    TrainingProgressCreate,
)
