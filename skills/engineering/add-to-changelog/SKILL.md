---
name: add-to-changelog
description: Add a new entry to the project's CHANGELOG.md following the Keep a Changelog format and Semantic Versioning. Use when the user asks to "add a changelog entry", "update the changelog", "log this change", or runs /add-to-changelog with a version, change type, and message. Creates CHANGELOG.md if missing, adds the entry under the right version + change-type section, and keeps formatting consistent.
argument-hint: <version> <change_type> <message>
disable-model-invocation: true
compatibility: Requires git.
metadata:
  author: kellykampen
  version: "1.0.1"
  requires: "git"
---

# Add to Changelog

Add a new entry to the project's `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format and [Semantic Versioning](https://semver.org/).

## Arguments

- `<version>` — SemVer version (e.g. `1.1.0`, `2.0.0-beta.1`)
- `<change_type>` — one of: `added`, `changed`, `deprecated`, `removed`, `fixed`, `security`
- `<message>` — description of the change (quote multi-word messages)

If any argument is missing, infer sensible values from context (e.g. the current work) or ask the user.

## Process

1. Parse the version, change type, and message from the arguments.
2. Check if `CHANGELOG.md` exists in the project root. If not, create it with the standard Keep a Changelog header:
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   The format is based on [Keep a Changelog](https://keepachangelog.com/),
   and this project adheres to [Semantic Versioning](https://semver.org/).
   ```
3. Look for an existing `## [<version>]` section.
   - If it exists, add the entry under the appropriate `### <Change Type>` heading (create the heading if absent).
   - If it doesn't, create a new version section with today's date: `## [<version>] - YYYY-MM-DD` (get the date from `date +%F`), then the change-type heading and entry.
4. Keep versions in reverse-chronological order and entries tidy.
5. Write the file back.

## Change types

- **Added** — new features
- **Changed** — changes to existing functionality
- **Deprecated** — soon-to-be-removed features
- **Removed** — removed features
- **Fixed** — bug fixes
- **Security** — security fixes

## Example

`/add-to-changelog 1.1.0 added "Waitlist referral source configuration"` →

```markdown
## [1.1.0] - 2026-01-15

### Added

- Waitlist referral source configuration
```
