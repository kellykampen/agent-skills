# coderabbit-request

Dispatch a CodeRabbit review of your uncommitted changes and get back a structured issue list.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill coderabbit-request
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill coderabbit-request --agent claude-code
```

## What it does

The first step of a change → review → triage → fix loop: run CodeRabbit against your uncommitted diff and return a clean, severity-categorized list of what it found.

## Why it exists

"It's just docs" or "it's a small change" is exactly when review gets skipped — and exactly when a lightweight pass still catches something. Making review a one-command habit closes that gap.

## How it works

Stages your changes, runs the `coderabbit` CLI in the background via `gob` (reviews take 1-3 minutes), and parses the output into `critical` / `important` / `minor` buckets with file, line, issue, and suggestion for each — CodeRabbit's exact wording preserved, nothing invented or filtered.

## Requirements

Requires `gob`, `coderabbit`, `git` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
