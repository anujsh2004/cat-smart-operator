import { HardHat, Radar, ShieldCheck, ShieldX } from "lucide-react";
import type { SafetyStatus } from "@/api/types";
import { RiskGauge } from "@/components/RiskGauge";
import { cx, StatusBadge } from "@/components/ui";
import { RISK } from "@/lib/status";

const DANGER_ZONE_M = 5;

function Stat({ icon: Icon, label, value, danger }: { icon: typeof Radar; label: string; value: string; danger: boolean }) {
  return (
    <div className={cx("flex items-center gap-3 rounded-xl border px-4 py-3", danger ? "border-danger bg-danger/20" : "border-line bg-raised")}>
      <Icon className={cx("size-8 shrink-0", danger ? "text-danger" : "text-good")} aria-hidden />
      <div>
        <p className="text-sm text-muted">{label}</p>
        <p className="tabular font-mono text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}

/** Top-of-dashboard safety summary. The whole strip turns red at HIGH risk. */
export function SafetyStrip({ safety }: { safety: SafetyStatus }) {
  const risk = RISK[safety.risk_level];
  const high = safety.risk_level === "HIGH";
  const belted = safety.seatbelt_status === "Fastened";
  const close = safety.proximity_m < DANGER_ZONE_M;

  return (
    <section
      aria-label="Safety status"
      className={cx(
        "grid items-center gap-5 rounded-2xl border p-5 md:grid-cols-[auto_1fr] 2xl:grid-cols-[auto_1fr_auto]",
        high ? "border-danger bg-danger/20" : "border-line bg-card",
      )}
    >
      <RiskGauge score={safety.risk_score} level={safety.risk_level} size={180} />

      <div className="min-w-0">
        <StatusBadge tone={risk.tone} label={risk.label} icon={risk.icon} size="lg" />
        {safety.factors.length > 0 ? (
          <ul className="mt-3 space-y-1.5">
            {safety.factors.slice(0, 2).map((f) => (
              <li key={f.factor} className="flex items-baseline gap-2 text-lg">
                <span className="tabular font-mono text-sm font-bold text-danger">+{f.contribution}</span>
                <span>{f.label}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-lg text-muted">No active hazards detected.</p>
        )}
        <p className={cx("mt-2 text-sm", high ? "font-semibold text-ink" : "text-muted")}>{safety.recommended_action}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3 md:col-span-2 2xl:col-span-1">
        <Stat icon={belted ? ShieldCheck : ShieldX} label="Seatbelt" value={belted ? "Fastened" : "Unfastened"} danger={!belted} />
        <Stat icon={Radar} label="Nearest object" value={`${safety.proximity_m.toFixed(1)} m`} danger={close} />
        <Stat icon={HardHat} label="People in zone" value={String(safety.people_in_zone)} danger={safety.people_in_zone > 0} />
      </div>
    </section>
  );
}
