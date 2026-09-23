import type { RiskLevel } from "@/api/types";
import { RISK } from "@/lib/status";

const COLOR: Record<RiskLevel, string> = { LOW: "#22c55e", MEDIUM: "#f59e0b", HIGH: "#ef4444" };

/** Semicircle 0–100 gauge coloured by risk level, with the score and level as text. */
export function RiskGauge({ score, level, size = 200 }: { score: number; level: RiskLevel; size?: number }) {
  const r = 80;
  const len = Math.PI * r; // half-circle arc length
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const { label } = RISK[level];
  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg viewBox="0 0 200 116" width={size} role="img" aria-label={`Risk score ${score} of 100, ${label}`}>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#2a313b" strokeWidth="18" strokeLinecap="round" />
        <path
          d="M20 100 A80 80 0 0 1 180 100"
          fill="none"
          stroke={COLOR[level]}
          strokeWidth="18"
          strokeLinecap="round"
          strokeDasharray={`${len * pct} ${len}`}
          style={{ transition: "stroke-dasharray 0.6s ease, stroke 0.3s" }}
        />
        <text x="100" y="92" textAnchor="middle" fill="#eceef1" fontSize="44" fontWeight="700"
          fontFamily="JetBrains Mono, ui-monospace, monospace">
          {score}
        </text>
        <text x="100" y="112" textAnchor="middle" fill="#9aa4b1" fontSize="12">
          of 100
        </text>
      </svg>
    </div>
  );
}
