"""Task-time prediction (Phase A3). Output matches TaskTimePrediction in ARCHITECTURE.md Â§5.6.

No leakage: only features known BEFORE the task starts are used (docs/TRACK_A.md rule 2).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd
import xgboost as xgb

from common import GROUND_CONDITIONS, SKILL_LEVELS, TASK_TYPES, WEATHER

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
MODEL_NAME = "xgb_task_time_v1"
BAND_Z = 1.28  # ~80% band

CATEGORICAL = {
    "task_type": TASK_TYPES,
    "operator_skill": SKILL_LEVELS,
    "weather": WEATHER,
    "ground_condition": GROUND_CONDITIONS,
}
NUMERIC = ["operator_experience_yrs", "machine_age_yrs", "temperature_c"]
FEATURES = list(CATEGORICAL) + NUMERIC
TARGET = "actual_time_min"
# task_type is explained by historical_avg_min, so it is not repeated as a "factor"
FACTOR_EXCLUDE = {"task_type"}


def encode(df: pd.DataFrame, categories: Mapping[str, list[str]] = CATEGORICAL) -> pd.DataFrame:
    """One-hot encode with a fixed column order: numerics, then each category in list order."""
    out = df[NUMERIC].astype(float).copy()
    for col, cats in categories.items():
        for cat in cats:
            out[f"{col}={cat}"] = (df[col] == cat).astype(float)
    return out


def source_feature(column: str) -> str:
    """Map an encoded column name back to its original feature."""
    return column.split("=", 1)[0]


def factor_label(feature: str, value: Any) -> str:
    if feature == "weather":
        return f"{value} weather"
    if feature == "ground_condition":
        return f"{value} ground"
    if feature == "operator_skill":
        return f"{value} operator"
    if feature == "operator_experience_yrs":
        return f"{int(value)} yrs operator experience"
    if feature == "machine_age_yrs":
        return f"Machine age {int(value)} yrs"
    if feature == "temperature_c":
        return f"Heat {float(value):g} Â°C" if float(value) > 38 else f"Temperature {float(value):g} Â°C"
    return f"{feature} = {value}"


_cache: dict[str, Any] = {}


def load(artifacts: Path = ARTIFACTS) -> tuple[xgb.XGBRegressor, dict]:
    key = str(artifacts)
    if key not in _cache:
        model = joblib.load(artifacts / "task_time_model.joblib")
        meta = json.loads((artifacts / "task_time_meta.json").read_text(encoding="utf-8"))
        _cache[key] = (model, meta)
    return _cache[key]


def predict(request: Mapping[str, Any], artifacts: Path = ARTIFACTS) -> dict:
    """request: TaskTimeRequest-shaped dict (operator_id is accepted and ignored)."""
    model, meta = load(artifacts)
    row = pd.DataFrame([{f: request[f] for f in FEATURES}])
    X = encode(row, meta["categories"])[meta["feature_columns"]]

    predicted = float(model.predict(X)[0])
    contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]  # drop bias

    by_feature: dict[str, float] = {}
    for col, c in zip(meta["feature_columns"], contribs):
        feat = source_feature(col)
        by_feature[feat] = by_feature.get(feat, 0.0) + float(c)

    top = sorted(
        (f for f in by_feature if f not in FACTOR_EXCLUDE),
        key=lambda f: abs(by_feature[f]),
        reverse=True,
    )[:3]
    band = BAND_Z * meta["residual_std"]
    return {
        "predicted_time_min": round(predicted, 1),
        "lower_min": round(max(0.0, predicted - band), 1),
        "upper_min": round(predicted + band, 1),
        "historical_avg_min": round(meta["historical_avg_min"][request["task_type"]], 1),
        "model": MODEL_NAME,
        "top_factors": [
            {"feature": f, "label": factor_label(f, request[f]), "impact_min": round(by_feature[f], 1)}
            for f in top
        ],
    }


if __name__ == "__main__":
    base = {
        "task_type": "Trenching", "operator_id": "OP1001", "operator_skill": "Intermediate",
        "operator_experience_yrs": 4, "machine_age_yrs": 2, "temperature_c": 27,
    }
    print(json.dumps(predict({**base, "weather": "Rainy", "ground_condition": "Wet"}), indent=2))
    print(json.dumps(predict({**base, "weather": "Sunny", "ground_condition": "Firm"}), indent=2))
