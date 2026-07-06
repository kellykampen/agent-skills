# Changelog

All notable changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Individual skills carry their own `metadata.version` (semver `x.y.z`); this file
tracks the collection as a whole.

## [Unreleased]

## [0.1.0] - 2026-07-06

Initial collection of reusable Claude Code agent skills.

### Added

- **11 skills** across three categories:
  - `agents/` — `cmux-agent-orchestrator`, `antigravity-cli`, `cmux-pr-qc-agent`
  - `engineering/` — `coderabbit-request`, `convex-domain-folder`, `add-to-changelog`, `update-docs`
  - `workflow/` — `skill-maker`, `model-classifier`, `check-model-usage`, `interview`
- `interview` skill unifying three former slash commands (plan-file / `plans/` spec / Linear project + issues).
- `commands/` directory (symlinked to `~/.claude/commands`) so custom slash commands are version-controlled alongside skills.
- Root `README.md` skill index, MIT `LICENSE`, and a `.claude-plugin/plugin.json` manifest for `npx skills add kellykampen/agent-skills`.
- Metadata spec: every skill declares `metadata.author`, semver `metadata.version` (`x.y.z`), and — when it has external tool dependencies — `metadata.requires` plus a human-readable `compatibility:` line. `skill-maker`'s `quick_validate.py` enforces the `x.y.z` version format and type-checks `requires`.

### Changed

- Standardized all skill metadata to semver `x.y.z`, set `author` consistently, and added per-skill tool requirements (`cmux`, `agy`, `gh`, `git`, `convex`, `codexbar`, `gob`, `python3`).

### Removed

- Redundant per-category README files — the root `README.md` is the single source of truth for the skill index.

[Unreleased]: https://github.com/kellykampen/agent-skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kellykampen/agent-skills/releases/tag/v0.1.0
