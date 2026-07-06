# Fleet Bootstrap — rebuild the <PROJECT> fleet from cold start

<!-- Template: the orchestrator fills every <PLACEHOLDER> and keeps the AS-BUILT snapshot
     current whenever the fleet shape changes. This file is what makes crash recovery a
     10-minute mechanical job instead of an archaeology dig. -->

## AS-BUILT snapshot (<DATE>, workspace "<WORKSPACE-NAME>") — rebuild to THIS
- Orchestrator pane: tabs `orch·sonnet5` (the lead's single contact) + `esc·fable5` (escalation, summoned on demand)
- QA station pane: tabs `qa·sonnet` + `regr·haiku` + `qa-browser` (browser surface → <DEV-URL>)
- Builder seats: cast per task — panes exist as empty chairs or get created on demand
  (`build-a·codex`, `build-b·kimi`, `build-c·glm`, …; tab renamed at each casting)
- Infra pane: `webserver` + `git`
<OTHER-STANDING-PANES>

For: cmux crash, computer restart, or first-time setup. The ORCHESTRATOR executes this — the
lead orchestrator only relaunches *you* and points here. cmux restores pane geometry itself after most
restarts; agents inside are dead — usually you only relaunch agents into existing panes
(Phase B) and fix tab titles. Only build panes (Phase A) that are missing.

## Tab naming convention (MANDATORY)

Every agent tab is named `role·agent-model` so a glance identifies seat + brain. Set the title
from INSIDE the pane before launching the agent:

```bash
printf '\033]0;qa·sonnet\007'
```

If the agent's TUI later overwrites it, re-run the printf or rename via the tab UI.

## Layout

```
<ASCII-LAYOUT — draw your workspace's pane arrangement here, like:
┌─────────────────────┬──────────────────┐
│ 1 ORCHESTRATOR      │ 2 builder seats  │
│   (+tab: esc·fable5)│   (cast per task)│
├─────────────────────┼──────────────────┤
│ 3 QA STATION        │ 4 (more seats)   │
│   qa·sonnet         │                  │
│   +regr·haiku       │                  │
│   +qa-browser       │                  │
├─────────────────────┴──────────────────┤
│ 5 INFRA: webserver | git   (full width)│
└─────────────────────────────────────────┘>
```

Phase A — create missing panes (from your own surface):
```bash
cmux new-split right --surface <orch-surface>     # adjust to your layout
cmux new-split down  --surface <orch-surface>
```

Phase B — per seat: set title → launch agent → wait ~12s → verify with capture-pane:

| Seat | Title | Launch |
|---|---|---|
| Orchestrator | `orch·sonnet5` | `claude --model sonnet --dangerously-skip-permissions`, first message: "You are the orchestrator — read .claude/orchestration/ORCHESTRATOR-PLAYBOOK.md" |
| Escalation (tab) | `esc·fable5` | summoned on demand, not at boot |
| QA | `qa·sonnet` | `claude --model sonnet --dangerously-skip-permissions`, first message: adopt QA role per playbook §2 — builders report commits to you; regression checklist on every commit + pre-merge; GO/NO-GO to orchestrator; read fleet-rules.md |
| QA browser (tab) | `qa-browser` | cmux browser surface → <DEV-URL> |
| Regression (tab) | `regr·haiku` | `claude --model haiku --dangerously-skip-permissions` — only once regression-checklist.md has lines to run |
| Builder seats | `build-*·<harness>` | cast per task: `codex` / `claudekimi --dangerously-skip-permissions` / `claudeglm --dangerously-skip-permissions` / `claude --model <m> --dangerously-skip-permissions` |
| Infra | `webserver` / `git` | `<DEV-SERVER-COMMAND>` (port <PORT>) / plain shell |

Phase C — wire the fleet:
1. Read ORCHESTRATOR-PLAYBOOK.md + ORCHESTRATION-HANDOFF.md (your wake ritual covers the rest).
2. Send QA its role brief + pointer to fleet-rules.md via `.claude/orchestration/cmux-send-verified.sh`.
3. Verify every send landed (the script does this) and capture each pane once.
4. Confirm the dev server is up: `curl -s -o /dev/null -w '%{http_code}' <DEV-URL>` → 200.

## Boot checklist (cold start)
1. `cmux identify --json` + `cmux list-panes` — map what survived; verify you can spawn panes
   (test-split + close; if rejected, you're detached — tell the lead, it runs the
   relaunch-in-cmux fix).
2. Compare against the layout above; create only what's missing; fix tab titles.
3. Relaunch dead agents (a restored pane holds a fresh shell, not the agent).
4. TaskList + `git log --oneline -10` + `git status` + handoff — restore work state.
5. Report fleet status to the lead in one message.
