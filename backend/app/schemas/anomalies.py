from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AnomalyType, Severity


class AnomalyCreate(BaseModel):
    """An anomaly before it is stored (no ID yet). Returned by detect_anomalies()."""

    timestamp: datetime
    machine_id: str
    operator_id: str
    anomaly_type: AnomalyType
    observed_value: float
    baseline_value: float
    unit: str
    severity: Severity
    anomaly_score: float
    message: str
    recommended_module_id: str | None = None


class Anomaly(AnomalyCreate):
    anomaly_id: str
