import { useMutation, useQuery, useQueryClient, type QueryKey } from "@tanstack/react-query";
import { api, DEFAULT_OPERATOR_ID } from "./client";
import type {
  IncidentCreate,
  IncidentFilters,
  Scenario,
  TaskTimeRequest,
  TrainingProgressCreate,
} from "./types";

// Polling (TRACK_B B5): live + safety 2 s, incidents + anomalies 5 s, the rest on demand.
const LIVE_MS = 2000;
const FEED_MS = 5000;
const HEALTH_MS = 10000; // connection dot in the TopBar
const TELEMETRY_MS = 10000; // backend persists telemetry every 5 ticks (~10 s)

export const keys = {
  health: ["health"] as const,
  context: (op: string) => ["context", op] as const,
  tasks: (op: string) => ["tasks", op] as const,
  live: (m: string) => ["live", m] as const,
  telemetry: (m: string, minutes: number) => ["telemetry", m, minutes] as const,
  safety: (m: string) => ["safety", m] as const,
  incidents: (f: IncidentFilters) => ["incidents", f] as const,
  anomalies: (op: string, limit: number) => ["anomalies", op, limit] as const,
  analytics: (op: string, days: number) => ["analytics", op, days] as const,
  modules: ["modules"] as const,
  recommendations: (op: string) => ["recommendations", op] as const,
  progress: (op: string) => ["progress", op] as const,
  quiz: (id: string) => ["quiz", id] as const,
};

function useInvalidate() {
  const qc = useQueryClient();
  return (...prefixes: string[]) =>
    Promise.all(prefixes.map((p) => qc.invalidateQueries({ queryKey: [p] as QueryKey })));
}

// --- Queries ---

export const useHealth = () =>
  useQuery({ queryKey: keys.health, queryFn: api.health, refetchInterval: HEALTH_MS, retry: false });

export const useOperatorContext = (operatorId = DEFAULT_OPERATOR_ID) =>
  useQuery({ queryKey: keys.context(operatorId), queryFn: () => api.context(operatorId) });

/** Machine the operator is on today (from /context). */
export const useMachineId = (): string | undefined => useOperatorContext().data?.machine.machine_id;

export const useTasksToday = (operatorId = DEFAULT_OPERATOR_ID) =>
  useQuery({ queryKey: keys.tasks(operatorId), queryFn: () => api.tasksToday(operatorId) });

export const useLive = (machineId: string | undefined) =>
  useQuery({
    queryKey: keys.live(machineId ?? ""),
    queryFn: () => api.live(machineId!),
    enabled: !!machineId,
    refetchInterval: LIVE_MS,
  });

export const useTelemetry = (machineId: string | undefined, minutes = 60) =>
  useQuery({
    queryKey: keys.telemetry(machineId ?? "", minutes),
    queryFn: () => api.telemetry(machineId!, minutes),
    enabled: !!machineId,
    refetchInterval: TELEMETRY_MS,
  });

export const useSafety = (machineId: string | undefined) =>
  useQuery({
    queryKey: keys.safety(machineId ?? ""),
    queryFn: () => api.safety(machineId!),
    enabled: !!machineId,
    refetchInterval: LIVE_MS,
  });

export const useIncidents = (filters: IncidentFilters = {}) =>
  useQuery({ queryKey: keys.incidents(filters), queryFn: () => api.incidents(filters), refetchInterval: FEED_MS });

export const useAnomalies = (operatorId = DEFAULT_OPERATOR_ID, limit = 20) =>
  useQuery({
    queryKey: keys.anomalies(operatorId, limit),
    queryFn: () => api.anomalies({ operator_id: operatorId, limit }),
    refetchInterval: FEED_MS,
  });

export const useAnalytics = (operatorId = DEFAULT_OPERATOR_ID, days = 7) =>
  useQuery({ queryKey: keys.analytics(operatorId, days), queryFn: () => api.analytics(operatorId, days) });

export const useModules = () => useQuery({ queryKey: keys.modules, queryFn: api.modules, staleTime: Infinity });

export const useRecommendations = (operatorId = DEFAULT_OPERATOR_ID) =>
  useQuery({ queryKey: keys.recommendations(operatorId), queryFn: () => api.recommendations(operatorId) });

export const useProgress = (operatorId = DEFAULT_OPERATOR_ID) =>
  useQuery({ queryKey: keys.progress(operatorId), queryFn: () => api.progress(operatorId) });

export const useQuiz = (moduleId: string | undefined) =>
  useQuery({
    queryKey: keys.quiz(moduleId ?? ""),
    queryFn: () => api.quiz(moduleId!),
    enabled: !!moduleId,
    staleTime: Infinity,
  });

// --- Mutations ---

export function useStartTask() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: api.startTask,
    onSuccess: () => invalidate("tasks", "live", "safety", "context"),
  });
}

export function useCompleteTask() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: api.completeTask,
    onSuccess: () => invalidate("tasks", "live", "safety", "context", "analytics"),
  });
}

export function useCreateIncident() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: IncidentCreate) => api.createIncident(body),
    onSuccess: () => invalidate("incidents", "analytics", "recommendations"),
  });
}

export function useResolveIncident() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution: string }) => api.resolveIncident(id, { resolution }),
    onSuccess: () => invalidate("incidents"),
  });
}

export const usePredictTaskTime = () => useMutation({ mutationFn: (body: TaskTimeRequest) => api.predictTaskTime(body) });

export function useSaveProgress() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: TrainingProgressCreate) => api.saveProgress(body),
    onSuccess: () => invalidate("progress", "recommendations"),
  });
}

const SIM_KEYS = ["live", "safety", "context", "incidents", "anomalies", "recommendations"];

export function useSetScenario() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ machineId, scenario }: { machineId: string; scenario: Scenario }) =>
      api.setScenario({ machine_id: machineId, scenario }),
    onSuccess: () => invalidate(...SIM_KEYS),
  });
}

export function useResetSim() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (machineId: string) => api.resetSim({ machine_id: machineId }),
    onSuccess: () => invalidate(...SIM_KEYS),
  });
}
