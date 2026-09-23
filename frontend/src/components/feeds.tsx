// Compact list items shared by the Dashboard, Safety and Machine pages.
import { GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";
import type { Anomaly, Incident } from "@/api/types";
import { cx, StatusBadge, TONE_TEXT } from "@/components/ui";
import { EVENT_LABEL, fmtDuration, timeAgo } from "@/lib/format";
import { EVENT_ICON, INCIDENT_STATUS, SEVERITY } from "@/lib/status";

export function AnomalyItem({ anomaly }: { anomaly: Anomaly }) {
  const Icon = EVENT_ICON[anomaly.anomaly_type];
  const sev = SEVERITY[anomaly.severity];
  return (
    <li className="flex gap-3 rounded-xl border border-line bg-raised p-4">
      <Icon className={cx("mt-0.5 size-6 shrink-0", TONE_TEXT[sev.tone])} aria-hidden />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold">{EVENT_LABEL[anomaly.anomaly_type]}</span>
          <StatusBadge tone={sev.tone} label={sev.label} icon={sev.icon} />
          <span className="ml-auto text-sm text-muted">{timeAgo(anomaly.timestamp)}</span>
        </div>
        <p className="mt-1">{anomaly.message}</p>
        {anomaly.recommended_module_id && (
          <Link
            to={`/training/${anomaly.recommended_module_id}`}
            className="mt-2 inline-flex min-h-12 items-center gap-2 rounded-lg text-accent hover:underline"
          >
            <GraduationCap className="size-5" aria-hidden />
            Recommended training
          </Link>
        )}
      </div>
    </li>
  );
}

export function IncidentItem({ incident }: { incident: Incident }) {
  const Icon = EVENT_ICON[incident.event_type];
  const status = INCIDENT_STATUS[incident.status];
  return (
    <li className="flex items-center gap-3 rounded-xl border border-line bg-raised p-3">
      <Icon className="size-6 shrink-0 text-muted" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{EVENT_LABEL[incident.event_type]}</p>
        <p className="text-sm text-muted">
          {incident.incident_id} · {timeAgo(incident.timestamp)}
          {incident.status === "resolved" && ` · lasted ${fmtDuration(incident.duration_s)}`}
        </p>
      </div>
      <StatusBadge tone={status.tone} label={status.label} icon={status.icon} />
    </li>
  );
}
