# add-to-changelog

Add a properly-formatted entry to CHANGELOG.md — Keep a Changelog + SemVer.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill add-to-changelog
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill add-to-changelog --agent claude-code
```

## What it does

A one-shot command: give it a version, a change type, and a message, and it adds a correctly-formatted entry to your project's `CHANGELOG.md`, creating the file if it doesn't exist yet.

## Why it exists

Changelogs rot the same way docs do — usually because updating one by hand means remembering the exact heading format, section order, and where today's version block goes. This skill removes the friction so there's no excuse to skip it.

## How it works

Parses `<version> <change_type> <message>`, finds or creates the right `## [version] - date` section, and slots the entry under the matching `### Added/Changed/Fixed/...` heading — keeping versions in reverse-chronological order.

## Requirements

Requires `git` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
