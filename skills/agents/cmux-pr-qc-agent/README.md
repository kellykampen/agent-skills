# cmux-pr-qc-agent

An autonomous agent that shepherds a GitHub PR to mergeable, end to end.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill cmux-pr-qc-agent
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill cmux-pr-qc-agent --agent claude-code
```

## What it does

Spins up an independent, autonomous Claude Code instance in a separate cmux pane that owns a single GitHub PR until it's done — CI green, every review comment answered.

## Why it exists

Watching CI, re-running failed checks, and replying to review comments one by one is exactly the kind of loop that's better delegated than done by hand — especially once you've moved on to the next piece of work.

## How it works

Polls for new review comments and CI status, drives every check to green by *fixing* failures with tests (not just re-running them), addresses each review comment with a failing-test-first change, and replies to each comment individually with the fixing commit — looping until the PR is green and every thread is answered.

## Requirements

Requires `cmux`, `gh`, `git` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
