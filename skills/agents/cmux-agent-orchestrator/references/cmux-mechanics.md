# cmux mechanics for driving sub-orchestrators

The cmux CLI controls other panes/sessions over a Unix socket. This is how you read and drive
the sub-orchestrators. Load the `cmux` skill for full topology commands; this file is the
lead-orchestrator-specific subset plus the gotchas learned the hard way.

## Finding the sub-orchestrators

```bash
CMUX_QUIET=1 cmux workspace list          # workspaces; sub-orchestrator ws named like the project
cmux list-pane-surfaces --workspace <ws>  # the sub-orchestrator surface (named like the project, ✳)
cmux identify --json                      # your own caller context
```

Surface/workspace refs **change between sessions** — re-resolve them at the start of every
session; never reuse a ref from a previous run.

## Reading a pane (receiving the sub-orchestrator's report)

```bash
cmux capture-pane --surface <s> --lines 12
```

- **Prefer `capture-pane` over `read-screen`.** In practice `read-screen` (and large captures)
  frequently time out or hang on busy/heavy panes, while `capture-pane` works. If a capture
  times out, **retry with fewer lines** (`--lines 6`). If it returns
  `internal_error: Failed to read terminal text`, the pane is mid-render/booting — wait a few
  seconds and retry; it's not necessarily stuck.
- Reading the pane **is** how the sub-orchestrator reports to you. That's within your lane —
  you're receiving a report, not reading the issue tracker or doing project work.
- To confirm cmux itself is alive when a surface hangs, run a global command like
  `cmux workspace list` — if that works, the problem is that one surface, not the daemon.

## Sending a directive — use the bundled verified-send script

```bash
<skill-dir>/scripts/cmux-send-verified.sh <surface> "<your directive text>"
```

The script sends, submits, and **capture-verifies the message actually left the input line**
(retrying Enter if it's stuck, and treating a "queued" marker as success). Raw
`cmux send` + `send-key Enter` silently leaves messages sitting unsubmitted often enough that
every inter-pane message — yours and the sub-orchestrators' — goes through the script. Give
sub-orchestrators the script's **full path** when you spin them up (copy it into their repo's
`.claude/orchestration/` or point at the skill copy).

- **Flush operator drafts first.** If the pane's input line already holds text (the operator
  typed a draft, or a queued instruction), sending appends onto it and mangles it. Use the
  script's `--flush` flag (ctrl+c the input line) **only when the pane is idle** — ctrl+c on a
  busy agent aborts its turn. Watch for the collision hazard whenever the operator is also
  typing into panes.
- Long directives are fine — cmux sends them as one block. Quotes/pipes in the text are just
  text to a Claude prompt (they only cause trouble in a raw shell — see spin-up).
- If the sub-orchestrator is busy, your message **queues** ("Press up to edit queued messages")
  and is processed when its current turn ends. That's expected.

## Answering a sub-orchestrator's interactive menu (AskUserQuestion inside it)

When a sub-orchestrator escalates a decision, its pane shows an interactive menu. Driving that
menu by blind arrow-key navigation is fragile (and multi-question forms are worse). **Instead:**

```bash
cmux send-key --surface <s> Escape   # dismiss the menu
cmux send --surface <s> "<the decision, as clear free-text, covering every sub-question>"
cmux send-key --surface <s> Enter
```

Free-text is unambiguous, lets you add nuance ("do X, and log the open Y question for the
operator"), and covers multi-part forms in one shot.

## Resetting a sub-orchestrator's context (the reliable procedure)

Sub-orchestrators **cannot `/clear` themselves** — that command only fires from outside. When
one hits a clean task boundary or climbs past ~50% context, **you** reset it:

1. **Ensure the reset-safety files are actually on disk first** — `ORCHESTRATOR-PLAYBOOK.md` +
   `ORCHESTRATION-HANDOFF.md` in the repo's `.claude/orchestration/` (older projects: repo
   root). Sub-orchestrators sometimes *narrate* writing them without doing it; verify
   (`ls`/`find`) or a `/clear` lobotomizes the fresh session.
2. **Send `/clear` at an IDLE prompt.** If the pane is busy, `/clear` queues as literal text and
   does nothing — wait for idle. Typing `/clear` can open the slash-command palette; if so,
   `send-key Escape` first, then send `/clear` + `Enter` together.
3. **It lags ~10–15 s.** The context readout won't drop immediately. Verify via `capture-pane`
   a few seconds later — ctx blanks/drops when it actually fired.
4. **Send a boot-pointer** to the fresh session: *"Read ORCHESTRATOR-PLAYBOOK.md then
   ORCHESTRATION-HANDOFF.md, then continue with <next task>."* A fresh session does nothing
   until prompted.
5. **Don't fight `/clear` when ctx is already low** (< ~40%) — just send a go-message; a reset
   isn't needed.
6. `ctrl+c` is the abort-key name (not `C-c`) if you need to clear a stuck input line.

Keep reset bash **lean** — stacked `sleep`s can blow the tool's ~40 s timeout mid-sequence
(the `/clear`+boot usually still lands, but verify).

## Tab titles (the `role·agent-model` convention)

Every agent tab is named `role·agent-model` (`orch·sonnet5`, `esc·fable5`, `qa·sonnet`,
`build-a·codex`) so a glance identifies seat + brain — this matters most at wake/triage time
when you're scanning panes. Set it from **inside** the pane before launching the agent:

```bash
printf '\033]0;orch·sonnet5\007'
```

If the agent's TUI later overwrites the title, re-run the printf or rename via the tab UI.
When relaunching agents after a crash, fixing tab titles is part of the job.

## Spinning up a fresh cmux agent (non-project tasks only)

```bash
cmux new-workspace --name "<name>" --command "claude" --focus false   # creates a workspace
```

Gotchas observed:
- `--command "claude"` sometimes drops you into a **plain shell** instead of launching Claude.
  If capture shows a shell prompt, launch it yourself: `cmux send --surface <s> "claude
  --dangerously-skip-permissions"` + `Enter`, then handle the **trust-folder** prompt
  (`send-key Enter` to select "Yes, I trust this folder"), then send the task brief.
- The new agent-session surface can be **unreadable** (`Failed to read terminal text`) for
  30–60 s while Claude cold-starts — wait, then `capture-pane` works.
- **Don't send a brief into a raw shell** — quotes/pipes/`?` in it trigger shell quote-continuation
  (`quote>`) or globbing. Only send the brief once Claude's TUI is up.
- Reactivating a **stood-down** sub-orchestrator: its pane shows a resume prompt — choose
  **"Resume from summary (recommended)"** (cheap, keeps continuity), let it compact, then send
  the task.

## A sub-orchestrator must be cmux-SPAWNED to spawn worker panes (ancestry gate)

cmux authorizes pane-spawn calls (`new-split`/`new-surface`) by the caller's **process
ancestry** — the daemon reads the caller's peer-PID and requires it to be inside cmux's process
tree. A Claude launched **by cmux** (a real pane/agent-session) is in-tree and can spawn panes; a
Claude started **out-of-tree** (e.g. a launchd-detached `~/.local/bin/claude` job) is NOT — its
surface still registers (so you can `capture-pane`/`send` to it), but every spawn call it makes
is rejected. A live process **cannot be re-parented** — no env var, `CMUX_SOCKET`, or flag fixes
it. This is invisible until the sub-orchestrator tries to hire its first pane worker.

**Diagnose, don't accept "I can't":** have the sub-orchestrator run `cmux identify --json` +
attempt `cmux new-split` and paste the exact error. If one sub-orchestrator spawns panes fine
(cmux-spawned) and another can't (detached), that asymmetry **is** the tell.

**Relaunch-in-cmux procedure** (the fix — an external in-tree actor must do it; the detached
sub-orchestrator can't relaunch itself). First confirm **you** (the lead) are in-tree: `cmux
identify --json` must resolve a caller surface, and a test `cmux new-split` must succeed. Then:
1. Tell the detached sub-orchestrator to **flush** `ORCHESTRATOR-PLAYBOOK.md` +
   `ORCHESTRATION-HANDOFF.md` to disk (all state — PRs, next steps, worker model) and **stand
   down** (no new work). Wait for its "STOOD DOWN".
2. Create a real pane in its workspace: `cmux new-split down --workspace <ws> --surface
   <orchestrator-surface>` (`--surface`/`--panel` takes a **surface** ref, not a pane ref — a
   pane ref returns `not_found: Surface not found`).
3. The fresh terminal may be lazy/unrendered (`Failed to read terminal text`) until touched —
   `send` the launch command to kick it: `cmux send --surface <new> "claude
   --dangerously-skip-permissions"` + `Enter`. Claude launched inside this cmux-spawned terminal
   is in-tree. Handle the trust prompt if it appears (often pre-trusted → straight to prompt).
4. Boot it: **verify pane-spawn first** (`cmux identify --json` + test-spawn a throwaway pane and
   `close-surface` it), then read playbook + handoff, then resume the roadmap.
5. Retire the old surface (`cmux close-surface --surface <old>`) once the new one has read the
   handoff and proven it can spawn. Track the **new** surface ref for that sub-orchestrator going
   forward.

## Delivering artifacts up to the operator

When a sub-orchestrator produces a screenshot/report file (e.g. `/tmp/<project>-app/*.png`), you
retrieve it and hand it to the operator with `SendUserFile` (render for images). Reading a
produced artifact to relay it is fine — it's the sub-orchestrator's output, not you doing
project work.
