"""SQLAlchemy tables from docs/ARCHITECTURE.md §4.1 (sessions columns from §4.2)."""
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSONB on Postgres, plain JSON on the SQLite emergency fallback
JsonType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    skill_level: Mapped[str] = mapped_column(String)
    experience_yrs: Mapped[int] = mapped_column(Integer)
    shift: Mapped[str] = mapped_column(String)


class Machine(Base):
    __tablename__ = "machines"

    machine_id: Mapped[str] = mapped_column(String, primary_key=True)
    model: Mapped[str] = mapped_column(String)
    machine_type: Mapped[str] = mapped_column(String)
    age_yrs: Mapped[int] = mapped_column(Integer)
    engine_hours: Mapped[float] = mapped_column(Float)


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String, primary_key=True)
    operator_id: Mapped[str] = mapped_column(ForeignKey("operators.operator_id"))
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"))
    task_type: Mapped[str] = mapped_column(String)
    site_zone: Mapped[str] = mapped_column(String)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime)
    weather: Mapped[str] = mapped_column(String)
    ground_condition: Mapped[str] = mapped_column(String)
    estimated_time_min: Mapped[float] = mapped_column(Float)
    predicted_time_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_time_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, default="scheduled")
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SessionRecord(Base):
    """Historical operating session (ML training set). Named to avoid clashing with ORM Session."""

    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    task_type: Mapped[str] = mapped_column(String)
    operator_skill: Mapped[str] = mapped_column(String)
    operator_experience_yrs: Mapped[int] = mapped_column(Integer)
    machine_age_yrs: Mapped[int] = mapped_column(Integer)
    engine_hours: Mapped[float] = mapped_column(Float)
    weather: Mapped[str] = mapped_column(String)
    ground_condition: Mapped[str] = mapped_column(String)
    temperature_c: Mapped[float] = mapped_column(Float)
    fuel_used_l: Mapped[float] = mapped_column(Float)
    load_cycles: Mapped[int] = mapped_column(Integer)
    avg_payload_kg: Mapped[float] = mapped_column(Float)
    idle_time_min: Mapped[float] = mapped_column(Float)
    operating_time_min: Mapped[float] = mapped_column(Float)
    seatbelt_status: Mapped[str] = mapped_column(String)
    proximity_min_m: Mapped[float] = mapped_column(Float)
    people_in_zone: Mapped[int] = mapped_column(Integer)
    estimated_time_min: Mapped[float] = mapped_column(Float)
    actual_time_min: Mapped[float] = mapped_column(Float)
    safety_risk_score: Mapped[float] = mapped_column(Float)
    safety_alert_triggered: Mapped[bool] = mapped_column(Boolean)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean)
    anomaly_type: Mapped[str | None] = mapped_column(String, nullable=True)


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String)
    task_id: Mapped[str | None] = mapped_column(String, nullable=True)
    engine_hours: Mapped[float] = mapped_column(Float)
    fuel_used_l: Mapped[float] = mapped_column(Float)
    fuel_rate_lph: Mapped[float] = mapped_column(Float)
    load_cycles: Mapped[int] = mapped_column(Integer)
    idle_time_min: Mapped[float] = mapped_column(Float)
    operating_time_min: Mapped[float] = mapped_column(Float)
    avg_payload_kg: Mapped[float] = mapped_column(Float)
    seatbelt_status: Mapped[str] = mapped_column(String)
    proximity_m: Mapped[float] = mapped_column(Float)
    people_in_zone: Mapped[int] = mapped_column(Integer)
    speed_kmh: Mapped[float] = mapped_column(Float)


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Anomaly(Base):
    __tablename__ = "anomalies"

    anomaly_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    machine_id: Mapped[str] = mapped_column(String, index=True)
    operator_id: Mapped[str] = mapped_column(String, index=True)
    anomaly_type: Mapped[str] = mapped_column(String)
    observed_value: Mapped[float] = mapped_column(Float)
    baseline_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    anomaly_score: Mapped[float] = mapped_column(Float)
    message: Mapped[str] = mapped_column(Text)
    recommended_module_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str | None] = mapped_column(String, nullable=True)
    model_name: Mapped[str] = mapped_column(String)
    predicted_value: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TrainingModule(Base):
    __tablename__ = "training_modules"

    module_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    format: Mapped[str] = mapped_column(String)
    duration_min: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    content_url: Mapped[str | None] = mapped_column(String, nullable=True)
    trigger_anomaly_type: Mapped[str | None] = mapped_column(String, nullable=True)


class OperatorTraining(Base):
    __tablename__ = "operator_training"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operator_id: Mapped[str] = mapped_column(ForeignKey("operators.operator_id"))
    module_id: Mapped[str] = mapped_column(ForeignKey("training_modules.module_id"))
    status: Mapped[str] = mapped_column(String, default="not_started")
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
