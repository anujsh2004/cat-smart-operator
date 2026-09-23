// Realistic mock data matching the §5 contract. Times are relative to today so the UI looks current.
import type {
  AnalyticsSummary,
  Anomaly,
  Context,
  Incident,
  LiveState,
  SafetyStatus,
  Task,
  TaskMetric,
  TaskType,
  TrainingProgress,
} from "@/api/types";

const pad = (n: number) => String(n).padStart(2, "0");

/** Local ISO string without timezone, like the backend returns. */
export function isoLocal(d: Date): string {
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  );
}

export function todayAt(hh: number, mm: number): string {
  const d = new Date();
  d.setHours(hh, mm, 0, 0);
  return isoLocal(d);
}

export function minutesAgo(min: number): string {
  return isoLocal(new Date(Date.now() - min * 60_000));
}

export const mockContext: Context = {
  operator: { operator_id: "OP1001", name: "Ravi Kumar", skill_level: "Intermediate", experience_yrs: 4, shift: "Morning" },
  machine: { machine_id: "EXC001", model: "320 GC", machine_type: "Excavator", age_yrs: 2, engine_hours: 1523.5 },
  weather: { condition: "Sunny", temperature_c: 31, visibility: "Good" },
  ground_condition: "Firm",
  shift: { name: "Morning", start: "08:00", end: "16:00" },
};

export function initialTasks(): Task[] {
  const base = { machine_id: "EXC001", operator_id: "OP1001", actual_time_min: null };
  return [
    { ...base, task_id: "T001", task_type: "Earth Excavation", site_zone: "Pit B", scheduled_start: todayAt(8, 0),
      status: "in_progress", progress_pct: 45, weather: "Sunny", ground_condition: "Firm",
      estimated_time_min: 60, predicted_time_min: 57.4 },
    { ...base, task_id: "T002", task_type: "Trenching", site_zone: "Utility Corridor 2", scheduled_start: todayAt(9, 10),
      status: "scheduled", progress_pct: 0, weather: "Rainy", ground_condition: "Wet",
      estimated_time_min: 45, predicted_time_min: 51.8 },
    { ...base, task_id: "T003", task_type: "Material Loading", site_zone: "Stockpile A", scheduled_start: todayAt(10, 5),
      status: "scheduled", progress_pct: 0, weather: "Cloudy", ground_condition: "Loose",
      estimated_time_min: 30, predicted_time_min: 30.0 },
    { ...base, task_id: "T004", task_type: "Grading", site_zone: "Access Road North", scheduled_start: todayAt(10, 45),
      status: "scheduled", progress_pct: 0, weather: "Sunny", ground_condition: "Firm",
      estimated_time_min: 35, predicted_time_min: 35.0 },
    { ...base, task_id: "T005", task_type: "Demolition", site_zone: "Block C", scheduled_start: todayAt(13, 0),
      status: "scheduled", progress_pct: 0, weather: "Windy", ground_condition: "Rocky",
      estimated_time_min: 90, predicted_time_min: 94.5 },
  ];
}

export function mockTaskMetrics(taskType: TaskType | null, cycles: number): TaskMetric[] {
  switch (taskType) {
    case "Earth Excavation":
    case "Trenching":
      return [
        { key: "bucket_cycles", label: "Bucket cycles", value: cycles, unit: "" },
        { key: "avg_bucket_load", label: "Avg bucket load", value: 1.45, unit: "t" },
        { key: "dig_depth", label: taskType === "Trenching" ? "Trench depth" : "Excavation depth", value: 2.8, unit: "m" },
        { key: "cycle_time", label: "Cycle time", value: 21, unit: "s" },
      ];
    case "Material Loading":
      return [
        { key: "load_cycles", label: "Load cycles", value: cycles, unit: "" },
        { key: "avg_payload", label: "Avg payload", value: 1.6, unit: "t" },
        { key: "payload_utilisation", label: "Payload utilisation", value: 80, unit: "%" },
        { key: "loading_cycle_time", label: "Loading cycle time", value: 18, unit: "s" },
      ];
    case "Grading":
      return [
        { key: "passes_completed", label: "Passes completed", value: Math.floor(cycles / 6), unit: "" },
        { key: "grade_accuracy", label: "Grade accuracy", value: 96.4, unit: "%" },
        { key: "surface_deviation", label: "Surface deviation", value: 2.9, unit: "cm" },
        { key: "travel_speed", label: "Travel speed", value: 5.1, unit: "km/h" },
      ];
    case "Demolition":
      return [
        { key: "impact_cycles", label: "Impact cycles", value: cycles, unit: "" },
        { key: "material_removed", label: "Material removed", value: +(cycles * 1.4).toFixed(1), unit: "t" },
        { key: "proximity_risk", label: "Proximity risk", value: 0, unit: "%" },
        { key: "structural_alerts", label: "Structural alerts", value: 0, unit: "" },
      ];
    default:
      return [];
  }
}

export function baseLive(): LiveState {
  return {
    timestamp: isoLocal(new Date()), machine_id: "EXC001", operator_id: "OP1001",
    task_id: "T001", task_type: "Earth Excavation", engine_on: true,
    engine_hours: 1524.8, fuel_used_l: 38.2, fuel_rate_lph: 14.1,
    idle_time_min: 22.0, operating_time_min: 95.0, idle_pct: 23.2,
    load_cycles: 118, avg_payload_kg: 1450,
    seatbelt_status: "Fastened", proximity_m: 18.5, people_in_zone: 0, speed_kmh: 2.1,
    health: "Good", active_scenario: "normal", task_metrics: mockTaskMetrics("Earth Excavation", 118),
  };
}

export const mockSafetyLow: SafetyStatus = {
  machine_id: "EXC001", evaluated_at: isoLocal(new Date()),
  risk_score: 0, risk_level: "LOW", alert: false,
  seatbelt_status: "Fastened", proximity_m: 18.5, people_in_zone: 0,
  factors: [], recommended_action: "No action needed. Continue operating safely.",
};

export const mockSafetyHigh: SafetyStatus = {
  machine_id: "EXC001", evaluated_at: isoLocal(new Date()),
  risk_score: 82, risk_level: "HIGH", alert: true,
  seatbelt_status: "Unfastened", proximity_m: 4.2, people_in_zone: 1,
  factors: [
    { factor: "people_in_zone", label: "Person detected within 4.2 m of operating zone", contribution: 40 },
    { factor: "seatbelt", label: "Seatbelt unfastened while engine running", contribution: 30 },
    { factor: "weather", label: "Rain reduces traction and visibility", contribution: 12 },
  ],
  recommended_action: "Stop swing movement, fasten seatbelt, and sound horn before resuming.",
};

export function initialIncidents(): Incident[] {
  return [
    { incident_id: "INC1002", timestamp: minutesAgo(95), machine_id: "EXC001", operator_id: "OP1001",
      event_type: "proximity_hazard", severity: "high", risk_score: 82,
      details: { proximity_m: 4.2, people_in_zone: 1 }, action_taken: "Operator alerted",
      status: "resolved", resolved_at: minutesAgo(94.8), duration_s: 11 },
    { incident_id: "INC1001", timestamp: minutesAgo(60 * 26), machine_id: "EXC001", operator_id: "OP1001",
      event_type: "seatbelt_unfastened", severity: "high", risk_score: 72,
      details: { seatbelt_status: "Unfastened" }, action_taken: "Operator alerted",
      status: "resolved", resolved_at: minutesAgo(60 * 26 - 0.5), duration_s: 28 },
  ];
}

export function initialAnomalies(): Anomaly[] {
  return [
    { anomaly_id: "ANM0002", timestamp: minutesAgo(60 * 30), machine_id: "EXC001", operator_id: "OP1001",
      anomaly_type: "fuel_spike", observed_value: 30.3, baseline_value: 13.3, unit: "L/h",
      severity: "medium", anomaly_score: 0.42, message: "Fuel rate 30.3 L/h vs your usual 13.3 L/h",
      recommended_module_id: "TM03" },
    { anomaly_id: "ANM0001", timestamp: minutesAgo(60 * 96), machine_id: "EXC001", operator_id: "OP1001",
      anomaly_type: "abnormal_cycle_time", observed_value: 47, baseline_value: 35, unit: "s",
      severity: "medium", anomaly_score: 0.11, message: "Cycle time 47 s vs your usual 35 s",
      recommended_module_id: "TM04" },
  ];
}

export function mockAnalytics(days: number): AnalyticsSummary {
  const fuel = [92.4, 53.0, 37.6, 88.2, 110.1, 71.3, 38.2];
  const idle = [31.0, 21.1, 26.1, 25.2, 24.1, 27.9, 23.2];
  const cycles = [410, 502, 297, 724, 790, 560, 118];
  const operating = [420, 252, 171, 398, 455, 330, 95];
  const incidents = [0, 1, 0, 0, 1, 0, 1];
  const rows = Array.from({ length: days }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (days - 1 - i));
    const k = (i + 7 - (days % 7)) % 7;
    return {
      date: isoLocal(d).slice(0, 10), fuel_l: fuel[k], idle_pct: idle[k],
      load_cycles: cycles[k], operating_min: operating[k], incidents: incidents[k],
    };
  });
  const sum = (f: (r: (typeof rows)[number]) => number) => rows.reduce((a, r) => a + f(r), 0);
  const idleMin = sum((r) => (r.idle_pct / 100) * r.operating_min);
  return {
    days: rows,
    totals: {
      fuel_l: +sum((r) => r.fuel_l).toFixed(1),
      idle_pct: +((idleMin / sum((r) => r.operating_min)) * 100).toFixed(1),
      load_cycles: sum((r) => r.load_cycles),
      incidents: sum((r) => r.incidents),
    },
    fleet_avg: { idle_pct: 35.0, fuel_per_cycle_l: 0.24 },
  };
}

export function initialProgress(): TrainingProgress[] {
  return [
    { module_id: "TM01", status: "completed", progress_pct: 100, score: 100 },
    { module_id: "TM07", status: "in_progress", progress_pct: 40, score: null },
  ];
}
