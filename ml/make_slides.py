"""Slide-ready figures for the deck (Phase A8). Reads the CSVs and the saved metrics; invents nothing.

Writes ml/reports/slide_data_relationships.png, slide_task_time_metrics.png,
slide_anomaly_metrics.png and slide_safety_weights.png.

Usage: python ml/make_slides.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from common import GROUND_CONDITIONS, SKILL_LEVELS, WEATHER, idle_pct  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "ml" / "reports"
ARTIFACTS = ROOT / "ml" / "artifacts"
SESSIONS = ROOT / "data" / "generated" / "sessions.csv"

# Default dataviz palette (light): one accent series, gray for comparison baselines, ink for text
ACCENT = "#2a78d6"
BASELINE = "#b9b7b0"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
})


def _label_bars(ax, bars, fmt: str, horizontal: bool = False) -> None:
    for b in bars:
        v = b.get_width() if horizontal else b.get_height()
        if horizontal:
            ax.text(v, b.get_y() + b.get_height() / 2, f" {fmt.format(v)}", va="center", color=INK, fontsize=11)
        else:
            ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", color=INK, fontsize=11)


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(REPORTS / name, dpi=150)
    plt.close(fig)
    print(f"wrote {REPORTS / name}")


def data_relationships(df: pd.DataFrame) -> None:
    normal = df[~df["anomaly_flag"]].copy()
    normal["ratio"] = normal["actual_time_min"] / normal["estimated_time_min"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
    for ax, col, order, title in [
        (axes[0], "weather", WEATHER, "Weather"),
        (axes[1], "ground_condition", GROUND_CONDITIONS, "Ground"),
        (axes[2], "operator_skill", SKILL_LEVELS, "Operator skill"),
    ]:
        vals = normal.groupby(col)["ratio"].mean().reindex(order)
        bars = ax.bar(vals.index, vals.values, color=ACCENT, width=0.6)
        _label_bars(ax, bars, "{:.2f}×")
        ax.axhline(1.0, color=MUTED, lw=1, ls="--")
        ax.set_ylim(0.8, max(1.6, vals.max() + 0.1))
        ax.set_title(title, loc="left")
        ax.tick_params(axis="x", labelrotation=20)
    axes[0].set_ylabel("actual ÷ planned time")
    ip = idle_pct(normal)
    counts, _, _ = axes[3].hist(ip, bins=40, color=ACCENT, edgecolor=SURFACE, linewidth=0.5)
    top = counts.max() * 1.25
    axes[3].set_ylim(0, top)
    axes[3].axvspan(30, 40, color=BASELINE, alpha=0.35, zorder=0)
    axes[3].text(35, top * 0.98, "industry 30–40%", ha="center", va="top", color=INK_2, fontsize=10)
    axes[3].set_title(f"Idle % (median {ip.median():.0f}%)", loc="left")
    axes[3].set_ylabel("sessions")
    axes[3].set_xlabel("idle % of engine-on time")
    fig.suptitle("Synthetic data encodes real-world relationships (20,000 sessions, normal rows)",
                 fontsize=15, fontweight="bold", x=0.01, ha="left")
    _save(fig, "slide_data_relationships.png")


def task_time_metrics() -> None:
    m = json.loads((REPORTS / "task_time_metrics.json").read_text(encoding="utf-8"))["metrics"]
    rows = [
        ("Planner's estimate", m["baseline_estimated_time"], BASELINE),
        ("Average for task type", m["baseline_task_type_mean"], BASELINE),
        ("XGBoost model", m["xgb_task_time_v1"], ACCENT),
    ]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    bars = ax.barh([r[0] for r in rows], [r[1]["MAE"] for r in rows], color=[r[2] for r in rows], height=0.55)
    for b, (_, met, _) in zip(bars, rows):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2,
                f"  {met['MAE']:.1f} min   (R² {met['R2']:.2f})", va="center", color=INK, fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(r[1]["MAE"] for r in rows) * 1.45)
    ax.set_xlabel("mean absolute error on held-out sessions (minutes, lower is better)")
    ax.set_title(f"Task-time prediction: {rows[2][1]['MAE']:.1f} min average error vs "
                 f"{rows[0][1]['MAE']:.1f} min for the planner", loc="left")
    _save(fig, "slide_task_time_metrics.png")


def anomaly_metrics() -> None:
    m = json.loads((REPORTS / "anomaly_metrics.json").read_text(encoding="utf-8"))
    types = list(m["hybrid_detect"]["recall_by_type"])
    labels = [t.replace("_", " ") for t in types]
    iso = [m["isolation_forest_only"]["recall_by_type"][t] * 100 for t in types]
    hyb = [m["hybrid_detect"]["recall_by_type"][t] * 100 for t in types]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = range(len(types))
    w = 0.36
    b1 = ax.bar([i - w / 2 - 0.01 for i in x], iso, w, color=BASELINE, label="IsolationForest alone")
    b2 = ax.bar([i + w / 2 + 0.01 for i in x], hyb, w, color=ACCENT, label="IsolationForest + your-baseline rules")
    _label_bars(ax, b1, "{:.0f}%")
    _label_bars(ax, b2, "{:.0f}%")
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 128)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("recall (% of injected anomalies caught)")
    h = m["hybrid_detect"]
    ax.set_title(f"Unusual behaviour: combined detector catches {h['recall'] * 100:.0f}% "
                 f"(precision {h['precision'] * 100:.0f}%, F1 {h['f1']:.2f})", loc="left")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 1.0), ncol=2)
    _save(fig, "slide_anomaly_metrics.png")


def safety_weights() -> None:
    meta = json.loads((ARTIFACTS / "safety_meta.json").read_text(encoding="utf-8"))
    w = meta["rule_weights"]
    names = {
        "people_in_zone": "Person in operating zone", "seatbelt": "Seatbelt unfastened",
        "proximity_danger": "Obstacle < 3 m", "proximity_warning": "Obstacle < 5 m",
        "weather_bad": "Rain or fog", "interaction": "Unbelted AND person in zone",
        "speed_near_people": "Speed > 8 km/h near people", "weather_windy": "Wind",
    }
    order = sorted(w, key=w.get)
    lr = meta["logistic_regression"]
    lr_names = {"people_in_zone": "Person in operating zone", "proximity_lt_5": "Obstacle < 5 m",
                "bad_weather": "Rain or fog", "unfastened_x_people": "Unbelted AND person in zone",
                "unfastened": "Seatbelt unfastened"}
    lr_order = sorted(lr["coefficients"], key=lr["coefficients"].get)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.2, 1]})
    bars = a1.barh([names[k] for k in order], [w[k] for k in order], color=ACCENT, height=0.6)
    _label_bars(a1, bars, "+{:.0f}", horizontal=True)
    a1.set_xlim(0, max(w.values()) * 1.2)
    a1.set_xlabel(f"points added to a base of {meta['base_score']} (alert at ≥ 70)")
    a1.set_title("Runtime rules: every point has a reason", loc="left")

    bars = a2.barh([lr_names[k] for k in lr_order], [lr["coefficients"][k] for k in lr_order],
                   color=BASELINE, height=0.6)
    _label_bars(a2, bars, "{:.1f}", horizontal=True)
    a2.set_xlim(0, max(lr["coefficients"].values()) * 1.25)
    a2.set_xlabel(f"logistic-regression coefficient (ROC AUC {lr['test_roc_auc']:.2f})")
    a2.set_title("Check on 20k historical sessions", loc="left")
    _save(fig, "slide_safety_weights.png")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SESSIONS, keep_default_na=False, na_values=[""])
    data_relationships(df)
    task_time_metrics()
    anomaly_metrics()
    safety_weights()


if __name__ == "__main__":
    main()
