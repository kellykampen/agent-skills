# antigravity-cli

Delegate work to Google's Antigravity CLI (`agy`) — a different model harness entirely.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill antigravity-cli
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill antigravity-cli --agent claude-code
```

## What it does

Drives Google's Antigravity CLI (the `agy` command, successor to the Gemini CLI) from the shell so you can hand a task to a genuinely different model/harness than the one you're currently running in.

## Why it exists

Sometimes you want a review or a chunk of grunt work done by something that isn't Claude — a truly independent second opinion, or a cheaper/faster model for well-scoped bulk work. Bouncing between terminal tools by hand is friction; this skill makes `agy` a first-class delegate.

## How it works

Shells out to `agy` for coding, review, or bulk work; supports resuming an existing agy conversation; and composes cleanly with an orchestration/cmux workflow where `agy` is just another seat you can cast a task to.

## Requirements

Requires `agy` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
