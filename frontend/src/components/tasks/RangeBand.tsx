import type { TaskTimePrediction } from "@/api/types";
import { CHART } from "@/lib/chart";

/** Prediction range as a band on a minutes scale, with the prediction and the historical average marked. */
export function RangeBand({ p }: { p: TaskTimePrediction }) {
  const lo = Math.min(p.lower_min, p.historical_avg_min) * 0.85;
  const hi = Math.max(p.upper_min, p.historical_avg_min) * 1.1;
  const x = (v: number) => `${((v - lo) / (hi - lo)) * 100}%`;

  return (
    <div className="pt-6 pb-8" aria-label={`Likely range ${p.lower_min} to ${p.upper_min} minutes`}>
      <div className="relative h-4 rounded-full bg-raised">
        <div
          className="absolute inset-y-0 rounded-full"
          style={{ left: x(p.lower_min), width: `calc(${x(p.upper_min)} - ${x(p.lower_min)})`, background: `${CHART.series1}55` }}
        />
        <div className="absolute -inset-y-1.5 w-1 -translate-x-1/2 rounded bg-accent" style={{ left: x(p.predicted_time_min) }} />
        <div className="absolute -inset-y-1 w-0.5 -translate-x-1/2 bg-muted" style={{ left: x(p.historical_avg_min) }} />
        <span className="absolute -top-6 -translate-x-1/2 whitespace-nowrap text-xs font-semibold text-accent" style={{ left: x(p.predicted_time_min) }}>
          Predicted
        </span>
        <span className="absolute top-6 -translate-x-1/2 whitespace-nowrap text-xs text-muted" style={{ left: x(p.historical_avg_min) }}>
          Hist. avg {p.historical_avg_min} min
        </span>
      </div>
    </div>
  );
}
