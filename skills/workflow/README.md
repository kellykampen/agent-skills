# workflow

Meta-skills about the AI development workflow itself.

- **[model-classifier](./model-classifier/SKILL.md)** — Classify any task into the single best underlying model to run it on, scored on cost, intelligence, and taste across a roster of current frontier and budget models. Returns a model, not a harness — consult it before delegating work or picking a model for implement/review/design.
- **[skill-maker](./skill-maker/SKILL.md)** — A toolkit for authoring and iterating on Claude Code skills end to end: create, edit, and improve skills; run evals; benchmark performance with baseline comparison; and optimize a skill's description for reliable triggering. Enforces versioning on every skill it touches.
- **[check-model-usage](./check-model-usage/SKILL.md)** — Check quota/usage and session + weekly pacing across your AI coding harnesses (Claude Code, Codex, Antigravity, GLM/Z.ai, Kimi) in one command, via the [CodexBar](https://github.com/steipete/CodexBar) CLI. Answers "how much quota is left / am I going to run out before the reset / how's my burn rate."
- **[interview](./interview/SKILL.md)** — Interview you in depth (via the AskUserQuestion tool) to turn a rough idea, plan file, or feature request into a concrete spec — then capture it as a written spec (in place or in `plans/`) or as a Linear project + issues. _(user-invoked)_
