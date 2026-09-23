import { mockRequest } from "@/mocks/handlers";
import { ApiError, type HttpMethod } from "./errors";
import type {
  AnalyticsSummary,
  Anomaly,
  Context,
  HealthResponse,
  Incident,
  IncidentCreate,
  IncidentFilters,
  IncidentResolve,
  LiveState,
  Module,
  Quiz,
  Recommendation,
  ResetRequest,
  SafetyStatus,
  ScenarioRequest,
  Task,
  TaskTimePrediction,
  TaskTimeRequest,
  TelemetryPoint,
  TrainingProgress,
  TrainingProgressCreate,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";
export const DEFAULT_OPERATOR_ID = import.meta.env.VITE_DEFAULT_OPERATOR_ID ?? "OP1001";

export { ApiError };

async function request<T>(method: HttpMethod, path: string, body?: unknown): Promise<T> {
  if (USE_MOCKS) return mockRequest(method, path, body) as Promise<T>;

  const res = await fetch(BASE_URL + path, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data: unknown = await res.json();
      if (data && typeof data === "object" && "detail" in data) {
        const d = (data as { detail: unknown }).detail;
        detail = typeof d === "string" ? d : JSON.stringify(d);
      }
    } catch {
      // non-JSON error body: keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  return entries.length ? "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString() : "";
}

export const api = {
  health: () => request<HealthResponse>("GET", "/health"),
  context: (operatorId: string) => request<Context>("GET", `/context${qs({ operator_id: operatorId })}`),

  tasksToday: (operatorId: string) => request<Task[]>("GET", `/tasks/today${qs({ operator_id: operatorId })}`),
  startTask: (taskId: string) => request<Task>("POST", `/tasks/${taskId}/start`),
  completeTask: (taskId: string) => request<Task>("POST", `/tasks/${taskId}/complete`),

  live: (machineId: string) => request<LiveState>("GET", `/machines/${machineId}/live`),
  telemetry: (machineId: string, minutes = 60) =>
    request<TelemetryPoint[]>("GET", `/machines/${machineId}/telemetry${qs({ minutes })}`),

  safety: (machineId: string) => request<SafetyStatus>("GET", `/safety/status${qs({ machine_id: machineId })}`),

  incidents: (filters: IncidentFilters = {}) => request<Incident[]>("GET", `/incidents${qs({ ...filters })}`),
  createIncident: (body: IncidentCreate) => request<Incident>("POST", "/incidents", body),
  resolveIncident: (incidentId: string, body: IncidentResolve) =>
    request<Incident>("PATCH", `/incidents/${incidentId}/resolve`, body),

  predictTaskTime: (body: TaskTimeRequest) => request<TaskTimePrediction>("POST", "/predict/task-time", body),

  anomalies: (params: { operator_id?: string; machine_id?: string; limit?: number } = {}) =>
    request<Anomaly[]>("GET", `/anomalies${qs(params)}`),

  analytics: (operatorId: string, days = 7) =>
    request<AnalyticsSummary>("GET", `/analytics/summary${qs({ operator_id: operatorId, days })}`),

  modules: () => request<Module[]>("GET", "/training/modules"),
  recommendations: (operatorId: string) =>
    request<Recommendation[]>("GET", `/training/recommendations${qs({ operator_id: operatorId })}`),
  progress: (operatorId: string) =>
    request<TrainingProgress[]>("GET", `/training/progress${qs({ operator_id: operatorId })}`),
  saveProgress: (body: TrainingProgressCreate) => request<TrainingProgress>("POST", "/training/progress", body),
  quiz: (moduleId: string) => request<Quiz>("GET", `/training/modules/${moduleId}/quiz`),

  setScenario: (body: ScenarioRequest) => request<LiveState>("POST", "/sim/scenario", body),
  resetSim: (body: ResetRequest) => request<LiveState>("POST", "/sim/reset", body),
};
