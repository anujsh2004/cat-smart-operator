import { CheckCircle2, ClipboardList, MapPin, PlayCircle } from "lucide-react";
import { useCompleteTask, useStartTask } from "@/api/hooks";
import type { LiveState, Task } from "@/api/types";
import { Button, Card, EmptyState, ProgressBar, StatusBadge } from "@/components/ui";
import { fmtNum, fmtTime } from "@/lib/format";
import { TASK_STATUS } from "@/lib/status";
import { overrun } from "@/lib/tasks";

function TimeStat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div>
      <p className="text-sm text-muted">{label}</p>
      <p className="tabular font-mono text-3xl font-bold">
        {value}
        <span className="ml-1 text-base font-normal text-muted">min</span>
      </p>
      {note && <p className="text-sm text-muted">{note}</p>}
    </div>
  );
}

export function CurrentTaskCard({ task, live }: { task: Task | null; live: LiveState | undefined }) {
  const start = useStartTask();
  const complete = useCompleteTask();

  if (!task) {
    return (
      <Card title="Current task" icon={ClipboardList}>
        <EmptyState title="All tasks for today are done" hint="Nice work. Check the schedule for tomorrow." />
      </Card>
    );
  }

  const status = TASK_STATUS[task.status];
  const running = task.status === "in_progress";
  // Elapsed = machine operating time the sim has logged on this task
  const elapsed = running && live?.task_id === task.task_id ? live.operating_time_min : null;
  const diff = overrun(task);
  const busy = start.isPending || complete.isPending;
  const error = start.error ?? complete.error;

  return (
    <Card title="Current task" icon={ClipboardList} action={<StatusBadge {...status} />}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-3xl font-bold">{task.task_type}</p>
          <p className="mt-1 flex items-center gap-1.5 text-muted">
            <MapPin className="size-4" aria-hidden />
            {task.site_zone} · {task.task_id} · starts {fmtTime(task.scheduled_start)}
          </p>
        </div>
        {running ? (
          <Button variant="primary" icon={CheckCircle2} disabled={busy} onClick={() => complete.mutate(task.task_id)}>
            Complete task
          </Button>
        ) : (
          <Button variant="primary" icon={PlayCircle} disabled={busy} onClick={() => start.mutate(task.task_id)}>
            Start task
          </Button>
        )}
      </div>

      <div className="mt-5">
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-muted">Progress</span>
          <span className="tabular font-mono font-bold">{task.progress_pct}%</span>
        </div>
        <ProgressBar value={task.progress_pct} label="Task progress" />
      </div>

      <div className="mt-5 grid grid-cols-3 gap-4">
        <TimeStat label="Planned" value={fmtNum(task.estimated_time_min, 0)} />
        <TimeStat
          label="Predicted"
          value={fmtNum(task.predicted_time_min)}
          note={diff == null ? undefined : diff > 0 ? `+${diff} vs plan` : `${diff} vs plan`}
        />
        <TimeStat label="Elapsed" value={elapsed == null ? "—" : fmtNum(elapsed)} note={elapsed == null ? "not started" : "machine time"} />
      </div>
      {error && <p className="mt-3 text-sm text-danger" role="alert">{error.message}</p>}
    </Card>
  );
}
