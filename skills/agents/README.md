# agents

Skills for running, delegating to, and coordinating other agents.

- **[agent-orchestrator](./agent-orchestrator/SKILL.md)** — Run a hierarchy of Claude Code orchestrators across cmux workspaces: a single lead orchestrator drives several per-project sub-orchestrators over the cmux control plane, relays the human's decisions, runs digest/watch loops, and enforces evidence-based QC.
- **[antigravity-cli](./antigravity-cli/SKILL.md)** — Drive Google's Antigravity CLI (`agy`) from the shell to hand coding, review, or bulk work to a *different* model harness than the one you're in (independent, non-Claude review; cheaper/faster grunt work).
- **[pr-qc-bot](./pr-qc-bot/SKILL.md)** — Spin up an independent, autonomous Claude Code instance in a separate cmux pane that shepherds a GitHub PR to mergeable: polls CI + review comments, drives every check green (fixing with tests), and replies to each thread until the PR is done.
