---
description: Add new entries to project CHANGELOG.md following Keep a Changelog format
argument-hint: <version> <change_type> <message>
allowed-tools: |
  Bash(git:*)
  Read
  Edit
  Write
  LS
model: sonnet
---

# Add to Changelog Command

Add a new entry to the project's CHANGELOG.md file following the [Keep a Changelog](https://keepachangelog.com/) format and [Semantic Versioning](https://semver.org/) standards.

## What this command does

1. **Parses arguments** - Extracts version, change type, and message from command arguments
2. **Manages CHANGELOG.md** - Creates the file if it doesn't exist with proper header structure
3. **Organizes entries** - Adds entries to appropriate version sections and change type categories
4. **Maintains format** - Ensures consistent formatting according to Keep a Changelog standards
5. **Version management** - Creates new version sections with timestamps when needed

## Command Execution

The command will:

1. Parse the provided arguments: version, change type, and message
2. Check if CHANGELOG.md exists in the project root
3. If the file doesn't exist, create one with standard Keep a Changelog header
4. Look for an existing section for the specified version
5. If version section exists, add the entry under the appropriate change type
6. If version section doesn't exist, create new version section with today's date
7. Format the entry according to Keep a Changelog conventions
8. Write the updated content back to the file

## Usage

```text
/add-to-changelog <version> <change_type> <message>
```

### Parameters

- `<version>` - Version number following semantic versioning (e.g., "1.1.0", "2.0.0-beta.1")
- `<change_type>` - One of: "added", "changed", "deprecated", "removed", "fixed", "security"
- `<message>` - Description of the change (use quotes for multi-word descriptions)

### Examples

```text
/add-to-changelog 1.1.0 added "New waitlist referral source configuration"
```

```text
/add-to-changelog 1.0.2 fixed "Bug in subscription billing proration logic"
```

```text
/add-to-changelog 2.0.0 changed "Migrated to new authentication system"
```

```text
/add-to-changelog 1.2.1 security "Updated dependencies to address vulnerabilities"
```

## Change Type Categories

- **Added** - New features and capabilities
- **Changed** - Changes to existing functionality
- **Deprecated** - Features that will be removed in future versions
- **Removed** - Features that have been removed
- **Fixed** - Bug fixes and corrections
- **Security** - Security-related changes and vulnerability fixes

## Example Output

After running the command, CHANGELOG.md will be updated with entries like:

```markdown
## [1.1.0] - 2024-08-25

### Added

- New waitlist referral source configuration

### Fixed

- Bug in subscription billing proration logic
```

The command maintains chronological order and proper markdown formatting for consistency and readability.
