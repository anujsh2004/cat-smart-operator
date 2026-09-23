# CLAUDE.md — Smart Operator Assistant (CAT Hackathon)

You are helping a 2-person team build a hackathon prototype in ONE DAY. Speed, a working demo, and code the humans can explain matter more than completeness or cleverness.

## What we are building

An AI-assisted companion app for CAT excavator/loader operators. It is **decision support only**: it predicts, detects, explains and recommends. It never controls the machine.

Everything we build must map to one of the five required outcomes in the problem statement:

1. **Daily task dashboard**: scheduled tasks for the day
2. **Safety features**: seatbelt compliance, proximity hazards, incident logging, with working conditions considered
3. **Operator training hub**: any creative learning format
4. **Unusual behaviour detection**: excessive idling, unsafe operation patterns
5. **Task time estimation**: predicted from past data and environmental conditions

If a request does not serve one of these five, flag it before building it.

## Read these before any work

- `docs/ARCHITECTURE.md`: system design, DB schema, **API contract (source of truth)**, ML interface, simulation engine
- `docs/TEAM_PLAN.md`: who owns which folders, branches, checkpoints
- `docs/TRACK_B.md`: phase-by-phase build spec for Platform & Experience (Track B)
- `docs/TRACK_A.md`: phase-by-phase build spec for ML & Intelligence (Track A), if present

## Stack (locked; do not introduce alternatives)

| Layer | Choice |
|---|---|
| Database | PostgreSQL 16 in Docker |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync, `psycopg` driver), Uvicorn |
| ML | pandas, numpy, scikit-learn, XGBoost, joblib, Faker (synthetic data) |
| Frontend | React 18 + Vite + TypeScript, Tailwind CSS, Recharts, React Router, TanStack Query, lucide-react |
| Infra | Docker Compose (db always; backend + frontend via `full` profile) |

No Alembic: use `Base.metadata.create_all()` plus a seed script. No Redux, no websockets (polling via TanStack Query `refetchInterval`), no component libraries beyond Tailwind + lucide.

## Out of scope for the MVP (Phase 2 roadmap only)

Voice assistant, LangGraph/agents, camera/CV detection, Three.js digital twin, Autodesk Fusion. **Do not start these unless a human explicitly asks.** Seatbelt and proximity come from (simulated) telemetry fields, not cameras.

## Repo layout

```
cat-smart-operator/
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── docs/                     # shared, read-only unless asked
├── data/                     # Track A: generator + generated CSVs
│   ├── generate.py
│   └── generated/            # operators.csv, machines.csv, sessions.csv, tasks_today.csv
├── ml/                       # Track A: training scripts, notebooks
│   ├── train_task_time.py
│   ├── train_anomaly.py
│   └── artifacts/            # *.joblib + metadata JSON (loaded by backend)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # Track B
│       ├── config.py         # Track B
│       ├── db/               # Track B: models.py, session.py, seed.py, fixtures/
│       ├── schemas/          # SHARED + FROZEN: Pydantic models mirroring the API contract
│       ├── routers/          # Track B: thin HTTP layer only
│       ├── sim/              # Track B: live telemetry simulation engine
│       └── services/
│           ├── ml/           # Track A: interface.py + implementation (the "brains")
│           └── *.py          # Track B: non-ML services (tasks, incidents, training)
└── frontend/                 # Track B
```

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

## Working rules

1. **The API contract in `docs/ARCHITECTURE.md` §5 is frozen.** Never change an endpoint path, field name, type or enum silently. If a change is genuinely required, stop and tell the human. When approved, update the doc, `backend/app/schemas/`, and `frontend/src/api/types.ts` in the same commit.
2. **Stay inside your track's folders** (see `docs/TEAM_PLAN.md`). Don't edit the other track's files. If you need something from the other track, say so rather than doing it.
3. **Work one phase at a time.** At the end of each phase: run it, verify the "Done when" checks, summarise what changed and how to test it, then stop so the human can review and commit.
4. **Always demoable.** Never leave `dev` or `main` broken. Prefer simple and working over clever and half-done. Hardcode or stub rather than block.
5. **Numbers come from data, never invented.** Every value shown in the UI comes from the DB, the simulation engine, or an ML service. No LLM-generated figures.
6. **Explainability over black boxes.** Safety and anomaly outputs always include human-readable reasons.
7. **Secrets** live in `.env` only. Never commit `.env`.
8. **Code style**: Python with type hints and Pydantic v2 models; SQLAlchemy 2.0 `Mapped[]` style. TypeScript strict; no `any` in API types. Small files, descriptive names, brief comments only where logic isn't obvious.
9. **Testing**: smoke tests only. One `pytest` file hitting each router with `TestClient` is enough. Manually verify in the browser/Swagger.
10. **Dependencies**: don't add a package not listed in the stack without asking.
11. Before saying a phase is done, actually run the server/build and fix errors. Don't claim something works without running it.
