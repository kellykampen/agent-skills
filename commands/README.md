# commands

Version-controlled Claude Code slash commands, symlinked into `~/.claude/commands`.

This directory is the home for custom `/command` prompts so they're backed up and shareable alongside the [skills](../skills/). Drop a `<name>.md` here (with the usual command frontmatter — `description`, `argument-hint`, `allowed-tools`, `model`) and it becomes available as `/<name>`.

Several commands that started life here have since graduated into full [skills](../skills/) (e.g. `interview`, `add-to-changelog`, `update-docs`) — a skill is the better home once a command grows real logic, modes, or supporting files.
