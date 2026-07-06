# update-docs

Sync README, /docs, and CLAUDE.md/AGENTS.md with what actually changed.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill update-docs
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill update-docs --agent claude-code
```

## What it does

Looks at what changed since your last commit and updates the documentation that should reflect it — README, `/docs/`, and CLAUDE.md/AGENTS.md — without you having to remember everywhere docs might now be stale.

## Why it exists

Documentation drifts from code by default; someone has to notice and go fix it. Running this after a meaningful change makes 'the docs match the code' the default instead of an occasional cleanup pass.

## How it works

Diffs `HEAD`, checks recent commit messages for context, categorizes the change (feature, fix/refactor, UI, config, schema), reads the existing docs first to match their structure and voice, then makes only the targeted edits that change actually calls for.

## Requirements

Requires `git` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
