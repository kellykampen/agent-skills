import React from "react";
import { AbsoluteFill } from "remotion";
import { COLOR, sans } from "../theme";

/** Numbered chapter badge, top-left — one per scene, in sequence ("01", "02", ...). */
const SceneBadge: React.FC<{ number: string; label: string }> = ({ number, label }) => (
  <div style={{ position: "absolute", top: 56, left: 80, display: "flex", alignItems: "center", gap: 14 }}>
    <div
      style={{
        width: 34,
        height: 34,
        background: COLOR.accent,
        borderRadius: 4,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: sans,
        fontWeight: 700,
        fontSize: 18,
        color: COLOR.bg,
      }}
    >
      {number}
    </div>
    <div style={{ fontFamily: sans, fontWeight: 600, fontSize: 17, color: COLOR.muted, letterSpacing: 0.3 }}>
      {label}
    </div>
  </div>
);

/** Persistent running-caption chip, bottom-left — a colored dot + a one-line status per scene. */
const StatusChip: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      position: "absolute",
      bottom: 56,
      left: 80,
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "9px 16px",
      borderRadius: 999,
      border: `1px solid ${COLOR.edgeLight}`,
      background: COLOR.bgPanel,
    }}
  >
    <div style={{ width: 8, height: 8, borderRadius: "50%", background: COLOR.accent }} />
    <div style={{ fontFamily: sans, fontSize: 15, color: COLOR.muted }}>{text}</div>
  </div>
);

/**
 * Shared wrapper every scene renders inside — background, ambient glow, the
 * chapter badge, and the running status chip. Keeps chrome consistent without
 * copy-pasting it into every scene file.
 */
export const Scene: React.FC<{
  children: React.ReactNode;
  number?: string;
  label?: string;
  status?: string;
}> = ({ children, number, label, status }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLOR.bg, fontFamily: sans, color: COLOR.fg }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 90% at 50% -10%, ${COLOR.accent}0f, transparent 55%)`,
        }}
      />
      {number && label && <SceneBadge number={number} label={label} />}
      {status && <StatusChip text={status} />}
      <AbsoluteFill style={{ padding: "80px 120px", justifyContent: "center", alignItems: "center" }}>
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
