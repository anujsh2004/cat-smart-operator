"""Create all tables and load seed data.  Run from backend/:  python -m app.db.seed

Data sources, per file: DATA_DIR (Track A's generated CSVs) if present, else app/db/fixtures/.
If no sessions.csv exists anywhere, ~200 plausible historical sessions are generated here.
Idempotent: drops and recreates every table on each run.
"""
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Boolean, DateTime, Float, Integer, func, insert, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.session import SessionLocal, engine
from app.schemas import TaskTimeRequest
from app.services.ml import interface as ml

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TRAINING_JSON = Path(__file__).parent / "seed_training.json"

# Used only when generating fallback sessions
BASE_TIME_MIN = {"Earth Excavation": 60, "Trenching": 45, "Material Loading": 30, "Grading": 35, "Demolition": 90}
CYCLE_TIME_S = {"Earth Excavation": 21, "Trenching": 24, "Material Loading": 18, "Grading": 40, "Demolition": 30}
FUEL_RATE_LPH = {"Earth Excavation": 14.0, "Trenching": 12.5, "Material Loading": 13.0, "Grading": 11.0, "Demolition": 16.0}
SKILL_FACTOR = {"Beginner": 1.2, "Intermediate": 1.0, "Expert": 0.85}
WEATHER_FACTOR = {"Sunny": 1.0, "Cloudy": 1.0, "Windy": 1.05, "Foggy": 1.1, "Rainy": 1.15}
GROUND_FACTOR = {"Firm": 1.0, "Loose": 1.05, "Wet": 1.1, "Rocky": 1.12}
TEMP_RANGE = {"Sunny": (30, 38), "Cloudy": (24, 30), "Windy": (22, 28), "Rainy": (20, 26), "Foggy": (16, 22)}


# --- CSV loading -------------------------------------------------------------

def _csv_path(name: str) -> Path | None:
    for folder in (Path(settings.DATA_DIR), FIXTURES_DIR):
        path = folder / name
        if path.exists():
            return path
    return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return bool(value)


def _coerce(model: type[models.Base], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the model's columns and convert values to the column's Python type."""
    columns = model.__table__.columns
    out = []
    for row in rows:
        rec: dict[str, Any] = {}
        for col in columns:
            if col.name not in row:
                continue
            value = row[col.name]
            if value is None or (isinstance(value, float) and pd.isna(value)) or value == "":
                rec[col.name] = None
            elif isinstance(col.type, Boolean):
                rec[col.name] = _to_bool(value)
            elif isinstance(col.type, DateTime):
                rec[col.name] = pd.Timestamp(value).to_pydatetime()
            elif isinstance(col.type, Integer):
                rec[col.name] = int(float(value))
            elif isinstance(col.type, Float):
                rec[col.name] = float(value)
            else:
                rec[col.name] = str(value)
        out.append(rec)
    return out


def _read_csv(name: str) -> tuple[list[dict[str, Any]], str]:
    path = _csv_path(name)
    if path is None:
        return [], "missing"
    df = pd.read_csv(path)
    return df.to_dict("records"), str(path)


# --- Fallback session generator ----------------------------------------------

def _generate_sessions(operators: list[dict], machines: list[dict], n: int = 200) -> list[dict]:
    rng = random.Random(42)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    weights = [3 if o["operator_id"] == settings.DEFAULT_OPERATOR_ID else 1 for o in operators]
    rows = []
    for i in range(n):
        op = rng.choices(operators, weights=weights)[0]
        machine = rng.choice(machines)
        task_type = rng.choice(list(BASE_TIME_MIN))
        weather = rng.choices(list(WEATHER_FACTOR), weights=[5, 3, 1, 2, 1])[0]
        ground = "Wet" if weather == "Rainy" else rng.choice(["Firm", "Firm", "Loose", "Rocky"])
        est = BASE_TIME_MIN[task_type]
        actual = est * SKILL_FACTOR[op["skill_level"]] * WEATHER_FACTOR[weather] * GROUND_FACTOR[ground]
        actual *= rng.gauss(1.0, 0.08)
        idle_frac = rng.uniform(0.25, 0.4) if op["skill_level"] == "Beginner" else rng.uniform(0.18, 0.32)
        fuel_rate = FUEL_RATE_LPH[task_type] * rng.gauss(1.0, 0.07)
        cycle_s = CYCLE_TIME_S[task_type] * SKILL_FACTOR[op["skill_level"]] * rng.gauss(1.0, 0.06)

        anomaly_type = None
        roll = rng.random()
        if roll < 0.03:
            anomaly_type, idle_frac = "excessive_idling", rng.uniform(0.6, 0.75)
        elif roll < 0.05:
            anomaly_type, fuel_rate = "fuel_spike", fuel_rate * rng.uniform(1.9, 2.3)
        elif roll < 0.06:
            anomaly_type, cycle_s = "abnormal_cycle_time", cycle_s * rng.uniform(1.8, 2.2)

        operating = actual
        idle = operating * idle_frac
        working_s = (operating - idle) * 60
        seatbelt = "Unfastened" if rng.random() < 0.05 else "Fastened"
        people = 1 if rng.random() < 0.1 else 0
        proximity = rng.uniform(2.5, 6) if people else rng.uniform(8, 40)
        risk = (30 if seatbelt == "Unfastened" else 0) + 40 * people + (20 if proximity < 5 else 0)
        risk += 12 if weather in ("Rainy", "Foggy") else 0
        risk = min(100, risk)
        ts = now - timedelta(days=rng.randint(1, 21), hours=rng.randint(0, 9))
        ts = ts.replace(hour=rng.randint(8, 17))

        rows.append({
            "session_id": f"S{i + 1:05d}",
            "timestamp": ts,
            "machine_id": machine["machine_id"],
            "operator_id": op["operator_id"],
            "task_type": task_type,
            "operator_skill": op["skill_level"],
            "operator_experience_yrs": op["experience_yrs"],
            "machine_age_yrs": machine["age_yrs"],
            "engine_hours": round(machine["engine_hours"] - rng.uniform(5, 300), 1),
            "weather": weather,
            "ground_condition": ground,
            "temperature_c": round(rng.uniform(*TEMP_RANGE[weather]), 1),
            "fuel_used_l": round(fuel_rate * operating / 60, 2),
            "load_cycles": int(working_s / cycle_s),
            "avg_payload_kg": round(rng.uniform(1200, 1800), 0),
            "idle_time_min": round(idle, 1),
            "operating_time_min": round(operating, 1),
            "seatbelt_status": seatbelt,
            "proximity_min_m": round(proximity, 1),
            "people_in_zone": people,
            "estimated_time_min": est,
            "actual_time_min": round(actual, 1),
            "safety_risk_score": risk,
            "safety_alert_triggered": risk >= 70,
            "anomaly_flag": anomaly_type is not None,
            "anomaly_type": anomaly_type,
        })
    return rows


# --- Derived history (incidents + anomalies from the last 7 days of sessions) ---

def _operator_baselines(db: Session) -> dict[str, dict[str, float]]:
    s = models.SessionRecord
    rows = db.execute(
        select(
            s.operator_id,
            func.avg(s.idle_time_min),
            func.avg(s.fuel_used_l / (s.operating_time_min / 60.0)),
            func.avg(s.operating_time_min * 60.0 / func.nullif(s.load_cycles, 0)),
            func.avg(s.safety_risk_score),
        ).where(s.anomaly_flag.is_(False)).group_by(s.operator_id)
    ).all()
    return {
        op: {"idle_time_min": idle or 0, "fuel_rate_lph": fuel or 0, "cycle_time_s": cycle or 0, "risk": risk or 0}
        for op, idle, fuel, cycle, risk in rows
    }


def _derive_history(db: Session, modules: list[dict]) -> tuple[int, int]:
    rng = random.Random(7)
    since = datetime.now() - timedelta(days=7)
    s = models.SessionRecord
    recent = db.scalars(select(s).where(s.timestamp >= since).order_by(s.timestamp)).all()
    baselines = _operator_baselines(db)
    module_by_trigger = {m["trigger_anomaly_type"]: m["module_id"] for m in modules if m["trigger_anomaly_type"]}

    incidents, anomalies = [], []
    for row in recent:
        if row.safety_alert_triggered:
            event = "seatbelt_unfastened" if row.seatbelt_status == "Unfastened" and not row.people_in_zone \
                else "proximity_hazard"
            duration = rng.randint(8, 60)
            incidents.append({
                "incident_id": f"INC{1001 + len(incidents)}",
                "timestamp": row.timestamp,
                "machine_id": row.machine_id,
                "operator_id": row.operator_id,
                "event_type": event,
                "severity": "high",
                "risk_score": int(row.safety_risk_score),
                "details": {"proximity_m": row.proximity_min_m, "people_in_zone": row.people_in_zone,
                            "seatbelt_status": row.seatbelt_status},
                "action_taken": "Operator alerted",
                "status": "resolved",
                "resolved_at": row.timestamp + timedelta(seconds=duration),
                "duration_s": duration,
            })

        if row.anomaly_flag and row.anomaly_type:
            base = baselines.get(row.operator_id)
            if not base:
                continue
            if row.anomaly_type == "excessive_idling":
                obs, ref, unit = row.idle_time_min, base["idle_time_min"], "min"
                msg = f"Idle time {obs:.0f} min vs your usual {ref:.0f} min this session"
            elif row.anomaly_type == "fuel_spike":
                obs, ref, unit = row.fuel_used_l / (row.operating_time_min / 60), base["fuel_rate_lph"], "L/h"
                msg = f"Fuel rate {obs:.1f} L/h vs your usual {ref:.1f} L/h"
            elif row.anomaly_type == "abnormal_cycle_time":
                obs, ref, unit = row.operating_time_min * 60 / max(row.load_cycles, 1), base["cycle_time_s"], "s"
                msg = f"Cycle time {obs:.0f} s vs your usual {ref:.0f} s"
            else:  # unsafe_operation
                obs, ref, unit = row.safety_risk_score, base["risk"], "pts"
                msg = f"Safety risk score {obs:.0f} vs your usual {ref:.0f}"
            if not ref:
                continue
            ratio = obs / ref
            anomalies.append({
                "anomaly_id": f"ANM{len(anomalies) + 1:04d}",
                "timestamp": row.timestamp,
                "machine_id": row.machine_id,
                "operator_id": row.operator_id,
                "anomaly_type": row.anomaly_type,
                "observed_value": round(obs, 1),
                "baseline_value": round(ref, 1),
                "unit": unit,
                "severity": "high" if ratio >= 3 else "medium",
                "anomaly_score": round(min(1.0, abs(ratio - 1) / 3), 2),
                "message": msg,
                "recommended_module_id": module_by_trigger.get(row.anomaly_type),
            })

    if incidents:
        db.execute(insert(models.Incident), incidents)
    if anomalies:
        db.execute(insert(models.Anomaly), anomalies)
    return len(incidents), len(anomalies)


# --- Main --------------------------------------------------------------------

def _today_tasks(rows: list[dict], operators: dict[str, dict], machines: dict[str, dict],
                 temps: dict[str, float]) -> list[dict]:
    today = date.today()
    tasks = []
    for rec in _coerce(models.Task, rows):
        rec["scheduled_start"] = datetime.combine(today, rec["scheduled_start"].time())
        rec["status"] = "scheduled"
        rec["progress_pct"] = 0
        op, machine = operators[rec["operator_id"]], machines[rec["machine_id"]]
        pred = ml.predict_task_time(TaskTimeRequest(
            task_type=rec["task_type"], operator_id=op["operator_id"], operator_skill=op["skill_level"],
            operator_experience_yrs=op["experience_yrs"], machine_age_yrs=machine["age_yrs"],
            weather=rec["weather"], ground_condition=rec["ground_condition"],
            temperature_c=temps.get(rec["weather"], 28.0),
        ))
        rec["predicted_time_min"] = pred.predicted_time_min
        tasks.append(rec)

    tasks.sort(key=lambda t: t["scheduled_start"])
    if tasks:
        # The default operator's first task (T001) is in progress at startup
        first = next((t for t in tasks if t["operator_id"] == settings.DEFAULT_OPERATOR_ID), tasks[0])
        first["status"] = "in_progress"
        first["started_at"] = first["scheduled_start"]
    return tasks


def seed() -> dict[str, int]:
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)

    operator_rows, op_src = _read_csv("operators.csv")
    machine_rows, m_src = _read_csv("machines.csv")
    task_rows, t_src = _read_csv("tasks_today.csv")
    session_rows, s_src = _read_csv("sessions.csv")
    operators = _coerce(models.Operator, operator_rows)
    machines = _coerce(models.Machine, machine_rows)
    if not session_rows:
        session_rows, s_src = _generate_sessions(operators, machines), "generated in seed"
    sessions = _coerce(models.SessionRecord, session_rows)
    for label, src in (("operators", op_src), ("machines", m_src), ("tasks_today", t_src), ("sessions", s_src)):
        print(f"  {label:<12} <- {src}")

    modules = json.loads(TRAINING_JSON.read_text(encoding="utf-8"))

    with SessionLocal() as db:
        db.execute(insert(models.Operator), operators)
        db.execute(insert(models.Machine), machines)
        db.execute(insert(models.SessionRecord), sessions)

        # Average historical temperature per weather, used as the task-time prediction input
        temps = dict(db.execute(
            select(models.SessionRecord.weather, func.avg(models.SessionRecord.temperature_c))
            .group_by(models.SessionRecord.weather)
        ).all())
        tasks = _today_tasks(
            task_rows,
            {o["operator_id"]: o for o in operators},
            {m["machine_id"]: m for m in machines},
            {k: round(float(v), 1) for k, v in temps.items()},
        )
        db.execute(insert(models.Task), tasks)

        db.execute(insert(models.TrainingModule), [{k: v for k, v in m.items() if k != "quiz"} for m in modules])
        now = datetime.now()
        db.execute(insert(models.OperatorTraining), [
            {"operator_id": settings.DEFAULT_OPERATOR_ID, "module_id": "TM01", "status": "completed",
             "progress_pct": 100, "score": 100.0, "updated_at": now - timedelta(days=5)},
            {"operator_id": settings.DEFAULT_OPERATOR_ID, "module_id": "TM07", "status": "in_progress",
             "progress_pct": 40, "score": None, "updated_at": now - timedelta(days=1)},
        ])

        _derive_history(db, modules)
        db.commit()

        counts = {
            table.name: db.scalar(select(func.count()).select_from(table))
            for table in models.Base.metadata.sorted_tables
        }
    return counts


if __name__ == "__main__":
    print(f"Seeding {settings.DATABASE_URL.rsplit('@', 1)[-1]}")
    for table, count in seed().items():
        print(f"  {table:<20} {count:>6} rows")
