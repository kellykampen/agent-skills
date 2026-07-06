# Onboarding a new project into the fleet

Run this when the operator adds a project. You (the lead) do the workspace-level setup and
verify; the new sub-orchestrator fills in everything project-specific. Templates live in this
skill's `templates/` directory.

## 1. Create the workspace + sub-orchestrator

```bash
cmux new-workspace --name "<ProjectName>" --command "claude" --focus false
```

Gotchas (see cmux-mechanics.md): `--command "claude"` may drop into a plain shell — if capture
shows a shell prompt, set the tab title (`printf '\033]0;orch·sonnet5\007'`) and launch
`claude --model sonnet --dangerously-skip-permissions` yourself; handle the trust-folder
prompt. The pane can be unreadable for 30-60 s while Claude cold-starts.

**Verify pane-spawn ancestry immediately** — have the new sub-orchestrator run
`cmux identify --json` + test-spawn a throwaway split and close it. A detached (out-of-tree)
sub-orchestrator can't hire seats and the failure is invisible until it tries (fix: the
relaunch-in-cmux procedure in cmux-mechanics.md).

## 2. Generate the repo's `.claude/orchestration/` files

Have the sub-orchestrator create `.claude/orchestration/` in its repo containing:

| File | Source | Who fills the blanks |
|---|---|---|
| `ORCHESTRATOR-PLAYBOOK.md` | verbatim copy of `references/directive-playbook.md` | nobody — identical fleet-wide |
| `ORCHESTRATION-HANDOFF.md` | starts near-empty | sub-orchestrator, continuously |
| `fleet-bootstrap.md` | `templates/fleet-bootstrap.template.md` | sub-orchestrator (layout, launch commands, ports) |
| `fleet-rules.md` | `templates/fleet-rules.template.md` | sub-orchestrator (dev server, package manager, verify steps, feature context) |
| `regression-checklist.md` | `templates/regression-checklist.template.md` | QA seat, grows over time |
| `cmux-send-verified.sh` | copy of `scripts/cmux-send-verified.sh` (`chmod +x`) | nobody |

Plus the **project-local skill shim**: `.claude/skills/orchestration/SKILL.md` from
`templates/skill-shim.template.md` — a thin redirect so any worker spawned in that repo
auto-discovers the orchestration rules + project gotchas without you re-briefing them.

Send the sub-orchestrator the template paths (full paths — skill-relative paths don't resolve in
its session) and the playbook, then **verify the files exist on disk yourself** (a capture of
`ls .claude/orchestration/`) before considering the project onboarded — sub-orchestrators
sometimes narrate file-writes without doing them.

## 3. First boot

Send the boot directive:

> You are the orchestrator for <Project> — read `.claude/orchestration/ORCHESTRATOR-PLAYBOOK.md`,
> then `fleet-rules.md`, then `ORCHESTRATION-HANDOFF.md`. Build your fleet per
> `fleet-bootstrap.md` (QA station first). Report fleet status when standing.

## 4. Register the project

Add it to your **fleet-roster memory note**: project name, repo path, cmux workspace name,
issue-tracker prefix, design oracle (comp URL + MCP if any), trunk branch, anything the operator
said about its goals. The roster lives in memory, not in the skill — projects come and go.

## Migrating an existing project (root-file layout → `.claude/orchestration/`)

Older projects keep `ORCHESTRATOR-PLAYBOOK.md`/`ORCHESTRATION-HANDOFF.md` at repo root. Honor
them where they are; at a quiet moment have the sub-orchestrator `git mv` them into
`.claude/orchestration/`, add the missing files from templates, and update any boot pointers.
Never migrate mid-task — a reset pointing at a moved-but-uncommitted path lobotomizes the
fresh session.
