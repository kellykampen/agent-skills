# Sourcing a soundtrack from Pixabay Music

Pixabay Music (`pixabay.com/music/search/<genre>`) hosts tracks under the
**Pixabay Content License** — free for commercial use, no attribution required.
That makes it a good default source for a video soundtrack. The catch is entirely
mechanical, not legal: getting the actual file.

## The gotcha: Cloudflare blocks scripted downloads

Pixabay's download endpoint sits behind a Cloudflare Turnstile bot-check. `curl`
or `wget` against the download URL returns a "Just a moment..." Cloudflare
challenge page, not the audio file — every time, no matter how the request is
shaped. **Do not spend time trying to script around this** (spoofing headers,
following redirects, etc.) — it's not a solvable curl problem, because the
challenge requires a real browser session that's already passed Turnstile.

## The fix: drive a real browser through the actual UI

Use whichever browser-automation tool is available in this environment (`cmux
browser`, `claude-in-chrome`, or similar) to:

1. Navigate to `https://pixabay.com/music/search/<mood-or-genre>/` (e.g.
   `synthwave`, `lo-fi`, `corporate`, `cinematic` — match the video's tone).
2. Browse previews and pick a track that fits the pacing and mood.
3. Click that track's own download button in the real page — the browser's
   session has already cleared Turnstile, so this succeeds where curl can't.
4. The file lands in the browser's default download directory (commonly
   `~/Downloads`).

**Verify the download landed by checking the filesystem directly**, not by
trusting the automation tool's own "did this succeed" signal — those can be
unreliable for file-download side effects. A plain, un-aliased listing sorted
by time works:

```bash
/bin/ls -lat ~/Downloads/*.mp3 | head -5
```

Use `/bin/ls` explicitly — if the user's shell aliases `ls` to something else
(`eza`, `exa`, etc.) with different flag semantics, a plain `ls -lat` can throw
an error that gets silently swallowed if you piped `2>/dev/null` earlier while
debugging. Confirm the file is real and playable before wiring it in:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 ~/Downloads/<file>.mp3
```

## Wiring it into the composition

Copy the file into the Remotion project's `public/` directory with a
descriptive name (not the raw Pixabay slug), then reference it via
`staticFile()` and `<Audio>` from `@remotion/media` — always with a frame-driven
fade-in/fade-out `volume` callback, never a flat volume even for a short clip:

```tsx
import { Audio } from "@remotion/media";
import { interpolate, staticFile } from "remotion";

const FADE_IN_FRAMES = 20;
const FADE_OUT_FRAMES = 35;
const MUSIC_PEAK_VOLUME = 0.4;

<Audio
  src={staticFile("soundtrack.mp3")}
  volume={(f) => {
    const fadeIn = interpolate(f, [0, FADE_IN_FRAMES], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const fadeOut = interpolate(f, [TOTAL_DURATION_IN_FRAMES - FADE_OUT_FRAMES, TOTAL_DURATION_IN_FRAMES], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return Math.min(fadeIn, fadeOut) * MUSIC_PEAK_VOLUME;
  }}
/>
```

Note the actual track title and artist name (shown on its Pixabay page) in a
one-line comment or the project's README — "Pixabay Content License, no
attribution required" is still worth recording for your own future reference,
even though it isn't legally required on the video itself.

## If the user already has a track in hand

If the user hands you a local file path directly (as opposed to asking you to
find one), skip all of the above — just copy it into `public/` and wire it in
the same way. The browser-automation dance is only for the "go find me
something" case.
