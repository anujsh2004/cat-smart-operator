/** Top-down view: machine in the centre, 5 m danger zone ring, and a dot for the nearest person/object. */
const DANGER_M = 5;
const MAX_M = 20; // outer ring = 20 m

export function ProximityRing({ distance, person }: { distance: number; person: boolean }) {
  const R = 90; // svg radius for MAX_M
  // Square-root scale so the 5 m danger zone fills half the radius and stays readable
  const scale = (m: number) => Math.sqrt(Math.min(m, MAX_M) / MAX_M) * R;
  const inDanger = distance < DANGER_M;
  // Fixed bearing (front-right of the machine); the sensor only reports distance
  const angle = -Math.PI / 4;
  const dx = Math.cos(angle) * scale(distance);
  const dy = Math.sin(angle) * scale(distance);

  return (
    <svg viewBox="-100 -100 200 200" className="size-48 shrink-0" role="img"
      aria-label={`Nearest ${person ? "person" : "object"} ${distance.toFixed(1)} metres away; danger zone is ${DANGER_M} metres`}>
      <circle r={scale(MAX_M)} fill="none" stroke="#2a313b" />
      <circle r={scale(10)} fill="none" stroke="#2a313b" />
      <circle r={scale(DANGER_M)} fill={inDanger ? "rgb(239 68 68 / 0.35)" : "rgb(239 68 68 / 0.12)"} stroke="#ef4444" strokeWidth="1.5" />
      <text x="0" y={-scale(DANGER_M) + 12} textAnchor="middle" fill="#ef4444" fontSize="11">5 m</text>
      <text x="0" y={-scale(10) + 12} textAnchor="middle" fill="#9aa4b1" fontSize="11">10 m</text>
      <text x="0" y={-scale(MAX_M) + 12} textAnchor="middle" fill="#9aa4b1" fontSize="11">20 m</text>
      {/* machine */}
      <rect x="-7" y="-9" width="14" height="18" rx="2" fill="#f5b800" />
      {/* nearest person / object */}
      <circle cx={dx} cy={dy} r="8" fill={person ? (inDanger ? "#ef4444" : "#f59e0b") : "#9aa4b1"} stroke="#15191f" strokeWidth="2" />
    </svg>
  );
}
