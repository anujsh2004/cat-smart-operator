# Track B — Platform & Experience (Person B)

Branches: `b/infra-api` for phases B0–B4 and B12 backend parts, `b/frontend` for B5–B11.

## How to drive Claude Code through this file

1. Open the repo root in the Antigravity terminal and run `claude`. It loads `CLAUDE.md` automatically.
2. For each phase: press **Shift+Tab** to enter plan mode, paste the phase prompt, review the plan, then approve.
3. When Claude says the phase is done, check the **Done when** list yourself (open Swagger at `localhost:8000/docs` or the browser).
4. Commit: `git add -A && git commit -m "feat(...): phase Bx ..."`.
5. Run `/clear` before the next phase to keep context small. Every prompt below re-points Claude at the docs it needs.
6. If Claude drifts (adds voice, 3D, new libraries, renames fields), stop it and say: "Re-read CLAUDE.md rules 1, 2 and the out-of-scope list."

Push and open a PR to `dev` at each checkpoint in `TEAM_PLAN.md`.

## UI design direction (give Claude this context in B5)

The primary user is an operator in a cab, glancing at a tablet mounted beside them, often in bright sun, with gloves on.

- **Dark, high-contrast theme** (near-black `#0B0D10` background, `#15191F` cards), large numbers, minimal text.
- **Accent: industrial yellow `#F5B800`** for primary actions and highlights. Don't use Caterpillar logos or trademarked assets unless the organisers provide them.
- **Status colours**: green `#22C55E` good, amber `#F59E0B` attention, red `#EF4444` danger. Never rely on colour alone: every status also has an icon and a text label.
- **Touch targets at least 48 px**, generous spacing, 16 px minimum body text, 32–48 px KPI numbers.
- **Glanceable hierarchy**: safety first (top), current task second, everything else below.
- Fonts: Inter for text, JetBrains Mono for numeric readouts (Google Fonts with system fallbacks).
- Layout: a slim left icon sidebar (Dashboard, Tasks, Safety, Machine, Training), a top bar with operator · machine · shift · weather · clock · connection dot, and a global **safety alert banner** that appears on every page when `alert` is true.

---

## Phase B0 — Scaffold (branch `b/infra-api`)

```
Read CLAUDE.md and docs/ARCHITECTURE.md sections 1–3 and 8.
Phase B0: scaffold the repo structure exactly as in CLAUDE.md "Repo layout".
- Create empty folders with .gitkeep where needed: data/generated, ml/artifacts, backend/app/{db/fixtures,schemas,routers,sim,services/ml}, frontend (leave empty for now).
- Create .gitignore (Python, Node, .env, .venv, node_modules, __pycache__, .DS_Store, *.joblib is allowed so do NOT ignore it).
- Create .env.example with the variables in ARCHITECTURE.md §3, and copy it to .env.
- Create docker-compose.yml with services db (postgres:16-alpine, host port 5433, named volume, healthcheck), adminer (profile tools, port 8080), backend and frontend (profile full) as described in §8. The backend service should run the seed and then uvicorn with --reload, mount ./data and ./ml/artifacts, and use DATABASE_URL pointing at db:5432.
- Create a README.md with the commands from CLAUDE.md.
Then run `docker compose up -d db` and confirm the healthcheck passes. Stop when done.
```

**Done when:** `docker compose ps` shows `db` healthy; `.env` exists and is ignored by git.

## Phase B1 — Backend skeleton, schemas, ML stub (branch `b/infra-api`) → M1

```
Read docs/ARCHITECTURE.md §3–6 carefully. The API contract in §5 and the ML interface in §6 are frozen.
Phase B1:
1. backend/requirements.txt: fastapi, uvicorn[standard], pydantic>=2, pydantic-settings, sqlalchemy>=2, psycopg[binary], pandas, numpy, python-dotenv, pytest, httpx. (Track A will append ML packages later.)
2. backend/app/config.py using pydantic-settings reading .env (all §3 variables).
3. backend/app/schemas/: Pydantic v2 models for EVERY request/response in §5, with field names, types and Literal enums exactly as in §4.3 and §5. Group into files: common.py (enums as Literal types), context.py, tasks.py, live.py, safety.py, incidents.py, prediction.py, anomalies.py, analytics.py, training.py, sim.py, and re-export all from schemas/__init__.py. Also add TaskTimeRequest and AnomalyCreate as referenced in §6.
4. backend/app/services/ml/interface.py with the exact signatures in §6 and the STUB behaviour described there (deterministic, readable factor labels). ml_mode() returns settings.ML_MODE. load_models() is a no-op in stub mode. Put the stub logic in services/ml/stub.py and have interface.py dispatch on ml_mode(), so Track A can add services/ml/live.py without touching routers.
5. backend/app/main.py: FastAPI app with CORS from settings, a lifespan that calls load_models(), `GET /api/health` returning status, db connectivity and ml_mode.
6. backend/Dockerfile (python:3.11-slim).
Run uvicorn, open /docs, confirm /api/health works. Write tests/test_health.py. Stop when done.
```

**Done when:** `/api/health` returns `{"status":"ok","db":true,"ml_mode":"stub"}`; all schemas import without errors.

Then: push, PR into `dev`, and tell Person A the ML interface is ready for them to take over.

## Phase B2 — Database models and seed

```
Read docs/ARCHITECTURE.md §4 (data model and CSV contract).
Phase B2:
1. backend/app/db/session.py: engine + SessionLocal + get_db dependency (SQLAlchemy 2.0, sync, psycopg).
2. backend/app/db/models.py: all tables in §4.1 using Mapped[] style. For incidents.details and predictions.features use JSON().with_variant(JSONB, "postgresql") so the models also work on SQLite as an emergency fallback.
3. backend/app/db/fixtures/: small CSVs matching the §4.2 contract, built from the organisers' sample:
   - operators: OP1001 (Intermediate, 4 yrs, Morning) + 2 others
   - machines: EXC001 (Excavator, 320 GC, age 2, 1523.5 h) + 1 wheel loader
   - tasks_today: T001 Earth Excavation Sunny est 60, T002 Trenching Rainy est 45, T003 Material Loading Cloudy est 30, T004 Grading Sunny est 35, T005 Demolition Windy est 90, all for OP1001/EXC001 today with staggered start times from 08:00
   - sessions: ~200 plausible historical rows for OP1001 and others (generate programmatically in the seed if easier)
4. backend/app/db/seed_training.json: 8 training modules across the 4 categories and 4 formats, each safety/efficiency module linked via trigger_anomaly_type or event type (e.g. TM01 Seatbelt & Cab Safety → seatbelt_unfastened, TM02 Working Near People → proximity_hazard, TM03 Fuel-Efficient Operation → excessive_idling, TM04 Smooth Cycle Technique → abnormal_cycle_time, TM05 Incident Response Basics, TM06 Wet-Weather Operation, TM07 Trenching Best Practice, TM08 Book an Instructor Session with format instructor). Include a 3–5 question quiz per module.
5. backend/app/db/seed.py (run as `python -m app.db.seed`): drop & create all tables, then load CSVs from DATA_DIR if present, otherwise from fixtures. Tasks from tasks_today get today's date. Set T001 to in_progress. Idempotent.
Run the seed against Docker Postgres and print row counts. Stop when done.
```

**Done when:** seed prints row counts for every table; Adminer shows the data.

## Phase B3 — API routers

```
Read docs/ARCHITECTURE.md §5 and §6. Contract is frozen.
Phase B3: implement all routers in backend/app/routers/ as a thin HTTP layer. DB logic goes in backend/app/services/<domain>_service.py (NOT in services/ml/). Every intelligence call goes through app.services.ml.interface only.
Routers: system (context), tasks, machines (live + telemetry), safety, incidents, predict, anomalies, analytics, training, sim (sim endpoints can return 501 until B4).
- /api/context: operator from DB, machine from their in_progress (or first) task today, weather from that task, shift times from operator.shift.
- /api/predict/task-time: call interface.predict_task_time, store a row in predictions.
- /api/safety/status: build/obtain the machine's LiveState (for now a static one from latest telemetry or defaults; B4 replaces this with the sim engine) and call assess_safety.
- /api/anomalies: read from the anomalies table.
- /api/training/recommendations: gather recent anomalies + incidents for the operator, call recommend_training.
- operator_baseline helper in services/baseline_service.py: mean idle_time_min, fuel rate and cycle time from sessions for that operator.
- Incident IDs formatted INC1001, INC1002...; anomaly IDs ANM0001...
Register routers in main.py under /api. Return 404 with {"detail"} for unknown IDs.
Add tests/test_smoke.py hitting every GET endpoint once. Run pytest and fix failures. Stop when done.
```

**Done when:** every endpoint in Swagger returns contract-shaped JSON; `pytest` passes.

## Phase B4 — Live simulation engine

```
Read docs/ARCHITECTURE.md §5.3, §5.10 and §7.
Phase B4: implement backend/app/sim/:
- state.py: in-memory dict machine_id → LiveState plus active_scenario and baseline values.
- metrics.py: task_metrics per task type (§5.3 list) derived from load_cycles, payload, time.
- scenarios.py: overrides for normal, seatbelt_off, proximity_hazard, excessive_idle, fuel_spike, rain. "normal" drifts values back to baseline over ~3 ticks.
- engine.py: async loop started in the FastAPI lifespan, ticking every SIM_TICK_SECONDS. Each tick exactly as §7: advance values with small noise, apply scenario, compute task_metrics, update task progress_pct in DB, call assess_safety, auto-create incident when HIGH (no duplicate open incident of the same event_type per machine), auto-resolve with duration_s when risk falls below HIGH, call detect_anomalies every 5 ticks with 10-minute de-duplication per type, persist telemetry every 5 ticks.
  Choose event_type from the top safety factor: people_in_zone/proximity → proximity_hazard, seatbelt → seatbelt_unfastened.
- Wire /api/machines/{id}/live, /api/machines/{id}/telemetry, /api/safety/status to the engine, and implement /api/sim/scenario and /api/sim/reset.
- Use a fresh DB session per tick; catch and log exceptions so the loop never dies.
Verify: start the server, poll /live and watch values change; POST proximity_hazard and confirm safety goes HIGH and an incident appears; POST normal and confirm it auto-resolves with a duration. Stop when done.
```

**Done when:** the hazard → incident → auto-resolve loop works through Swagger alone. **Push and PR to `dev` (backend done in stub mode, M2 for backend).**

## Phase B5 — Frontend scaffold with mocks (branch `b/frontend`)

```
Read CLAUDE.md, docs/ARCHITECTURE.md §5, and the "UI design direction" section of docs/TRACK_B.md.
Phase B5: create the frontend in ./frontend:
- Vite + React 18 + TypeScript (strict), Tailwind CSS (current version with its Vite plugin), React Router, TanStack Query, Recharts, lucide-react. No other UI libraries.
- src/api/types.ts: TypeScript types mirroring EVERY §5 schema and §4.3 enum exactly.
- src/api/client.ts: fetch wrapper using VITE_API_BASE_URL; when VITE_USE_MOCKS=true, return data from src/mocks/*.ts instead (realistic mock data matching the contract, including a HIGH-risk safety variant).
- src/api/hooks.ts: TanStack Query hooks for every endpoint. Polling: live + safety every 2 s, incidents + anomalies every 5 s, others no polling. Mutations invalidate relevant queries.
- Design tokens in Tailwind config / CSS variables per the design direction. Load Inter and JetBrains Mono.
- Layout: left icon sidebar (Dashboard, Tasks, Safety, Machine, Training), TopBar (operator, machine, shift, weather, live clock, connection dot from /api/health), global SafetyAlertBanner shown on all pages when safety.alert is true (red, icon, top factor text, pulsing but not seizure-inducing).
- Shared components: Card, KpiTile (label, big mono value, unit, trend), StatusBadge (icon + text + colour), RiskGauge (semicircle 0–100 coloured by level), EmptyState, ErrorState, Skeleton.
- Placeholder pages for each route.
- frontend/Dockerfile (node:20-alpine, vite dev --host).
Run `VITE_USE_MOCKS=true npm run dev`, confirm it renders with no console errors, and `npm run build` passes. Stop when done.
```

**Done when:** the shell runs on mocks, navigation works, and the build passes.

## Phase B6 — Dashboard page

```
Phase B6: build the Dashboard (route "/") using the hooks from B5. Layout top to bottom:
1. Safety strip: RiskGauge + risk level badge + top 2 factor labels + seatbelt status + nearest proximity (m) + people in zone. Whole strip turns red at HIGH.
2. Current task card: task type, zone, progress bar, planned vs predicted vs elapsed time, start/complete buttons.
3. KPI row: fuel used today, fuel rate, idle % (amber if > 35), engine hours, load cycles, machine health.
4. Task-specific metrics grid from live.task_metrics (layout identical for every task type; only the tiles change).
5. Two columns: "AI insights & alerts" (latest anomalies with message + recommended training link) and "Recent incidents" (last 5 with status badge and duration).
6. Today's schedule mini-list (all tasks with status chips).
Everything must handle loading, empty and error states. Verify with mocks, including the HIGH-risk mock. Stop when done.
```

## Phase B7 — Tasks page and task-time estimator

```
Phase B7: Tasks page ("/tasks"):
- Timeline/list of today's tasks with scheduled start, status, planned vs predicted minutes (difference highlighted), start/complete actions.
- "Task Time Estimator" panel: form (task type, operator skill, experience, machine age, weather, ground condition, temperature) pre-filled from the selected task and context. Submitting calls POST /api/predict/task-time and shows: big predicted minutes, range band, historical average, and a horizontal bar chart (Recharts) of top_factors in +/− minutes with readable labels.
- A "what-if" row of quick chips (Rainy, Wet ground, Beginner) that re-run the prediction instantly.
Stop when done.
```

## Phase B8 — Safety page and incidents

```
Phase B8: Safety page ("/safety"):
- Large RiskGauge, risk level, every factor with its contribution as a bar and its label, recommended_action in a prominent callout.
- Compliance tiles: seatbelt (big icon + text), proximity (distance with a simple top-down SVG ring showing a 5 m danger zone and a dot for the nearest person), working conditions (weather, ground, visibility).
- Incident log table: ID, time, event type (icon + label), severity badge, risk score, status, duration, resolve action for open ones. Filters by status and type.
- "Report incident" button → modal form → POST /api/incidents.
Stop when done.
```

## Phase B9 — Machine insights and unusual behaviour

```
Phase B9: Machine page ("/machine"):
- Live charts (Recharts) from /api/machines/{id}/telemetry: fuel rate, idle %, load cycles over the last 60 minutes.
- 7-day analytics from /api/analytics/summary: bar chart fuel per day, line idle % vs fleet average reference line, incidents per day.
- "Unusual behaviour" feed: each anomaly as a card with type icon, message, observed vs baseline (small comparison bar), severity, anomaly score, time, and a "Start recommended training" button linking to the module.
Stop when done.
```

## Phase B10 — Training hub

```
Phase B10: Training page ("/training"):
- "Recommended for you" row from /api/training/recommendations with reason and priority badge.
- Module grid filterable by category and format; each card shows format icon, duration, progress.
- Module detail view: for video, a placeholder player area with description (content_url if present); for quiz/simulation, an interactive quiz from /api/training/modules/{id}/quiz with instant feedback and explanation; for instructor, a simple "request a session" slot picker (local state only, show confirmation).
- Completing a quiz posts progress with score; progress bars update.
Stop when done.
```

## Phase B11 — Real API integration + demo control panel → M3

```
Phase B11:
1. Run the frontend against the real backend (VITE_USE_MOCKS=false). Fix every mismatch; if the backend is wrong, fix the backend on this branch only for Track B files and tell me about any contract issue.
2. Demo Control Panel: a slide-out drawer toggled by pressing "D" or a small button in the TopBar, with scenario buttons (Normal, Seatbelt off, Proximity hazard, Excessive idle, Fuel spike, Rain) calling POST /api/sim/scenario, plus Reset. Show the active scenario.
3. Walk through the demo script in docs/TEAM_PLAN.md §7 and make sure each step visibly works within 2–4 seconds.
Stop when done and list anything that still looks off.
```

**Done when:** the full demo script runs end to end. Merge `b/frontend` and `b/infra-api` into `dev`, integrate with Person A's `ML_MODE=live`, then `dev → main`, tag `v0.1-base`.

## Phase B12 — Polish and full Docker → M4

```
Phase B12:
- Make `docker compose --profile full up --build` bring up db, seed, backend and frontend with no manual steps. Test it from a clean state (docker compose down -v first).
- README: one-paragraph pitch, screenshot placeholders, architecture diagram (copy from ARCHITECTURE.md), run instructions, API docs link, Phase 2 roadmap.
- UI polish: consistent spacing, no layout shift during polling, favicon, page titles, 1280×800 tablet layout check and a narrow-width check.
Stop when done.
```

---

## Fallbacks if something breaks near the deadline

- Postgres/Docker problems on the demo laptop → switch `DATABASE_URL` to `sqlite:///./soa.db` (the models use a JSON type with a JSONB variant, so they work unchanged).
- Backend down during the demo → `VITE_USE_MOCKS=true npm run dev` still shows every screen, including the HIGH-risk state.
- Record a 2-minute screen capture of the full demo after M3 as insurance.
