"""Synthetic data generator (Phases A1 + A2).

Writes operators.csv, machines.csv, tasks_today.csv and sessions.csv with EXACTLY the
columns and enum strings of docs/ARCHITECTURE.md §4.2/§4.3, then validates them.
Sessions have deliberate, explainable relationships (skill, weather, ground, machine age,
heat -> time; idle/safety habits per operator; ~4% injected anomalies).

Usage: python data/generate.py --rows 20000 --seed 42 --out data/generated
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
from common import (  # noqa: E402
    ANOMALY_TYPES,
    GROUND_CONDITIONS,
    SEATBELT_STATUSES,
    SKILL_LEVELS,
    TASK_TYPES,
    WEATHER,
    idle_pct,
)

# --- CSV contract (ARCHITECTURE.md §4.2, exact order) ---
OPERATOR_COLS = ["operator_id", "name", "skill_level", "experience_yrs", "shift"]
MACHINE_COLS = ["machine_id", "model", "machine_type", "age_yrs", "engine_hours"]
TASK_COLS = [
    "task_id", "operator_id", "machine_id", "task_type", "site_zone",
    "scheduled_start", "weather", "ground_condition", "estimated_time_min",
]
SESSION_COLS = [
    "session_id", "timestamp", "machine_id", "operator_id", "task_type", "operator_skill",
    "operator_experience_yrs", "machine_age_yrs", "engine_hours", "weather",
    "ground_condition", "temperature_c", "fuel_used_l", "load_cycles", "avg_payload_kg",
    "idle_time_min", "operating_time_min", "seatbelt_status", "proximity_min_m",
    "people_in_zone", "estimated_time_min", "actual_time_min", "safety_risk_score",
    "safety_alert_triggered", "anomaly_flag", "anomaly_type",
]

SHIFTS = ["Morning", "Evening", "Night"]
MACHINE_TYPES = ["Excavator", "Wheel Loader", "Dozer", "Motor Grader"]
SITE_ZONES = ["Pit A", "Pit B", "Haul Road", "North Bench", "Old Structure"]
BASE_MINUTES = {
    "Earth Excavation": 60, "Trenching": 45, "Material Loading": 30,
    "Grading": 35, "Demolition": 90,
}
EXPERIENCE_RANGE = {"Beginner": (0, 2), "Intermediate": (2, 6), "Expert": (6, 15)}


def make_operators(rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    skills = ["Beginner"] * 15 + ["Intermediate"] * 22 + ["Expert"] * 13  # ~30/45/25
    rng.shuffle(skills)
    rows = []
    for i, skill in enumerate(skills):
        lo, hi = EXPERIENCE_RANGE[skill]
        rows.append({
            "operator_id": f"OP{1001 + i}",
            "name": f"{fake.first_name()} {fake.last_name()}",
            "skill_level": skill,
            "experience_yrs": int(rng.integers(lo, hi + 1)),
            "shift": str(rng.choice(SHIFTS)),
        })
    df = pd.DataFrame(rows, columns=OPERATOR_COLS)
    # Demo operator from the organisers' sample. Swap its skill with another
    # Intermediate slot's owner so the overall mix stays unchanged.
    if df.at[0, "skill_level"] != "Intermediate":
        j = df.index[df["skill_level"] == "Intermediate"][0]
        df.loc[j, ["skill_level", "experience_yrs"]] = [
            df.at[0, "skill_level"], df.at[0, "experience_yrs"]
        ]
    df.loc[0, ["skill_level", "experience_yrs", "shift"]] = ["Intermediate", 4, "Morning"]
    return df


def make_machines(rng: np.random.Generator) -> pd.DataFrame:
    fleet = (
        [("EXC", i, "Excavator", ["320 GC", "323", "330", "336"]) for i in range(1, 13)]
        + [("WL", i, "Wheel Loader", ["950 GC", "966"]) for i in range(1, 5)]
        + [("DZ", i, "Dozer", ["D6", "D8T"]) for i in range(1, 3)]
        + [("MG", i, "Motor Grader", ["140", "150"]) for i in range(1, 3)]
    )
    rows = []
    for prefix, i, mtype, models in fleet:
        age = int(rng.integers(1, 11))
        rows.append({
            "machine_id": f"{prefix}{i:03d}",
            "model": str(rng.choice(models)),
            "machine_type": mtype,
            "age_yrs": age,
            "engine_hours": round(age * rng.uniform(700, 900) + rng.normal(0, 50), 1),
        })
    df = pd.DataFrame(rows, columns=MACHINE_COLS)
    df.loc[0, ["model", "age_yrs", "engine_hours"]] = ["320 GC", 2, 1530.0]  # EXC001
    return df


def make_tasks_today(today: date) -> pd.DataFrame:
    spec = [
        ("T001", "Earth Excavation", "Pit A", time(8, 0), "Sunny", "Firm", 60),
        ("T002", "Trenching", "Pit B", time(9, 15), "Rainy", "Wet", 45),
        ("T003", "Material Loading", "Haul Road", time(10, 15), "Cloudy", "Loose", 30),
        ("T004", "Grading", "North Bench", time(11, 30), "Sunny", "Firm", 35),
        ("T005", "Demolition", "Old Structure", time(13, 0), "Windy", "Rocky", 90),
    ]
    rows = [
        {
            "task_id": tid, "operator_id": "OP1001", "machine_id": "EXC001",
            "task_type": ttype, "site_zone": zone,
            "scheduled_start": datetime.combine(today, start).isoformat(),
            "weather": weather, "ground_condition": ground,
            "estimated_time_min": float(est),
        }
        for tid, ttype, zone, start, weather, ground, est in spec
    ]
    return pd.DataFrame(rows, columns=TASK_COLS)


# --- Phase A2: explainable relationships (docs/TRACK_A.md Phase A2) ---
SKILL_FACTOR = {"Beginner": 1.25, "Intermediate": 1.05, "Expert": 0.90}
IDLE_HABIT_RANGE = {"Beginner": (0.33, 0.45), "Intermediate": (0.27, 0.38), "Expert": (0.25, 0.32)}
SAFETY_HABIT_RANGE = {"Beginner": (0.06, 0.12), "Intermediate": (0.03, 0.08), "Expert": (0.02, 0.05)}
DEMO_OPERATOR_IDLE_HABIT = 0.38  # OP1001: mildly high, so "your usual idle" is believable

TASKS_BY_MACHINE = {
    "Excavator": {"Earth Excavation": 0.45, "Trenching": 0.35, "Demolition": 0.20},
    "Wheel Loader": {"Material Loading": 1.0},
    "Motor Grader": {"Grading": 1.0},
    "Dozer": {"Grading": 0.6, "Earth Excavation": 0.4},
}
WEATHER_FACTOR = {"Sunny": 1.00, "Cloudy": 1.05, "Windy": 1.10, "Rainy": 1.20, "Foggy": 1.25}
GROUND_FACTOR = {"Firm": 1.00, "Loose": 1.08, "Rocky": 1.12, "Wet": 1.15}
TEMP_RANGE = {"Sunny": (30, 42), "Cloudy": (26, 36), "Windy": (25, 35), "Rainy": (22, 30), "Foggy": (22, 27)}
CYCLE_TIME_S = {  # seconds per productive cycle (grading = long passes, so few cycles)
    "Earth Excavation": 20, "Trenching": 24, "Material Loading": 35, "Grading": 90, "Demolition": 30,
}
WORK_FUEL_LPH = {  # working fuel burn by task
    "Earth Excavation": 16, "Trenching": 15, "Material Loading": 14, "Grading": 12, "Demolition": 19,
}
IDLE_FUEL_LPH = 3.0
PAYLOAD_KG = {"Excavator": (1200, 1800), "Wheel Loader": (3000, 4500), "Dozer": (2000, 3000), "Motor Grader": (500, 900)}
ANOMALY_RATE = 0.04


def operator_traits(rng: np.random.Generator, operators: pd.DataFrame) -> pd.DataFrame:
    """Latent per-operator habits, sampled once. Never written to CSV; they only shape sessions."""
    traits = []
    for op_id, skill in zip(operators["operator_id"], operators["skill_level"]):
        traits.append({
            "operator_id": op_id,
            "skill_factor": SKILL_FACTOR[skill] * (1 + rng.normal(0, 0.04)),
            "idle_habit": DEMO_OPERATOR_IDLE_HABIT if op_id == "OP1001" else rng.uniform(*IDLE_HABIT_RANGE[skill]),
            "safety_habit": rng.uniform(*SAFETY_HABIT_RANGE[skill]),
        })
    return pd.DataFrame(traits)


def sample_weather(rng: np.random.Generator, days_ago: np.ndarray) -> np.ndarray:
    """Seasonal-ish: rain is likelier further back (monsoon), easing towards today."""
    p_rain = 0.12 + 0.18 * (days_ago / 90)
    out = np.empty(len(days_ago), dtype=object)
    for i, pr in enumerate(p_rain):
        probs = np.array([0.38, 0.25, 0.12, pr, 0.05])  # Sunny, Cloudy, Windy, Rainy, Foggy
        out[i] = rng.choice(WEATHER, p=probs / probs.sum())
    return out


def sample_ground(rng: np.random.Generator, weather: np.ndarray) -> np.ndarray:
    """Rain strongly raises the chance of Wet ground. Order: Firm, Loose, Wet, Rocky."""
    probs = {
        "Rainy": [0.10, 0.20, 0.60, 0.10],
        "Foggy": [0.35, 0.20, 0.30, 0.15],
    }
    default = [0.50, 0.22, 0.10, 0.18]
    return np.array([rng.choice(GROUND_CONDITIONS, p=probs.get(w, default)) for w in weather])


def make_sessions(
    rng: np.random.Generator, n: int, operators: pd.DataFrame, machines: pd.DataFrame, now: datetime
) -> pd.DataFrame:
    traits = operator_traits(rng, operators).set_index("operator_id")
    ops = operators.iloc[rng.integers(0, len(operators), n)].reset_index(drop=True)
    mcs = machines.iloc[rng.integers(0, len(machines), n)].reset_index(drop=True)
    tr = traits.loc[ops["operator_id"]].reset_index(drop=True)

    offsets = rng.uniform(0, 90 * 24 * 3600, n)
    timestamps = [(now - timedelta(seconds=float(s))).replace(microsecond=0).isoformat() for s in offsets]
    days_ago = offsets / 86400

    task_type = np.array([
        rng.choice(list(TASKS_BY_MACHINE[m]), p=list(TASKS_BY_MACHINE[m].values()))
        for m in mcs["machine_type"]
    ])
    weather = sample_weather(rng, days_ago)
    ground = sample_ground(rng, weather)
    temperature = np.array([rng.uniform(*TEMP_RANGE[w]) for w in weather]).round(1)

    age = mcs["age_yrs"].to_numpy(dtype=float)
    estimated = np.array([BASE_MINUTES[t] for t in task_type], dtype=float)  # planner's naive estimate
    actual = (
        estimated
        * tr["skill_factor"].to_numpy()
        * np.array([WEATHER_FACTOR[w] for w in weather])
        * np.array([GROUND_FACTOR[g] for g in ground])
        * (1 + 0.01 * age)
        * np.where(temperature > 38, 1.05, 1.0)
        * rng.lognormal(0, 0.07, n)
    )
    operating = actual

    # idle_habit is the idle share of engine-on time: idle = op * s / (1 - s)
    idle_share = np.clip(tr["idle_habit"].to_numpy() + rng.normal(0, 0.05, n), 0.05, 0.70)
    idle = operating * idle_share / (1 - idle_share)

    cycle_s = np.array([CYCLE_TIME_S[t] for t in task_type]) * rng.normal(1, 0.10, n)
    load_cycles = np.maximum(1, operating * 60 / cycle_s)
    payload = np.array([rng.uniform(*PAYLOAD_KG[m]) for m in mcs["machine_type"]])
    work_rate = np.array([WORK_FUEL_LPH[t] for t in task_type]) * rng.normal(1, 0.08, n)

    seatbelt = np.where(rng.random(n) < tr["safety_habit"].to_numpy(), "Unfastened", "Fastened")
    p_people = np.where(np.isin(task_type, ["Demolition", "Material Loading"]), 0.18, 0.10)
    people = (rng.random(n) < p_people).astype(int)
    proximity = np.where(people > 0, rng.uniform(1, 5, n), rng.uniform(8, 50, n))

    # Inject anomalies, each with a clear signature.
    anomaly_flag = rng.random(n) < ANOMALY_RATE
    anomaly_type = np.where(anomaly_flag, rng.choice(ANOMALY_TYPES, n), "")
    fuel_mult = np.ones(n)
    for i in np.flatnonzero(anomaly_flag):
        kind = anomaly_type[i]
        if kind == "excessive_idling":
            idle[i] *= rng.uniform(2.5, 3.5)
        elif kind == "fuel_spike":
            fuel_mult[i] = rng.uniform(1.8, 2.5)
        elif kind == "abnormal_cycle_time":
            load_cycles[i] *= rng.uniform(0.3, 0.5)
        elif kind == "unsafe_operation":
            seatbelt[i], people[i], proximity[i] = "Unfastened", 1, rng.uniform(1, 3)

    fuel = (operating / 60 * work_rate + idle / 60 * IDLE_FUEL_LPH) * (1 + 0.015 * age) * fuel_mult

    unfastened = seatbelt == "Unfastened"
    in_zone = people > 0
    risk = (
        10
        + 30 * unfastened
        + 40 * in_zone
        + 20 * (proximity < 5)
        + 12 * np.isin(weather, ["Rainy", "Foggy"])
        + 10 * (unfastened & in_zone)
        + rng.normal(0, 3, n)
    )
    risk = np.clip(risk, 0, 100).round(1)

    df = pd.DataFrame({
        "session_id": [f"S{i:06d}" for i in range(1, n + 1)],
        "timestamp": timestamps,
        "machine_id": mcs["machine_id"],
        "operator_id": ops["operator_id"],
        "task_type": task_type,
        "operator_skill": ops["skill_level"],
        "operator_experience_yrs": ops["experience_yrs"].astype(int),
        "machine_age_yrs": mcs["age_yrs"].astype(int),
        "engine_hours": mcs["engine_hours"].astype(float),
        "weather": weather,
        "ground_condition": ground,
        "temperature_c": temperature,
        "fuel_used_l": np.round(fuel, 2),
        "load_cycles": np.maximum(1, load_cycles).astype(int),
        "avg_payload_kg": np.round(payload, 1),
        "idle_time_min": np.round(idle, 2),
        "operating_time_min": np.round(operating, 2),
        "seatbelt_status": seatbelt,
        "proximity_min_m": np.round(proximity, 2),
        "people_in_zone": people,
        "estimated_time_min": estimated,
        "actual_time_min": np.round(actual, 2),
        "safety_risk_score": risk,
        "safety_alert_triggered": risk >= 70,
        "anomaly_flag": anomaly_flag,
        "anomaly_type": anomaly_type,
    })
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["session_id"] = [f"S{i:06d}" for i in range(1, n + 1)]  # chronological ids
    return df[SESSION_COLS]


def write_sanity_plots(sessions: pd.DataFrame, path: Path) -> None:
    """4 small plots showing the intended relationships (ml/reports/data_sanity.png)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    sessions.boxplot(column="actual_time_min", by="task_type", ax=ax[0, 0], showfliers=False)
    ax[0, 0].set_title("Actual time by task type (min)")
    sessions.groupby("weather")["actual_time_min"].mean().reindex(WEATHER).plot.bar(ax=ax[0, 1], color="#4c78a8")
    ax[0, 1].set_title("Mean actual time by weather (min)")
    normal = sessions[~sessions["anomaly_flag"]]
    ax[1, 0].hist(idle_pct(normal), bins=40, alpha=0.7, density=True, label="normal")
    ax[1, 0].hist(idle_pct(sessions[sessions["anomaly_type"] == "excessive_idling"]), bins=20, alpha=0.7, density=True, label="excessive_idling")
    ax[1, 0].set_title("Idle % of engine-on time (density)")
    ax[1, 0].legend()
    grp = sessions.groupby([sessions["seatbelt_status"], sessions["people_in_zone"] > 0])["safety_risk_score"].mean()
    grp.index = [f"{s}\n{'person in zone' if p else 'zone clear'}" for s, p in grp.index]
    grp.plot.bar(ax=ax[1, 1], color="#e45756", rot=0)
    ax[1, 1].axhline(70, ls="--", color="grey")
    ax[1, 1].set_title("Mean risk score: seatbelt x people in zone (alert >= 70)")
    for a in ax.flat:
        a.set_xlabel("")
    fig.suptitle("")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)


def _check(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def _check_enum(df: pd.DataFrame, col: str, allowed: list[str], errors: list[str], file: str) -> None:
    bad = set(df[col].dropna().unique()) - set(allowed)
    _check(not bad, f"{file}.{col} has values outside contract: {sorted(bad)}", errors)


def validate(out: Path) -> bool:
    errors: list[str] = []
    contract = {
        "operators.csv": OPERATOR_COLS, "machines.csv": MACHINE_COLS,
        "tasks_today.csv": TASK_COLS, "sessions.csv": SESSION_COLS,
    }
    dfs: dict[str, pd.DataFrame] = {}
    for file, cols in contract.items():
        df = pd.read_csv(out / file, keep_default_na=False, na_values=[""])
        dfs[file] = df
        _check(list(df.columns) == cols, f"{file} columns {list(df.columns)} != contract {cols}", errors)

    ops, mcs, tasks, ses = (dfs[f] for f in contract)

    _check_enum(ops, "skill_level", SKILL_LEVELS, errors, "operators")
    _check_enum(ops, "shift", SHIFTS, errors, "operators")
    _check_enum(mcs, "machine_type", MACHINE_TYPES, errors, "machines")
    _check_enum(tasks, "task_type", TASK_TYPES, errors, "tasks_today")
    _check_enum(tasks, "weather", WEATHER, errors, "tasks_today")
    _check_enum(tasks, "ground_condition", GROUND_CONDITIONS, errors, "tasks_today")
    for col, allowed in [
        ("task_type", TASK_TYPES), ("operator_skill", SKILL_LEVELS), ("weather", WEATHER),
        ("ground_condition", GROUND_CONDITIONS), ("seatbelt_status", SEATBELT_STATUSES),
        ("anomaly_type", ANOMALY_TYPES),
    ]:
        _check_enum(ses, col, allowed, errors, "sessions")

    _check(len(ops) == 50 and ops["operator_id"].is_unique, "operators: need 50 unique ids", errors)
    _check(len(mcs) == 20 and mcs["machine_id"].is_unique, "machines: need 20 unique ids", errors)
    _check(len(tasks) == 5, "tasks_today: need 5 rows", errors)
    op1 = ops.set_index("operator_id").loc["OP1001"]
    _check((op1["skill_level"], op1["experience_yrs"], op1["shift"]) == ("Intermediate", 4, "Morning"),
           "OP1001 must be Intermediate / 4 yrs / Morning", errors)
    exc1 = mcs.set_index("machine_id").loc["EXC001"]
    _check(exc1["age_yrs"] == 2 and abs(exc1["engine_hours"] - 1530) < 1, "EXC001 must be 2 yrs / ~1530 h", errors)
    _check(set(ses["operator_id"]) <= set(ops["operator_id"]), "sessions: unknown operator_id", errors)
    _check(set(ses["machine_id"]) <= set(mcs["machine_id"]), "sessions: unknown machine_id", errors)
    _check(not ses.drop(columns="anomaly_type").isna().any().any(), "sessions: unexpected NaNs", errors)
    _check(ses["safety_risk_score"].between(0, 100).all(), "sessions: risk score out of 0-100", errors)
    _check(ses["safety_alert_triggered"].dtype == bool and ses["anomaly_flag"].dtype == bool,
           "sessions: flag columns must be boolean", errors)
    _check((ses["anomaly_flag"] == ses["anomaly_type"].notna()).all(),
           "sessions: anomaly_type must be set iff anomaly_flag", errors)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    for file, df in dfs.items():
        print(f"\n=== {file}: {len(df)} rows ===")
        print(df.describe(include="all").T.to_string())

    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    print("\nVALIDATION PASSED: all 4 CSVs match the §4.2 columns and §4.3 enums.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=int, default=20000, help="number of historical sessions")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "generated")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    random.seed(args.seed)
    Faker.seed(args.seed)
    fake = Faker("en_IN")
    now = datetime.now().replace(microsecond=0)

    args.out.mkdir(parents=True, exist_ok=True)
    operators = make_operators(rng, fake)
    machines = make_machines(rng)
    tasks = make_tasks_today(now.date())
    sessions = make_sessions(rng, args.rows, operators, machines, now)

    for name, df in [("operators.csv", operators), ("machines.csv", machines),
                     ("tasks_today.csv", tasks), ("sessions.csv", sessions)]:
        df.to_csv(args.out / name, index=False)
        print(f"wrote {args.out / name} ({len(df)} rows)")

    plot_path = ROOT / "ml" / "reports" / "data_sanity.png"
    write_sanity_plots(sessions, plot_path)
    print(f"wrote {plot_path}")

    ok = validate(args.out)
    print(f"\nanomaly rate: {sessions['anomaly_flag'].mean():.1%}  "
          f"{sessions.loc[sessions['anomaly_flag'], 'anomaly_type'].value_counts().to_dict()}")
    print(f"alert rate:   {sessions['safety_alert_triggered'].mean():.1%}")
    op1 = sessions[sessions["operator_id"] == "OP1001"]
    print(f"OP1001: {len(op1)} sessions, median idle {op1['idle_time_min'].median():.1f} min, "
          f"median idle% {idle_pct(op1).median():.1f} (fleet {idle_pct(sessions).median():.1f})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
