---
name: orchestration
description: >-
  Local redirect to this project's fleet orchestration rules. Use this skill whenever you are
  an agent working in the <PROJECT> repo as part of the cmux fleet — before starting any
  dispatched task, when you need the standing fleet rules (dev server, git/worktree rules,
  reporting flow), when sending a message to another pane, or when the user mentions the
  orchestrator, QA, seats, panes, surfaces, or fleet rules.
---

# <PROJECT> fleet orchestration — redirect

<!-- Template: install as .claude/skills/orchestration/SKILL.md in the project repo. The
     point of the shim: any worker spawned in this repo auto-discovers the rules from the
     skill list without the orchestrator re-briefing every seat, and project-specific gotchas
     have one durable home. -->

The canonical rules live in `.claude/orchestration/` at the repo root:

- **`fleet-rules.md`** — the standing rules every seat follows (READ FIRST, fully)
- **`ORCHESTRATOR-PLAYBOOK.md`** — the full playbook (only if you are the orchestrator)
- **`regression-checklist.md`** — QA's known-answer checks
- **`fleet-bootstrap.md`** — fleet layout + relaunch procedure (crash recovery)

Quick contract for a dispatched worker seat:
1. Read `fleet-rules.md` before touching anything.
2. Work only in the worktree named in your brief.
3. Report commits (sha + evidence) to the QA seat, not the orchestrator; send every
   inter-pane message via `.claude/orchestration/cmux-send-verified.sh <surface> "msg"`.
4. Your seat ends when QA passes your commit.

## Project-specific gotchas

<PROJECT-GOTCHAS — durable environment quirks workers keep rediscovering, e.g. broken CLI
subcommands, cache-corruption interactions, full binary paths. Keep each to one line.>
