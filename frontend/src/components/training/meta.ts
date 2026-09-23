import { CircleHelp, Gamepad2, PlayCircle, UserRound, type LucideIcon } from "lucide-react";
import type { ModuleFormat, Priority, TrainingProgress, TrainingStatus } from "@/api/types";
import type { Tone } from "@/components/ui";

export const FORMAT_ICON: Record<ModuleFormat, LucideIcon> = {
  video: PlayCircle,
  quiz: CircleHelp,
  simulation: Gamepad2,
  instructor: UserRound,
};

export const PRIORITY_TONE: Record<Priority, Tone> = { high: "danger", medium: "warn", low: "info" };

export const TRAINING_STATUS: Record<TrainingStatus, { tone: Tone; label: string }> = {
  not_started: { tone: "neutral", label: "Not started" },
  in_progress: { tone: "info", label: "In progress" },
  completed: { tone: "good", label: "Completed" },
};

export const progressFor = (list: TrainingProgress[] | undefined, moduleId: string): TrainingProgress =>
  list?.find((p) => p.module_id === moduleId) ?? { module_id: moduleId, status: "not_started", progress_pct: 0, score: null };
