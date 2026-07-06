# cmux-agent-orchestrator

Run a hierarchy of Claude Code orchestrators across cmux workspaces.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill cmux-agent-orchestrator
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill cmux-agent-orchestrator --agent claude-code
```

## What it does

A single **lead orchestrator** that drives several per-project **sub-orchestrators** over the cmux control plane — reading their state, relaying your decisions down, and keeping the whole fleet aligned to one set of standing directives.

## Why it exists

Once you're running more than one or two agents on more than one project, keeping track of what each one is doing — and making sure they're all following the same quality bar — stops being something you can hold in your head. This skill turns that into a repeatable loop instead of ad hoc babysitting.

## How it works

The lead orchestrator discovers live sub-orchestrators via the cmux control plane (no hardcoded project list), runs a continuous-digest or overnight-autonomous watch loop, resets a sub-orchestrator's context when it gets low, spins up new cmux agents, onboards a new project into the fleet, rebuilds everything after a crash, and enforces evidence-based QC across the board.

## Requirements

Requires `cmux` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
