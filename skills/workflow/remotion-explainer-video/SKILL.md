---
name: remotion-explainer-video
description: >-
  Use this to create a short animated explainer video or a README/social GIF for a skill, feature, product, workflow, or process — one render produces both an MP4 (with a real royalty-free soundtrack sourced live from Pixabay Music) and a matching GIF, in a shared dark editorial-diagram visual system (numbered scenes, curved arrows, node circles, status caption). Trigger on: "make a video/demo/hype video", a "walkthrough" of how something works, wanting a GIF for a README or social post that shows a flow/process (even if "video" is never said), sourcing or adding royalty-free/Pixabay music to a demo or product video, or extending an existing Remotion project with another explainer (e.g. a second skill/feature video alongside one already made). Also use when only one output format is requested — a GIF-only ask, or a music-only ask for an existing video — since the same render pipeline handles it. Not for trimming/editing already-finished raw footage, or podcast/audio editing unrelated to an explainer render.
compatibility: Requires Node.js/npm (Remotion), ffmpeg (GIF export), and a real browser-automation tool (e.g. cmux or claude-in-chrome) to get past Pixabay's Cloudflare bot-check when sourcing music.
metadata:
  author: kellykampen
  version: "1.0.0"
  requires: "node, ffmpeg"
---

# Remotion Explainer Video

Produces a ~15-30s explainer video (MP4 + GIF, with a real royalty-free soundtrack) for
whatever the user wants explained — a skill, a feature, a product, a workflow. The video is a
sequence of scenes built from a shared, tested visual system, not hand-rolled from scratch
each time.

## Workflow

### 1. Understand the subject and set scope

Before writing anything, get from the user (or infer from context and confirm):

- **What is this video explaining?** Read the actual source (a `SKILL.md`, a README, the
  feature's code) — don't write scene content from a vague gist of what it does. A video that
  gets the mechanics wrong is worse than no video.
- **Target length.** Default to "quick hype cut" (~20s) unless told otherwise. Longer needs
  explicit ask — most subjects don't need more than 6 scenes to land.
- **Music**: does the user have a track already, or should you find one? See
  `references/pixabay-sourcing.md` either way — even a user-provided file gets wired in the
  same way (fade in/out, `<Audio>` + `staticFile()`).
- **Where does this live?** Check for an existing Remotion project first (see
  `references/scaffolding.md`) — most of the time this is "add one more video to the project
  that already has others," not "start from zero."

### 2. Design the scene sequence

A typical explainer is 5-6 scenes, each a few seconds:

1. **Boot/title** — a typed command (if the subject is a CLI/skill) or a short hook line, then
   the title.
2. **The problem** — why does this need to exist? Scattered chip/tag visuals reading like
   overheard complaints work well here.
3. **The core mechanism** — the one diagram that actually explains how it works. This is the
   scene worth the most design effort; see "Choosing a diagram shape" below.
4. **A two-word contrast or a short checklist** — whatever the subject's second-most-important
   idea is (two responsibilities, two axes, a set of guardrails/rules).
5. **A short checklist/gates scene** — rules, tiers, or steps, if the subject has them.
6. **Outro** — tagline, install/usage command typed out, link.

Not every subject needs all six — a simple utility can do fine in 3 (boot → one diagram →
outro). Match the scene count to how much there actually is to say, not to a fixed template.

### 3. Choosing a diagram shape for the core scene

Don't default to the same tree/hub-and-spoke diagram every time — pick the shape that actually
matches the subject's structure:

- **Hierarchy / fan-out** (one thing dispatching to several): a root node with `CurveArrow`s
  fanning out to child nodes.
- **Standing loop** (poll → act → repeat until some exit condition): arrange 4-ish nodes in a
  circle/diamond, `CurveArrow` between consecutive ones, a small dot that continuously travels
  the loop (position via `frame % loopDuration`), and a resolution state that fades in once the
  loop "completes."
- **Before/after transformation** (a reorg, a migration, a refactor): two bordered panels
  side by side with a big arrow between them — works especially well when the "after" is
  genuinely just a file tree or a diff, rendered directly.
- **Classify-and-route** (input in, one of N choices out): a single classifier node, N option
  nodes below/around it, and a repeating sequence of "example in → route to the matching
  option → highlight it → fade" cycles (see `references/ephemeral-lifecycle-pattern.md`).
- **Repeating cast/clear** (ephemeral workers, retries, requests): read
  `references/ephemeral-lifecycle-pattern.md` before building this one — it's the trickiest to
  get right and there's a specific pattern that avoids a mechanical/looped feel.

### 4. Build it

Copy `assets/templates/theme.ts`, `Scene.tsx`, `Diagram.tsx`, `Typewriter.tsx` into the
project's `src/theme.ts` / `src/components/` (see `references/scaffolding.md` for exact
placement if scaffolding fresh). Customize `theme.ts`'s palette for this subject's brand —
everything else in the templates should work unmodified.

Write one file per scene, each returning `<Scene number="NN" label="..." status="...">...
</Scene>`. Wire them into a `<TransitionSeries>` composition with a ~12-frame `fade()` between
scenes; recompute the total duration in a comment every time a scene's length changes (fade
transitions overlap adjacent scenes, so total ≠ sum of scene durations — it's
`sum(scenes) - transitionFrames * (sceneCount - 1)`).

**Animation rule, no exceptions**: every visual change is driven by `useCurrentFrame()` via
`interpolate()`/`spring()`. No CSS transitions or `@keyframes` — Remotion renders frame-by-frame
and CSS-timed animation doesn't render correctly. Text that "types in" is always string-slicing
(`Typewriter` component), never per-character opacity fades.

### 5. Iterate via stills, not full renders

A full render takes 1-3 minutes; a single frame takes seconds. Check every scene this way
before committing to a full render:

```bash
npx remotion still <CompositionId> out/check-<frame>.png --frame=<n>
```

Pick frame numbers that land mid-animation for whatever you just built — remember scenes
overlap by the transition duration when computing a scene's global start offset (scene N's
global start = sum of previous scene durations minus `transitionFrames * N`). Read the PNG
back and actually look at it before moving on or rendering the full video.

### 6. Render, convert, ship

```bash
bash scripts/render-version.sh <CompositionId> <output-name-prefix>   # never overwrites, see Gotchas
bash scripts/make-gif.sh out/versions/<file>-vN.mp4 out/versions/<file>-vN.gif
```

Send both the MP4 (for anyone who wants audio/full quality) and the GIF (for inline preview) to
the user for review. If this is going into a README on GitHub: a plain markdown image
(`![alt](path.gif)`) is the only reliable way to get an animated inline preview — see the
"GitHub video embedding" gotcha below before trying anything with a `<video>` tag.

## Gotchas

- **SVG arrowheads render before their line draws in.** `marker-end` isn't clipped by
  `stroke-dasharray`/`dashoffset` — the fix (`progress > 0.97` gating the marker) is already in
  `assets/templates/Diagram.tsx`'s `CurveArrow`. Don't drop it if copying the arrow logic
  elsewhere.
- **The render-version script's version-detection must use `find`, not `ls`.** Under `set -o
  pipefail`, `ls` returning non-zero (no matches for a brand-new prefix) aborts the whole script
  silently before rendering starts. Already handled in `scripts/render-version.sh`.
- **`ffmpeg` steals stdin if you don't pass `-nostdin`.** Converting several videos to GIF in a
  `while read` loop will corrupt later filenames if `ffmpeg` is reading from the same stdin the
  loop is trying to read from. Already handled in `scripts/make-gif.sh`.
- **GitHub video embedding**: a `<video src="relative/path.mp4">` tag gets stripped entirely by
  GitHub's markdown sanitizer for repo-committed files (verified against the `/markdown` API
  directly — it renders as an empty paragraph). `<video>`/`<audio>` only survive when the `src`
  is on GitHub's own `user-attachments` asset domain, which requires uploading through the web
  UI (an issue/PR comment box), not a git commit. For a reliable inline-preview embed in a
  README, use the GIF as a plain markdown image and link the MP4 separately for anyone who
  wants audio.
- **Don't assume a browser-automation tool's success signal means the download landed** — see
  `references/pixabay-sourcing.md`. Verify on the filesystem directly.
- **Never `Math.random()` or `Date.now()`** anywhere in a composition — Remotion re-renders
  frames out of order and on repeat calls; anything non-deterministic breaks that. Use
  `frame`-derived pseudo-variation (e.g. `(slotIndex * 5) % 13`) instead.

## Completion criteria

- Both an MP4 and a GIF exist in `out/versions/` under a new version number (never overwritten).
- Every scene was checked via at least one still-frame render before the full render.
- The soundtrack has a fade-in and fade-out, and its filename/license is noted somewhere in the
  project (comment or README), even though Pixabay's license doesn't require on-video
  attribution.
- The user has seen and approved the actual rendered output — this is a creative/qualitative
  deliverable, not something a script can validate for you.
