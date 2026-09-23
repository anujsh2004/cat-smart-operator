import { Send } from "lucide-react";
import { useState } from "react";
import { useCreateIncident } from "@/api/hooks";
import { EVENT_TYPES, SEVERITIES, type EventType, type Severity } from "@/api/types";
import { Modal } from "@/components/Modal";
import { Button, Field, inputClass, Select } from "@/components/ui";
import { EVENT_LABEL, titleCase } from "@/lib/format";

export function ReportIncidentModal({
  open,
  onClose,
  machineId,
  operatorId,
}: {
  open: boolean;
  onClose: () => void;
  machineId: string;
  operatorId: string;
}) {
  const [eventType, setEventType] = useState<EventType>("manual_report");
  const [severity, setSeverity] = useState<Severity>("medium");
  const [description, setDescription] = useState("");
  const create = useCreateIncident();

  const close = () => {
    create.reset();
    setDescription("");
    onClose();
  };

  return (
    <Modal title="Report incident" open={open} onClose={close}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate(
            { machine_id: machineId, operator_id: operatorId, event_type: eventType, severity, description: description.trim() },
            { onSuccess: close },
          );
        }}
      >
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type">
            <Select value={eventType} options={EVENT_TYPES} labels={EVENT_LABEL} onChange={setEventType} />
          </Field>
          <Field label="Severity">
            <Select
              value={severity}
              options={SEVERITIES}
              labels={Object.fromEntries(SEVERITIES.map((s) => [s, titleCase(s)]))}
              onChange={setSeverity}
            />
          </Field>
        </div>
        <Field label="What happened?">
          <textarea
            required
            rows={4}
            className={`${inputClass} py-2`}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Loose rock near the trench edge"
          />
        </Field>
        <p className="text-sm text-muted">
          Machine {machineId} · Operator {operatorId}
        </p>
        {create.isError && <p className="text-sm text-danger" role="alert">{create.error.message}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" icon={Send} disabled={create.isPending || !description.trim()}>
            Submit report
          </Button>
        </div>
      </form>
    </Modal>
  );
}
