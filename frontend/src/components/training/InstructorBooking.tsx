import { CalendarCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Button, cx } from "@/components/ui";

const SLOT_TIMES = ["07:00", "12:30", "16:30"];

/** Local-only slot picker: no booking backend in the MVP, so it just confirms on screen. */
export function InstructorBooking() {
  const days = useMemo(
    () =>
      Array.from({ length: 3 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i + 1);
        return d;
      }),
    [],
  );
  const [slot, setSlot] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState<string | null>(null);

  if (confirmed) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-good bg-good/10 p-6 text-center" role="status">
        <CalendarCheck className="size-12 text-good" aria-hidden />
        <p className="text-xl font-semibold">Session requested</p>
        <p className="text-muted">{confirmed}. Your site supervisor will confirm the instructor.</p>
        <Button onClick={() => { setConfirmed(null); setSlot(null); }}>Pick another slot</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-muted">Choose a slot for a one-to-one session with a certified instructor.</p>
      <div className="grid gap-4 md:grid-cols-3">
        {days.map((d) => {
          const dayLabel = d.toLocaleDateString([], { weekday: "long", day: "2-digit", month: "short" });
          return (
            <div key={dayLabel}>
              <p className="mb-2 font-semibold">{dayLabel}</p>
              <div className="flex flex-col gap-2">
                {SLOT_TIMES.map((t) => {
                  const id = `${dayLabel} at ${t}`;
                  return (
                    <button
                      key={id}
                      type="button"
                      aria-pressed={slot === id}
                      onClick={() => setSlot(id)}
                      className={cx(
                        "tabular min-h-12 rounded-xl border font-mono text-lg transition",
                        slot === id ? "border-accent bg-accent/15 text-accent" : "border-line bg-raised hover:border-muted",
                      )}
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <Button variant="primary" icon={CalendarCheck} disabled={!slot} onClick={() => setConfirmed(slot)}>
        Request session
      </Button>
    </div>
  );
}
