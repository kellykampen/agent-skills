# The ephemeral-entity lifecycle pattern

Read this when the video needs to show something being **repeatedly created,
doing work, and disappearing** — worker processes being cast/cleared, requests
being handled, retries, polling cycles, anything that isn't a single static
structure but a *rhythm* that repeats on independent schedules.

## The core idea

Everything downstream asks the same question — "is there an active cycle right
now, and how far into it are we?" — and renders nothing if the answer is no.
That single shared question is what keeps visually-paired elements (e.g. a node
and the line connecting it to its parent) in perfect sync: they can't drift
apart because they're both computed from the same `activeCycle()` call, not
from two independently-tuned timers.

```ts
// A cycle is fully described by its start frame; everything else is relative to it.
const CYCLE = { workEnd: 30, checkHoldEnd: 42, fadeEnd: 54 };

function activeCycle(frame: number, starts: number[]): { t: number; index: number } | null {
  let idx = -1;
  for (let i = 0; i < starts.length; i++) {
    if (starts[i] <= frame) idx = i;
    else break;
  }
  if (idx === -1) return null;
  const t = frame - starts[idx];
  if (t > CYCLE.fadeEnd) return null;
  return { t, index: idx };
}

function getCycleStarts(base: number, phase: number, cycleLen: number, sceneEnd: number): number[] {
  const starts: number[] = [];
  let t = base + phase;
  while (t < sceneEnd) {
    starts.push(t);
    t += cycleLen;
  }
  return starts;
}
```

Every visual element that belongs to one "slot" (a worker seat, a connection
line, a retry indicator) takes the *same* `starts` array and calls
`activeCycle(frame, starts)` to decide whether it's visible and, if so, its
local animation phase `t`.

## Making it read as organic, not mechanical

- **Stagger both phase and cycle length per slot.** `cycleLen = base +
  ((slotIndex * 5) % 13)` is enough deterministic irregularity that slots don't
  all cast/clear in lockstep, without resorting to `Math.random()` — which
  breaks Remotion's deterministic re-renders and must never appear in a
  composition.
- **Vary what appears on each re-cast**, if applicable — e.g. `models[(slotIndex
  + cycleIndex) % models.length]` so the same seat shows something different
  each time it's re-cast, avoiding an obviously-looped feel.
- **Don't forget the fade-out.** A component that fully draws in via
  `stroke-dashoffset` but has no fade-out logic will happily stay at 100%
  opacity forever once drawn — decaying opacity has to be computed
  independently (typically via the same `t` value, e.g. `interpolate(t,
  [CYCLE.checkHoldEnd, CYCLE.fadeEnd], [1, 0])`), it doesn't happen for free.

## Common mistake this pattern avoids

An early, tempting shortcut is "cast once, then respawn the one designated slot
a single time" — it looks fine in a demo but reads as static and rehearsed on a
second viewing. The `getCycleStarts` approach generates a genuinely repeating
schedule per slot for the life of the scene, which is what actually sells "this
happens continuously," not "this happened twice for the demo."
