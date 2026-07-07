---
name: peek
description: >-
  Use whenever you are an agent inside a multi-agent orchestration fleet (the conductor, a
  project-orchestrator, or a worker/builder seat) and need to report your own status so the
  level above you can see it, or need to check what your own children are doing right now.
  Trigger on: starting a new task, getting blocked, finishing a task, being asked "what's your
  fleet doing", wanting a live view of workers/orchestrators instead of capturing panes, or
  onboarding a new agent into the `PEEK_ID`/`PEEK_ROLE`/`PEEK_PARENT`/`PEEK_WORKSPACE` env
  contract. This is the fix for orchestrators losing track of fleet state in chat and having to
  capture-pane every worker to know if it's alive.
compatibility: Requires the `peek` CLI on PATH (build from ~/code/peek with `bun build --compile`,
  or a brew install once packaged) and the PEEK_* env vars set at spawn time.
metadata:
  author: kellykampen
  version: "1.0.0"
  requires: "peek CLI (github.com/kellykampen/peek, local repo ~/code/peek)"
---

# peek (fleet status reporting)

`peek` is a tiny, local, serverless CLI that makes an agent-orchestration fleet **legible**: each
agent reports its own status via `peek update`, which peek stores in a per-agent JSON file
behind the scenes; anyone above it in the hierarchy can read the tree instantly (via `peek`)
instead of capturing panes to guess what's alive. No server, no daemon — just files under
`~/.peek/projects/<project-slug>/`, which you never touch directly (see below).

## The CLI is the only contract — never touch `~/.peek/` yourself

`~/.peek/` is peek's **private internal storage**, not something you read, write, or inspect
directly. **Always** go through the CLI: `peek update`, `peek`, `peek --all`, `peek watch`,
`peek web`. **Never** `cat`/`echo`/hand-edit a file under `~/.peek/`, and never glob it yourself
to "check" something — if you need to know the current state, run `peek`/`peek --json`, not a
filesystem read. This keeps the on-disk schema free to change without breaking every agent that
depends on it, keeps every write atomic/valid (the CLI validates; a hand-written JSON file
might not), and means you never have to know or care what the record shape actually is.

## Are you set up to use it?

**Setup is plain env exports, set once per session — there is no `peek register` command.**
You export your identity a single time (at spawn, or once at session start if you're the
conductor); every `peek update` call after that is bare (just `--task`/`--status`/etc, never
re-exporting anything). **Reading needs no identity at all** — `peek`, `peek --all`, and
`peek web` all work with zero `PEEK_*` env vars set, for anyone just looking. Only *writing*
(`peek update`) requires your identity to already be exported.

You need four env vars, normally set by whatever spawned you (a launcher script, an
orchestrator's cast command, or your own boot sequence if you're the fleet's `conductor`):

| Var | What it is |
|---|---|
| `PEEK_ID` | Your own unique identifier |
| `PEEK_ROLE` | `conductor`, `orchestrator`, or `worker` |
| `PEEK_PARENT` | Your parent's `PEEK_ID` (omit only if you're `conductor`) |
| `PEEK_WORKSPACE` | Your project's computed slug (omit only if you're `conductor` — see below) |

The tree is built strictly from these **stored `PEEK_PARENT` links** — never from position,
spawn order, or directory structure — so get your own parent right at registration time.

If these aren't set and you're not `conductor`, `peek update` will hard-error rather than write
a silently-wrong record — that's intentional. Ask whoever cast you to set them, or if you're
bootstrapping a fresh fleet yourself, compute `PEEK_WORKSPACE` as your project root's absolute
path with every `/` replaced by `-` (same scheme as `~/.claude/projects/<slug>`), normalized to
the **main** checkout if you're in a git worktree — never a worktree's own path.

**Special case — you're the `conductor`:** your whole setup is one line, once:
```
export PEEK_ROLE=conductor PEEK_ID=conductor
```
Registration is **cwd-agnostic** — your own directory is irrelevant, `PEEK_ROLE=conductor` alone
routes your record into the reserved `~/.peek/projects/_conductor/<PEEK_ID>.json` slot, no
`PEEK_PARENT`/`PEEK_WORKSPACE` needed. Every `peek update` after that one export is bare.

## When to `peek update`

Call it at these three moments, not continuously — `peek` has no lifecycle hooks in v1, so if
you don't call it, your record goes stale and eventually looks crashed to whoever's watching:

1. **On task start** — the moment you pick up a ticket/task, before doing any real work:
   ```
   peek update --task "implementing PEK-6: --json output on peek" --status working
   ```
2. **On block** — the moment you're stuck waiting on something (a decision, another seat, a
   quota reset):
   ```
   peek update --task "same as above" --status blocked --note "waiting on CEO: --all scope decision"
   ```
   Go back to `--status working` the moment you're unblocked and resume — don't leave a stale
   `blocked` record sitting once you're moving again.
3. **On done** — the moment your work is actually complete (committed, gates passed — not just
   "code written"):
   ```
   peek update --task "implementing PEK-6" --status done --ticket PEK-6
   ```
   A `done` record is still visible (briefly) before `peek prune` clears it — this is what lets
   the level above you see completion without you having to send a separate chat message.

`--ticket` and `--note` are optional; omitting them on a later call clears any previously-set
value (each `peek update` fully overwrites your record, it doesn't patch it).

## When to check on your own children

If you have workers or sub-orchestrators reporting to you (your `PEEK_ID` shows up as their
`PEEK_PARENT`), don't rely on capturing their panes to know what they're doing:

- **`peek`** — one-shot: your project's tree (or the whole fleet if you're `conductor` with no
  `PEEK_WORKSPACE`), each agent's task/status and a relative "Xm ago", with a dim/gray ⚠ on
  anything stale past ~10 minutes. Run this before deciding whether a seat needs a nudge.
- **`peek watch`** — same view, live-refreshing (~3s) until Ctrl-C. Use this instead of
  re-running `peek` in a loop yourself when you're actively monitoring a cast in progress.
- **`peek --all`** — force the full cross-project view regardless of your own `PEEK_WORKSPACE`
  scope (usable by any role, not just `conductor` — see PLAN.md's clarification on why a
  conductor-only restriction would be pointless).
- **`peek --json`** — same data as a flat JSON array (each record plus a computed `stale`
  boolean) if you need to consume it programmatically rather than read it.
- A stale (⚠) entry that hasn't moved to `done` is your signal to actually check that seat —
  capture its pane, ask it a direct question, or treat it as crashed and re-cast the work.

## What NOT to do

- Don't call `peek update` on every tool call or thought — three moments (start/block/done) is
  the contract. Spamming updates defeats the "at a glance" design and adds noise no one reads.
- Don't skip reporting because "the task is quick" — a worker that starts and finishes in two
  minutes without ever calling `peek update` is invisible the whole time; call it at start even
  for small tasks.
- Don't use `peek` as a substitute for the actual reporting flow in your fleet's playbook (e.g.
  builders still report commits to QA with sha + evidence) — `peek` is a status *radar*, not a
  replacement for the evidence-bearing handoffs a fleet's QC gates require.
