import { CheckCircle2, ClipboardList } from "lucide-react";
import { useState, type ReactNode } from "react";
import { useIncidents, useResolveIncident } from "@/api/hooks";
import { EVENT_TYPES, type EventType, type Incident, type IncidentStatus } from "@/api/types";
import { Modal } from "@/components/Modal";
import { Button, Card, EmptyState, Field, inputClass, QueryBlock, Select, Skeleton, StatusBadge } from "@/components/ui";
import { EVENT_LABEL, fmtDateTime, fmtDuration } from "@/lib/format";
import { EVENT_ICON, INCIDENT_STATUS, SEVERITY } from "@/lib/status";

type StatusFilter = "all" | IncidentStatus;
type TypeFilter = "all" | EventType;

function ResolveModal({ incident, onClose }: { incident: Incident | null; onClose: () => void }) {
  const [resolution, setResolution] = useState("Hazard cleared");
  const resolve = useResolveIncident();
  return (
    <Modal title={`Resolve ${incident?.incident_id ?? ""}`} open={!!incident} onClose={onClose}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (incident) resolve.mutate({ id: incident.incident_id, resolution }, { onSuccess: onClose });
        }}
      >
        <Field label="Resolution">
          <input className={inputClass} required value={resolution} onChange={(e) => setResolution(e.target.value)} />
        </Field>
        {resolve.isError && <p className="text-sm text-danger" role="alert">{resolve.error.message}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" icon={CheckCircle2} disabled={resolve.isPending || !resolution.trim()}>
            Mark resolved
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export function IncidentLog({ machineId, action }: { machineId: string | undefined; action?: ReactNode }) {
  const [status, setStatus] = useState<StatusFilter>("all");
  const [type, setType] = useState<TypeFilter>("all");
  const [resolving, setResolving] = useState<Incident | null>(null);
  const incidents = useIncidents({ machine_id: machineId, status: status === "all" ? undefined : status, limit: 100 });

  return (
    <Card title="Incident log" icon={ClipboardList} action={action}>
      <div className="mb-4 flex flex-wrap gap-3">
        <Field label="Status">
          <Select<StatusFilter>
            value={status}
            options={["all", "open", "resolved"]}
            labels={{ all: "All statuses", open: "Open", resolved: "Resolved" }}
            onChange={setStatus}
          />
        </Field>
        <Field label="Type">
          <Select<TypeFilter>
            value={type}
            options={["all", ...EVENT_TYPES]}
            labels={{ all: "All types", ...EVENT_LABEL }}
            onChange={setType}
          />
        </Field>
      </div>

      <QueryBlock query={incidents} skeleton={<Skeleton className="h-64" />}>
        {(all) => {
          const rows = type === "all" ? all : all.filter((i) => i.event_type === type);
          if (rows.length === 0) return <EmptyState title="No incidents match these filters" />;
          return (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left">
                <thead className="text-sm text-muted">
                  <tr className="border-b border-line">
                    {["ID", "Time", "Event", "Severity", "Risk", "Status", "Duration", ""].map((h) => (
                      <th key={h} className="px-3 py-2 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((i) => {
                    const Icon = EVENT_ICON[i.event_type];
                    const sev = SEVERITY[i.severity];
                    const st = INCIDENT_STATUS[i.status];
                    return (
                      <tr key={i.incident_id} className="border-b border-line/60 last:border-0">
                        <td className="tabular px-3 py-2 font-mono font-bold">{i.incident_id}</td>
                        <td className="px-3 py-2 text-muted">{fmtDateTime(i.timestamp)}</td>
                        <td className="px-3 py-2">
                          <span className="flex items-center gap-2">
                            <Icon className="size-5 text-muted" aria-hidden />
                            {EVENT_LABEL[i.event_type]}
                          </span>
                        </td>
                        <td className="px-3 py-2"><StatusBadge tone={sev.tone} label={sev.label} icon={sev.icon} /></td>
                        <td className="tabular px-3 py-2 font-mono">{i.risk_score ?? "—"}</td>
                        <td className="px-3 py-2"><StatusBadge tone={st.tone} label={st.label} icon={st.icon} /></td>
                        <td className="tabular px-3 py-2 font-mono">{fmtDuration(i.duration_s)}</td>
                        <td className="px-3 py-2 text-right">
                          {i.status === "open" && (
                            <Button icon={CheckCircle2} onClick={() => setResolving(i)}>
                              Resolve
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        }}
      </QueryBlock>
      <ResolveModal key={resolving?.incident_id} incident={resolving} onClose={() => setResolving(null)} />
    </Card>
  );
}
