import { loadFont as loadMono } from "@remotion/google-fonts/IBMPlexMono";
import { loadFont as loadSans } from "@remotion/google-fonts/IBMPlexSans";

// Swap these two for whatever the target project's own type pair should be —
// `mono` is for literal command-line/code text, `sans` for everything else.
export const { fontFamily: mono } = loadMono("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export const { fontFamily: sans } = loadSans("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

// CUSTOMIZE THIS PALETTE per project — these are placeholder values in a
// dark-editorial-diagram style (see references/design-system.md). Keep the
// *roles* (bg/fg/accent/muted/etc.), just change the actual hex values to
// match whatever brand/product this video is for.
export const COLOR = {
  bg: "#15120d", // page background
  bgPanel: "#1c1811", // card/panel background
  edge: "#332a1e", // subtle borders
  edgeLight: "#4a3f2d", // slightly brighter borders (dividers, outros)
  fg: "#ece4d3", // primary text
  ink: "#d9d0ba", // secondary text (arrows, captions)
  muted: "#93876f", // tertiary text (labels, status chip)
  accent: "#ffb454", // the ONE accent color — conductor/lead/primary-action nodes
  accentDim: "#caa15e",
  accentDeep: "#8a6a2e",
  worker: "#7ea3c7", // secondary node color, when you need a second hue
  workerDim: "#5c7a99",
  green: "#7cd992", // success/checkmark color — keep this semantic, not the accent
};

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
