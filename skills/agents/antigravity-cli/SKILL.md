---
name: antigravity-cli
description: >-
  Drive Google's Antigravity CLI (the `agy` command — a Gemini/Antigravity terminal
  coding agent, successor to Gemini CLI) from the shell to delegate coding, review, and
  bulk work to a DIFFERENT model harness than the one you're running in. Use this whenever
  you want to hand a task to `agy`, run a cheaper/faster model for grunt work, get a
  genuinely independent (non-Claude) code review, resume an agy conversation, or wire agy
  into an orchestration/cmux workflow. Triggers on "agy", "antigravity", "run this with
  antigravity", "have Gemini/Antigravity review it", "delegate this to agy", "use a cheaper
  model for this", or any headless invocation of a terminal coding agent that isn't Claude.
  Do NOT trigger for the Gemini API/SDK, the old `gemini` CLI, Google Sign-in/OAuth, the Codex
  CLI, a Claude subagent/cmux pane, or the `antigravity` Python xkcd joke module.
metadata:
  version: "1.0"
---

# Antigravity CLI (`agy`)

`agy` is Google's terminal coding agent (Antigravity; the successor to Gemini CLI). It runs
Gemini, Claude, and open models behind one harness with tools for reading/editing files and
running commands. Binary lives at `~/.local/bin/agy`.

**Why you reach for it:** it is a *different harness* from the Claude session you're in. That
makes it valuable for two things you can't do well from inside Claude:

1. **Cost/speed arbitrage** — push mechanical or high-volume work onto a cheaper, faster model
   (Gemini 3.5 Flash) instead of spending premium tokens.
2. **Genuinely independent review** — a Gemini- or GPT-OSS-backed reviewer is a real second
   opinion, not the same model grading its own homework. This is the "different-harness QC"
   pattern: the author is Claude, the reviewer is Antigravity.

Before doing anything, confirm it's installed and current: `agy --version` (expect `1.0.x`).
If the command is missing, tell the user to install it — don't try to install it yourself.

## Defaults — start here

When you just need to hand work to agy and the user hasn't specified details, this is the
safe default shape. Adjust from here; don't reason it out from scratch each time.

```bash
cd <repo-or-worktree>                       # scope the workspace
agy -p "<goal + an explicit verification step>" \
  --model "Gemini 3.1 Pro (High)" \         # capable default; drop to Flash for grunt work
  --dangerously-skip-permissions \          # or --sandbox; a headless run hangs without one
  --print-timeout 20m                       # bump above the 5m default for anything non-trivial
```

Then pick deliberately: **model** by task difficulty (table below), **timeout** by expected
runtime, **permission flag** by how much you trust the workspace, and — for review/handoff —
tell agy in the prompt to **write its result to a file** you can poll.

## Gotchas that will bite you

- **A wrong `--model` string does not error — it silently runs the default model.** Copy strings
  verbatim from `agy models`. A typo means you paid for the wrong tier and never knew.
- **The default `--print-timeout` is 5m, and if it fires mid-run you lose all output.** Size it
  to the task; a real refactor or full-repo review needs 15–20m+.
- **Without `--dangerously-skip-permissions` or `--sandbox`, a `-p` run hangs** waiting for
  interactive tool approval that never comes.
- **"Independent" review on a Claude model isn't independent** if you (the caller) are Claude.
  Route QC to Gemini or GPT-OSS. See the harness-diversity rule below.
- **Some commands in blog posts don't exist** in the installed CLI (e.g. `agy run`, `agy inspect`,
  `-m`, `/context`, `config.toml`). Worse, **an unknown subcommand doesn't error — `agy` prints
  its usage banner and exits 0**, so a bogus `agy inspect` *looks* like it worked while doing
  nothing. Trust `agy --help` / `agy help` over anything you half-remember.

## The one command you'll use most

Headless, single-shot, prints the answer to stdout and exits:

```bash
agy -p "PROMPT" --model "MODEL" [--add-dir PATH ...] [--dangerously-skip-permissions]
```

- `-p` / `--print` / `--prompt` — run one prompt non-interactively. This is the mode for
  orchestration: output is clean stdout you can capture, pipe, or redirect to a file.
- Runs against the **current working directory** as its workspace. `cd` into the repo (or the
  right worktree) first, or add roots with `--add-dir` (repeatable).
- Default `--print-timeout` is **5m**. Long tasks (large refactors, full-repo review) need a
  bigger budget: `--print-timeout 20m`. If agy is still working when the timeout fires you
  lose the output, so size this to the task.
- Without `--dangerously-skip-permissions`, agy will block waiting for interactive approval of
  tool calls — which hangs a headless run. For autonomous delegation you almost always want
  either `--dangerously-skip-permissions` or `--sandbox` (see Permissions & safety).

Interactive variants (rarely what you want when *you* are the caller):
- `agy` — open the TUI in the current dir.
- `agy "PROMPT"` — open the TUI seeded with an initial prompt.
- `agy -i "PROMPT"` / `--prompt-interactive` — run an initial prompt, then stay interactive.

## Picking the model (cost-arbitrage — do this deliberately)

`agy` does **not** default to its strongest model — it uses whatever is in
`~/.gemini/antigravity-cli/settings.json` (often Flash). Always pass `--model` explicitly so
the run is reproducible and matched to the task. Get the exact strings from `agy models` and
copy them **verbatim, including the parenthetical reasoning level** — the string is the model's
display name, e.g. `"Gemini 3.1 Pro (High)"`.

⚠️ **Silent fallback gotcha:** an unrecognized `--model` string does **not** error — agy
quietly falls back to the default model and runs anyway. A typo means you paid for the wrong
model without knowing. Copy from `agy models`; don't hand-type.

Available models (verify with `agy models`, they change):

| Model string | Reach for it when |
| --- | --- |
| `Gemini 3.5 Flash (Low)` | Trivial, deterministic, high-volume: renames, formatting, one-line lookups, "grep-and-summarize". Cheapest/fastest. |
| `Gemini 3.5 Flash (Medium)` / `(High)` | Everyday mechanical edits and straightforward coding where you want it done cheaply but not carelessly. |
| `Gemini 3.1 Pro (Low)` | Solid reasoning on a budget — moderate refactors, multi-file edits with clear scope. |
| `Gemini 3.1 Pro (High)` | The default workhorse for real coding and hard reasoning on the Gemini side. Standard-to-hard tasks. |
| `Claude Sonnet 4.6 (Thinking)` | Strong general coding via a non-Gemini harness. |
| `Claude Opus 4.6 (Thinking)` | The hardest tasks where you want maximum capability. |
| `GPT-OSS 120B (Medium)` | A third, open-model harness — useful as a tie-breaker or an independent voice distinct from both Gemini and Claude. |

**Routing heuristic:** match model cost to task difficulty. Flash for grunt work, Gemini 3.1
Pro (High) as the default for genuine coding, Claude/GPT-OSS when the *harness diversity itself*
is the point.

**Harness-diversity rule for independent review:** if you (the caller) are Claude, a review is
only independent if it runs on a *non-Claude* model. Route QC/second-opinion work to
`Gemini 3.1 Pro (High)` or `GPT-OSS 120B (Medium)` — not to `Claude Opus 4.6`, which would just
be Claude reviewing Claude in a thin disguise.

## Two workflows that carry their weight

### 1. Delegate a coding task
```bash
cd /path/to/repo   # or the specific worktree
agy -p "Convert the callback-based handlers in @internal/api to context.Context. \
Run the tests when done and report what changed." \
  --model "Gemini 3.1 Pro (High)" \
  --dangerously-skip-permissions \
  --print-timeout 15m
```
Give agy a *goal plus a verification step* ("run the tests", "make it typecheck"), not a
keystroke script — it's an agent, so let it plan and self-check. Reference files with `@path`
(e.g. `@src/main.go`, `@src/`, `@**/*.ts`) instead of pasting contents.

### 2. Independent, different-harness code review
The high-value pattern for the separate-model-review doctrine. Point agy at a diff, tell it to
post its verdict where you can collect it:
```bash
cd /path/to/worktree
agy -p "You are an independent code reviewer (Gemini/Antigravity — a DIFFERENT harness \
from the Claude author). Review this branch vs origin/develop: run 'git fetch origin' then \
'git diff origin/develop...HEAD'. Assess correctness, missed edge cases, and any invented \
scope. Post your review with 'gh pr comment <N> --body ...' starting with the marker \
<!-- review-gemini -->, then write your VERDICT (SHIP / APPROVE_WITH_NITS / REQUEST_CHANGES) \
to /tmp/review-DONE.md. Do NOT merge." \
  --model "Gemini 3.1 Pro (High)" \
  --dangerously-skip-permissions \
  --print-timeout 15m
```
Because the reviewer writes its verdict to a known file / PR comment, the orchestrator can
poll for completion and read the result without parsing agy's stdout.

## Continuing a conversation

agy persists each session as a SQLite DB under `~/.gemini/antigravity-cli/conversations/<UUID>.db`;
the UUID is the conversation ID.

- `agy -c "follow-up"` / `--continue` — continue the **most recent** conversation.
- `agy --conversation <UUID> "follow-up"` — resume a **specific** one by ID.

For orchestration prefer **fresh, self-contained one-shot prompts** over resuming — each `-p`
run is stateless and reproducible, which is what you want when you're the caller. Reach for
`--continue` only when a task genuinely needs the prior turn's context and re-establishing it
in the prompt would be costly.

## Permissions & safety

Headless runs need a permission strategy or they hang on the first tool approval:

- `--dangerously-skip-permissions` — auto-approve every tool call. Fast and autonomous, but the
  agent can run arbitrary commands and edit anything in the workspace. Use it for trusted repos
  / disposable worktrees, and scope the workspace (`cd` + `--add-dir`) so it can't wander.
- `--sandbox` — run with terminal restrictions (an isolation boundary). Safer for untrusted or
  exploratory work; pair with the `proceed-in-sandbox` permission behavior so it proceeds
  without prompts *inside* the sandbox.

Prefer the least dangerous option that still lets the run complete unattended. When you hand a
destructive-capable flag to agy, say so in your summary to the user.

## Capturing output for orchestration

- Redirect for later inspection: `agy -p "..." --model "..." > /tmp/agy-out.txt 2>&1`.
- For a machine-readable handoff, instruct agy in the prompt to **write its result to a
  specific file** (e.g. a verdict file or a patch) rather than relying on stdout scraping — the
  review workflow above does exactly this, and it's the robust pattern for a poller.
- `--log-file PATH` overrides where agy writes its own debug log (separate from the answer).

## Deeper reference

Slash commands, interactive session management (`/resume`, `/rewind`, `/fork`, `/model`,
`/planning`), `AGENTS.md` project context, plugins (`agy plugin ...`, incl. importing Gemini/
Claude plugins), MCP configuration, and settings files are documented in
`references/reference.md`. Read it when a task goes beyond headless one-shots — e.g. setting up
per-repo `AGENTS.md` context, wiring an MCP server, or working inside the TUI.
