# check-model-usage

One command to check quota and pacing across every AI coding harness you use.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill check-model-usage
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill check-model-usage --agent claude-code
```

## What it does

A consolidated usage report — current quota plus session (5h) and weekly pacing — across Claude Code, Codex CLI, Antigravity, GLM/Z.ai, and Kimi/Moonshot, in one command.

## Why it exists

Running out of quota mid-task, or discovering you've been burning a weekly cap too fast to last until reset, is avoidable — but only if you actually check. This makes checking cheap enough to do proactively instead of after the fact.

## How it works

Wraps the [CodexBar](https://github.com/steipete/CodexBar) CLI — the only data source; no TUI probing, no direct provider API calls, no writes to your codexbar config. Fetches each harness's usage in parallel and computes a pace line (`% in reserve/deficit`, expected vs. actual, time to reset) and a burn-rate line so you know how hard to throttle.

## Requirements

Requires `codexbar` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
