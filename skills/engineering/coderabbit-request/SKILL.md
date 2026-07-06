---
name: coderabbit-request
description: Use after completing file changes - strongest for source code (AST-aware linting, security, tests), lighter support for markdown/config. Dispatches CodeRabbit reviewer subagent. ALWAYS request review before considering work complete.
metadata:
  version: "1.0.1"
---

# Requesting Review

## Overview

This skill dispatches a CodeRabbit reviewer subagent to analyze your uncommitted changes and return a structured list of issues. It's the first step in the change → review → triage → fix pipeline.

**When to use**: After making ANY file changes (code, skills, documentation, config), before considering work complete.

## CRITICAL: Always Request Review

After completing changes, invoke this skill:

- ✅ Code files (.ts, .vue, .js, etc.) - **strongest support** (AST-aware linting, security, auto-tests)
- ✅ Test files - **strongest support**
- ✅ Skill files (SKILL.md) - lighter support (markdownlint)
- ✅ Documentation (.md files) - lighter support (markdownlint)
- ✅ Configuration files - lighter support (generic config linting)

**Do NOT skip review** because "it's just documentation" or "it's a small change". Even lighter analysis catches issues.

**Outputs**: Structured JSON with categorized issues (Critical/Important/Minor).

## Process

### Step 1: Prepare Context

Stage all changes before review. The `--type uncommitted` flag analyzes both staged and unstaged changes, but staging ensures nothing is missed:

```bash
# Stage all changes
git add -A

# Verify staged changes
git diff --cached --stat
```

Document in your mind what was just implemented. This context helps the reviewer subagent understand scope.

### Step 2: Run CodeRabbit in the background

CodeRabbit reviews take **1-3 minutes**, so run the CLI as a background task rather than blocking on it. In Claude Code, dispatch it with a background Bash call (`run_in_background`); with any other harness, use whatever background-job mechanism you have (or just run it and wait).

```bash
# CodeRabbit CLI — review uncommitted changes, succinct output
coderabbit --prompt-only --type uncommitted
```

The `--prompt-only` flag makes output succinct and token-efficient. (Requires the [CodeRabbit CLI](https://www.coderabbit.ai/cli) to be installed and authenticated.)

### Step 3: Parse Results

When CodeRabbit completes, parse the output into this JSON structure:

```json
{
  "critical": [
    {"file": "...", "line": NNN, "issue": "...", "suggestion": "..."}
  ],
  "important": [...],
  "minor": [...]
}
```

Include only genuine issues CodeRabbit found. Do not invent.

Verify:
- All issues have `file`, `line`, `issue`, and `suggestion`
- Issues are correctly categorized by severity
- No invented issues
- CodeRabbit's exact wording preserved

### Step 4: Return Results

Return the structured issue list so it can feed your fix workflow — triage each finding (accept / reject / defer), then address the accepted ones (a failing test first where it applies).

## Example Output

```json
{
  "critical": [
    {
      "file": "src/webhooks.ts",
      "line": 42,
      "issue": "Missing HMAC signature verification for webhook authenticity",
      "suggestion": "Add HMAC-SHA256 signature verification using crypto module. Compare against timestamp to prevent replay attacks."
    }
  ],
  "important": [
    {
      "file": "src/webhooks.ts",
      "line": 89,
      "issue": "Race condition in concurrent webhook handling. Multiple async calls can update state simultaneously.",
      "suggestion": "Implement idempotency key handling. Store processed keys in cache with TTL to deduplicate retries."
    },
    {
      "file": "src/webhooks.ts",
      "line": 156,
      "issue": "Missing error logging for webhook failures. Makes debugging production issues difficult.",
      "suggestion": "Add structured logging with timestamp, error type, and webhook ID. Include full error stack."
    }
  ],
  "minor": []
}
```

## Key Principles

**Objectivity**: CodeRabbit is the source of truth. Don't filter or reinterpret findings.

**Completeness**: Return all issues CodeRabbit found, regardless of difficulty.

**Clarity**: Preserve CodeRabbit's exact issue descriptions and suggestions.

**Structure**: Always return JSON with three severity levels, even if some are empty arrays.

## Common Patterns

**When CodeRabbit finds nothing**: Return empty arrays for all severity levels.

```json
{
  "critical": [],
  "important": [],
  "minor": []
}
```

**When issues span multiple files**: Group by file but preserve line numbers.

**When suggestion is vague**: Include CodeRabbit's exact wording. Don't interpret or improve it.

## Constraints

- **DO**: Use `--prompt-only` flag for efficiency
- **DO**: Let CodeRabbit run to completion
- **DO**: Preserve exact issue descriptions from CodeRabbit output
- **DON'T**: Filter out any findings
- **DON'T**: Add your own issues
- **DON'T**: Modify or improve CodeRabbit's suggestions

## Integration Points

This skill produces the review; it's the first step of a review → triage → fix pipeline you drive with your normal workflow:

```
request review   → structured JSON of findings
        ↓
triage           → accept / reject / defer each finding
        ↓
fix              → address accepted findings (test-first where it applies)
```
