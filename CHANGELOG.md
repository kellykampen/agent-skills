# Changelog

All notable changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Individual skills carry their own `metadata.version` (semver `x.y.z`); this file
tracks the collection as a whole.

## [Unreleased]

### Changed

- **`issue-breakdown`** → 1.3.0 and **`interview`** → 1.1.0 (`workflow/`): both now require wiring **project-level (project↔project) dependencies** when creating a Linear epic, not just issue-level `blocks` links. Added the exact mechanic to `issue-breakdown/references/linear-cli.md`: project relations are created via raw GraphQL `projectRelationCreate` (`linear-cli api mutate`) — the Linear MCP and `linear-cli rel` don't do them — with the load-bearing **finish-to-start** anchor orientation (prerequisite `end` → dependent `start`); the reverse order silently fails to render in the Dependencies column. The `/interview-linear` command carries the same instruction.

## [0.7.0] - 2026-07-07

### Added

- **`remotion-explainer-video`** skill (`workflow/`) — turns a skill, feature, or product into a short explainer video (MP4 + GIF) with a real royalty-free soundtrack sourced live from Pixabay Music, in the same dark editorial-diagram visual system used across this collection's own videos. 13 skills total.

### Fixed

- `skill-maker`'s trigger-eval harness (`run_eval.py`) tested an unreliable proxy file instead of the real skill, which silently undercounted every true trigger whenever the skill already existed on disk (i.e. essentially always, since `skill-maker`'s own documented flow creates the skill before optimizing its description). Now swaps the real skill's description in place for the duration of a batch, with a backup and signal-safe restore, and tests the actual triggering mechanism directly. `skill-maker` bumped to 2.5.0.
- `skill-maker`'s description-optimization report (`generate_report.py`) was a wide table with one column per query and full description text repeated in every row — hard to read once there were more than a few queries. Redesigned: queries are now rows, iterations are columns, and each iteration's description appears once in a collapsible list above the table.

## [0.6.0] - 2026-07-06

### Added

- Explainer GIF/video for every skill (11 more, alongside `cmux-agent-orchestrator`'s from 0.4.0): `cmux-pr-qc-agent`, `skill-maker`, `convex-domain-folder`, `antigravity-cli`, `model-classifier`, `add-to-changelog`, `update-docs`, `check-model-usage`, `interview`, `issue-breakdown`, `coderabbit-request` — each linked from its README entry. A real screenshot of `skill-maker`'s eval-viewer tool (old-vs-new output + pass/fail benchmark table) is embedded in its section.
- README banner image (`media/banner.png`) and two Mermaid flowcharts illustrating `cmux-agent-orchestrator`'s dispatch tree and `cmux-pr-qc-agent`'s watch loop.
- Release and license badges on the root README.

### Changed

- Root README's project description expanded to mention the per-skill demo GIFs.

## [0.5.0] - 2026-07-06

### Changed

- New **`harness/`** category — for skills that drive a different AI coding harness entirely, not Claude Code. Moved `antigravity-cli` there from `agents/` (it never fit "running & delegating to other agents" alongside the cmux-based skills, which stay within the Claude Code process).

## [0.4.0] - 2026-07-06

### Added

- `media/cmux-agent-orchestrator-explainer.mp4` — a short explainer video for `cmux-agent-orchestrator` (dark editorial-diagram style: node/arrow hierarchy, model-brand-colored workers, running status captions), linked from its README entry in `skills/agents/README.md`. Built with [Remotion](https://remotion.dev) in the companion `agent-skills-remotion` repo.

## [0.3.0] - 2026-07-06

### Added

- **`issue-breakdown`** skill (`workflow/`) — break a feature into a Linear epic + small, review-ready issues (user stories, acceptance criteria, Fibonacci ≤3, dependency links). 12 skills total.

### Changed

- **README structure reverted to per-category** (`skills/<category>/README.md`), not per-skill. Each category README now holds one `##` section per skill — tagline, one-off install command, try-without-installing, what/why/how, requirements — instead of a separate `README.md` in every skill folder. The top-level README links to `skills/<category>/README.md#<skill-name>` for each skill.
- `skill-maker` documents the corrected per-category convention and bumps to 2.4.1.

## [0.2.0] - 2026-07-06

### Added

- Per-skill `README.md` for all 11 skills — a human-facing landing page (tagline, one-off install command via `npx skills add kellykampen/agent-skills --skill <name>`, "try without installing" via `npx skills use`, what/why/how, requirements) alongside each `SKILL.md`.
- `skill-maker` now documents this per-skill README convention for any skill published in a shared collection.

### Changed

- Repo made **public**.
- Root `README.md` table links now point to each skill's `README.md` instead of straight to `SKILL.md`, and calls out the one-off `--skill` install flag.

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

[Unreleased]: https://github.com/kellykampen/agent-skills/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/kellykampen/agent-skills/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/kellykampen/agent-skills/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/kellykampen/agent-skills/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/kellykampen/agent-skills/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/kellykampen/agent-skills/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kellykampen/agent-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kellykampen/agent-skills/releases/tag/v0.1.0
