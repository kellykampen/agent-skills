import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

/** Blinking cursor — a solid block that toggles visibility every `blinkFrames`. */
export const Cursor: React.FC<{ color: string; blinkFrames?: number }> = ({ color, blinkFrames = 15 }) => {
  const frame = useCurrentFrame();
  const visible = Math.floor(frame / blinkFrames) % 2 === 0;
  return (
    <span
      style={{
        display: "inline-block",
        width: "0.55em",
        height: "1em",
        background: color,
        opacity: visible ? 1 : 0,
        verticalAlign: "text-bottom",
        marginLeft: 2,
      }}
    />
  );
};

/**
 * Types out `text` one character at a time, `charFrames` frames per character,
 * starting at `startFrame`. Always string-slicing — never per-character opacity
 * animation, which reads as a fade, not a type.
 */
export const Typewriter: React.FC<{
  text: string;
  charFrames?: number;
  startFrame?: number;
  style?: React.CSSProperties;
  cursorColor?: string;
}> = ({ text, charFrames = 1.5, startFrame = 0, style, cursorColor }) => {
  const frame = useCurrentFrame();
  const local = Math.max(0, frame - startFrame);
  const chars = interpolate(local, [0, text.length * charFrames], [0, text.length], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shown = text.slice(0, Math.floor(chars));
  const done = shown.length >= text.length;

  return (
    <span style={style}>
      {shown}
      {!done && <Cursor color={cursorColor ?? (style?.color as string) ?? "#fff"} />}
    </span>
  );
};
