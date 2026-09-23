import { Calculator, CloudRain, Droplets, GraduationCap, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { usePredictTaskTime } from "@/api/hooks";
import {
  GROUND_CONDITIONS,
  SKILL_LEVELS,
  TASK_TYPES,
  WEATHERS,
  type Context,
  type Task,
  type TaskTimeRequest,
} from "@/api/types";
import { Button, Card, cx, EmptyState, ErrorState, Field, inputClass, Select, Skeleton } from "@/components/ui";
import { fmtNum } from "@/lib/format";
import { FactorChart } from "./FactorChart";
import { RangeBand } from "./RangeBand";

function fromTask(task: Task, ctx: Context): TaskTimeRequest {
  return {
    task_type: task.task_type,
    operator_id: ctx.operator.operator_id,
    operator_skill: ctx.operator.skill_level,
    operator_experience_yrs: ctx.operator.experience_yrs,
    machine_age_yrs: ctx.machine.age_yrs,
    weather: task.weather,
    ground_condition: task.ground_condition,
    temperature_c: Math.round(ctx.weather.temperature_c),
  };
}

const WHAT_IF: { label: string; icon: typeof CloudRain; patch: Partial<TaskTimeRequest> }[] = [
  { label: "Rainy", icon: CloudRain, patch: { weather: "Rainy" } },
  { label: "Wet ground", icon: Droplets, patch: { ground_condition: "Wet" } },
  { label: "Beginner", icon: GraduationCap, patch: { operator_skill: "Beginner", operator_experience_yrs: 1 } },
];

export function TaskTimeEstimator({ task, ctx }: { task: Task; ctx: Context }) {
  const [form, setForm] = useState<TaskTimeRequest>(() => fromTask(task, ctx));
  const predict = usePredictTaskTime();
  const { mutate } = predict;

  // New task selected: pre-fill from it and predict straight away
  useEffect(() => {
    const next = fromTask(task, ctx);
    setForm(next);
    mutate(next);
  }, [task.task_id, mutate]); // only on task change, so a context refetch never wipes edits

  const set = <K extends keyof TaskTimeRequest>(k: K, v: TaskTimeRequest[K]) => setForm((f) => ({ ...f, [k]: v }));
  const run = (next: TaskTimeRequest) => {
    setForm(next);
    mutate(next);
  };
  const isActive = (patch: Partial<TaskTimeRequest>) =>
    Object.entries(patch).every(([k, v]) => form[k as keyof TaskTimeRequest] === v);
  const p = predict.data;

  return (
    <Card title={`Task time estimator · ${task.task_id}`} icon={Calculator}>
      <form
        className="grid grid-cols-2 gap-3 md:grid-cols-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutate(form);
        }}
      >
        <div className="col-span-2">
        <Field label="Task type">
          <Select value={form.task_type} options={TASK_TYPES} onChange={(v) => set("task_type", v)} />
        </Field>
        </div>
        <Field label="Operator skill">
          <Select value={form.operator_skill} options={SKILL_LEVELS} onChange={(v) => set("operator_skill", v)} />
        </Field>
        <Field label="Experience (yrs)">
          <input type="number" min={0} max={40} className={inputClass} value={form.operator_experience_yrs}
            onChange={(e) => set("operator_experience_yrs", Number(e.target.value))} />
        </Field>
        <Field label="Machine age (yrs)">
          <input type="number" min={0} max={30} className={inputClass} value={form.machine_age_yrs}
            onChange={(e) => set("machine_age_yrs", Number(e.target.value))} />
        </Field>
        <Field label="Weather">
          <Select value={form.weather} options={WEATHERS} onChange={(v) => set("weather", v)} />
        </Field>
        <Field label="Ground">
          <Select value={form.ground_condition} options={GROUND_CONDITIONS} onChange={(v) => set("ground_condition", v)} />
        </Field>
        <Field label="Temperature (°C)">
          <input type="number" min={-20} max={55} className={inputClass} value={form.temperature_c}
            onChange={(e) => set("temperature_c", Number(e.target.value))} />
        </Field>
        <div className="col-span-2 flex items-end md:col-span-1">
          <Button type="submit" variant="primary" icon={Calculator} className="w-full" disabled={predict.isPending}>
            Predict
          </Button>
        </div>
      </form>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="mr-1 text-sm text-muted">What if:</span>
        {WHAT_IF.map(({ label, icon, patch }) => (
          <Button
            key={label}
            icon={icon}
            aria-pressed={isActive(patch)}
            className={cx("rounded-full", isActive(patch) && "border-accent text-accent")}
            onClick={() => run({ ...form, ...patch })}
          >
            {label}
          </Button>
        ))}
        <Button variant="ghost" icon={RotateCcw} onClick={() => run(fromTask(task, ctx))}>
          Reset
        </Button>
      </div>

      <div className="mt-6 border-t border-line pt-5">
        {predict.isError ? (
          <ErrorState error={predict.error} onRetry={() => mutate(form)} />
        ) : !p ? (
          predict.isPending ? <Skeleton className="h-48" /> : <EmptyState title="Run a prediction" />
        ) : (
          <div className={cx("grid gap-6 2xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]", predict.isPending && "opacity-60")}>
            <div>
              <p className="text-sm text-muted">Predicted time</p>
              <p className="tabular font-mono text-6xl font-bold text-accent">
                {fmtNum(p.predicted_time_min)}
                <span className="ml-2 text-xl font-normal text-muted">min</span>
              </p>
              <p className="mt-1 text-muted">
                Likely {fmtNum(p.lower_min)}–{fmtNum(p.upper_min)} min · planned {fmtNum(task.estimated_time_min, 0)} min
              </p>
              <RangeBand p={p} />
              <p className="text-xs text-muted">Model: {p.model}</p>
            </div>
            <div>
              <p className="mb-1 text-sm font-semibold uppercase tracking-wide text-muted">Why this estimate</p>
              {p.top_factors.some((f) => f.impact_min !== 0) ? (
                <FactorChart factors={p.top_factors} />
              ) : (
                <p className="py-4 text-muted">
                  Neutral conditions: {p.top_factors.map((f) => f.label).join(", ") || "no factors"} add no time over the
                  historical average.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
