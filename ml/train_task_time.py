"""Train the task-time model (Phase A3).

Features: only what is known before the task starts (no fuel, idle, cycles or actual time).
Baselines to beat: (a) the planner's estimated_time_min, (b) mean actual time per task_type.

Usage: python ml/train_task_time.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
import xgboost as xgb  # noqa: E402
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from predict_task_time import (  # noqa: E402
    ARTIFACTS, CATEGORICAL, FEATURES, MODEL_NAME, TARGET, encode, predict, source_feature,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated" / "sessions.csv"
REPORTS = ROOT / "ml" / "reports"
SEED = 42


def metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3),
        "R2": round(float(r2_score(y_true, y_pred)), 4),
    }


def main() -> None:
    df = pd.read_csv(DATA)
    train, test = train_test_split(df, test_size=0.2, random_state=SEED)

    X_train, X_test = encode(train), encode(test)
    feature_columns = list(X_train.columns)
    y_train, y_test = train[TARGET], test[TARGET]

    task_means = train.groupby("task_type")[TARGET].mean()
    results = {
        "baseline_estimated_time": metrics(y_test, test["estimated_time_min"].to_numpy()),
        "baseline_task_type_mean": metrics(y_test, test["task_type"].map(task_means).to_numpy()),
    }

    model = xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.9,
        colsample_bytree=0.9, random_state=SEED, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    results[MODEL_NAME] = metrics(y_test, pred)
    residual_std = float(np.std(y_test - pred))

    print(f"{'model':28} {'MAE':>8} {'RMSE':>8} {'R2':>8}")
    for name, m in results.items():
        print(f"{name:28} {m['MAE']:8.2f} {m['RMSE']:8.2f} {m['R2']:8.3f}")
    beats = all(results[MODEL_NAME]["MAE"] < results[b]["MAE"] for b in results if b != MODEL_NAME)
    print(f"beats both baselines on MAE: {beats}   residual std: {residual_std:.2f} min")

    REPORTS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "task_time_metrics.json").write_text(
        json.dumps({"test_rows": len(test), "metrics": results, "beats_baselines_on_mae": beats}, indent=2),
        encoding="utf-8",
    )

    joblib.dump(model, ARTIFACTS / "task_time_model.joblib")
    meta = {
        "model": MODEL_NAME,
        "features": FEATURES,
        "feature_columns": feature_columns,
        "categories": CATEGORICAL,
        "target": TARGET,
        "historical_avg_min": {k: round(float(v), 2) for k, v in df.groupby("task_type")[TARGET].mean().items()},
        "residual_std": round(residual_std, 3),
        "band_z": 1.28,
        "metrics": results,
        "versions": {
            "xgboost": xgb.__version__, "scikit-learn": sklearn.__version__,
            "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__,
        },
    }
    (ARTIFACTS / "task_time_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Importance = mean |XGBoost contribution| on the test set, one-hots summed to their feature.
    contribs = model.get_booster().predict(xgb.DMatrix(X_test), pred_contribs=True)[:, :-1]
    imp = pd.Series(np.abs(contribs).mean(axis=0), index=feature_columns)
    imp = imp.groupby(source_feature).sum().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    imp.plot.barh(ax=ax, color="#4c78a8")
    ax.set_xlabel("mean |impact| on predicted minutes")
    ax.set_title("Task-time model: feature importance")
    fig.tight_layout()
    fig.savefig(REPORTS / "task_time_importance.png", dpi=110)
    plt.close(fig)
    print("importance (mean |impact| min):", imp.sort_values(ascending=False).round(2).to_dict())

    # Demo: T002 (Trenching, Rainy, Wet) vs the same task in Sunny/Firm.
    base = {
        "task_type": "Trenching", "operator_id": "OP1001", "operator_skill": "Intermediate",
        "operator_experience_yrs": 4, "machine_age_yrs": 2, "temperature_c": 27,
    }
    for label, cond in [("T002 Rainy/Wet", {"weather": "Rainy", "ground_condition": "Wet"}),
                        ("Same task Sunny/Firm", {"weather": "Sunny", "ground_condition": "Firm"})]:
        p = predict({**base, **cond})
        print(f"\n{label}: {p['predicted_time_min']} min "
              f"[{p['lower_min']}–{p['upper_min']}], historical avg {p['historical_avg_min']}")
        for f in p["top_factors"]:
            print(f"   {f['impact_min']:+6.1f} min  {f['label']}")


if __name__ == "__main__":
    main()
