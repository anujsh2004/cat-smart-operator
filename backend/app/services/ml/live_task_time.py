"""Task-time prediction with the trained XGBoost model (port of ml/predict_task_time.py).

Pure functions on dicts; live.py handles loading and the Pydantic boundary.
"""
from typing import Any, Mapping

import pandas as pd
import xgboost as xgb

MODEL_NAME = "xgb_task_time_v1"
NUMERIC = ["operator_experience_yrs", "machine_age_yrs", "temperature_c"]
# task_type is already explained by historical_avg_min, so it is not repeated as a factor
FACTOR_EXCLUDE = {"task_type"}


def encode(row: Mapping[str, Any], meta: Mapping[str, Any]) -> pd.DataFrame:
    """One-hot encode a single request in the exact column order the model was trained on."""
    values: dict[str, float] = {col: float(row[col]) for col in NUMERIC}
    for col, cats in meta["categories"].items():
        for cat in cats:
            values[f"{col}={cat}"] = 1.0 if row[col] == cat else 0.0
    return pd.DataFrame([values])[meta["feature_columns"]]


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
        return f"Heat {float(value):g} °C" if float(value) > 38 else f"Temperature {float(value):g} °C"
    return f"{feature} = {value}"


def predict(model: xgb.XGBRegressor, meta: Mapping[str, Any], request: Mapping[str, Any]) -> dict:
    """request: TaskTimeRequest as a dict. Returns a TaskTimePrediction-shaped dict."""
    X = encode(request, meta)
    predicted = float(model.predict(X)[0])
    contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]  # drop bias

    # Sum one-hot contributions back to their original feature
    by_feature: dict[str, float] = {}
    for col, c in zip(meta["feature_columns"], contribs):
        feat = col.split("=", 1)[0]
        by_feature[feat] = by_feature.get(feat, 0.0) + float(c)

    top = sorted((f for f in by_feature if f not in FACTOR_EXCLUDE),
                 key=lambda f: abs(by_feature[f]), reverse=True)[:3]
    band = meta.get("band_z", 1.28) * meta["residual_std"]
    return {
        "predicted_time_min": round(predicted, 1),
        "lower_min": round(max(0.0, predicted - band), 1),
        "upper_min": round(predicted + band, 1),
        "historical_avg_min": round(meta["historical_avg_min"][request["task_type"]], 1),
        "model": meta.get("model", MODEL_NAME),
        "top_factors": [
            {"feature": f, "label": factor_label(f, request[f]), "impact_min": round(by_feature[f], 1)}
            for f in top
        ],
    }
