"""Live telemetry simulation (docs/ARCHITECTURE.md §7).

A background loop ticks every SIM_TICK_SECONDS. Each tick advances every machine's live values,
applies the active demo scenarios, updates task progress, assesses safety (auto-opening and
auto-resolving incidents), and every 5 ticks detects anomalies and persists telemetry.
Simulated time runs faster than real time so a task visibly progresses during a demo.
"""
import asyncio
import logging
import random
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.session import SessionLocal
from app.schemas import LiveState, SafetyStatus
from app.services import anomaly_service, baseline_service, incident_service, live_service, task_service, \
    telemetry_service
from app.services.ml import interface as ml
from app.sim import metrics, scenarios
from app.sim.state import MachineSim, SimTask, lock, machines

logger = logging.getLogger(__name__)
rng = random.Random()

SIM_MIN_PER_TICK = 0.2           # simulated machine minutes per normal tick
IDLE_SCENARIO_MIN_PER_TICK = 5.0  # excessive_idle: idle time climbs fast
ANOMALY_EVERY_TICKS = 5
TELEMETRY_EVERY_TICKS = 5
COUNTERS = {"fuel_used_l": 0.0, "idle_time_min": 0.0, "operating_time_min": 0.0, "load_cycles": 0}
EVENT_BY_FACTOR = {"people_in_zone": "proximity_hazard", "proximity": "proximity_hazard",
                   "seatbelt": "seatbelt_unfastened"}


# --- Building state ------------------------------------------------------------

def _build(db: Session, machine_id: str, previous: MachineSim | None, fresh: bool) -> MachineSim | None:
    """Load a machine's sim state from the DB. fresh=True starts new session counters (new task/reset)."""
    start = live_service.initial_state(db, machine_id)  # latest telemetry reading, else defaults
    if start is None:
        return None
    task = task_service.in_progress_task(db, machine_id)
    planned = task or task_service.current_task(db, machine_id=machine_id)
    operator_id = planned.operator_id if planned else ""

    values = start.model_dump(exclude={"timestamp", "machine_id", "operator_id", "task_id", "task_type",
                                       "health", "active_scenario", "task_metrics", "idle_pct"})
    if previous is not None:
        values = dict(previous.values)
    if fresh:
        values |= COUNTERS
    values["engine_on"] = task is not None

    profile = baseline_service.task_profile(db, operator_id, task.task_type if task else None)
    m = MachineSim(
        machine_id=machine_id,
        operator_id=operator_id,
        task=SimTask(task.task_id, task.task_type, task.estimated_time_min) if task else None,
        task_weather=planned.weather if planned else "Sunny",
        task_ground=planned.ground_condition if planned else "Firm",
        profile=profile,
        baseline=baseline_service.operator_baseline(db, operator_id) if operator_id else {},
        values=values,
        live=start,
        cycle_time_s=profile["cycle_time_s"],
        cycles_at_start=values["load_cycles"],
        progress_offset=task.progress_pct if task else 0,
        progress_pct=task.progress_pct if task else 0,
    )
    if previous is not None:
        m.overlays, m.active_scenario = previous.overlays, previous.active_scenario
        m.open_incidents, m.alerts, m.tick = previous.open_incidents, previous.alerts, previous.tick
    else:
        # Pick up incidents left open by a previous run so they still auto-resolve
        m.open_incidents = {i.event_type: i.incident_id for i in incident_service.open_auto_incidents(db, machine_id)}
    _refresh_live(m)
    return m


def _health(m: MachineSim, idle_pct: float) -> str:
    ratio = m.values["fuel_rate_lph"] / m.profile["fuel_rate_lph"] if m.profile["fuel_rate_lph"] else 1
    if ratio >= 2.0:
        return "Critical"
    if ratio >= 1.4 or idle_pct > 40:
        return "Attention"
    return "Good"


def _refresh_live(m: MachineSim) -> None:
    v = m.values
    idle_pct = v["idle_time_min"] / v["operating_time_min"] * 100 if v["operating_time_min"] else 0.0
    m.live = LiveState(
        timestamp=datetime.now(),
        machine_id=m.machine_id,
        operator_id=m.operator_id,
        task_id=m.task.task_id if m.task else None,
        task_type=m.task.task_type if m.task else None,
        engine_on=v["engine_on"],
        engine_hours=round(v["engine_hours"], 2),
        fuel_used_l=round(v["fuel_used_l"], 1),
        fuel_rate_lph=round(v["fuel_rate_lph"], 1),
        idle_time_min=round(v["idle_time_min"], 1),
        operating_time_min=round(v["operating_time_min"], 1),
        idle_pct=round(idle_pct, 1),
        load_cycles=int(v["load_cycles"]),
        avg_payload_kg=round(v["avg_payload_kg"]),
        seatbelt_status=v["seatbelt_status"],
        proximity_m=round(v["proximity_m"], 1),
        people_in_zone=v["people_in_zone"],
        speed_kmh=round(v["speed_kmh"], 1),
        health=_health(m, idle_pct),
        active_scenario=m.active_scenario,
        task_metrics=metrics.task_metrics(
            m.task.task_type if m.task else None, v,
            cycle_time_s=m.cycle_time_s, base_cycle_time_s=m.profile["cycle_time_s"],
            progress_pct=m.progress_pct, weather=m.weather, alerts=m.alerts,
        ),
    )


# --- One tick --------------------------------------------------------------------

def _advance(m: MachineSim) -> None:
    """Move cumulative counters forward by one tick of simulated time."""
    v = m.values
    if not v["engine_on"]:
        return
    if "excessive_idle" in m.overlays:
        dt = IDLE_SCENARIO_MIN_PER_TICK
        v["idle_time_min"] += dt
    else:
        dt = SIM_MIN_PER_TICK
        idle_share = min(0.9, max(0.02, rng.gauss(m.profile["idle_frac"], 0.04)))
        v["idle_time_min"] += dt * idle_share
        m.cycle_time_s = m.profile["cycle_time_s"] * rng.gauss(1, 0.05)
        m.cycle_acc += dt * 60 * (1 - idle_share) / m.cycle_time_s
        whole = int(m.cycle_acc)
        v["load_cycles"] += whole
        m.cycle_acc -= whole
    v["operating_time_min"] += dt
    v["engine_hours"] += dt / 60
    v["fuel_used_l"] += v["fuel_rate_lph"] * dt / 60

    if m.task:
        idle_share = m.profile["idle_frac"]
        expected = m.task.estimated_time_min * 60 * (1 - idle_share) / m.profile["cycle_time_s"]
        done = (v["load_cycles"] - m.cycles_at_start) / expected * 100 if expected else 0
        m.progress_pct = min(100, m.progress_offset + int(done))


def _handle_incidents(db: Session, m: MachineSim, safety: SafetyStatus) -> None:
    if not m.operator_id:
        return
    if safety.risk_level == "HIGH":
        top = safety.factors[0].factor if safety.factors else ""
        event = EVENT_BY_FACTOR.get(top, "unsafe_operation")
        if event not in m.open_incidents:
            incident = incident_service.create(
                db, machine_id=m.machine_id, operator_id=m.operator_id, event_type=event, severity="high",
                risk_score=safety.risk_score, action_taken="Operator alerted",
                details={"proximity_m": safety.proximity_m, "people_in_zone": safety.people_in_zone,
                         "seatbelt_status": safety.seatbelt_status, "weather": m.weather,
                         "factors": [f.label for f in safety.factors]},
            )
            m.open_incidents[event] = incident.incident_id
            m.alerts += 1
            logger.info("Incident %s opened (%s, risk %s)", incident.incident_id, event, safety.risk_score)
    elif m.open_incidents:
        for incident_id in m.open_incidents.values():
            incident = db.get(models.Incident, incident_id)
            if incident is not None:
                incident_service.resolve(db, incident, f"Auto-resolved: risk fell to {safety.risk_level}")
                logger.info("Incident %s auto-resolved after %ss", incident_id, incident.duration_s)
        m.open_incidents = {}


def _tick(db: Session, m: MachineSim, advance: bool) -> None:
    if advance:
        _advance(m)
        m.tick += 1
    scenarios.apply(m, m.values, rng)
    _refresh_live(m)
    m.safety = ml.assess_safety(m.live, m.weather)
    _handle_incidents(db, m, m.safety)

    if not advance or not m.operator_id:
        return
    if m.task:
        task_service.set_progress(db, m.task.task_id, m.progress_pct)
    if m.tick % ANOMALY_EVERY_TICKS == 0 and m.values["engine_on"]:
        for anomaly in ml.detect_anomalies(m.live, m.baseline):
            saved = anomaly_service.save_if_new(db, anomaly)
            if saved is not None:
                logger.info("Anomaly %s: %s", saved.anomaly_id, saved.message)
    if m.tick % TELEMETRY_EVERY_TICKS == 0:
        telemetry_service.record(db, m.live)


def tick_all() -> None:
    for machine_id in list(machines):
        try:
            with lock, SessionLocal() as db:
                if machine_id in machines:
                    _tick(db, machines[machine_id], advance=True)
        except Exception:  # the loop must never die mid-demo
            logger.exception("Sim tick failed for %s", machine_id)


# --- Lifecycle -------------------------------------------------------------------

def init_all() -> None:
    with lock, SessionLocal() as db:
        machines.clear()
        for machine_id in db.scalars(select(models.Machine.machine_id)):
            m = _build(db, machine_id, previous=None, fresh=False)
            if m is not None:
                machines[machine_id] = m
    logger.info("Sim engine tracking %s", ", ".join(machines) or "no machines")


async def run(stop: asyncio.Event) -> None:
    """Tick loop; call init_all() first."""
    while not stop.is_set():
        await asyncio.to_thread(tick_all)
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.SIM_TICK_SECONDS)
        except TimeoutError:
            pass


# --- Used by routers ---------------------------------------------------------------

def get_live(machine_id: str) -> LiveState | None:
    m = machines.get(machine_id)
    return m.live if m else None


def get_safety(machine_id: str) -> SafetyStatus | None:
    m = machines.get(machine_id)
    if m is None:
        return None
    return m.safety or ml.assess_safety(m.live, m.weather)


def get_conditions(machine_id: str) -> tuple[str, str] | None:
    """(weather, ground_condition) as currently simulated."""
    m = machines.get(machine_id)
    return (m.weather, m.ground) if m else None


def reload_task(machine_id: str) -> None:
    """Called after a task starts or completes: new task, fresh session counters, same scenarios."""
    with lock, SessionLocal() as db:
        previous = machines.get(machine_id)
        m = _build(db, machine_id, previous=previous, fresh=True)
        if m is not None:
            machines[machine_id] = m
            _tick(db, m, advance=False)


def set_scenario(machine_id: str, scenario: str) -> LiveState | None:
    with lock, SessionLocal() as db:
        m = machines.get(machine_id)
        if m is None:
            return None
        if scenario == "normal":
            m.overlays = set()
        else:
            m.overlays = m.overlays | {scenario}
        m.active_scenario = scenario
        _tick(db, m, advance=False)  # apply now so the response and next poll already show it
        return m.live


def reset(machine_id: str) -> LiveState | None:
    """Clear scenarios, snap values to baseline and start fresh session counters."""
    with lock, SessionLocal() as db:
        previous = machines.get(machine_id)
        if previous is None:
            return None
        previous.overlays, previous.active_scenario = set(), "normal"
        m = _build(db, machine_id, previous=previous, fresh=True)
        if m is None:
            return None
        m.values |= {"fuel_rate_lph": m.profile["fuel_rate_lph"] if m.values["engine_on"] else 0.0,
                     "proximity_m": scenarios.BASE_PROXIMITY_M, "people_in_zone": 0}
        machines[machine_id] = m
        _tick(db, m, advance=False)
        return m.live
