import { ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { useMachineId, useSafety } from "@/api/hooks";

/** Global banner shown on every page while the safety assessment says alert. */
export function SafetyAlertBanner() {
  const { data: safety } = useSafety(useMachineId());
  if (!safety?.alert) return null;
  const top = safety.factors[0];

  return (
    <div role="alert" className="alert-pulse flex flex-wrap items-center gap-4 px-6 py-3 text-white">
      <ShieldAlert className="size-8 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-lg font-bold">
          HIGH RISK · {safety.risk_score}/100{top ? ` · ${top.label}` : ""}
        </p>
        <p className="text-sm text-white/90">{safety.recommended_action}</p>
      </div>
      <Link
        to="/safety"
        className="inline-flex min-h-12 items-center rounded-xl bg-white px-4 font-semibold text-danger hover:bg-white/90"
      >
        View safety
      </Link>
    </div>
  );
}
