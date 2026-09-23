// Chart colours for the dark card surface (#15191f). Validated with the dataviz palette checker:
// series-1 blue and the blue<->red diverging pair pass lightness, chroma, CVD and contrast checks.
// Status colours (good/warn/danger) are reserved for status and never used as series colours.
export const CHART = {
  series1: "#3987e5",
  adds: "#e66767", // diverging warm pole: adds time
  saves: "#3987e5", // diverging cool pole: saves time
  grid: "#2a313b",
  axis: "#9aa4b1",
  ink: "#eceef1",
  surface: "#15191f",
  reference: "#9aa4b1",
} as const;

export const tooltipStyle = {
  contentStyle: {
    background: "#1d232b",
    border: "1px solid #2a313b",
    borderRadius: 12,
    color: CHART.ink,
    fontSize: 14,
  },
  labelStyle: { color: CHART.axis, marginBottom: 4 },
  itemStyle: { color: CHART.ink },
  cursor: { fill: "rgb(255 255 255 / 0.04)", stroke: CHART.grid },
} as const;

export const axisProps = {
  stroke: CHART.grid,
  tick: { fill: CHART.axis, fontSize: 13 },
  tickLine: false,
} as const;
