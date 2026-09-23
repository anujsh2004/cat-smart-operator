import { CloudSun, Eye, Megaphone, Plus, Radar, ShieldCheck, ShieldX } from "lucide-react";
import { useState } from "react";
import { useOperatorContext, useSafety } from "@/api/hooks";
import type { Context, SafetyStatus } from "@/api/types";
import { RiskGauge } from "@/components/RiskGauge";
import { IncidentLog } from "@/components/safety/IncidentLog";
import { ProximityRing } from "@/components/safety/ProximityRing";
import { ReportIncidentModal } from "@/components/safety/ReportIncidentModal";
import { WEATHER_ICON } from "@/components/layout/TopBar";
import { Button, Card, cx, EmptyState, QueryBlock, Skeleton, StatusBadge } from "@/components/ui";
import { RISK } from "@/lib/status";

function RiskCard({ s }: { s: SafetyStatus }) {
  const risk = RISK[s.risk_level];
  const high = s.risk_level === "HIGH";
  return (
    <Card title="Risk assessment" icon={risk.icon} tone={high ? "danger" : undefined}>
      <div className="grid items-start gap-6 md:grid-cols-[auto_1fr]">
        <div className="flex flex-col items-center gap-3">
          <RiskGauge score={s.risk_score} level={s.risk_level} size={240} />
          <StatusBadge tone={risk.tone} label={risk.label} icon={risk.icon} size="lg" />
        </div>
        <div className="min-w-0 space-y-4">
          <div>
            <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted">Contributing factors</p>
            {s.factors.length === 0 ? (
              <EmptyState icon={ShieldCheck} title="No risk factors right now" hint="Seatbelt fastened, zone clear, conditions normal." />
            ) : (
              <ul className="space-y-3">
                {s.factors.map((f) => (
                  <li key={f.factor}>
                    <div className="mb-1 flex items-baseline justify-between gap-3">
                      <span className="text-lg">{f.label}</span>
                      <span className="tabular font-mono font-bold text-danger">+{f.contribution}</span>
                    </div>
                    <div className="h-2.5 rounded-full bg-raised">
                      <div className="h-full rounded-full bg-danger" style={{ width: `${f.contribution}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className={cx("flex gap-3 rounded-xl border p-4", high ? "border-danger bg-danger/20" : "border-accent/40 bg-accent/10")}>
            <Megaphone className={cx("size-7 shrink-0", high ? "text-danger" : "text-accent")} aria-hidden />
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-muted">Recommended action</p>
              <p className="text-xl font-semibold">{s.recommended_action}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

function ComplianceTiles({ s, ctx }: { s: SafetyStatus; ctx: Context | undefined }) {
  const belted = s.seatbelt_status === "Fastened";
  const person = s.people_in_zone > 0;
  const WeatherIcon = ctx ? WEATHER_ICON[ctx.weather.condition] : CloudSun;
  const badConditions = ctx && (["Rainy", "Foggy"].includes(ctx.weather.condition) || ctx.ground_condition === "Wet");

  return (
    <div className="grid gap-5 md:grid-cols-3">
      <Card title="Seatbelt" icon={belted ? ShieldCheck : ShieldX} tone={belted ? undefined : "danger"}>
        <div className="flex flex-col items-center gap-3 py-2 text-center">
          {belted ? <ShieldCheck className="size-20 text-good" aria-hidden /> : <ShieldX className="size-20 text-danger" aria-hidden />}
          <p className={cx("text-3xl font-bold", belted ? "text-good" : "text-danger")}>{belted ? "Fastened" : "Unfastened"}</p>
          <p className="text-sm text-muted">{belted ? "Compliant" : "Fasten before operating"}</p>
        </div>
      </Card>

      <Card title="Proximity" icon={Radar} tone={s.proximity_m < 5 ? "danger" : undefined}>
        <div className="flex items-center justify-center gap-4">
          <ProximityRing distance={s.proximity_m} person={person} />
          <div>
            <p className="tabular font-mono text-4xl font-bold">{s.proximity_m.toFixed(1)}<span className="ml-1 text-lg text-muted">m</span></p>
            <p className="text-sm text-muted">nearest {person ? "person" : "object"}</p>
            <p className="mt-2 text-sm">
              <span className="tabular font-mono font-bold">{s.people_in_zone}</span> in zone
            </p>
          </div>
        </div>
      </Card>

      <Card title="Working conditions" icon={WeatherIcon}>
        {ctx ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <WeatherIcon className={cx("size-10", badConditions ? "text-warn" : "text-muted")} aria-hidden />
              <div>
                <p className="text-2xl font-bold">{ctx.weather.condition}</p>
                <p className="text-sm text-muted">{Math.round(ctx.weather.temperature_c)}°C</p>
              </div>
            </div>
            <p className="flex justify-between"><span className="text-muted">Ground</span><span className="font-semibold">{ctx.ground_condition}</span></p>
            <p className="flex justify-between">
              <span className="flex items-center gap-1.5 text-muted"><Eye className="size-4" aria-hidden />Visibility</span>
              <span className="font-semibold">{ctx.weather.visibility}</span>
            </p>
            {badConditions && <StatusBadge tone="warn" label="Adjust speed for conditions" />}
          </div>
        ) : (
          <Skeleton className="h-32" />
        )}
      </Card>
    </div>
  );
}

export function SafetyPage() {
  const ctx = useOperatorContext();
  const machineId = ctx.data?.machine.machine_id;
  const safety = useSafety(machineId);
  const [reporting, setReporting] = useState(false);

  return (
    <div className="space-y-5">
      <QueryBlock query={safety} skeleton={<Skeleton className="h-80" />}>
        {(s) => (
          <>
            <RiskCard s={s} />
            <ComplianceTiles s={s} ctx={ctx.data} />
          </>
        )}
      </QueryBlock>

      <IncidentLog
        machineId={machineId}
        action={
          <Button variant="primary" icon={Plus} onClick={() => setReporting(true)} disabled={!ctx.data}>
            Report incident
          </Button>
        }
      />
      {ctx.data && (
        <ReportIncidentModal
          open={reporting}
          onClose={() => setReporting(false)}
          machineId={ctx.data.machine.machine_id}
          operatorId={ctx.data.operator.operator_id}
        />
      )}
    </div>
  );
}
