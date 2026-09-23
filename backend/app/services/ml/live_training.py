"""Training recommender (Phase A7). Pure logic; live.py passes in the loaded anomaly_meta.

1. Every recent anomaly / incident maps to a module: via the module's trigger_anomaly_type, plus
   a small table for events without a direct trigger (and rain/fog incidents -> Wet-Weather).
2. Priority: high if a triggering event was high severity or repeated >= 2 times, else medium.
3. Up to 3 recommendations, fill with "low" general upskilling from the operator's weakest area:
   the metric where their own baselines run furthest above the fleet for the same tasks.
4. De-duplicated, max 4, sorted by priority then most recent trigger.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from app.schemas import Anomaly, Incident, Module

MAX_RECOMMENDATIONS = 4
FILL_TO = 3
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Events whose module has no matching trigger_anomaly_type, by module title
EXTRA_EVENT_MODULES = {
    "manual_report": "Incident Response Basics",
    "fuel_spike": "Fuel-Efficient Operation",
}
BAD_WEATHER_MODULE = "Wet-Weather Operation"
BAD_WEATHER = {"Rainy": "rain", "Foggy": "fog"}

# Weakest-area metric -> (module title, readable name)
WEAK_AREA_MODULES = {
    "idle_pct": ("Fuel-Efficient Operation", "idle share"),
    "fuel_rate_lph": ("Fuel-Efficient Operation", "fuel burn"),
    "cycle_time_s": ("Smooth Cycle Technique", "cycle time"),
}
WEAK_AREA_MIN_RATIO = 1.03  # only call it "weak" if at least 3% worse than the fleet


@dataclass
class Event:
    event_type: str
    timestamp: datetime
    severity: str
    machine_id: str
    weather: str | None = None


def _label(event_type: str) -> str:
    return event_type.replace("_", " ")


def _reason(events: list[Event], now: datetime, weather_note: str | None = None) -> str:
    """Specific, newest first, leading with today's events:
    'Proximity hazard at 10:32 on EXC001', 'Triggered by 2 excessive-idling alerts today',
    'Excessive idling at 23:11 on EXC001 (5 in the last 3 days)'."""
    today = [e for e in events if e.timestamp.date() == now.date()]
    lead = today or events
    oldest = min(e.timestamp for e in events)
    earlier = (f" ({len(events)} in the last {(now.date() - oldest.date()).days + 1} days)"
               if today and len(today) < len(events) else "")

    if len(lead) == 1:
        e = lead[0]
        where = f" in {weather_note}" if weather_note else ""
        date = "" if e.timestamp.date() == now.date() else f", {e.timestamp:%d %b}"
        return f"{_label(e.event_type).capitalize()}{where} at {e.timestamp:%H:%M} on {e.machine_id}{date}{earlier}"

    when = "today" if today else f"since {oldest:%d %b}"
    if weather_note:
        return f"Triggered by {len(lead)} incidents in {weather_note} {when}{earlier}"
    counts: dict[str, int] = defaultdict(int)
    for e in lead:
        counts[e.event_type] += 1
    what = " and ".join(f"{n} {_label(t).replace(' ', '-')}"
                        for t, n in sorted(counts.items(), key=lambda kv: -kv[1]))
    return f"Triggered by {what} alerts {when}{earlier}"


def _weakest_areas(meta: Mapping[str, Any] | None, operator_id: str | None) -> list[tuple[str, float]]:
    """Metrics where this operator's per-task medians exceed the fleet's, worst first."""
    if not meta or not operator_id:
        return []
    baselines = meta["baselines"]
    ratios: dict[str, list[float]] = defaultdict(list)
    for key, own in baselines["operator_task"].items():
        op, task = key.split("|", 1)
        fleet = baselines["task_type"].get(task)
        if op != operator_id or not fleet:
            continue
        for metric in WEAK_AREA_MODULES:
            if own.get(metric) and fleet.get(metric):
                ratios[metric].append(own[metric] / fleet[metric])
    avg = {m: sum(r) / len(r) for m, r in ratios.items() if r}
    return sorted(((m, v) for m, v in avg.items() if v >= WEAK_AREA_MIN_RATIO), key=lambda mv: -mv[1])


def recommend(anomalies: list[Anomaly], incidents: list[Incident], modules: list[Module],
              anomaly_meta: Mapping[str, Any] | None = None,
              now: datetime | None = None) -> list[tuple[str, str, str]]:
    now = now or datetime.now()
    by_trigger = {m.trigger_anomaly_type: m for m in modules if m.trigger_anomaly_type}
    by_title = {m.title: m for m in modules}

    events = [Event(a.anomaly_type, a.timestamp, a.severity, a.machine_id) for a in anomalies]
    events += [Event(i.event_type, i.timestamp, i.severity, i.machine_id, (i.details or {}).get("weather"))
               for i in incidents]

    # module_id -> triggering events (and whether it is the weather mapping)
    triggered: dict[str, list[Event]] = defaultdict(list)
    weather_modules: set[str] = set()
    for e in events:
        module = by_trigger.get(e.event_type) or by_title.get(EXTRA_EVENT_MODULES.get(e.event_type, ""))
        if module:
            triggered[module.module_id].append(e)
        if e.weather in BAD_WEATHER and e.event_type != "manual_report" and BAD_WEATHER_MODULE in by_title:
            wet = by_title[BAD_WEATHER_MODULE].module_id
            triggered[wet].append(e)
            weather_modules.add(wet)

    recs: list[tuple[str, str, str, datetime]] = []
    for module_id, evs in triggered.items():
        evs.sort(key=lambda e: e.timestamp, reverse=True)
        repeated = len(evs) >= 2
        priority = "high" if repeated or any(e.severity == "high" for e in evs) else "medium"
        note = None
        if module_id in weather_modules:
            note = BAD_WEATHER.get(evs[0].weather or "", "bad weather")
        recs.append((module_id, _reason(evs, now, note), priority, evs[0].timestamp))

    # Low-priority upskilling from the operator's weakest area
    operator_id = next((x.operator_id for x in [*anomalies, *incidents]), None)
    taken = {r[0] for r in recs}
    for metric, ratio in _weakest_areas(anomaly_meta, operator_id):
        if len(recs) >= FILL_TO:
            break
        title, name = WEAK_AREA_MODULES[metric]
        module = by_title.get(title)
        if module and module.module_id not in taken:
            taken.add(module.module_id)
            recs.append((module.module_id,
                         f"Your {name} runs {(ratio - 1) * 100:.0f}% above the fleet for the same tasks",
                         "low", datetime.min))

    recs.sort(key=lambda r: (PRIORITY_ORDER[r[2]], -r[3].timestamp() if r[3] != datetime.min else 0))
    return [(m, reason, p) for m, reason, p, _ in recs[:MAX_RECOMMENDATIONS]]
