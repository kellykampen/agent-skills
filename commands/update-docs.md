---
description: Update README and documentation with changes since last commit
allowed-tools: |
  Bash(git:*)
  Read
  Edit
  MultiEdit
  Write
  LS
  Grep
  Glob
model: claude-sonnet-4-5-20250929
---

# Update Documentation Command

Analyze changes since the last git commit and update README.md and relevant documentation files in the `/docs/` directory to reflect new features, improvements, and architectural changes.

## What this command does

1. **Analyzes git changes** - Examines git diff and recent commits to identify what has changed
2. **Identifies documentation gaps** - Determines what new features or changes need documentation
3. **Updates README.md** with:
   - New features in the Key Features section
   - Updated environment variables in setup sections
   - New commands or scripts if added
4. **Updates relevant documentation** in `/docs/` directories:
   - Feature documentation for new capabilities
   - Technical documentation for architectural changes
   - API reference for new endpoints or functions
   - Guides for new setup requirements
5. **Updates CLAUDE.md** if there are new patterns or development practices

## Command Execution

The command will:

1. First run `git diff HEAD` to see current uncommitted changes
2. Check `git log --oneline -10` for recent commit messages to understand recent development
3. Analyze the codebase changes to categorize them into:
   - New features
   - Bug fixes and refactoring
   - UI/UX improvements
   - Configuration or environment changes
   - Database schema changes
4. Read current README.md and documentation files to understand existing structure
5. Make targeted updates to keep documentation current and accurate
6. Provide a summary of what was updated

## Usage:

```text
/update-docs
```

This command requires no arguments and will automatically detect and document changes since the last git commit.

## Example Output:

After running, you'll see updates to:

- README.md (if new features were added)
- docs/features/ (for new feature documentation)
- docs/technical/ (for architectural changes)
- CLAUDE.md (for new development patterns)

The command ensures your documentation stays synchronized with your codebase evolution.
