import { CheckCircle2, ListChecks, PlayCircle } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useCompleteTask, useOperatorContext, useStartTask, useTasksToday } from "@/api/hooks";
import type { Task } from "@/api/types";
import { TaskTimeEstimator } from "@/components/tasks/TaskTimeEstimator";
import { Button, Card, cx, EmptyState, ProgressBar, QueryBlock, Skeleton, StatusBadge } from "@/components/ui";
import { fmtNum, fmtTime } from "@/lib/format";
import { TASK_STATUS } from "@/lib/status";
import { currentTask, overrun } from "@/lib/tasks";

function DiffChip({ task }: { task: Task }) {
  const d = overrun(task);
  if (d == null) return null;
  const over = d > 0.5;
  const under = d < -0.5;
  return (
    <span
      className={cx(
        "tabular rounded-md px-2 py-0.5 font-mono text-sm font-bold",
        over ? "bg-warn/15 text-warn" : under ? "bg-good/15 text-good" : "bg-raised text-muted",
      )}
    >
      {over ? "▲ +" : under ? "▼ " : "≈ "}
      {d} min
    </span>
  );
}

function TaskRow({ task, selected, onSelect }: { task: Task; selected: boolean; onSelect: () => void }) {
  const start = useStartTask();
  const complete = useCompleteTask();
  const st = TASK_STATUS[task.status];
  const busy = start.isPending || complete.isPending;

  return (
    <li
      className={cx(
        "rounded-2xl border p-4 transition",
        selected ? "border-accent bg-accent/5" : "border-line bg-raised hover:border-muted",
      )}
    >
      <button type="button" onClick={onSelect} className="w-full text-left" aria-pressed={selected}>
        <div className="flex items-center gap-3">
          <span className="tabular font-mono text-xl font-bold">{fmtTime(task.scheduled_start)}</span>
          <StatusBadge tone={st.tone} label={st.label} icon={st.icon} />
          <span className="ml-auto text-sm text-muted">{task.task_id}</span>
        </div>
        <p className="mt-2 text-lg font-semibold">{task.task_type}</p>
        <p className="text-sm text-muted">
          {task.site_zone} · {task.weather} · {task.ground_condition} ground
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          <span>
            <span className="text-muted">Planned </span>
            <span className="tabular font-mono font-bold">{fmtNum(task.estimated_time_min, 0)}</span>
          </span>
          <span>
            <span className="text-muted">Predicted </span>
            <span className="tabular font-mono font-bold">{fmtNum(task.predicted_time_min)}</span>
          </span>
          {task.actual_time_min != null && (
            <span>
              <span className="text-muted">Actual </span>
              <span className="tabular font-mono font-bold">{fmtNum(task.actual_time_min)}</span>
            </span>
          )}
          <DiffChip task={task} />
        </div>
      </button>
      {task.status === "in_progress" && (
        <div className="mt-3">
          <ProgressBar value={task.progress_pct} label={`${task.task_id} progress`} />
        </div>
      )}
      {task.status !== "completed" && (
        <div className="mt-3 flex gap-2">
          {task.status === "scheduled" ? (
            <Button icon={PlayCircle} disabled={busy} onClick={() => start.mutate(task.task_id)}>
              Start
            </Button>
          ) : (
            <Button variant="primary" icon={CheckCircle2} disabled={busy} onClick={() => complete.mutate(task.task_id)}>
              Complete
            </Button>
          )}
        </div>
      )}
    </li>
  );
}

export function TasksPage() {
  const tasks = useTasksToday();
  const ctx = useOperatorContext();
  const [params] = useSearchParams(); // /tasks?task=T002 deep-links a task into the estimator
  const [selectedId, setSelectedId] = useState<string | null>(params.get("task"));

  const list = tasks.data ?? [];
  const selected = list.find((t) => t.task_id === selectedId) ?? currentTask(list) ?? list[0];

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,8fr)]">
      <Card title="Today's tasks" icon={ListChecks}>
        <QueryBlock query={tasks} skeleton={<Skeleton className="h-96" />}>
          {(ts) =>
            ts.length === 0 ? (
              <EmptyState title="No tasks scheduled today" />
            ) : (
              <ol className="space-y-3">
                {ts.map((t) => (
                  <TaskRow key={t.task_id} task={t} selected={t.task_id === selected?.task_id} onSelect={() => setSelectedId(t.task_id)} />
                ))}
              </ol>
            )
          }
        </QueryBlock>
      </Card>

      <div>
        {selected && ctx.data ? (
          <TaskTimeEstimator task={selected} ctx={ctx.data} />
        ) : (
          <QueryBlock query={ctx} skeleton={<Skeleton className="h-96" />}>
            {() => <EmptyState title="Select a task to estimate its time" />}
          </QueryBlock>
        )}
      </div>
    </div>
  );
}
