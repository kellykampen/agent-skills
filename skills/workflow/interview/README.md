# interview

A deep, iterative interview (via AskUserQuestion) that turns an idea into a real spec.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill interview
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill interview --agent claude-code
```

## What it does

Interviews you thoroughly about a plan, feature, or rough idea — technical implementation, UI/UX, edge cases, tradeoffs, the works — then writes the result down one of three ways: back into a plan file, into `plans/<name>.md`, or as a Linear project + issues.

## Why it exists

The gap between what's in your head and what's actually written down is where most misalignment starts. A single round of clarifying questions rarely closes it; this skill keeps going until it actually does.

## How it works

Every question goes through AskUserQuestion — never a wall of prose — batched and grounded in the current codebase when there is one. It keeps interviewing round after round, on purpose, until the picture is genuinely complete, then persists it in whichever of the three modes fits what you asked for.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
