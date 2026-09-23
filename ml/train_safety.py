"""Check the safety rule weights against history (Phase A4).

Fits a logistic regression on sessions.csv (target: safety_alert_triggered) and compares how
its coefficients rank the factors with the rule weights in ml/safety.py. The rules stay the
runtime source of truth (explainable); the LR is evidence for the deck that they are sensible.

Usage: python ml/train_safety.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from safety import BASE_SCORE, WEIGHTS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated" / "sessions.csv"
ARTIFACTS = ROOT / "ml" / "artifacts"
SEED = 42

# LR feature -> the rule weight it corresponds to
RULE_FOR_FEATURE = {
    "unfastened": "seatbelt",
    "people_in_zone": "people_in_zone",
    "proximity_lt_5": "proximity_warning",
    "bad_weather": "weather_bad",
    "unfastened_x_people": "interaction",
}


def features(df: pd.DataFrame) -> pd.DataFrame:
    unfastened = (df["seatbelt_status"] == "Unfastened").astype(int)
    people = (df["people_in_zone"] > 0).astype(int)
    return pd.DataFrame({
        "unfastened": unfastened,
        "people_in_zone": people,
        "proximity_lt_5": (df["proximity_min_m"] < 5).astype(int),
        "bad_weather": df["weather"].isin(["Rainy", "Foggy"]).astype(int),
        "unfastened_x_people": unfastened * people,
    })


def main() -> None:
    df = pd.read_csv(DATA)
    X, y = features(df), df["safety_alert_triggered"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)

    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    proba = lr.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, proba >= 0.5)
    auc = roc_auc_score(y_test, proba)

    coefs = dict(zip(X.columns, lr.coef_[0].round(3).tolist()))
    rule_w = {f: WEIGHTS[r] for f, r in RULE_FOR_FEATURE.items()}
    lr_rank = sorted(coefs, key=coefs.get, reverse=True)
    rule_rank = sorted(rule_w, key=rule_w.get, reverse=True)

    print(f"logistic regression: accuracy {acc:.3f}, ROC AUC {auc:.3f}")
    print(f"{'feature':22} {'rule weight':>11} {'LR coef':>9}")
    for f in rule_rank:
        print(f"{f:22} {rule_w[f]:11} {coefs[f]:9.2f}")
    print(f"rule ranking: {rule_rank}")
    print(f"LR ranking:   {lr_rank}")
    print(f"corr(people_in_zone, proximity_lt_5) = {X['people_in_zone'].corr(X['proximity_lt_5']):.3f} "
          "(highly collinear in history, so LR splits credit between them)")
    print("note: the LR target is the thresholded alert (score >= 70). Unfastened alone scores 40, so it only "
          "tips a session into alert together with a person in zone; its weight shows up in the interaction term.")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    meta = {
        "runtime": "rules",
        "base_score": BASE_SCORE,
        "rule_weights": WEIGHTS,
        "levels": {"LOW": "<40", "MEDIUM": "40-69", "HIGH": ">=70"},
        "logistic_regression": {
            "target": "safety_alert_triggered",
            "coefficients": coefs,
            "intercept": round(float(lr.intercept_[0]), 3),
            "test_accuracy": round(float(acc), 4),
            "test_roc_auc": round(float(auc), 4),
            "rule_ranking": rule_rank,
            "lr_ranking": lr_rank,
        },
    }
    (ARTIFACTS / "safety_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {ARTIFACTS / 'safety_meta.json'}")


if __name__ == "__main__":
    main()
