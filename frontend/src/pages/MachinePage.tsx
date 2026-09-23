import { Activity, BarChart3, Radar } from "lucide-react";
import type { ReactNode } from "react";
import { useAnalytics, useAnomalies, useLive, useMachineId, useTelemetry } from "@/api/hooks";
import { AnomalyCard } from "@/components/machine/AnomalyCard";
import { DayBarChart, IdleVsFleetChart, TimeLineChart } from "@/components/machine/charts";
import { Card, EmptyState, KpiTile, QueryBlock, Skeleton, StatusBadge } from "@/components/ui";
import { fmtDay, fmtNum, fmtTime } from "@/lib/format";
import { HEALTH } from "@/lib/status";

function ChartBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-sm font-semibold text-muted">{title}</p>
      {children}
    </div>
  );
}

export function MachinePage() {
  const machineId = useMachineId();
  const live = useLive(machineId);
  const telemetry = useTelemetry(machineId, 60);
  const analytics = useAnalytics(undefined, 7);
  const anomalies = useAnomalies(undefined, 20);

  return (
    <div className="space-y-5">
      <Card
        title={`Live telemetry · ${machineId ?? ""} · last 60 min`}
        icon={Activity}
        action={live.data && <StatusBadge {...HEALTH[live.data.health]} label={`Health: ${HEALTH[live.data.health].label}`} />}
      >
        <QueryBlock query={telemetry} skeleton={<Skeleton className="h-48" />}>
          {(points) => {
            if (points.length < 2)
              return <EmptyState title="Collecting telemetry…" hint="Readings are saved about every 10 seconds while the machine runs." />;
            const rows = points.map((p) => ({ ...p, time: fmtTime(p.timestamp) }));
            return (
              <div className="grid gap-6 lg:grid-cols-3">
                <ChartBlock title="Fuel rate (L/h)">
                  <TimeLineChart data={rows} dataKey="fuel_rate_lph" unit="L/h" label="Fuel rate" />
                </ChartBlock>
                <ChartBlock title="Idle (%)">
                  <TimeLineChart data={rows} dataKey="idle_pct" unit="%" label="Idle" />
                </ChartBlock>
                <ChartBlock title="Load cycles (cumulative)">
                  <TimeLineChart data={rows} dataKey="load_cycles" unit="" label="Load cycles" />
                </ChartBlock>
              </div>
            );
          }}
        </QueryBlock>
      </Card>

      <Card title="Last 7 days" icon={BarChart3}>
        <QueryBlock query={analytics} skeleton={<Skeleton className="h-64" />}>
          {(a) => {
            const rows = a.days.map((d) => ({ ...d, day: fmtDay(d.date) }));
            const idleTone = a.totals.idle_pct > a.fleet_avg.idle_pct ? "warn" : "good";
            return (
              <>
                <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
                  <KpiTile label="Fuel used" value={fmtNum(a.totals.fuel_l, 0)} unit="L" />
                  <KpiTile
                    label="Idle"
                    value={fmtNum(a.totals.idle_pct)}
                    unit="%"
                    tone={idleTone}
                    hint={`fleet avg ${a.fleet_avg.idle_pct}%`}
                  />
                  <KpiTile label="Load cycles" value={a.totals.load_cycles.toLocaleString()} />
                  <KpiTile label="Incidents" value={a.totals.incidents} tone={a.totals.incidents > 0 ? "warn" : "good"} />
                </div>
                <div className="grid gap-6 lg:grid-cols-3">
                  <ChartBlock title="Fuel per day (L)">
                    <DayBarChart data={rows} dataKey="fuel_l" unit="L" label="Fuel" />
                  </ChartBlock>
                  <ChartBlock title="Idle % vs fleet average">
                    <IdleVsFleetChart data={rows} fleetAvg={a.fleet_avg.idle_pct} />
                  </ChartBlock>
                  <ChartBlock title="Incidents per day">
                    <DayBarChart data={rows} dataKey="incidents" unit="" label="Incidents" allowDecimals={false} />
                  </ChartBlock>
                </div>
              </>
            );
          }}
        </QueryBlock>
      </Card>

      <Card title="Unusual behaviour" icon={Radar}>
        <QueryBlock query={anomalies} skeleton={<Skeleton className="h-64" />}>
          {(list) =>
            list.length === 0 ? (
              <EmptyState title="No unusual behaviour detected" hint="Idle, fuel and cycle times are within your normal range." />
            ) : (
              <ul className="grid gap-4 xl:grid-cols-2">
                {list.map((a) => (
                  <AnomalyCard key={a.anomaly_id} anomaly={a} />
                ))}
              </ul>
            )
          }
        </QueryBlock>
      </Card>
    </div>
  );
}
