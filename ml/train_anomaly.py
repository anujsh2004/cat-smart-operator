"""Train the unusual-behaviour detector (Phase A5).

StandardScaler + IsolationForest on per-session behaviour features, evaluated against the
injected anomaly_flag, plus per-operator baselines for the explainable ratio rules.

Usage: python ml/train_anomaly.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from anomaly import (
    ARTIFACTS, BASELINE_KEYS, FEATURE_COLUMNS, MODEL_NAME, THRESHOLDS, detect_with_score,
    feature_frame, normalise_score,
)
from common import ANOMALY_TYPES, idle_pct

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated" / "sessions.csv"
REPORTS = ROOT / "ml" / "reports"
SEED = 42


def baselines(df: pd.DataFrame) -> dict:
    """Median behaviour per operator, per operator+task_type, and fleet per task_type."""
    b = pd.DataFrame({
        "operator_id": df["operator_id"],
        "task_type": df["task_type"],
        "idle_time_min": df["idle_time_min"],
        "idle_pct": idle_pct(df),
        "fuel_rate_lph": feature_frame(df)["fuel_rate_lph"],
        "cycle_time_s": feature_frame(df)["cycle_time_s"],
    })

    def table(keys: list[str]) -> dict:
        med = b.groupby(keys)[BASELINE_KEYS].median().round(3)
        return {("|".join(k) if isinstance(k, tuple) else k): row.to_dict() for k, row in med.iterrows()}

    return {
        "operator": table(["operator_id"]),
        "operator_task": table(["operator_id", "task_type"]),
        "task_type": table(["task_type"]),
    }


def scores(y_true: pd.Series, y_pred: np.ndarray, types: pd.Series) -> dict:
    per_type = {t: round(float(y_pred[(types == t).to_numpy()].mean()), 3) for t in ANOMALY_TYPES}
    return {
        "precision": round(float(precision_score(y_true, y_pred)), 3),
        "recall": round(float(recall_score(y_true, y_pred)), 3),
        "f1": round(float(f1_score(y_true, y_pred)), 3),
        "recall_by_type": per_type,
        "flagged_rate": round(float(y_pred.mean()), 4),
    }


def main() -> None:
    df = pd.read_csv(DATA, keep_default_na=False, na_values=[""])
    train, test = train_test_split(df, test_size=0.2, random_state=SEED, stratify=df["anomaly_flag"])
    contamination = float(train["anomaly_flag"].mean())

    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("iforest", IsolationForest(n_estimators=200, contamination=contamination, random_state=SEED)),
    ])
    pipe.fit(feature_frame(train))

    raw_train = -pipe.score_samples(feature_frame(train))
    scaling = {"lo": float(np.percentile(raw_train, 50)), "hi": float(np.percentile(raw_train, 99.9))}
    scaling["threshold"] = float(normalise_score(np.array([-pipe[-1].offset_]), scaling)[0])

    meta = {
        "model": MODEL_NAME,
        "feature_columns": FEATURE_COLUMNS,
        "contamination": round(contamination, 4),
        "score_scaling": {k: round(v, 5) for k, v in scaling.items()},
        "thresholds": THRESHOLDS,
        "baselines": baselines(train),
        "versions": {"scikit-learn": sklearn.__version__, "pandas": pd.__version__,
                     "numpy": np.__version__, "joblib": joblib.__version__},
    }

    # Evaluate on the held-out 20%: IsolationForest alone, then the full hybrid detect().
    y_true = test["anomaly_flag"].astype(bool)
    types = test["anomaly_type"]
    X_test = feature_frame(test)
    if_pred = pipe.predict(X_test) == -1
    if_score = normalise_score(-pipe.score_samples(X_test), scaling)

    hybrid_pred, hybrid_type_hit = [], []
    for (_, row), s in zip(test.iterrows(), if_score):
        state = row.to_dict()
        found = detect_with_score(state, row["operator_id"], None, float(s), meta)
        hybrid_pred.append(bool(found))
        hybrid_type_hit.append(any(a["anomaly_type"] == row["anomaly_type"] for a in found))
    hybrid_pred_arr = np.array(hybrid_pred)
    hybrid = scores(y_true, hybrid_pred_arr, types)
    anomalous = y_true.to_numpy()
    hybrid["correct_type_rate_on_true_anomalies"] = round(float(np.array(hybrid_type_hit)[anomalous].mean()), 3)

    results = {
        "test_rows": len(test),
        "test_anomaly_rate": round(float(y_true.mean()), 4),
        "isolation_forest_only": scores(y_true, if_pred, types),
        "hybrid_detect": hybrid,
    }
    meta["metrics"] = results

    for name in ("isolation_forest_only", "hybrid_detect"):
        m = results[name]
        print(f"{name:22} precision {m['precision']:.3f}  recall {m['recall']:.3f}  f1 {m['f1']:.3f}  "
              f"flagged {m['flagged_rate']:.1%}")
        print(f"{'':22} recall by type: {m['recall_by_type']}")
    print(f"hybrid picks the correct type for {hybrid['correct_type_rate_on_true_anomalies']:.1%} of true anomalies")

    REPORTS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "anomaly_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    joblib.dump(pipe, ARTIFACTS / "anomaly_model.joblib")
    (ARTIFACTS / "anomaly_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    op1 = meta["baselines"]["operator"]["OP1001"]
    print(f"OP1001 baseline: {op1}")
    print(f"wrote {ARTIFACTS / 'anomaly_model.joblib'}, anomaly_meta.json and {REPORTS / 'anomaly_metrics.json'}")


if __name__ == "__main__":
    main()
