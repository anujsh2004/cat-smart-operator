// Single-series charts for the Machine page. One measure per chart (never a dual axis),
// series-1 blue, recessive solid grid, hover tooltip on every chart.
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { axisProps, CHART, tooltipStyle } from "@/lib/chart";

type Row = Record<string, string | number>;

export function TimeLineChart({
  data,
  dataKey,
  unit,
  label,
  xKey = "time",
  height = 180,
}: {
  data: Row[];
  dataKey: string;
  unit: string;
  label: string;
  xKey?: string;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
        <CartesianGrid vertical={false} stroke={CHART.grid} />
        <XAxis dataKey={xKey} {...axisProps} minTickGap={40} />
        <YAxis {...axisProps} width={48} domain={["auto", "auto"]} />
        <Tooltip {...tooltipStyle} cursor={{ stroke: CHART.axis }} formatter={(v: number) => [`${v} ${unit}`, label]} />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={CHART.series1}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: CHART.surface, strokeWidth: 2 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function DayBarChart({
  data,
  dataKey,
  unit,
  label,
  height = 200,
  allowDecimals = true,
}: {
  data: Row[];
  dataKey: string;
  unit: string;
  label: string;
  height?: number;
  allowDecimals?: boolean;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
        <CartesianGrid vertical={false} stroke={CHART.grid} />
        <XAxis dataKey="day" {...axisProps} />
        <YAxis {...axisProps} width={48} allowDecimals={allowDecimals} />
        <Tooltip {...tooltipStyle} formatter={(v: number) => [`${v} ${unit}`.trim(), label]} />
        <Bar dataKey={dataKey} fill={CHART.series1} radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Idle % per day against the fleet average (a labelled reference line, same axis). */
export function IdleVsFleetChart({ data, fleetAvg, height = 200 }: { data: Row[]; fleetAvg: number; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 16, right: 76, bottom: 0, left: -8 }}>
        <CartesianGrid vertical={false} stroke={CHART.grid} />
        <XAxis dataKey="day" {...axisProps} />
        <YAxis {...axisProps} width={48} domain={[0, (max: number) => Math.max(50, Math.ceil(max / 10) * 10)]} unit="%" />
        <Tooltip {...tooltipStyle} cursor={{ stroke: CHART.axis }} formatter={(v: number) => [`${v}%`, "Your idle"]} />
        <ReferenceLine
          y={fleetAvg}
          stroke={CHART.reference}
          label={{ value: `Fleet ${fleetAvg}%`, position: "right", fill: CHART.axis, fontSize: 12 }}
        />
        <Line
          type="monotone"
          dataKey="idle_pct"
          stroke={CHART.series1}
          strokeWidth={2}
          dot={{ r: 4, fill: CHART.series1, stroke: CHART.surface, strokeWidth: 2 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
