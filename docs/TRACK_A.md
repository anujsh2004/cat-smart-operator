# Track A — ML & Intelligence (Person A)

Branches: `a/data-ml` for phases A0–A5 and A8, `a/ml-service` for A6–A7 (created only after checkpoint M1, when B's stub interface is in `dev`).

## How to drive Claude Code through this file

1. Open the repo root in the Antigravity terminal and run `claude`. It loads `CLAUDE.md` automatically.
2. For each phase, give it one line:
   `Read CLAUDE.md and docs/TRACK_A.md. I am Person A. Do Phase A<n> only, following its prompt exactly, then stop and show me the "Done when" checks.`
3. Use plan mode (Shift+Tab) to review its plan before approving.
4. Check the **Done when** list yourself, commit, run `/clear`, move to the next phase.
5. If Claude drifts (renames CSV columns, changes enums, edits `backend/` outside `services/ml/`), say: "Re-read CLAUDE.md rules 1 and 2 and docs/ARCHITECTURE.md §4.2–4.3."

## Three rules that matter more than model accuracy

1. **Column names and enum strings must match `ARCHITECTURE.md` §4.2–4.3 exactly.** Person B's seed script and UI depend on them.
2. **No leakage in task-time prediction.** The model predicts time *before* the task starts, so it may only use what is known then: task type, operator skill and experience, machine age, weather, ground condition, temperature. Never `fuel_used_l`, `idle_time_min`, `load_cycles` or `actual_time_min`. This is a likely interview question.
3. **Same library versions in `ml/` and `backend/`.** A model saved with one scikit-learn/XGBoost version may fail to load with another. Pin identical versions in `ml/requirements.txt` and `backend/requirements.txt`.

## Shared definitions (use consistently in data, training and live inference)

- `operating_time_min`: productive working minutes in the session (excludes idle).
- `idle_time_min`: engine on, no productive work.
- Engine-on minutes = `operating_time_min + idle_time_min`.
- `idle_pct` = `idle_time_min / engine-on minutes × 100`.
- `fuel_rate_lph` = `fuel_used_l / (engine-on minutes / 60)`.
- `cycle_time_s` = `operating_time_min × 60 / load_cycles` (guard against 0 cycles).
- `fuel_per_cycle_l` = `fuel_used_l / load_cycles` (guard against 0).

Every one of these can be computed both from a `sessions.csv` row and from the live `LiveState` (which has `idle_time_min`, `operating_time_min`, `fuel_used_l`, `fuel_rate_lph`, `load_cycles`). That's what lets the anomaly model trained on history run on live data.

---

## Phase A0 — Environment (branch `a/data-ml`)

```
Read CLAUDE.md and docs/ARCHITECTURE.md §4.
Phase A0:
- Create ml/requirements.txt with pinned versions: pandas, numpy, scikit-learn, xgboost, joblib, faker, matplotlib. Pick current stable versions and pin them exactly (==). Print the versions you chose so I can tell Person B to use the same ones in backend/requirements.txt.
- Create a venv at ml/.venv, install, and verify imports.
- Create folders if missing: data/generated, ml/artifacts, ml/reports.
- Create ml/common.py with the shared definitions from docs/TRACK_A.md "Shared definitions" as pure functions (engine_on_min, idle_pct, fuel_rate_lph, cycle_time_s, fuel_per_cycle_l) that work on both a pandas DataFrame and a dict, plus the enum lists from ARCHITECTURE.md §4.3.
Stop when done.
```

**Done when:** imports work; `ml/common.py` exists; you've sent the pinned versions to Person B.

## Phase A1 — Generator v0, contract-correct (target: by M1, ~1 hour in)

```
Read docs/ARCHITECTURE.md §4.2 and §4.3 and docs/TRACK_A.md.
Phase A1: create data/generate.py (CLI: --rows, --seed, --out data/generated) that writes 4 CSVs with EXACTLY the column names and enum strings in §4.2/§4.3:
- operators.csv: 50 operators OP1001..OP1050, Indian names via Faker (locale en_IN), skill mix ~30% Beginner / 45% Intermediate / 25% Expert, experience consistent with skill (Beginner 0–2, Intermediate 2–6, Expert 6–15 yrs), shifts Morning/Evening/Night. OP1001 must be Intermediate, 4 yrs, Morning.
- machines.csv: 20 machines. EXC001..EXC012 Excavators (models like 320 GC, 323, 330), WL001..WL004 Wheel Loaders, DZ001..DZ002 Dozers, MG001..MG002 Motor Graders. EXC001 age 2 yrs, ~1530 engine hours.
- tasks_today.csv: T001–T005 for OP1001 on EXC001 matching the organisers' sample: T001 Earth Excavation Sunny est 60, T002 Trenching Rainy est 45, T003 Material Loading Cloudy est 30, T004 Grading Sunny est 35, T005 Demolition Windy est 90. Start times 08:00, 09:15, 10:15, 11:30, 13:00 today. Add zones (Pit A, Pit B, Haul Road, North Bench, Old Structure) and ground conditions.
- sessions.csv: --rows historical sessions (default 500 for now) with every column in §4.2. Simple generation is OK in this phase, but values must be in realistic ranges and types must be right.
Validate: load each CSV back, assert column lists equal the contract exactly, assert all enum values are in the allowed sets, print row counts and df.describe().
Run with --rows 500. Stop when done.
```

**Done when:** all 4 CSVs exist with exact columns; validation passes. **Commit including the CSVs, push, PR to `dev`, tell Person B the CSVs are ready.**

## Phase A2 — Full realistic dataset

```
Read docs/TRACK_A.md (rules and shared definitions) and data/generate.py.
Phase A2: upgrade sessions generation to 20,000 rows over the last 90 days with deliberate, explainable relationships. Keep the CSV contract unchanged.
Per-operator latent traits (fixed per operator, sampled once): skill_factor from skill level (Beginner 1.25, Intermediate 1.05, Expert 0.90) with small individual noise; idle_habit (mean idle share 0.25–0.45, Beginners higher); safety_habit (probability of unfastened seatbelt 0.02–0.12, Beginners higher).
Per-machine: age affects time (+1% per year) and fuel (+1.5% per year).
Per session:
- task_type weighted by machine_type (excavators: excavation/trenching/demolition; loaders: material loading; graders: grading; dozers: grading/excavation).
- base minutes: Earth Excavation 60, Trenching 45, Material Loading 30, Grading 35, Demolition 90. estimated_time_min = base (the planner's naive estimate).
- weather with seasonal-ish probabilities; factor Sunny 1.00, Cloudy 1.05, Windy 1.10, Rainy 1.20, Foggy 1.25. ground factor Firm 1.00, Loose 1.08, Rocky 1.12, Wet 1.15. Rain strongly raises chance of Wet ground.
- temperature_c 22–42 depending on weather; above 38 °C adds +5%.
- actual_time_min = base × skill × weather × ground × age × heat × lognormal noise (sigma ~0.07).
- operating_time_min = actual_time_min; idle_time_min from operator idle_habit (share of engine-on time) with noise.
- load_cycles from operating time / task-specific cycle time (e.g. excavation ~20 s, loading ~35 s, grading passes much lower count); avg_payload_kg by machine type.
- fuel_used_l = operating hours × task-specific working rate (~12–20 L/h) + idle hours × ~3 L/h, scaled by machine age.
- seatbelt_status from safety_habit; people_in_zone ~12% (higher for Demolition and Material Loading); proximity_min_m 1–5 m when someone is in the zone, else 8–50 m.
- safety_risk_score: 10 + 30 if Unfastened + 40 if people_in_zone + 20 if proximity < 5 + 12 if Rainy/Foggy, with the seatbelt × people_in_zone interaction adding +10, clip 0–100, small noise. safety_alert_triggered = score ≥ 70.
- Inject anomalies in ~4% of rows, each with a clear signature and anomaly_flag=True: excessive_idling (idle × 2.5–3.5), fuel_spike (fuel × 1.8–2.5), abnormal_cycle_time (cycles × 0.3–0.5, i.e. very slow cycles), unsafe_operation (Unfastened + people_in_zone + proximity < 3). Normal rows: anomaly_flag False, anomaly_type empty.
- OP1001 sessions should show a mildly high idle habit so the demo's "your usual idle" is believable.
Also write ml/reports/data_sanity.png: 4 small plots (actual time by task type, actual time by weather, idle % distribution, risk score by seatbelt × people_in_zone).
Run with --rows 20000 --seed 42, re-run the contract validation, print anomaly rate and alert rate. Stop when done.
```

**Done when:** 20k rows; anomaly rate ~3–5%; alert rate plausible (~8–15%); sanity plots show the intended patterns. Commit and push the CSVs so Person B can seed with real data.

## Phase A3 — Task-time model

```
Read docs/TRACK_A.md (especially rule 2, no leakage) and docs/ARCHITECTURE.md §5.6 and §6.
Phase A3: create ml/train_task_time.py:
- Features ONLY: task_type, operator_skill, operator_experience_yrs, machine_age_yrs, weather, ground_condition, temperature_c. Target: actual_time_min.
- One-hot encode categoricals with a fixed column order; save that order.
- Baselines to beat: (a) estimated_time_min, (b) mean per task_type. Then XGBRegressor (reasonable defaults, e.g. 300 trees, depth 5, lr 0.05). 80/20 split, seed 42.
- Print and save MAE, RMSE, R² for baselines and model to ml/reports/task_time_metrics.json.
- Save ml/artifacts/task_time_model.joblib and ml/artifacts/task_time_meta.json containing: feature column order, category lists, historical average actual_time_min per task_type, residual std on the test set (for the ± band), metrics, library versions.
- Write ml/predict_task_time.py with a function predict(request_dict) -> dict matching TaskTimePrediction in §5.6: predicted_time_min, lower_min/upper_min (± 1.28 × residual std ≈ 80% band), historical_avg_min, model "xgb_task_time_v1", top_factors from XGBoost pred_contribs=True, summing one-hot contributions back to their original feature, keeping the 3 largest by absolute value, with readable labels ("Rainy weather", "Wet ground", "Beginner operator", "Machine age 6 yrs", "Heat 40 °C") and impact_min rounded to 1 decimal.
- Save ml/reports/task_time_importance.png (feature importance bar chart).
Demo it: print predictions for T002 (Trenching, Rainy, Wet, Intermediate) vs the same task in Sunny/Firm, and show the difference is explained by the factors. Stop when done.
```

**Done when:** the model beats both baselines on MAE; Rainy/Wet predictions are clearly higher with factors that explain why.

## Phase A4 — Safety risk engine

```
Read docs/ARCHITECTURE.md §5.4 and §6 and docs/TRACK_A.md.
Phase A4: create ml/safety.py:
- assess(state: dict, weather: str) -> dict matching SafetyStatus in §5.4 (without machine_id/evaluated_at, the backend adds those).
- Explainable weighted rules. Factors and default weights: seatbelt unfastened while engine on 30; person in operating zone 40; proximity < 5 m +20 (and < 3 m +30 instead); interaction seatbelt unfastened AND person in zone +10; weather Rainy/Foggy 12, Windy 6; speed > 8 km/h near people +10. Base 10. Clip 0–100. Level: LOW < 40, MEDIUM 40–69, HIGH ≥ 70. alert = HIGH.
- Each factor produces {factor, label, contribution} with specific labels using the live values, e.g. "Person detected within 4.2 m of operating zone". Sort by contribution.
- recommended_action chosen from the top factor (e.g. proximity: "Stop swing movement, sound horn and wait for the zone to clear."; seatbelt: "Fasten seatbelt before continuing operation.").
- Create ml/train_safety.py: fit a logistic regression on sessions.csv (features: unfastened, people_in_zone, proximity<5, bad weather, interaction; target safety_alert_triggered) and report how its coefficients rank the factors versus the rule weights. Save the weights actually used (rules) plus the LR coefficients to ml/artifacts/safety_meta.json. The rules stay the runtime source of truth because they're explainable to an operator; the LR is evidence for the deck that the weights are sensible.
Test on 5 hand-made states (all clear; seatbelt only; person at 4 m; person at 2 m + unfastened + rain; high speed near person). Stop when done.
```

**Done when:** the 5 test states give sensible levels and readable reasons.

## Phase A5 — Unusual behaviour detection

```
Read docs/TRACK_A.md (shared definitions) and docs/ARCHITECTURE.md §5.7 and §6.
Phase A5: create ml/train_anomaly.py and ml/anomaly.py:
- Features per session using ml/common.py: idle_pct, fuel_rate_lph, cycle_time_s, fuel_per_cycle_l, plus task_type one-hot (behaviour differs by task). All must be computable from a live state dict too.
- Train IsolationForest (contamination ≈ observed anomaly rate, seed 42) with a StandardScaler, in a sklearn Pipeline.
- Evaluate against the injected anomaly_flag: precision, recall, F1, and per-anomaly_type recall. Save to ml/reports/anomaly_metrics.json.
- Per-operator baselines (median idle_time_min, idle_pct, fuel_rate_lph, cycle_time_s per operator, also per operator+task_type) saved to ml/artifacts/anomaly_meta.json with the feature order and thresholds. Also save ml/artifacts/anomaly_model.joblib.
- anomaly.py: detect(state: dict, operator_id: str, fallback_baseline: dict | None) -> list[dict] matching AnomalyCreate. Logic: compute features, get the IsolationForest score (normalised to 0–1 as anomaly_score). Then assign type and message with explainable ratio rules against the operator's own baseline: idle_pct > 1.8× baseline or idle_time_min > 2× baseline → excessive_idling ("Idle time 75 min vs your usual 24 min"); fuel_rate > 1.6× → fuel_spike; cycle_time > 2× → abnormal_cycle_time; unfastened + person in zone + proximity < 3 → unsafe_operation. Report an anomaly if a ratio rule fires (always) or if the IF score is high AND some ratio is elevated. Severity from how far past the threshold. Use anomaly_meta baselines first; fall back to the baseline passed in by the backend.
Test on: a normal OP1001 state, an idle-heavy state, a fuel-spike state, and an unsafe state. Stop when done.
```

**Done when:** each test state produces the expected type with a clear message; metrics saved for the deck.

## Phase A6 — Live ML service in the backend (branch `a/ml-service`, after M1)

Before starting: `git checkout dev && git pull && git checkout -b a/ml-service`. Confirm `backend/app/services/ml/interface.py` exists (Person B's stub).

```
Read CLAUDE.md rules 1–2, docs/ARCHITECTURE.md §6, backend/app/services/ml/interface.py and backend/app/services/ml/stub.py. You may ONLY edit files inside backend/app/services/ml/ and append ML packages to backend/requirements.txt (same pinned versions as ml/requirements.txt). Do not change any function signature in interface.py or any schema.
Phase A6:
- Create backend/app/services/ml/live.py implementing predict_task_time, assess_safety, detect_anomalies and recommend_training (recommender can call the stub for now; A7 replaces it), porting logic from ml/predict_task_time.py, ml/safety.py and ml/anomaly.py. Convert between Pydantic schemas and dicts at the boundary.
- load_models(): load artifacts from settings.MODEL_DIR once into module-level state; log what loaded. If any artifact is missing or fails to load, log a warning and fall back to the stub for that function only, so the app never crashes.
- interface.py: dispatch to live when ml_mode() == "live", else stub. Keep signatures identical.
- Add backend/tests/test_ml_live.py calling each interface function in live mode with sample inputs and validating the returned schema.
Run the backend with ML_MODE=live, hit /api/health (ml_mode should be "live"), /api/predict/task-time with the T002 example, and /api/safety/status. Stop when done.
```

**Done when:** `/api/health` shows `live`; predictions come from the real model; deleting an artifact makes that function fall back to the stub without crashing.

## Phase A7 — Training recommender

```
Read docs/ARCHITECTURE.md §5.9 and §6 and backend/app/db/seed_training.json.
Phase A7: implement recommend_training in backend/app/services/ml/live.py:
- Map each recent anomaly_type / incident event_type to modules via trigger_anomaly_type (and a small mapping table for event types without a direct trigger, e.g. manual_report → Incident Response Basics; Rainy-weather incidents → Wet-Weather Operation).
- Priority: high if the triggering event was high severity or repeated ≥ 2 times in the recent window, medium otherwise, low for general upskilling (fill up to 3 recommendations using the operator's weakest area, e.g. most frequent anomaly type in their history).
- Reasons are specific: "Triggered by 2 excessive-idling alerts today", "Proximity hazard at 10:32 on EXC001".
- De-duplicate modules, max 4, sorted by priority.
Extend test_ml_live.py. Stop when done.
```

**Done when:** triggering `excessive_idle` in the demo panel produces a Fuel-Efficient Operation recommendation with a specific reason.

## Phase A8 — ML report and deck material

```
Phase A8: write docs/ML_REPORT.md for judges and interviewers:
1. Why synthetic data, and how the generator encodes real-world relationships (list them), grounded in public telematics facts: heavy equipment commonly idles ~30–40% of engine hours; idle reduction is a major fuel-saving lever.
2. Task-time model: features and why fuel/idle/cycles are excluded (leakage), baselines vs XGBoost metrics table, feature importance image, example explanation.
3. Safety engine: rules + why explainable rules for operator-facing alerts, LR coefficient check.
4. Anomaly detection: IsolationForest + per-operator baselines, precision/recall per type, why unsupervised (real anomalies are rarely labelled).
5. Limitations and next steps: real CAT telematics data, retraining pipeline, per-machine-model calibration, CV for seatbelt/person detection feeding the same safety engine.
Also produce 4 slide-ready PNGs in ml/reports/ (data relationships, task-time metrics, anomaly metrics, safety factor weights). Stop when done.
```

**Done when:** you can explain every number in the report without looking at the code.

---

## Interview-ready talking points (Person A should be able to say these)

- "We predict task time only from what's known before the task starts, so the model is usable for planning and has no leakage."
- "Safety alerts are rule-based with contributions, because an operator needs to know *why* they're being warned. We checked the weights against a logistic regression."
- "Anomaly detection combines an unsupervised IsolationForest with each operator's own baseline, so 'excessive' means excessive *for you*, not for the fleet average."
- "Synthetic data is a stand-in. The CSV contract mirrors telematics fields, so real Product Link / VisionLink-style data could replace it without changing the app."
