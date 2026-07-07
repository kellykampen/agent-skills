# Detecting or scaffolding the Remotion project

## Detect first

Before creating anything, check whether a Remotion project already exists —
either in the current directory or a sibling directory that's clearly the
video-project counterpart to what's being explained (e.g. `../foo-explainer`,
`../foo-video`, a repo named after the main project with `-remotion` or
`-video` appended). Signs it's a Remotion project:

```bash
grep -l '"remotion"' package.json 2>/dev/null
test -f src/Root.tsx
```

If found, **add a new composition to the existing project** rather than
spinning up a parallel one — this is the common case once a project has more
than one video in it (e.g. one video per feature/skill being explained). See
"Adding a composition to an existing project" below.

## Scaffolding a new project

If nothing exists yet:

```bash
mkdir <project-name> && cd <project-name>
npm init -y
npm install remotion @remotion/cli @remotion/google-fonts @remotion/transitions @remotion/media react react-dom
npm install --save-dev typescript @types/react @types/node
```

Then hand-write (the interactive `create-video` scaffolder doesn't cooperate
well with non-interactive/headless environments — hand-assembling is more
reliable and only a few files):

- `tsconfig.json` — standard React/bundler config, `noEmit: true`, `include`
  scoped to `src/**/*`.
- `remotion.config.ts` — `Config.setVideoImageFormat("jpeg")`,
  `Config.setOverwriteOutput(true)`.
- `src/index.ts` — `registerRoot(RemotionRoot)`.
- `src/theme.ts` — copy from `assets/templates/theme.ts`, then customize the
  palette for this project's brand.
- `src/components/Scene.tsx`, `src/components/Diagram.tsx`,
  `src/components/Typewriter.tsx` — copy from `assets/templates/`, unmodified
  (these are the reusable primitives; project-specific content lives in scene
  files, not here).
- `scripts/render-version.sh`, `scripts/make-gif.sh` — copy from this skill's
  `scripts/`, `chmod +x` them.
- `.gitignore` — `node_modules/`, `out/` (rendered output is regenerable; only
  source gets committed if this becomes its own repo).
- `package.json` scripts: `"dev": "remotion studio"`, and one `"render:<name>"`
  script per composition (see below) — never a bare `remotion render` with a
  fixed output filename, always through `render-version.sh`.

## Font loading gotcha

Font file names under `@remotion/google-fonts` don't always match what you'd
guess from the Google Fonts website. Check the actual export name before
importing:

```bash
find node_modules/@remotion/google-fonts/dist/esm -iname "*Mono*"
```

## Adding a composition to an existing project

Prefer a **data-driven composition list** in `src/Root.tsx` over hand-adding a
`<Composition>` JSX block each time — with more than 2-3 videos in one project
this gets unwieldy fast:

```tsx
import { Composition } from "remotion";
import { FooExplainer, TOTAL_DURATION_IN_FRAMES as FOO_DURATION } from "./FooExplainer";
// ...one import pair per composition

const COMPOSITIONS = [
  { id: "FooExplainer", component: FooExplainer, durationInFrames: FOO_DURATION },
  // ...
];

export const RemotionRoot: React.FC = () => (
  <>
    {COMPOSITIONS.map((c) => (
      <Composition key={c.id} id={c.id} component={c.component} durationInFrames={c.durationInFrames} fps={FPS} width={WIDTH} height={HEIGHT} />
    ))}
  </>
);
```

And generalize the render script call rather than writing a new wrapper per
video — `scripts/render-version.sh` already takes `<compositionId>
<outputNamePrefix>` as arguments for exactly this reason. Add one
`package.json` script per composition:

```json
"render:foo": "bash scripts/render-version.sh FooExplainer foo-explainer"
```
