import { Gauge } from "lucide-react";
import type { LiveState } from "@/api/types";
import { Card, EmptyState, KpiTile } from "@/components/ui";
import { fmtNum } from "@/lib/format";

/** Same layout for every task type; only the tiles (from live.task_metrics) change. */
export function TaskMetricsGrid({ live }: { live: LiveState }) {
  return (
    <Card title={live.task_type ? `${live.task_type} metrics` : "Task metrics"} icon={Gauge}>
      {live.task_metrics.length === 0 ? (
        <EmptyState title="No task running" hint="Start a task to see live task metrics." />
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {live.task_metrics.map((m) => (
            <KpiTile key={m.key} label={m.label} value={fmtNum(m.value)} unit={m.unit || undefined} />
          ))}
        </div>
      )}
    </Card>
  );
}
