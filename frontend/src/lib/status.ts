// Maps contract enums to a tone + label + icon, so every status is shown with icon and text.
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Clock,
  Fuel,
  Gauge,
  HardHat,
  PlayCircle,
  ShieldAlert,
  ShieldCheck,
  Timer,
  type LucideIcon,
} from "lucide-react";
import type { EventType, Health, IncidentStatus, RiskLevel, Severity, TaskStatus } from "@/api/types";
import type { Tone } from "@/components/ui";

interface StatusInfo {
  tone: Tone;
  label: string;
  icon: LucideIcon;
}

export const RISK: Record<RiskLevel, StatusInfo> = {
  LOW: { tone: "good", label: "Low risk", icon: ShieldCheck },
  MEDIUM: { tone: "warn", label: "Medium risk", icon: AlertTriangle },
  HIGH: { tone: "danger", label: "High risk", icon: ShieldAlert },
};

export const HEALTH: Record<Health, StatusInfo> = {
  Good: { tone: "good", label: "Good", icon: CheckCircle2 },
  Attention: { tone: "warn", label: "Attention", icon: AlertTriangle },
  Critical: { tone: "danger", label: "Critical", icon: AlertOctagon },
};

export const SEVERITY: Record<Severity, StatusInfo> = {
  low: { tone: "info", label: "Low", icon: CircleDot },
  medium: { tone: "warn", label: "Medium", icon: AlertTriangle },
  high: { tone: "danger", label: "High", icon: AlertOctagon },
};

export const TASK_STATUS: Record<TaskStatus, StatusInfo> = {
  scheduled: { tone: "neutral", label: "Scheduled", icon: Clock },
  in_progress: { tone: "info", label: "In progress", icon: PlayCircle },
  completed: { tone: "good", label: "Completed", icon: CheckCircle2 },
};

export const INCIDENT_STATUS: Record<IncidentStatus, StatusInfo> = {
  open: { tone: "danger", label: "Open", icon: AlertOctagon },
  resolved: { tone: "good", label: "Resolved", icon: CheckCircle2 },
};

export const EVENT_ICON: Record<EventType, LucideIcon> = {
  proximity_hazard: HardHat,
  seatbelt_unfastened: ShieldAlert,
  excessive_idling: Timer,
  fuel_spike: Fuel,
  abnormal_cycle_time: Gauge,
  unsafe_operation: AlertTriangle,
  manual_report: Activity,
};
