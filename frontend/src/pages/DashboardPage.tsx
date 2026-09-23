import { AlertOctagon, CalendarClock, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { useAnomalies, useIncidents, useLive, useMachineId, useSafety, useTasksToday } from "@/api/hooks";
import type { LiveState } from "@/api/types";
import { CurrentTaskCard } from "@/components/dashboard/CurrentTaskCard";
import { SafetyStrip } from "@/components/dashboard/SafetyStrip";
import { TaskMetricsGrid } from "@/components/dashboard/TaskMetricsGrid";
import { AnomalyItem, IncidentItem } from "@/components/feeds";
import { Card, EmptyState, KpiTile, QueryBlock, Skeleton, StatusBadge } from "@/components/ui";
import { fmtNum, fmtTime } from "@/lib/format";
import { HEALTH, TASK_STATUS } from "@/lib/status";
import { currentTask } from "@/lib/tasks";

const IDLE_WARN_PCT = 35;

function KpiRow({ live }: { live: LiveState }) {
  const health = HEALTH[live.health];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      <KpiTile label="Fuel used" value={fmtNum(live.fuel_used_l)} unit="L" hint="this session" />
      <KpiTile label="Fuel rate" value={fmtNum(live.fuel_rate_lph)} unit="L/h" tone={live.health === "Critical" ? "danger" : "neutral"} />
      <KpiTile
        label="Idle"
        value={fmtNum(live.idle_pct)}
        unit="%"
        tone={live.idle_pct > IDLE_WARN_PCT ? "warn" : "neutral"}
        hint={live.idle_pct > IDLE_WARN_PCT ? `above ${IDLE_WARN_PCT}% target` : `${fmtNum(live.idle_time_min)} min idle`}
      />
      <KpiTile label="Engine hours" value={live.engine_hours.toFixed(1)} unit="h" />
      <KpiTile label="Load cycles" value={live.load_cycles} />
      <KpiTile label="Machine health" value={health.label} tone={health.tone} />
    </div>
  );
}

export function DashboardPage() {
  const machineId = useMachineId();
  const safety = useSafety(machineId);
  const live = useLive(machineId);
  const tasks = useTasksToday();
  const anomalies = useAnomalies(undefined, 4);
  const incidents = useIncidents({ machine_id: machineId, limit: 5 });

  return (
    <div className="space-y-5">
      <QueryBlock query={safety} skeleton={<Skeleton className="h-52" />}>
        {(s) => <SafetyStrip safety={s} />}
      </QueryBlock>

      <QueryBlock query={tasks} skeleton={<Skeleton className="h-64" />}>
        {(t) => <CurrentTaskCard task={currentTask(t)} live={live.data} />}
      </QueryBlock>

      <QueryBlock query={live} skeleton={<Skeleton className="h-28" />}>
        {(l) => (
          <>
            <KpiRow live={l} />
            <TaskMetricsGrid live={l} />
          </>
        )}
      </QueryBlock>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="AI insights & alerts" icon={Sparkles} action={<Link to="/machine" className="text-sm text-accent hover:underline">All</Link>}>
          <QueryBlock query={anomalies}>
            {(list) =>
              list.length === 0 ? (
                <EmptyState title="No unusual behaviour detected" hint="Idle time and fuel use are within your normal range." />
              ) : (
                <ul className="space-y-3">{list.map((a) => <AnomalyItem key={a.anomaly_id} anomaly={a} />)}</ul>
              )
            }
          </QueryBlock>
        </Card>

        <Card title="Recent incidents" icon={AlertOctagon} action={<Link to="/safety" className="text-sm text-accent hover:underline">Log</Link>}>
          <QueryBlock query={incidents}>
            {(list) =>
              list.length === 0 ? (
                <EmptyState title="No incidents logged" />
              ) : (
                <ul className="space-y-2">{list.map((i) => <IncidentItem key={i.incident_id} incident={i} />)}</ul>
              )
            }
          </QueryBlock>
        </Card>
      </div>

      <Card title="Today's schedule" icon={CalendarClock} action={<Link to="/tasks" className="text-sm text-accent hover:underline">Tasks</Link>}>
        <QueryBlock query={tasks}>
          {(list) =>
            list.length === 0 ? (
              <EmptyState title="No tasks scheduled today" />
            ) : (
              <ul className="divide-y divide-line">
                {list.map((t) => {
                  const st = TASK_STATUS[t.status];
                  return (
                    <li key={t.task_id} className="flex min-h-14 items-center gap-4 py-2">
                      <span className="tabular w-16 font-mono text-lg font-bold">{fmtTime(t.scheduled_start)}</span>
                      <span className="flex-1">
                        <span className="font-semibold">{t.task_type}</span>
                        <span className="ml-2 text-sm text-muted">{t.site_zone}</span>
                      </span>
                      <span className="hidden text-sm text-muted sm:inline">{fmtNum(t.predicted_time_min ?? t.estimated_time_min)} min</span>
                      <StatusBadge tone={st.tone} label={st.label} icon={st.icon} />
                    </li>
                  );
                })}
              </ul>
            )
          }
        </QueryBlock>
      </Card>
    </div>
  );
}
