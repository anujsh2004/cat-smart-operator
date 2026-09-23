import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PredictionFactor } from "@/api/types";
import { axisProps, CHART, tooltipStyle } from "@/lib/chart";

const fmt = (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(1)} min`;

/** Horizontal diverging bars: red adds time, blue saves time, around a neutral zero line. */
export function FactorChart({ factors }: { factors: PredictionFactor[] }) {
  const data = factors.map((f) => ({ label: f.label, impact: f.impact_min }));
  const max = Math.ceil(Math.max(1, ...data.map((d) => Math.abs(d.impact))) * 1.35); // room for the value labels
  const ticks = [-max, -max / 2, 0, max / 2, max];

  return (
    <div>
      <div className="mb-2 flex gap-4 text-sm text-muted" aria-hidden>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm" style={{ background: CHART.adds }} /> Adds time
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm" style={{ background: CHART.saves }} /> Saves time
        </span>
      </div>
      <ResponsiveContainer width="100%" height={data.length * 52 + 36}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }} barCategoryGap={10}>
          <CartesianGrid horizontal={false} stroke={CHART.grid} />
          <XAxis type="number" domain={[-max, max]} ticks={ticks} tickFormatter={(v: number) => `${+v.toFixed(1)}`} {...axisProps} />
          <YAxis type="category" dataKey="label" width={170} {...axisProps} tick={{ fill: CHART.ink, fontSize: 14 }} />
          <ReferenceLine x={0} stroke={CHART.reference} />
          <Tooltip {...tooltipStyle} formatter={(v: number) => [fmt(v), "Impact"]} />
          <Bar dataKey="impact" isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.label} fill={d.impact >= 0 ? CHART.adds : CHART.saves} />
            ))}
            <LabelList dataKey="impact" position="right" formatter={fmt} fill={CHART.ink} fontSize={13} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
