import { GraduationCap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { Anomaly } from "@/api/types";
import { Button, cx, StatusBadge, TONE_TEXT } from "@/components/ui";
import { CHART } from "@/lib/chart";
import { EVENT_LABEL, fmtDateTime, fmtNum } from "@/lib/format";
import { EVENT_ICON, SEVERITY } from "@/lib/status";

function CompareBar({ label, value, max, unit, color }: { label: string; value: number; max: number; unit: string; color: string }) {
  return (
    <div className="grid grid-cols-[7rem_1fr_auto] items-center gap-3 text-sm">
      <span className="text-muted">{label}</span>
      <div className="h-3 rounded-full bg-raised">
        <div className="h-full rounded-full" style={{ width: `${(value / max) * 100}%`, background: color }} />
      </div>
      <span className="tabular w-20 text-right font-mono font-bold">
        {fmtNum(value)} {unit}
      </span>
    </div>
  );
}

export function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  const navigate = useNavigate();
  const Icon = EVENT_ICON[anomaly.anomaly_type];
  const sev = SEVERITY[anomaly.severity];
  const max = Math.max(anomaly.observed_value, anomaly.baseline_value) || 1;
  const ratio = anomaly.baseline_value ? anomaly.observed_value / anomaly.baseline_value : null;

  return (
    <li className="rounded-2xl border border-line bg-raised p-5">
      <div className="flex flex-wrap items-center gap-3">
        <Icon className={cx("size-7", TONE_TEXT[sev.tone])} aria-hidden />
        <h3 className="text-lg font-semibold">{EVENT_LABEL[anomaly.anomaly_type]}</h3>
        <StatusBadge tone={sev.tone} label={`${sev.label} severity`} icon={sev.icon} />
        <span className="ml-auto text-sm text-muted">{fmtDateTime(anomaly.timestamp)}</span>
      </div>
      <p className="mt-2 text-lg">{anomaly.message}</p>

      <div className="mt-4 space-y-2">
        <CompareBar label="This session" value={anomaly.observed_value} max={max} unit={anomaly.unit} color={CHART.series1} />
        <CompareBar label="Your usual" value={anomaly.baseline_value} max={max} unit={anomaly.unit} color={CHART.axis} />
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          Anomaly score <span className="tabular font-mono font-bold text-ink">{anomaly.anomaly_score.toFixed(2)}</span>
          {ratio && <> · {ratio.toFixed(1)}× your usual</>}
        </p>
        {anomaly.recommended_module_id && (
          <Button variant="primary" icon={GraduationCap} onClick={() => navigate(`/training/${anomaly.recommended_module_id}`)}>
            Start recommended training
          </Button>
        )}
      </div>
    </li>
  );
}
