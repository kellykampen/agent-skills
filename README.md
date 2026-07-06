# agent-skills

A small, composable collection of [Claude Code](https://claude.com/claude-code) agent skills for real engineering work — orchestrating fleets of agents, reviewing code, shipping PRs, and building more skills.

Each skill is a self-contained folder with a `SKILL.md` (plus any supporting docs/scripts). They're designed to be **small, easy to adapt, and model-agnostic** — fork them, rename them, make them your own.

## Install

Install with the [`skills`](https://skills.sh) CLI:

```bash
npx skills@latest add kellykampen/agent-skills
```

Pick the skills you want and the agents to install them on. Or just browse the folders and copy what's useful.

## Skills

### `agents/` — running & delegating to other agents

| Skill | What it does |
| --- | --- |
| [agent-orchestrator](./skills/agents/agent-orchestrator/SKILL.md) | Run a hierarchy of Claude Code orchestrators across cmux workspaces — a lead that drives per-project sub-orchestrators, relays decisions, runs digest/watch loops, and enforces evidence-based QC. |
| [antigravity-cli](./skills/agents/antigravity-cli/SKILL.md) | Drive Google's Antigravity CLI (`agy`) from the shell to delegate coding, review, or bulk work to a *different* (non-Claude) model harness. |
| [pr-qc-bot](./skills/agents/pr-qc-bot/SKILL.md) | Spin up an autonomous Claude Code instance in a separate cmux pane that watches a GitHub PR end-to-end — drives CI to green, fixes review comments test-first, and replies per thread until it's mergeable. |

### `engineering/` — code & backend work

| Skill | What it does |
| --- | --- |
| [coderabbit-request](./skills/engineering/coderabbit-request/SKILL.md) | Request a [CodeRabbit](https://coderabbit.ai) review of your uncommitted changes and return a structured, severity-categorized issue list. |
| [convex-domain-folder](./skills/engineering/convex-domain-folder/SKILL.md) | Reorganize a [Convex](https://convex.dev) backend into per-domain folders (schema/queries/mutations/model per domain), handling the api-path and test-resolution changes that trip people up. |

### `workflow/` — the AI workflow itself

| Skill | What it does |
| --- | --- |
| [model-classifier](./skills/workflow/model-classifier/SKILL.md) | Classify a task into the single best model to run it on — scored on cost, intelligence, and taste — across a roster of current frontier and budget models. |
| [skill-maker](./skills/workflow/skill-maker/SKILL.md) | A toolkit for authoring and iterating on Claude Code skills: create, edit, improve, run evals, benchmark, and optimize a skill's description for reliable triggering. |
| [check-model-usage](./skills/workflow/check-model-usage/SKILL.md) | Check quota/usage and session + weekly pacing across your AI coding harnesses (Claude Code, Codex, Antigravity, GLM, Kimi) in one command, via the [CodexBar](https://github.com/steipete/CodexBar) CLI. |

## How skills work

Claude Code discovers skills by scanning `~/.claude/skills/**/SKILL.md`. Each `SKILL.md` has YAML frontmatter (`name`, `description`, `metadata.version`) and a body of instructions. A strong `description` is what lets the model reach for the right skill at the right time.

## License

[MIT](./LICENSE). Use them, fork them, make them yours.
