import type { Task } from "@/api/types";

/** The in-progress task, else the next scheduled one, else null. */
export function currentTask(tasks: Task[]): Task | null {
  return tasks.find((t) => t.status === "in_progress") ?? tasks.find((t) => t.status === "scheduled") ?? null;
}

/** Predicted minus planned minutes (positive = expected to overrun). */
export function overrun(task: Task): number | null {
  return task.predicted_time_min == null ? null : +(task.predicted_time_min - task.estimated_time_min).toFixed(1);
}
