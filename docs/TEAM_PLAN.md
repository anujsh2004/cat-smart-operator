# Team Plan — Work Division, Branches, Checkpoints

## 1. Roles

| | Person A: ML & Intelligence (Track A) | Person B: Platform & Experience (Track B) |
|---|---|---|
| Mission | Make the system *smart*: realistic data, trained models, explainable outputs | Make the system *real*: infra, database, API, live simulation, UI |
| Owns | Synthetic data, 3 ML components, training recommender, ML report | Docker, DB, all API routes, sim engine, frontend, demo control panel |
| Demo role | Presents the data + ML slides, answers model questions | Drives the live demo, answers architecture questions |

Both must be able to explain the whole system at a high level; the technical interview after the hackathon may ask either of you about any part.

## 2. File ownership (prevents merge conflicts)

| Path | Owner | Notes |
|---|---|---|
| `data/**` | A | |
| `ml/**` | A | incl. `ml/artifacts/` |
| `backend/app/services/ml/**` | A (after M1) | B creates the stub in B1, then hands over |
| `docs/TRACK_A.md`, `docs/ML_REPORT.md` | A | |
| `docker-compose.yml`, `.env.example` | B | |
| `backend/**` (everything except `services/ml/`) | B | |
| `frontend/**` | B | |
| `docs/TRACK_B.md` | B | |
| `backend/app/schemas/**` | **Shared + frozen** | Change only with both people's agreement, same commit updates `docs/ARCHITECTURE.md` + `frontend/src/api/types.ts` |
| `docs/ARCHITECTURE.md`, `CLAUDE.md`, `README.md` | Shared | Small edits via PR |
| `backend/requirements.txt` | Shared | A adds ML packages; append-only to avoid conflicts |

## 3. Git branching

```
main                      ← always demoable; only tagged milestone merges
 └── dev                  ← integration; PRs land here
      ├── a/data-ml       ← Person A: data/, ml/
      ├── a/ml-service    ← Person A: backend/app/services/ml/ (after M1)
      ├── b/infra-api     ← Person B: docker, backend (db, routers, sim)
      └── b/frontend      ← Person B: frontend/
```

Rules:
- Branch from `dev`. Open a PR into `dev` at every checkpoint (or sooner). Squash-merge.
- Before each checkpoint, `git pull origin dev` into your branch first and fix conflicts on your side.
- `dev → main` only at M3 (tag `v0.1-base`) and M4 (tag `v1.0-demo`). If `main` breaks, you still have a demo from the last tag.
- Commit messages: `feat(api): incidents router`, `feat(ml): task-time xgb model`, `fix(ui): safety card colors`.
- Never commit `.env`, `node_modules/`, `.venv/`, `data/generated/*.csv` over 50 MB. The 20k-row CSV is fine to commit (~3 MB) so the other person can seed without regenerating.

Setup (Person B, once):
```bash
git init && git add . && git commit -m "chore: project docs and scaffold"
git branch -M main && git remote add origin <repo-url> && git push -u origin main
git checkout -b dev && git push -u origin dev
git checkout -b b/infra-api
```
Person A:
```bash
git clone <repo-url> && cd cat-smart-operator
git checkout dev && git checkout -b a/data-ml
```

## 4. Timeline and checkpoints

Times are relative to the start (H0). Adjust to the actual hackathon length; keep the **order** and the checkpoints.

| When | Person A | Person B | Checkpoint |
|---|---|---|---|
| H0–0:20 | **Both together:** read the problem statement, `ARCHITECTURE.md` §4–6, agree on the contract; create repo and branches | | Contract agreed |
| H0:20–1:15 | A1: generator v0, 500 rows, all CSVs with exact contract columns | B0–B1: scaffold, Docker Postgres, FastAPI skeleton, schemas, ML stub interface | |
| **~H1:15** | Push CSVs → PR to `dev` | PR B1 → `dev` | **M1**: Contract live in code. A takes over `services/ml/` |
| H1:15–4:00 | A2 full 20k dataset with correlations · A3 task-time model · A4 safety engine | B2 DB + seed · B3 all routers · B4 sim engine · B5 frontend scaffold with mocks | |
| **~H4:00** | Models saved to `ml/artifacts/`; `ML_MODE=live` works locally | Backend fully working in stub mode; UI shell + Dashboard on mocks | **M2**: Both halves work independently |
| H4:00–6:30 | A5 anomaly detector · A6 live `interface.py` · A7 recommender | B6–B10 all pages; switch UI to the real API | |
| **~H6:30** | Pair with B on integration | Pair with A on integration | **M3**: end-to-end base prototype. Merge to `main`, tag `v0.1-base` |
| H6:30–end−1h | A8 `ML_REPORT.md` (metrics, feature importance charts), deck ML slides | B11 demo control panel polish, B12 full Docker, README, screenshots | |
| end−1h | **Code freeze.** Rehearse the demo twice. Tag `v1.0-demo` | | **M4** |

If you fall behind, cut in this order: training quiz → analytics charts → anomaly persistence → full Docker for frontend. **Never cut:** dashboard, safety card + incidents, task-time prediction, and one anomaly showing up live.

## 5. Track A task list (Person A)

- **A1 Generator v0 (by M1).** `data/generate.py --rows 500` writing all 4 CSVs with exact column names from `ARCHITECTURE.md` §4.2 and enum strings from §4.3. Include OP1001/EXC001 and today's tasks T001–T005 matching the organisers' sample.
- **A2 Full generator.** 20k sessions, 50 operators, 20 machines, 90 days. Deliberate relationships: time = task base × skill × weather × ground × machine age + noise; idle ≈ 30–40% of engine time; fuel from operating + idle rates; risk has the seatbelt × people-in-zone interaction; ~4% injected anomalies with distinct signatures. Save a quick sanity plot or two for the deck.
- **A3 Task-time model.** XGBoost (or RandomForest) regressor on `actual_time_min`. 80/20 split, report MAE and R². Save `task_time_model.joblib` + `task_time_meta.json` (feature order, encoders, per-task historical averages, residual std for the prediction band). `top_factors` from feature contributions (XGBoost `pred_contribs=True`) mapped to readable labels in minutes.
- **A4 Safety engine.** Weighted rules with per-factor contributions (explainable). Optionally calibrate the weights with a logistic regression on `safety_alert_triggered` and mention that in the deck.
- **A5 Anomaly detector.** IsolationForest on idle/fuel/cycle features plus per-operator baselines. The rule on the observed-vs-baseline ratio assigns `anomaly_type` and `message`. Evaluate against injected `anomaly_flag` (precision/recall) for the deck.
- **A6 Live interface.** Implement `backend/app/services/ml/interface.py` in live mode: `load_models()` on startup, keep signatures identical, fall back to stub logic if an artifact is missing.
- **A7 Training recommender.** Map anomaly and incident types to modules with reasons and priority.
- **A8 ML report + slides.** `docs/ML_REPORT.md`: dataset design, relationships encoded, metrics, feature importance, limitations, and how real CAT telematics would replace synthetic data.

Person A: create `docs/TRACK_A.md` with Claude Code prompts in the same style as `TRACK_B.md` if helpful.

## 6. Integration protocol

- Anything crossing tracks goes through `schemas/` + `interface.py` only.
- At M3, sit together: run `docker compose up -d db`, seed with A's full CSVs, set `ML_MODE=live`, run through the demo script below, fix bugs on whichever side owns the file.
- Bug in the other person's area? Tell them; don't fix it on your branch.

## 7. Demo script (3–4 minutes, B drives, A narrates ML)

1. **Morning start**: top bar shows operator, machine, shift, weather. Today's tasks with predicted vs. planned time. Start T001.
2. **Live dashboard**: excavation metrics ticking, fuel, idle %, health all green.
3. **Hazard**: Demo panel → `proximity_hazard` + `seatbelt_off`. Risk jumps to HIGH with reasons, full-screen alert, incident auto-logged. Reset → incident auto-resolves with duration.
4. **Unusual behaviour**: `excessive_idle` → anomaly card "idle 75 min vs your usual 24", training recommendation appears.
5. **Training hub**: open the recommended module, complete the short quiz, progress updates.
6. **Task-time estimator**: change weather to Rainy and ground to Wet, prediction rises with explained factors.
7. **Close**: architecture slide + Phase 2 roadmap (voice, CV, digital twin, real telematics).
