---
name: e2e-remote-setup
description: Set up REMOTE execution of a focus-stealing Electron/GUI Playwright E2E suite so it runs on a remote headless Linux box (Xvfb virtual display) via crabbox + E2B, instead of opening real windows that steal the local machine's mouse and keyboard. Adds a `test:e2e:remote` script, a `.crabbox.yaml`, and a Dockerfile-built E2B template. Use when a project's E2E suite launches the real app locally (e.g. Playwright `_electron.launch`, or any suite that grabs the display), and the user wants to run it remotely / in CI-like isolation / "set up e2e:remote" / "run e2e on a remote box" / stop it stealing focus.
compatibility: Requires the `crabbox` CLI and an E2B account (`e2b` CLI). Target project must have a runnable E2E script (e.g. `pnpm test:e2e`).
metadata:
  author: kellykampen
  version: "1.1.0"
  requires: "crabbox, e2b"
---

# Remote E2E setup (crabbox + E2B)

Turn a **focus-stealing** local E2E suite into one that runs on a **remote headless Linux
box**. Electron E2E (Playwright `_electron.launch`) opens a real OS window that grabs
mouse/keyboard on the dev machine — there's no local headless display for a full Electron
app. This skill wires up **crabbox** to lease an **E2B** sandbox, rsync the working tree,
install deps, and run the suite under **Xvfb** (an in-RAM X display), streaming results
back. The developer's local focus is never touched.

The end state is a single command:

```bash
pnpm test:e2e:remote     # runs the E2E suite on a remote box, no local focus stealing
```

## When to use / not use

- **Use** for a suite that boots a real GUI app locally (Electron via `_electron.launch`;
  any Playwright/WebdriverIO suite that opens a non-headless window). Also the right tool
  when local CI can't run the GUI suite and you want an on-demand remote runner.
- **Don't** use for already-headless browser tests (`playwright test` against headless
  Chromium runs fine locally/in CI) — there's nothing to offload.

## Prerequisites (check first, install/guide as needed)

1. **crabbox CLI** — `crabbox --version`. If missing, tell the user to install it (it's the
   orchestrator that leases the sandbox, rsyncs, and execs). The skill assumes crabbox is
   already available on the machine (it was, in the source project).
2. **E2B account + CLI** — `e2b --version`; auth via `e2b auth login`. E2B is brokerless,
   per-second billing, fast boot. The run reads the team key from `~/.e2b/config.json`
   (never passed as a CLI arg — see `run.sh`).
3. **A runnable E2E script** in the target repo (e.g. `test:e2e` → `playwright test`). You
   will wrap THIS command; find its exact form (check `package.json` and, if present, the
   CI workflow's E2E step — mirror that recipe so remote == CI).

## Setup steps

Copy the three bundled templates into the target repo and adapt them. All live under this
skill's `templates/` directory.

### 1. `crabbox/Dockerfile.e2e` — the remote image

Copy `templates/Dockerfile.e2e` to `<repo>/crabbox/Dockerfile.e2e`. It's `node:22-bookworm`
+ the FULL Electron/Chromium system libs (a fresh sandbox has none of the libs GitHub's
`ubuntu-latest` ships preinstalled) + Xvfb + build toolchain + **baked Electron rebuild
headers** so `electron-rebuild` runs offline.

**Adapt:**
- `ARG ELECTRON_VERSION=...` → match `electron@` in the repo's lockfile (headers are baked
  per-version; a mismatch falls back to a slow network fetch at run time).
- Node version / pnpm version (`corepack prepare pnpm@X`) → match the repo's
  `packageManager` field.
- If the app isn't Electron, drop the `electron-gyp` bake + GTK libs and keep only what the
  suite's browser/runtime needs (Xvfb + fonts stay).

### 2. `.crabbox.yaml` — provider + sync + the job

Copy `templates/crabbox.yaml` to `<repo>/.crabbox.yaml`. **Adapt:**
- `e2b.template:` → your template name (see step 4). Keep it consistent everywhere.
- `sync.exclude:` → never ship `node_modules` (reinstalled remotely), build output
  (`dist`/`out`), `.git`, caches, and any big sibling dirs (e.g. `.worktrees`). Keeping the
  wire small is the difference between a 3 MiB and a multi-GiB sync.
- `jobs.e2e.command:` → the install + run recipe. Mirror the repo's CI E2E step exactly.
  The template runs: enable corepack → seed baked Electron headers → `pnpm install
  --frozen-lockfile` → `xvfb-run --auto-servernum pnpm run test:e2e`. Set `env: { CI: "true" }`.

### 3. `crabbox/run.sh` — the wrapper

Copy `templates/run.sh` to `<repo>/crabbox/run.sh` (`chmod +x`). It loads the E2B team key
from `~/.e2b/config.json` (and any `crabbox/.env.local` overrides), then `exec crabbox "$@"`.
Reusable almost verbatim; no per-project changes usually needed.

### 4. `package.json` script

Add:
```json
"test:e2e:remote": "bash crabbox/run.sh job run e2e"
```

### 5. One-time E2B template build

```bash
e2b auth login
# ~4 vCPU / 4 GB — Electron + Chromium OOM at E2B's 512 MB default:
e2b template create <TEMPLATE_NAME> \
  -d crabbox/Dockerfile.e2e \
  --cpu-count 4 --memory-mb 4096 \
  -c "sleep infinity" \
  --ready-cmd "node --version"      # E2B requires BOTH a start and a ready command
```
`<TEMPLATE_NAME>` MUST match `e2b.template` in `.crabbox.yaml`. Then verify:
`bash crabbox/run.sh doctor`.

## Usage

```bash
pnpm test:e2e:remote                       # full suite, remote, no local focus stealing
crabbox job run -dry-run e2e               # preview the exact remote commands, no lease
```

**Filter to one spec** (fast iteration / avoid a flaky spec / prove one spec green on a
clean box): wire it once as an env passthrough instead of hand-editing the job. In
`.crabbox.yaml` add `E2E_SPEC_FILTER` to `env.allow`, and end the job command with
`... pnpm run test:e2e -- ${E2E_SPEC_FILTER:-}` (turbo/pnpm forward args after `--` to
`playwright test`; an empty filter preserves full-suite behavior). Then a target-only run
is a one-liner, no yaml churn:

```bash
E2E_SPEC_FILTER=e2e/pane-tree.spec.ts pnpm test:e2e:remote
```

Verified on E2B: the filtered run leases a clean box and runs just that spec.

**Get diagnostics from a remote run**: add `FANTASTIC_DEV_E2E_DEBUG: "1"` (or the repo's
equivalent debug env) to `jobs.e2e.env` so host/main/renderer console forwards into the run
log. Read per-spec results from the streamed output, not just the suite exit code.

## Gotchas (hard-won)

- **Read the per-spec result, not the suite exit code.** A single flaky spec (classically a
  dev-server-boot smoke test that starts BOTH a bundler dev server and Electron under load —
  "Failed to create browser context") can fail the whole run's exit code even when the spec
  you care about passed. Grep the streamed output for your spec's ✓/✘ line. A retry usually
  clears that flake; a persistent one is often `/dev/shm` pressure — bump the box.
- **Suite-tail poisoning ≠ a flaky spec — learn the signature.** Playwright runs specs
  alphabetically on the one shared box. If a spec leaks state on failure (a hung
  `app.close()`, a dev server or app process left bound to a socket/port/display), **every
  later spec fails at app-launch** (`firstWindow: Timeout` / first-selector waits), each
  retry included. The tell: a clean alphabetical boundary — everything before spec X passes
  in seconds, everything after X fails at launch, identically across runs. Widening launch
  timeouts does NOT help (the app never opens a window on the poisoned box). Diagnose by
  running a victim spec target-only via `E2E_SPEC_FILTER` (clean box): if it passes there,
  the spec is fine — hunt the leaking spec at the boundary and fix its teardown (kill
  everything it spawned even on its failure path; isolate its socket/DB/port per the suite's
  isolation conventions).
- **Daytona is a trap right now.** crabbox routes Daytona command exec through an SDK call
  with a hardcoded **60s** client deadline (no override) — any suite over ~1 min times out
  at `context deadline exceeded`. The template keeps a `daytona:` block for a clean revisit,
  but **E2B is the working provider**; don't burn time on Daytona.
- **Native modules rebuild remotely.** The remote `pnpm install` + `electron-rebuild`
  recompiles native deps (better-sqlite3, node-pty) for the Electron ABI on the box — that's
  why the Dockerfile bakes headers and installs `build-essential`/`python3`. Locally you may
  need to rebuild those back to the Node ABI for unit tests (dual-ABI dance).
- **Keep `ELECTRON_VERSION` in sync** with the lockfile on every Electron bump, or the
  offline header seed misses and the rebuild does a slow network fetch.
- **CI parity**: mirror the repo's CI E2E command in `jobs.e2e.command` so remote and CI
  stay identical; update both together.

## What each bundled file is

- `templates/Dockerfile.e2e` — the E2B (and Daytona) image: Node + Electron/Chromium libs +
  Xvfb + toolchain + baked Electron headers.
- `templates/crabbox.yaml` — provider (e2b active, daytona parked), sync excludes, the
  `e2e` job (install + `xvfb-run pnpm run test:e2e -- ${E2E_SPEC_FILTER:-}`).
- `templates/run.sh` — credential-loading wrapper around `crabbox`.
