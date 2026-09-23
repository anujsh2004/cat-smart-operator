# Smart Operator Assistant (CAT Hackathon)

An AI-assisted companion app for CAT excavator/loader operators. It covers a daily task dashboard, safety monitoring, a training hub, unusual-behaviour detection and task-time estimation. It is decision support only and never controls the machine.

See `docs/ARCHITECTURE.md` for the design and API contract.

## Setup

```bash
cp .env.example .env
```

Postgres is exposed on host port **5433** so it doesn't clash with a local install. Inside Docker the backend uses `db:5432`.

## Commands

```bash
# Database only (daily dev)
docker compose up -d db
docker compose --profile tools up -d adminer      # DB browser on :8080

# Backend (local, hot reload)
cd backend && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.seed                             # create tables + seed
uvicorn app.main:app --reload --port 8000         # docs at http://localhost:8000/docs

# Frontend
cd frontend && npm install && npm run dev         # http://localhost:5173
# VITE_USE_MOCKS=true npm run dev                 # run UI against mock JSON, no backend needed

# Full stack in Docker (demo)
docker compose --profile full up --build

# Track A
python data/generate.py --rows 20000
python ml/train_task_time.py && python ml/train_anomaly.py
```
