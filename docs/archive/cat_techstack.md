# Smart Operator Assistant — Tech Stack

## 1. Project Overview

An AI-powered operator assistance platform for heavy/mining machinery. The system combines machine telemetry, operator information, task data, environmental conditions, ML predictions, anomaly detection, safety intelligence, a voice assistant, and a 3D digital-twin visualization.

## 2. Recommended Stack

### Frontend
- **React + Vite** — web application and operator dashboard
- **Tailwind CSS** — responsive UI
- **Recharts** — telemetry, task, safety, and performance charts
- **Three.js** — interactive 3D digital-twin viewer
- **React Three Fiber** — React integration for Three.js

### Backend
- **Python 3.x**
- **FastAPI** — REST API and ML-serving layer
- **Pydantic** — request/response validation
- **Uvicorn** — FastAPI server

### AI / Machine Learning
- **Pandas** — data processing
- **NumPy** — numerical operations
- **Scikit-learn** — baseline ML and anomaly detection
- **XGBoost** — task-time/safety prediction where useful
- **Joblib** — model serialization

### Core ML Models
1. **Task Time Prediction**
   - Regression model
   - Inputs: task type, operator skill, weather, machine age, workload, idle time, telemetry, etc.
   - Output: estimated completion time

2. **Safety Risk Prediction**
   - Classification/regression model or rule + ML hybrid
   - Output: risk score and risk category

3. **Unusual Behavior / Anomaly Detection**
   - Isolation Forest initially
   - Detects excessive idling, unusual fuel consumption, abnormal operating patterns, etc.

### Synthetic Data
- **Python + NumPy + Pandas**
- **Faker** where synthetic identities are required
- Custom rule/probability engine to preserve realistic relationships between variables
- Target: approximately **20,000+ records** for the initial prototype

Important: synthetic data should not be purely random. Relationships should be deliberately generated between task type, operator skill, machine condition, weather, workload, safety events, and task duration.

### Database
- **PostgreSQL**
- Suggested tables:
  - `operators`
  - `machines`
  - `tasks`
  - `machine_telemetry`
  - `safety_events`
  - `incidents`
  - `predictions`
  - `training_modules`
  - `operator_training`

For an early local prototype, SQLite can be used before moving to PostgreSQL.

### Voice Assistant
- **Gemini Live API** for real-time voice interaction, or
- **Whisper + LLM + TTS** as a modular alternative
- Voice assistant should use tool/function calling rather than inventing system data.

Suggested tools:
- `get_today_tasks()`
- `get_machine_status()`
- `get_safety_status()`
- `get_recent_incidents()`
- `predict_task_time()`
- `detect_unusual_behavior()`
- `get_operator_performance()`
- `get_fuel_consumption()`
- `start_training_module()`

### Agent / Tool Orchestration
- **LangGraph / LangChain** if required for the tool-calling agent
- Keep the agent layer thin and let the backend/ML services remain the source of truth.

### 3D / Digital Twin
- **Autodesk Fusion**
  - Machine CAD model
  - Sensor placement
  - AI edge-computer placement
  - Operator display/HMI placement
  - Exploded views
  - Assembly/motion visualization
  - Engineering visualization
- Export suitable 3D assets such as **OBJ/FBX** for web visualization where appropriate.
- **Three.js / React Three Fiber** for the interactive web digital twin.

### Development
- **VS Code**
- **Git + GitHub**
- Python virtual environment (`venv`) or Conda
- `.env` for API keys and environment configuration
- REST/JSON communication between frontend and backend

### Deployment
Hackathon-friendly option:
- **Frontend:** Vercel
- **Backend:** Render/Railway or local deployment for demonstration
- **Database:** Supabase PostgreSQL or another managed PostgreSQL provider
- **ML models:** served through FastAPI

## 3. High-Level Technology Flow

```text
Synthetic Data
     ↓
Pandas / NumPy
     ↓
Feature Engineering
     ↓
ML Models
 ┌───┼───────────┐
 ↓   ↓           ↓
Safety  Task     Anomaly
Risk    Time     Detection
 └───┬───────────┘
     ↓
FastAPI Backend
     ↓
 ┌───┼──────────────┐
 ↓   ↓              ↓
React Voice       PostgreSQL
UI    Assistant
 │
 ↓
Three.js Digital Twin
 │
 ↓
Fusion-designed Machine
```

## 4. Development Principles

- Build the MVP around the five expected outcomes: task dashboard, safety assistance, training, unusual-behavior detection, and task-time estimation.
- Keep the dashboard generalized across task types.
- Treat `task_type` as a model feature rather than creating a separate application for every task.
- Keep ML outputs explainable enough for operator-facing decisions.
- Treat the system as **operator decision support**, not autonomous machine control.
- Keep Fusion as the engineering/digital-twin layer rather than the ML execution environment.
