// Mirrors docs/ARCHITECTURE.md §4.3 enums and §5 schemas (backend/app/schemas). FROZEN: change all three together.

// --- Enums (§4.3) ---
export type TaskType = "Earth Excavation" | "Trenching" | "Material Loading" | "Grading" | "Demolition";
export type Weather = "Sunny" | "Cloudy" | "Windy" | "Rainy" | "Foggy";
export type GroundCondition = "Firm" | "Loose" | "Wet" | "Rocky";
export type SkillLevel = "Beginner" | "Intermediate" | "Expert";
export type SeatbeltStatus = "Fastened" | "Unfastened";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type Severity = "low" | "medium" | "high";
export type EventType =
  | "proximity_hazard"
  | "seatbelt_unfastened"
  | "excessive_idling"
  | "fuel_spike"
  | "abnormal_cycle_time"
  | "unsafe_operation"
  | "manual_report";
export type AnomalyType = "excessive_idling" | "fuel_spike" | "abnormal_cycle_time" | "unsafe_operation";
export type Health = "Good" | "Attention" | "Critical";
export type Scenario = "normal" | "seatbelt_off" | "proximity_hazard" | "excessive_idle" | "fuel_spike" | "rain";

// Table-level enums (§4.1)
export type TaskStatus = "scheduled" | "in_progress" | "completed";
export type IncidentStatus = "open" | "resolved";
export type TrainingStatus = "not_started" | "in_progress" | "completed";
export type ModuleCategory = "safety" | "efficiency" | "technique" | "incident_response";
export type ModuleFormat = "video" | "quiz" | "simulation" | "instructor";
export type ShiftName = "Morning" | "Evening" | "Night";
export type MachineType = "Excavator" | "Wheel Loader" | "Dozer" | "Motor Grader";
export type Priority = "high" | "medium" | "low";
export type MLMode = "stub" | "live";

/** ISO-8601 timestamp string */
export type ISODateTime = string;

// --- §5.1 System ---
export interface HealthResponse {
  status: string;
  db: boolean;
  ml_mode: MLMode;
}

export interface Operator {
  operator_id: string;
  name: string;
  skill_level: SkillLevel;
  experience_yrs: number;
  shift: ShiftName;
}

export interface Machine {
  machine_id: string;
  model: string;
  machine_type: MachineType;
  age_yrs: number;
  engine_hours: number;
}

export interface WeatherInfo {
  condition: Weather;
  temperature_c: number;
  visibility: string;
}

export interface ShiftInfo {
  name: ShiftName;
  start: string; // "HH:MM"
  end: string;
}

export interface Context {
  operator: Operator;
  machine: Machine;
  weather: WeatherInfo;
  ground_condition: GroundCondition;
  shift: ShiftInfo;
}

// --- §5.2 Tasks ---
export interface Task {
  task_id: string;
  task_type: TaskType;
  machine_id: string;
  operator_id: string;
  site_zone: string;
  scheduled_start: ISODateTime;
  status: TaskStatus;
  progress_pct: number;
  weather: Weather;
  ground_condition: GroundCondition;
  estimated_time_min: number;
  predicted_time_min: number | null;
  actual_time_min: number | null;
}

// --- §5.3 Live ---
export interface TaskMetric {
  key: string;
  label: string;
  value: number;
  unit: string;
}

export interface LiveState {
  timestamp: ISODateTime;
  machine_id: string;
  operator_id: string;
  task_id: string | null;
  task_type: TaskType | null;
  engine_on: boolean;
  engine_hours: number;
  fuel_used_l: number;
  fuel_rate_lph: number;
  idle_time_min: number;
  operating_time_min: number;
  idle_pct: number;
  load_cycles: number;
  avg_payload_kg: number;
  seatbelt_status: SeatbeltStatus;
  proximity_m: number;
  people_in_zone: number;
  speed_kmh: number;
  health: Health;
  active_scenario: Scenario;
  task_metrics: TaskMetric[];
}

export interface TelemetryPoint {
  timestamp: ISODateTime;
  fuel_rate_lph: number;
  idle_pct: number;
  load_cycles: number;
  proximity_m: number;
}

// --- §5.4 Safety ---
export interface SafetyFactor {
  factor: string;
  label: string;
  contribution: number;
}

export interface SafetyStatus {
  machine_id: string;
  evaluated_at: ISODateTime;
  risk_score: number;
  risk_level: RiskLevel;
  alert: boolean;
  seatbelt_status: SeatbeltStatus;
  proximity_m: number;
  people_in_zone: number;
  factors: SafetyFactor[];
  recommended_action: string;
}

// --- §5.5 Incidents ---
export type IncidentDetails = Record<string, string | number | boolean | null | string[]>;

export interface Incident {
  incident_id: string;
  timestamp: ISODateTime;
  machine_id: string;
  operator_id: string;
  event_type: EventType;
  severity: Severity;
  risk_score: number | null;
  details: IncidentDetails;
  action_taken: string | null;
  status: IncidentStatus;
  resolved_at: ISODateTime | null;
  duration_s: number | null;
}

export interface IncidentCreate {
  machine_id: string;
  operator_id: string;
  event_type: EventType;
  severity: Severity;
  description: string;
}

export interface IncidentResolve {
  resolution: string;
}

export interface IncidentFilters {
  machine_id?: string;
  operator_id?: string;
  status?: IncidentStatus;
  limit?: number;
}

// --- §5.6 Prediction ---
export interface TaskTimeRequest {
  task_type: TaskType;
  operator_id: string;
  operator_skill: SkillLevel;
  operator_experience_yrs: number;
  machine_age_yrs: number;
  weather: Weather;
  ground_condition: GroundCondition;
  temperature_c: number;
}

export interface PredictionFactor {
  feature: string;
  label: string;
  impact_min: number;
}

export interface TaskTimePrediction {
  predicted_time_min: number;
  lower_min: number;
  upper_min: number;
  historical_avg_min: number;
  model: string;
  top_factors: PredictionFactor[];
}

// --- §5.7 Anomalies ---
export interface Anomaly {
  anomaly_id: string;
  timestamp: ISODateTime;
  machine_id: string;
  operator_id: string;
  anomaly_type: AnomalyType;
  observed_value: number;
  baseline_value: number;
  unit: string;
  severity: Severity;
  anomaly_score: number;
  message: string;
  recommended_module_id: string | null;
}

// --- §5.8 Analytics ---
export interface AnalyticsDay {
  date: string; // YYYY-MM-DD
  fuel_l: number;
  idle_pct: number;
  load_cycles: number;
  operating_min: number;
  incidents: number;
}

export interface AnalyticsSummary {
  days: AnalyticsDay[];
  totals: { fuel_l: number; idle_pct: number; load_cycles: number; incidents: number };
  fleet_avg: { idle_pct: number; fuel_per_cycle_l: number };
}

// --- §5.9 Training ---
export interface Module {
  module_id: string;
  title: string;
  category: ModuleCategory;
  format: ModuleFormat;
  duration_min: number;
  description: string;
  content_url: string | null;
  trigger_anomaly_type: EventType | null;
}

export interface Recommendation {
  module: Module;
  reason: string;
  priority: Priority;
}

export interface TrainingProgress {
  module_id: string;
  status: TrainingStatus;
  progress_pct: number;
  score: number | null;
}

export interface TrainingProgressCreate {
  operator_id: string;
  module_id: string;
  progress_pct: number;
  score?: number | null;
}

export interface QuizQuestion {
  id: string;
  prompt: string;
  options: string[];
  answer_index: number;
  explanation: string;
}

export interface Quiz {
  questions: QuizQuestion[];
}

// --- §5.10 Sim ---
export interface ScenarioRequest {
  machine_id: string;
  scenario: Scenario;
}

export interface ResetRequest {
  machine_id: string;
}

// Enum value lists for form controls (same strings as the types above)
export const TASK_TYPES: readonly TaskType[] = ["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"];
export const WEATHERS: readonly Weather[] = ["Sunny", "Cloudy", "Windy", "Rainy", "Foggy"];
export const GROUND_CONDITIONS: readonly GroundCondition[] = ["Firm", "Loose", "Wet", "Rocky"];
export const SKILL_LEVELS: readonly SkillLevel[] = ["Beginner", "Intermediate", "Expert"];
export const SEVERITIES: readonly Severity[] = ["low", "medium", "high"];
export const EVENT_TYPES: readonly EventType[] = [
  "proximity_hazard", "seatbelt_unfastened", "excessive_idling", "fuel_spike",
  "abnormal_cycle_time", "unsafe_operation", "manual_report",
];
export const SCENARIOS: readonly Scenario[] = ["normal", "seatbelt_off", "proximity_hazard", "excessive_idle", "fuel_spike", "rain"];
