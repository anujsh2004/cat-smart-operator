// In-memory mock backend for VITE_USE_MOCKS=true. Keeps a little state so buttons visibly work,
// and mimics the sim scenarios. Add ?mock=high to the URL to force the HIGH-risk safety variant.
import { ApiError, type HttpMethod } from "@/api/errors";
import type {
  Anomaly,
  Incident,
  IncidentCreate,
  IncidentResolve,
  LiveState,
  PredictionFactor,
  SafetyFactor,
  SafetyStatus,
  Scenario,
  ScenarioRequest,
  TaskTimePrediction,
  TaskTimeRequest,
  TelemetryPoint,
  TrainingProgress,
  TrainingProgressCreate,
} from "@/api/types";
import {
  baseLive,
  initialAnomalies,
  initialIncidents,
  initialProgress,
  initialTasks,
  isoLocal,
  mockAnalytics,
  mockContext,
  mockSafetyHigh,
  mockSafetyLow,
  mockTaskMetrics,
} from "./data";
import { mockModules, mockQuizzes } from "./training";

const state = {
  tasks: initialTasks(),
  incidents: initialIncidents(),
  anomalies: initialAnomalies(),
  progress: initialProgress(),
  overlays: new Set<Scenario>(),
  active: "normal" as Scenario,
  started: Date.now(),
};

const forceHigh = () => new URLSearchParams(window.location.search).get("mock") === "high";

function live(): LiveState {
  const l = baseLive();
  const t = (Date.now() - state.started) / 1000;
  const task = state.tasks.find((x) => x.status === "in_progress") ?? null;
  const wobble = Math.sin(t / 3);
  const cycles = l.load_cycles + Math.floor(t / 4);
  const ov = state.overlays;
  const hazard = ov.has("proximity_hazard") || forceHigh();
  const idle = ov.has("excessive_idle");
  const idleMin = idle ? 22 + Math.min(60, t) : l.idle_time_min + t / 60;
  const operating = l.operating_time_min + t / 15 + (idle ? Math.min(60, t) : 0);
  const rate = ov.has("fuel_spike") ? 31.2 : idle ? 5.1 : +(14.1 + wobble * 0.4).toFixed(1);
  return {
    ...l,
    timestamp: isoLocal(new Date()),
    task_id: task?.task_id ?? null,
    task_type: task?.task_type ?? null,
    engine_on: task !== null,
    fuel_rate_lph: rate,
    fuel_used_l: +(l.fuel_used_l + t / 250).toFixed(1),
    idle_time_min: +idleMin.toFixed(1),
    operating_time_min: +operating.toFixed(1),
    idle_pct: +((idleMin / operating) * 100).toFixed(1),
    load_cycles: cycles,
    seatbelt_status: ov.has("seatbelt_off") || forceHigh() ? "Unfastened" : "Fastened",
    proximity_m: hazard ? 4.2 : +(18.5 + wobble).toFixed(1),
    people_in_zone: hazard ? 1 : 0,
    speed_kmh: idle ? 0 : +(2.1 + wobble * 0.3).toFixed(1),
    health: ov.has("fuel_spike") ? "Critical" : idle ? "Attention" : "Good",
    active_scenario: state.active,
    task_metrics: mockTaskMetrics(task?.task_type ?? null, cycles),
  };
}

function safety(): SafetyStatus {
  if (forceHigh()) return { ...mockSafetyHigh, evaluated_at: isoLocal(new Date()) };
  const l = live();
  const factors: SafetyFactor[] = [];
  if (l.people_in_zone > 0)
    factors.push({ factor: "people_in_zone", label: `Person detected within ${l.proximity_m} m of operating zone`, contribution: 40 });
  if (l.seatbelt_status === "Unfastened")
    factors.push({ factor: "seatbelt", label: "Seatbelt unfastened while engine running", contribution: 30 });
  if (l.proximity_m < 5)
    factors.push({ factor: "proximity", label: `Obstacle closer than 5 m (${l.proximity_m} m)`, contribution: 20 });
  if (state.overlays.has("rain"))
    factors.push({ factor: "weather", label: "Rain reduces traction and visibility", contribution: 12 });
  factors.sort((a, b) => b.contribution - a.contribution);
  const score = Math.min(100, factors.reduce((a, f) => a + f.contribution, 0));
  const level = score >= 70 ? "HIGH" : score >= 40 ? "MEDIUM" : "LOW";
  return {
    ...mockSafetyLow,
    evaluated_at: l.timestamp,
    risk_score: score,
    risk_level: level,
    alert: level === "HIGH",
    seatbelt_status: l.seatbelt_status,
    proximity_m: l.proximity_m,
    people_in_zone: l.people_in_zone,
    factors,
    recommended_action: level === "LOW" ? mockSafetyLow.recommended_action : mockSafetyHigh.recommended_action,
  };
}

function telemetry(): TelemetryPoint[] {
  return Array.from({ length: 60 }, (_, i) => {
    const d = new Date(Date.now() - (59 - i) * 60_000);
    return {
      timestamp: isoLocal(d),
      fuel_rate_lph: +(14 + Math.sin(i / 5) * 0.8).toFixed(1),
      idle_pct: +(23 + Math.cos(i / 7) * 3).toFixed(1),
      load_cycles: 60 + i,
      proximity_m: +(19 + Math.sin(i / 4) * 2).toFixed(1),
    };
  });
}

let nextIncident = 1003;

function syncIncidents(): void {
  // Mimic the engine: open an incident at HIGH risk, auto-resolve when it drops.
  const s = safety();
  const open = state.incidents.find((i) => i.status === "open" && i.event_type !== "manual_report");
  if (s.risk_level === "HIGH" && !open) {
    state.incidents.unshift({
      incident_id: `INC${nextIncident++}`, timestamp: isoLocal(new Date()), machine_id: "EXC001", operator_id: "OP1001",
      event_type: s.factors[0]?.factor === "seatbelt" ? "seatbelt_unfastened" : "proximity_hazard",
      severity: "high", risk_score: s.risk_score, details: { proximity_m: s.proximity_m, people_in_zone: s.people_in_zone },
      action_taken: "Operator alerted", status: "open", resolved_at: null, duration_s: null,
    });
  } else if (s.risk_level !== "HIGH" && open) {
    resolveIncident(open, "Auto-resolved: risk fell below HIGH");
  }
  if (state.overlays.has("excessive_idle") && !state.anomalies.some((a) => a.anomaly_type === "excessive_idling")) {
    const anomaly: Anomaly = {
      anomaly_id: `ANM${String(state.anomalies.length + 1).padStart(4, "0")}`, timestamp: isoLocal(new Date()),
      machine_id: "EXC001", operator_id: "OP1001", anomaly_type: "excessive_idling",
      observed_value: 75, baseline_value: 24, unit: "min", severity: "medium", anomaly_score: 0.71,
      message: "Idle time 75 min vs your usual 24 min this session", recommended_module_id: "TM03",
    };
    state.anomalies.unshift(anomaly);
  }
}

function resolveIncident(incident: Incident, resolution: string): Incident {
  const now = new Date();
  incident.status = "resolved";
  incident.resolved_at = isoLocal(now);
  incident.duration_s = Math.round((now.getTime() - new Date(incident.timestamp).getTime()) / 1000);
  incident.action_taken = resolution;
  return incident;
}

function predict(req: TaskTimeRequest): TaskTimePrediction {
  const base = { "Earth Excavation": 60, Trenching: 45, "Material Loading": 30, Grading: 35, Demolition: 90 }[req.task_type];
  const skill = { Beginner: 1.2, Intermediate: 1.0, Expert: 0.85 }[req.operator_skill];
  const weather = { Sunny: 1.0, Cloudy: 1.0, Windy: 1.05, Foggy: 1.1, Rainy: 1.15 }[req.weather];
  const ground = { Firm: 1.0, Loose: 1.05, Wet: 1.1, Rocky: 1.12 }[req.ground_condition];
  const predicted = base * skill * weather * ground;
  const factors: PredictionFactor[] = [
    { feature: "weather", label: `${req.weather} weather`, impact_min: +(base * skill * (weather - 1)).toFixed(1) },
    { feature: "ground_condition", label: `${req.ground_condition} ground`, impact_min: +(base * skill * weather * (ground - 1)).toFixed(1) },
    { feature: "operator_skill", label: `${req.operator_skill} operator`, impact_min: +(base * (skill - 1)).toFixed(1) },
  ].sort((a, b) => Math.abs(b.impact_min) - Math.abs(a.impact_min));
  return {
    predicted_time_min: +predicted.toFixed(1),
    lower_min: +(predicted * 0.9).toFixed(1),
    upper_min: +(predicted * 1.1).toFixed(1),
    historical_avg_min: base,
    model: "mock_task_time",
    top_factors: factors,
  };
}

function route(method: HttpMethod, path: string, body: unknown): unknown {
  const url = new URL(path, "http://mock");
  const p = url.pathname;
  const q = url.searchParams;
  let m: RegExpMatchArray | null;

  if (method === "GET") {
    if (p === "/health") return { status: "ok", db: true, ml_mode: "stub" };
    if (p === "/context")
      return state.overlays.has("rain")
        ? { ...mockContext, weather: { condition: "Rainy", temperature_c: 23, visibility: "Reduced" }, ground_condition: "Wet" }
        : mockContext;
    if (p === "/tasks/today") return state.tasks;
    if (/^\/machines\/[^/]+\/live$/.test(p)) return live();
    if (/^\/machines\/[^/]+\/telemetry$/.test(p)) return telemetry();
    if (p === "/safety/status") return safety();
    if (p === "/incidents") {
      const status = q.get("status");
      const limit = Number(q.get("limit") ?? 20);
      return state.incidents.filter((i) => !status || i.status === status).slice(0, limit);
    }
    if (p === "/anomalies") return state.anomalies.slice(0, Number(q.get("limit") ?? 20));
    if (p === "/analytics/summary") return mockAnalytics(Number(q.get("days") ?? 7));
    if (p === "/training/modules") return mockModules;
    if (p === "/training/progress") return state.progress;
    if (p === "/training/recommendations") {
      const types = [...state.anomalies.map((a) => a.anomaly_type), ...state.incidents.map((i) => i.event_type)];
      const seen = new Set<string>();
      return types.flatMap((t) => {
        const module = mockModules.find((mod) => mod.trigger_anomaly_type === t);
        if (!module || seen.has(module.module_id)) return [];
        seen.add(module.module_id);
        return [{ module, reason: `Triggered by ${t.replace(/_/g, " ")} today`, priority: t.includes("hazard") ? "high" : "medium" }];
      });
    }
    if ((m = p.match(/^\/training\/modules\/([^/]+)\/quiz$/))) {
      const quiz = mockQuizzes[m[1]];
      if (!quiz) throw new ApiError(404, `Module ${m[1]} not found`);
      return quiz;
    }
  }

  if (method === "POST") {
    if ((m = p.match(/^\/tasks\/([^/]+)\/(start|complete)$/))) {
      const task = state.tasks.find((t) => t.task_id === m![1]);
      if (!task) throw new ApiError(404, `Task ${m[1]} not found`);
      if (m[2] === "start") {
        state.tasks.forEach((t) => t.status === "in_progress" && (t.status = "scheduled"));
        task.status = "in_progress";
      } else {
        task.status = "completed";
        task.progress_pct = 100;
        task.actual_time_min = task.predicted_time_min;
      }
      return task;
    }
    if (p === "/incidents") {
      const b = body as IncidentCreate;
      const incident: Incident = {
        incident_id: `INC${nextIncident++}`, timestamp: isoLocal(new Date()), machine_id: b.machine_id,
        operator_id: b.operator_id, event_type: b.event_type, severity: b.severity, risk_score: null,
        details: { description: b.description }, action_taken: "Reported by operator", status: "open",
        resolved_at: null, duration_s: null,
      };
      state.incidents.unshift(incident);
      return incident;
    }
    if (p === "/predict/task-time") return predict(body as TaskTimeRequest);
    if (p === "/training/progress") {
      const b = body as TrainingProgressCreate;
      const pct = Math.max(0, Math.min(100, b.progress_pct));
      const rec: TrainingProgress = {
        module_id: b.module_id,
        status: pct >= 100 ? "completed" : pct > 0 ? "in_progress" : "not_started",
        progress_pct: pct,
        score: b.score ?? null,
      };
      state.progress = [...state.progress.filter((x) => x.module_id !== b.module_id), rec];
      return rec;
    }
    if (p === "/sim/scenario") {
      const b = body as ScenarioRequest;
      if (b.scenario === "normal") state.overlays.clear();
      else state.overlays.add(b.scenario);
      state.active = b.scenario;
      return live();
    }
    if (p === "/sim/reset") {
      state.overlays.clear();
      state.active = "normal";
      state.started = Date.now();
      return live();
    }
  }

  if (method === "PATCH" && (m = p.match(/^\/incidents\/([^/]+)\/resolve$/))) {
    const incident = state.incidents.find((i) => i.incident_id === m![1]);
    if (!incident) throw new ApiError(404, `Incident ${m[1]} not found`);
    return resolveIncident(incident, (body as IncidentResolve).resolution);
  }

  throw new ApiError(404, `No mock for ${method} ${p}`);
}

export async function mockRequest(method: HttpMethod, path: string, body?: unknown): Promise<unknown> {
  await new Promise((r) => setTimeout(r, 120)); // feel like a network call
  syncIncidents();
  // Deep copy so React Query never shares mutable objects with the mock store
  return structuredClone(route(method, path, body));
}
