/** Server-rendered sparkline with a CSS draw-on animation. */
export function Sparkline({
  values,
  width = 120,
  height = 32,
  tone = "neutral",
}: {
  values: number[];
  width?: number;
  height?: number;
  tone?: "positive" | "negative" | "neutral";
}) {
  if (values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pad = 3;
  const pts = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * (width - pad * 2);
    const y = pad + (1 - (v - min) / span) * (height - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const stroke =
    tone === "positive" ? "var(--positive)" : tone === "negative" ? "var(--negative)" : "var(--faint)";
  const [lastX, lastY] = pts[pts.length - 1].split(",");

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden
      className="shrink-0"
    >
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        style={{
          strokeDasharray: 1,
          strokeDashoffset: 1,
          animation: "spark-draw 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.15s forwards",
        }}
      />
      <circle cx={lastX} cy={lastY} r="2" fill={stroke} style={{ opacity: 0, animation: "spark-dot 0.3s ease-out 1.2s forwards" }} />
    </svg>
  );
}
