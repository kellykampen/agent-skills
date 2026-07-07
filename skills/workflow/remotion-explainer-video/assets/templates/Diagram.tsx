import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLOR } from "../theme";

/** Arrowhead marker defs — put once inside each <svg> that uses <CurveArrow>. */
export const ArrowDefs: React.FC = () => (
  <defs>
    <marker id="arrow-ink" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">
      <path d="M0,0 L12,5 L0,10 z" fill={COLOR.ink} />
    </marker>
    <marker id="arrow-accent" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">
      <path d="M0,0 L12,5 L0,10 z" fill={COLOR.accent} />
    </marker>
    <marker id="arrow-muted" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">
      <path d="M0,0 L12,5 L0,10 z" fill={COLOR.muted} />
    </marker>
  </defs>
);

function boundaryPoint(cx: number, cy: number, towardX: number, towardY: number, r: number) {
  const dx = towardX - cx;
  const dy = towardY - cy;
  const len = Math.hypot(dx, dy) || 1;
  return { x: cx + (dx / len) * r, y: cy + (dy / len) * r };
}

function quadPoint(
  p0: { x: number; y: number },
  q: { x: number; y: number },
  p1: { x: number; y: number },
  t: number,
) {
  const mt = 1 - t;
  return {
    x: mt * mt * p0.x + 2 * mt * t * q.x + t * t * p1.x,
    y: mt * mt * p0.y + 2 * mt * t * q.y + t * t * p1.y,
  };
}

function quadLength(
  p0: { x: number; y: number },
  q: { x: number; y: number },
  p1: { x: number; y: number },
  samples = 24,
) {
  let len = 0;
  let prev = p0;
  for (let i = 1; i <= samples; i++) {
    const pt = quadPoint(p0, q, p1, i / samples);
    len += Math.hypot(pt.x - prev.x, pt.y - prev.y);
    prev = pt;
  }
  return len;
}

/**
 * A directional connector between two NODE CENTERS (with their radii) that draws in
 * over time and ends in an arrowhead. Curves via a perpendicular "bow" offset (0 = straight).
 *
 * The start/end points are computed on each node's boundary along the curve's actual
 * approach angle (not just "above center") — this is what makes the arrowhead land
 * cleanly on the edge even for a diagonal connection between off-axis nodes.
 *
 * GOTCHA: SVG's marker-end renders at the path's final vertex regardless of
 * stroke-dasharray/dashoffset — so without the `progress > 0.97` gate below, the
 * arrowhead pops in at full opacity at frame 0, before the line has visibly drawn in.
 * Keep that gate; it's not optional polish.
 */
export const CurveArrow: React.FC<{
  x1: number;
  y1: number;
  r1?: number;
  x2: number;
  y2: number;
  r2?: number;
  bow?: number;
  delay: number;
  duration?: number;
  color?: "ink" | "accent" | "muted";
  strokeWidth?: number;
}> = ({ x1, y1, r1 = 0, x2, y2, r2 = 0, bow = 0, delay, duration = 18, color = "ink", strokeWidth = 3 }) => {
  const frame = useCurrentFrame();
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const q = { x: mx + (-dy / len) * bow, y: my + (dx / len) * bow };

  const start = boundaryPoint(x1, y1, q.x, q.y, r1);
  const end = boundaryPoint(x2, y2, q.x, q.y, r2);
  const total = quadLength(start, q, end);

  const progress = interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const dashoffset = total * (1 - progress);
  const strokeColor = color === "accent" ? COLOR.accent : color === "muted" ? COLOR.muted : COLOR.ink;

  return (
    <path
      d={`M ${start.x} ${start.y} Q ${q.x} ${q.y} ${end.x} ${end.y}`}
      fill="none"
      stroke={strokeColor}
      strokeWidth={strokeWidth}
      strokeDasharray={total}
      strokeDashoffset={dashoffset}
      markerEnd={progress > 0.97 ? `url(#arrow-${color})` : undefined}
    />
  );
};

/** A node in the conductor/agent/worker vocabulary: solid-filled or outlined-ring circle. */
export const NodeCircle: React.FC<{
  x: number;
  y: number;
  r: number;
  variant: "solid" | "ring";
  color?: string;
  delay: number;
  label?: string;
  labelBelow?: boolean;
  labelSize?: number;
}> = ({ x, y, r, variant, color = COLOR.accent, delay, label, labelBelow = true, labelSize = 17 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 15, stiffness: 150 } });
  const opacity = interpolate(s, [0, 1], [0, 1]);
  const scale = interpolate(s, [0, 1], [0.5, 1]);

  return (
    <>
      <g style={{ opacity }} transform={`translate(${x} ${y}) scale(${scale})`}>
        <circle
          cx={0}
          cy={0}
          r={r}
          fill={variant === "solid" ? color : "none"}
          stroke={color}
          strokeWidth={variant === "ring" ? 3 : 0}
        />
      </g>
      {label && (
        <foreignObject
          x={x - 140}
          y={labelBelow ? y + r + 10 : y - r - labelSize - 16}
          width={280}
          height={30}
          style={{ opacity }}
        >
          <div
            style={{
              fontFamily: "inherit",
              fontSize: labelSize,
              color: COLOR.muted,
              textAlign: "center",
              whiteSpace: "nowrap",
            }}
          >
            {label}
          </div>
        </foreignObject>
      )}
    </>
  );
};

/** A persistent soft glow behind an always-active node (e.g. the conductor/lead's ambient aura). */
export const StaticHalo: React.FC<{ x: number; y: number; r: number; color?: string; delay?: number }> = ({
  x,
  y,
  r,
  color = COLOR.accent,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  const opacity = interpolate(s, [0, 1], [0, 0.1]);
  return <circle cx={x} cy={y} r={r * 1.6} fill={color} opacity={opacity} />;
};

/** A one-shot expanding ring when a signal arrives at a node — a brief "it's live" ping. */
export const ArrivalPulse: React.FC<{ x: number; y: number; r: number; color?: string; delay: number }> = ({
  x,
  y,
  r,
  color = COLOR.accent,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 22 } });
  const scale = interpolate(s, [0, 1], [0.7, 2]);
  const opacity = interpolate(s, [0, 1], [0.4, 0]);
  if (opacity <= 0.005) return null;
  return (
    <circle
      cx={x}
      cy={y}
      r={r}
      fill="none"
      stroke={color}
      strokeWidth={2}
      opacity={opacity}
      transform={`translate(${x} ${y}) scale(${scale}) translate(${-x} ${-y})`}
    />
  );
};

/** Small colored square + number — for numbered panels/chapters/steps. */
export const NumberBadge: React.FC<{ x: number; y: number; number: string; delay: number }> = ({
  x,
  y,
  number,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  const opacity = interpolate(s, [0, 1], [0, 1]);

  return (
    <foreignObject x={x - 17} y={y - 17} width={34} height={34} style={{ opacity }}>
      <div
        style={{
          width: 34,
          height: 34,
          background: COLOR.accent,
          borderRadius: 4,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 700,
          fontSize: 17,
          color: COLOR.bg,
        }}
      >
        {number}
      </div>
    </foreignObject>
  );
};
