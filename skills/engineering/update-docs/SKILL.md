---
name: update-docs
description: Analyze changes since the last git commit and update README.md, docs in /docs/, and CLAUDE.md/AGENTS.md to reflect new features, config, commands, and architectural changes. Use when the user asks to "update the docs", "sync the README", "document what changed", or runs /update-docs. No arguments — it detects changes automatically.
disable-model-invocation: true
metadata:
  author: anonymous
  version: "1.0.0"
  requires: "git"
---

# Update Documentation

Keep docs synchronized with the code by analyzing changes since the last commit and updating the relevant documentation.

## Process

1. **See what changed**
   - `git diff HEAD` — current uncommitted changes.
   - `git log --oneline -10` — recent commits for context.
2. **Categorize** the changes: new features, bug fixes/refactors, UI/UX, config/env, schema/API.
3. **Read the existing docs** first (README.md, `docs/**`, CLAUDE.md/AGENTS.md) to match their structure and voice before editing — don't impose a new format.
4. **Make targeted updates**:
   - `README.md` — new features (features section), new env vars (setup), new commands/scripts.
   - `docs/` — feature docs for new capabilities, technical docs for architectural changes, API reference for new endpoints/functions, setup guides for new requirements.
   - `CLAUDE.md` / `AGENTS.md` — new patterns or development practices worth codifying.
5. **Summarize** what you updated.

## Principles

- Only document what actually changed — don't rewrite untouched sections.
- Prefer editing existing sections over adding new top-level ones.
- Match the project's existing tone, heading style, and formatting.
- If nothing meaningful changed for docs, say so rather than inventing updates.
