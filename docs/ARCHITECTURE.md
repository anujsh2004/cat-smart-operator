# Architecture — Smart Operator Assistant

## 1. System overview

```
                 ┌──────────────────────────────────────────┐
                 │   Track A: data/generate.py              │
                 │   synthetic CSVs (20k historical sessions)│
                 └───────────────┬──────────────────────────┘
                                 │ trains                     │ seeds
                                 ▼                            ▼
┌───────────────────────┐  ┌──────────────────────────────────────────────┐
│ Track A: ml/          │  │ PostgreSQL (Docker)                          │
│ train_*.py → joblib   │  │ operators, machines, tasks, telemetry,       │
│ ml/artifacts/         │  │ incidents, anomalies, predictions, training  │
└──────────┬────────────┘  └──────────────────┬───────────────────────────┘
           │ loaded at startup                │
           ▼                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FastAPI backend                                                        │
│                                                                        │
│  routers/ (Track B, thin HTTP)  ──calls──►  services/ml/interface.py   │
│        │                                     (Track A: task-time,      │
│        │                                      safety, anomaly,         │
│        ▼                                      training recommender)    │
│  sim/engine.py (Track B)                                               │
│  in-memory live state per machine, ticks every 2 s,                    │
│  applies demo scenarios, calls assess_safety + detect_anomalies,       │
│  auto-creates/resolves incidents, persists telemetry every 5 ticks     │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ REST/JSON (polled every 2–5 s)
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│ React + Vite frontend (Track B)                                        │
│ Dashboard · Tasks & Estimator · Safety & Incidents · Machine Insights  │
│ · Training Hub · Demo Control Panel                                    │
└────────────────────────────────────────────────────────────────────────┘
```

**Key design decision: the split between routers and services.** Track B owns every HTTP route. Track A owns the functions those routes call for intelligence (`services/ml/interface.py`). The only coupling is the Python function signatures in §6 and the Pydantic schemas in `backend/app/schemas/`. That means neither person edits the other's files.

## 2. Stack

| Layer | Tech | Why |
|---|---|---|
| DB | PostgreSQL 16 (Docker) | Real relational store, JSONB for incident details |
| API | FastAPI + Pydantic v2 | Auto Swagger docs at `/docs`, typed contract |
| ORM | SQLAlchemy 2.0 sync + psycopg | Simple, no async complexity |
| ML | scikit-learn, XGBoost, joblib | Fast to train, explainable, easy to serve |
| UI | React + Vite + TS + Tailwind | Fast dev loop, typed API |
| Charts | Recharts | Simple declarative charts |
| Data fetching | TanStack Query | Polling, caching, loading/error states for free |
| Infra | Docker Compose | One command to run the demo |

## 3. Environment variables (`.env`)

```
POSTGRES_USER=soa
POSTGRES_PASSWORD=soa_dev_pw
POSTGRES_DB=soa
DATABASE_URL=postgresql+psycopg://soa:soa_dev_pw@localhost:5433/soa
MODEL_DIR=../ml/artifacts
DATA_DIR=../data/generated
ML_MODE=stub                 # stub | live   (live = load joblib artifacts)
SIM_TICK_SECONDS=2
CORS_ORIGINS=http://localhost:5173
DEFAULT_OPERATOR_ID=OP1001
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCKS=false
```

Postgres is exposed on host port **5433** to avoid clashing with a local Postgres install. Inside Docker the backend uses `db:5432`.

## 4. Data model

### 4.1 PostgreSQL tables

| Table | Columns |
|---|---|
| `operators` | `operator_id` PK text (`OP1001`), `name`, `skill_level` (Beginner/Intermediate/Expert), `experience_yrs` int, `shift` (Morning/Evening/Night) |
| `machines` | `machine_id` PK text (`EXC001`), `model` text, `machine_type` (Excavator/Wheel Loader/Dozer/Motor Grader), `age_yrs` int, `engine_hours` float |
| `tasks` | `task_id` PK text (`T001`), `operator_id` FK, `machine_id` FK, `task_type`, `site_zone`, `scheduled_start` timestamp, `weather`, `ground_condition`, `estimated_time_min` float, `predicted_time_min` float null, `actual_time_min` float null, `status` (scheduled/in_progress/completed), `progress_pct` int, `started_at` null, `completed_at` null |
| `sessions` | Historical operating sessions (the ML training set, loaded from `sessions.csv`); columns exactly as §4.2 |
| `telemetry_readings` | `id` serial, `timestamp`, `machine_id`, `operator_id`, `task_id` null, `engine_hours`, `fuel_used_l`, `fuel_rate_lph`, `load_cycles`, `idle_time_min`, `operating_time_min`, `avg_payload_kg`, `seatbelt_status`, `proximity_m`, `people_in_zone` int, `speed_kmh` |
| `incidents` | `incident_id` PK text (`INC1042`), `timestamp`, `machine_id`, `operator_id`, `event_type`, `severity`, `risk_score` null, `details` JSONB, `action_taken`, `status` (open/resolved), `resolved_at` null, `duration_s` int null |
| `anomalies` | `anomaly_id` PK text (`ANM0001`), `timestamp`, `machine_id`, `operator_id`, `anomaly_type`, `observed_value`, `baseline_value`, `unit`, `severity`, `anomaly_score`, `message`, `recommended_module_id` null |
| `predictions` | `id` serial, `task_id` null, `model_name`, `predicted_value`, `features` JSONB, `created_at` |
| `training_modules` | `module_id` PK text (`TM01`), `title`, `category` (safety/efficiency/technique/incident_response), `format` (video/quiz/simulation/instructor), `duration_min`, `description`, `content_url` null, `trigger_anomaly_type` null |
| `operator_training` | `id` serial, `operator_id`, `module_id`, `status` (not_started/in_progress/completed), `progress_pct`, `score` null, `updated_at` |

### 4.2 CSV hand-off contract (Track A → Track B seed script)

Track A writes these to `data/generated/`. Column names are exact.

**`operators.csv`**: `operator_id,name,skill_level,experience_yrs,shift`

**`machines.csv`**: `machine_id,model,machine_type,age_yrs,engine_hours`

**`sessions.csv`** (historical, ~20k rows, one row per completed task session):
```
session_id,timestamp,machine_id,operator_id,task_type,operator_skill,operator_experience_yrs,
machine_age_yrs,engine_hours,weather,ground_condition,temperature_c,
fuel_used_l,load_cycles,avg_payload_kg,idle_time_min,operating_time_min,
seatbelt_status,proximity_min_m,people_in_zone,
estimated_time_min,actual_time_min,
safety_risk_score,safety_alert_triggered,anomaly_flag,anomaly_type
```

**`tasks_today.csv`**: `task_id,operator_id,machine_id,task_type,site_zone,scheduled_start,weather,ground_condition,estimated_time_min`

Until Track A delivers, `backend/app/db/fixtures/` holds a tiny hand-made version built from the organisers' sample (tasks T001–T005, EXC001, OP1001), so Track B is never blocked.

### 4.3 Enums (use these exact strings everywhere)

- `task_type`: `Earth Excavation`, `Trenching`, `Material Loading`, `Grading`, `Demolition`
- `weather`: `Sunny`, `Cloudy`, `Windy`, `Rainy`, `Foggy`
- `ground_condition`: `Firm`, `Loose`, `Wet`, `Rocky`
- `skill_level`: `Beginner`, `Intermediate`, `Expert`
- `seatbelt_status`: `Fastened`, `Unfastened`
- `risk_level`: `LOW` (<40), `MEDIUM` (40–69), `HIGH` (≥70)
- `severity`: `low`, `medium`, `high`
- `event_type`: `proximity_hazard`, `seatbelt_unfastened`, `excessive_idling`, `fuel_spike`, `abnormal_cycle_time`, `unsafe_operation`, `manual_report`
- `anomaly_type`: `excessive_idling`, `fuel_spike`, `abnormal_cycle_time`, `unsafe_operation`
- `health`: `Good`, `Attention`, `Critical`
- `scenario`: `normal`, `seatbelt_off`, `proximity_hazard`, `excessive_idle`, `fuel_spike`, `rain`

## 5. API contract (FROZEN)

Base URL: `/api`. All timestamps ISO-8601 strings. All responses are plain JSON (no envelope). Errors: `{"detail": "message"}` with a proper HTTP status.

### 5.1 System

**`GET /api/health`** → `{"status": "ok", "db": true, "ml_mode": "stub" | "live"}`

**`GET /api/context?operator_id=OP1001`**: everything the top bar needs
```json
{
  "operator": {"operator_id": "OP1001", "name": "Ravi Kumar", "skill_level": "Intermediate", "experience_yrs": 4, "shift": "Morning"},
  "machine": {"machine_id": "EXC001", "model": "320 GC", "machine_type": "Excavator", "age_yrs": 2, "engine_hours": 1523.5},
  "weather": {"condition": "Sunny", "temperature_c": 31, "visibility": "Good"},
  "ground_condition": "Firm",
  "shift": {"name": "Morning", "start": "08:00", "end": "16:00"}
}
```

### 5.2 Tasks

**`GET /api/tasks/today?operator_id=OP1001`** → `Task[]`

```json
{
  "task_id": "T001", "task_type": "Earth Excavation", "machine_id": "EXC001", "operator_id": "OP1001",
  "site_zone": "Pit B", "scheduled_start": "2026-09-23T08:00:00",
  "status": "in_progress", "progress_pct": 45,
  "weather": "Sunny", "ground_condition": "Firm",
  "estimated_time_min": 60, "predicted_time_min": 57.4, "actual_time_min": null
}
```

**`POST /api/tasks/{task_id}/start`** → `Task` (sets `in_progress`, points the sim engine at this task)

**`POST /api/tasks/{task_id}/complete`** → `Task`

### 5.3 Live machine state (from the simulation engine)

**`GET /api/machines/{machine_id}/live`** → `LiveState`
```json
{
  "timestamp": "2026-09-23T10:32:14", "machine_id": "EXC001", "operator_id": "OP1001",
  "task_id": "T001", "task_type": "Earth Excavation", "engine_on": true,
  "engine_hours": 1524.8, "fuel_used_l": 38.2, "fuel_rate_lph": 14.1,
  "idle_time_min": 22.0, "operating_time_min": 95.0, "idle_pct": 23.2,
  "load_cycles": 118, "avg_payload_kg": 1450,
  "seatbelt_status": "Fastened", "proximity_m": 18.5, "people_in_zone": 0, "speed_kmh": 2.1,
  "health": "Good",
  "active_scenario": "normal",
  "task_metrics": [
    {"key": "bucket_cycles", "label": "Bucket cycles", "value": 118, "unit": ""},
    {"key": "avg_bucket_load", "label": "Avg bucket load", "value": 1.45, "unit": "t"},
    {"key": "dig_depth", "label": "Excavation depth", "value": 2.8, "unit": "m"},
    {"key": "cycle_time", "label": "Cycle time", "value": 21, "unit": "s"}
  ]
}
```

`task_metrics` per task type:
- Earth Excavation / Trenching: bucket cycles, avg bucket load (t), depth (m), cycle time (s)
- Material Loading: load cycles, avg payload (t), payload utilisation (%), loading cycle time (s)
- Grading: passes completed, grade accuracy (%), surface deviation (cm), travel speed (km/h)
- Demolition: impact cycles, material removed (t), proximity risk (%), structural alerts (count)

**`GET /api/machines/{machine_id}/telemetry?minutes=60`** → `TelemetryPoint[]` (for sparkline charts)
```json
[{"timestamp": "...", "fuel_rate_lph": 13.8, "idle_pct": 21.0, "load_cycles": 110, "proximity_m": 20.1}]
```

### 5.4 Safety

**`GET /api/safety/status?machine_id=EXC001`** → `SafetyStatus`
```json
{
  "machine_id": "EXC001", "evaluated_at": "2026-09-23T10:32:14",
  "risk_score": 82, "risk_level": "HIGH", "alert": true,
  "seatbelt_status": "Unfastened", "proximity_m": 4.2, "people_in_zone": 1,
  "factors": [
    {"factor": "people_in_zone", "label": "Person detected within 4.2 m of operating zone", "contribution": 40},
    {"factor": "seatbelt", "label": "Seatbelt unfastened while engine running", "contribution": 30},
    {"factor": "weather", "label": "Rain reduces traction and visibility", "contribution": 12}
  ],
  "recommended_action": "Stop swing movement, fasten seatbelt, and sound horn before resuming."
}
```

### 5.5 Incidents

**`GET /api/incidents?machine_id=&operator_id=&status=&limit=20`** → `Incident[]` (newest first)
```json
{
  "incident_id": "INC1042", "timestamp": "2026-09-23T10:32:14",
  "machine_id": "EXC001", "operator_id": "OP1001",
  "event_type": "proximity_hazard", "severity": "high", "risk_score": 82,
  "details": {"proximity_m": 4.2, "people_in_zone": 1},
  "action_taken": "Operator alerted", "status": "resolved",
  "resolved_at": "2026-09-23T10:32:25", "duration_s": 11
}
```

**`POST /api/incidents`**, body `{"machine_id", "operator_id", "event_type": "manual_report", "severity", "description"}` → `Incident`

**`PATCH /api/incidents/{incident_id}/resolve`**, body `{"resolution": "Hazard cleared"}` → `Incident`

### 5.6 Task-time prediction

**`POST /api/predict/task-time`**
```json
{
  "task_type": "Trenching", "operator_id": "OP1001", "operator_skill": "Intermediate",
  "operator_experience_yrs": 4, "machine_age_yrs": 4,
  "weather": "Rainy", "ground_condition": "Wet", "temperature_c": 27
}
```
→ `TaskTimePrediction`
```json
{
  "predicted_time_min": 51.8, "lower_min": 46.0, "upper_min": 57.5,
  "historical_avg_min": 47.0, "model": "xgb_task_time_v1",
  "top_factors": [
    {"feature": "weather", "label": "Rainy weather", "impact_min": 6.2},
    {"feature": "ground_condition", "label": "Wet ground", "impact_min": 3.1},
    {"feature": "operator_skill", "label": "Intermediate operator", "impact_min": -0.8}
  ]
}
```

### 5.7 Anomalies

**`GET /api/anomalies?operator_id=&machine_id=&limit=20`** → `Anomaly[]` (newest first)
```json
{
  "anomaly_id": "ANM0007", "timestamp": "2026-09-23T11:05:00",
  "machine_id": "EXC001", "operator_id": "OP1001",
  "anomaly_type": "excessive_idling", "observed_value": 75, "baseline_value": 24, "unit": "min",
  "severity": "medium", "anomaly_score": 0.71,
  "message": "Idle time 75 min vs your usual 24 min this session",
  "recommended_module_id": "TM03"
}
```

### 5.8 Analytics

**`GET /api/analytics/summary?operator_id=OP1001&days=7`**
```json
{
  "days": [{"date": "2026-09-17", "fuel_l": 92.4, "idle_pct": 31.0, "load_cycles": 410, "operating_min": 420, "incidents": 1}],
  "totals": {"fuel_l": 640.2, "idle_pct": 29.4, "load_cycles": 2890, "incidents": 4},
  "fleet_avg": {"idle_pct": 35.0, "fuel_per_cycle_l": 0.24}
}
```

### 5.9 Training hub

**`GET /api/training/modules`** → `Module[]`
```json
{"module_id": "TM03", "title": "Fuel-Efficient Operation", "category": "efficiency", "format": "video",
 "duration_min": 12, "description": "...", "content_url": null, "trigger_anomaly_type": "excessive_idling"}
```

**`GET /api/training/recommendations?operator_id=OP1001`** → `[{"module": Module, "reason": "Triggered by excessive idling on 23 Sep", "priority": "high"}]`

**`GET /api/training/progress?operator_id=OP1001`** → `[{"module_id": "TM03", "status": "in_progress", "progress_pct": 40, "score": null}]`

**`POST /api/training/progress`**, body `{"operator_id", "module_id", "progress_pct", "score"?}` → progress record

**`GET /api/training/modules/{module_id}/quiz`** → `{"questions": [{"id": "q1", "prompt": "...", "options": ["..."], "answer_index": 1, "explanation": "..."}]}`

### 5.10 Demo simulation controls

**`POST /api/sim/scenario`**, body `{"machine_id": "EXC001", "scenario": "proximity_hazard"}` → `LiveState`

**`POST /api/sim/reset`**, body `{"machine_id": "EXC001"}` → `LiveState`

## 6. ML interface (Python contract between tracks)

File: `backend/app/services/ml/interface.py`. **Signatures are frozen.** Track B creates this file with stub implementations in phase B1; Track A takes ownership after checkpoint M1 and replaces the internals.

```python
from app.schemas import (TaskTimeRequest, TaskTimePrediction, LiveState,
                         SafetyStatus, AnomalyCreate, Anomaly, Incident, Module)

def ml_mode() -> str: ...                     # "stub" | "live"

def load_models() -> None: ...                # called once on FastAPI startup; no-op in stub mode

def predict_task_time(req: TaskTimeRequest) -> TaskTimePrediction: ...

def assess_safety(state: LiveState, weather: str) -> SafetyStatus: ...

def detect_anomalies(state: LiveState, operator_baseline: dict) -> list[AnomalyCreate]: ...
    # operator_baseline: {"idle_time_min": float, "fuel_rate_lph": float, "cycle_time_s": float}
    # computed by Track B's service from the sessions table for that operator

def recommend_training(anomalies: list[Anomaly], incidents: list[Incident],
                       modules: list[Module]) -> list[tuple[str, str, str]]: ...
    # returns [(module_id, reason, priority)]
```

Stub behaviour (so the UI works from minute one):
- `predict_task_time`: `base[task_type] × skill_factor × weather_factor`, ±10% band, fixed factor list
- `assess_safety`: rule weights (seatbelt 30, person in zone 40, proximity <5 m +20, bad weather +12), capped at 100, with labels
- `detect_anomalies`: idle > 2× baseline → excessive_idling; fuel rate > 1.8× baseline → fuel_spike
- `recommend_training`: map `anomaly_type`/`event_type` → module with matching `trigger_anomaly_type`

Live mode loads from `MODEL_DIR`: `task_time_model.joblib`, `task_time_meta.json` (feature order, historical averages per task type, residual std for the band), `anomaly_model.joblib`, `anomaly_meta.json`.

## 7. Simulation engine (`backend/app/sim/`)

Why: there are no real machines, so the demo needs believable live data and a way to trigger hazards on cue.

- One in-memory `LiveState` per machine, initialised from the DB (machine engine hours, the operator's in-progress task).
- A background asyncio task started in FastAPI's lifespan ticks every `SIM_TICK_SECONDS`:
  - advance engine hours, operating/idle time, fuel (rate depends on task type and whether idling), load cycles, with small Gaussian noise
  - apply `active_scenario` overrides (e.g. `proximity_hazard` → `people_in_zone=1`, `proximity_m≈3–5`; `seatbelt_off`; `excessive_idle` → engine on, no cycles, idle climbs fast; `fuel_spike` → rate ×2.2; `rain` → weather Rainy)
  - compute `task_metrics` for the current task type
  - update task `progress_pct` from cycles vs. expected cycles
  - call `assess_safety()`. If `HIGH` and there is no open incident of that event type for the machine, create one. When risk drops below `HIGH`, auto-resolve it with `duration_s`.
  - call `detect_anomalies()` every 5 ticks; de-duplicate the same type within 10 minutes; persist to `anomalies`
  - persist a `telemetry_readings` row every 5 ticks
- `normal` scenario drifts values back to baseline over a few ticks, so the demo visibly "recovers".

## 8. Docker

- `db`: postgres:16-alpine, host port 5433, named volume, healthcheck
- `adminer` (profile `tools`): DB browser on :8080
- `backend` (profile `full`): builds `./backend`, mounts `./data` and `./ml/artifacts`, waits for db healthy, runs seed, then uvicorn
- `frontend` (profile `full`): builds `./frontend`, Vite dev server on :5173

Daily dev: only `db` in Docker; backend and frontend run locally for the fastest reload. Demo: `docker compose --profile full up --build`.

## 9. Phase 2 roadmap (slide only; not built tomorrow)

- Voice assistant: Whisper/Gemini Live → LLM with tool calling onto these same endpoints (the API is already the tool layer)
- On-machine CV for seatbelt and person detection feeding the same `LiveState` fields
- Three.js digital twin highlighting hazard zones from `SafetyStatus`
- Autodesk Fusion model showing sensor and edge-computer placement
- Real telematics ingestion replacing `sim/` (same `LiveState` schema)
