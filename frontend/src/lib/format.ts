import type { EventType, ModuleCategory, ModuleFormat } from "@/api/types";

/** Backend timestamps are local ISO strings without a zone; Date parses them as local time. */
export const parseTs = (iso: string) => new Date(iso);

export const fmtTime = (iso: string) =>
  parseTs(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export const fmtDateTime = (iso: string) =>
  parseTs(iso).toLocaleString([], { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

export const fmtDay = (isoDate: string) =>
  new Date(isoDate + "T00:00:00").toLocaleDateString([], { weekday: "short", day: "2-digit" });

export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m}m ${seconds % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

export const fmtNum = (n: number | null | undefined, digits = 1) =>
  n == null ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });

export function timeAgo(iso: string): string {
  const s = Math.max(0, Math.round((Date.now() - parseTs(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

export const EVENT_LABEL: Record<EventType, string> = {
  proximity_hazard: "Proximity hazard",
  seatbelt_unfastened: "Seatbelt unfastened",
  excessive_idling: "Excessive idling",
  fuel_spike: "Fuel spike",
  abnormal_cycle_time: "Abnormal cycle time",
  unsafe_operation: "Unsafe operation",
  manual_report: "Manual report",
};

export const CATEGORY_LABEL: Record<ModuleCategory, string> = {
  safety: "Safety",
  efficiency: "Efficiency",
  technique: "Technique",
  incident_response: "Incident response",
};

export const FORMAT_LABEL: Record<ModuleFormat, string> = {
  video: "Video",
  quiz: "Quiz",
  simulation: "Simulation",
  instructor: "Instructor",
};

export const titleCase = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
