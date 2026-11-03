---
name: evidence-driven-testing
description: >
  Records visual proof while testing UI behavior — screen recording with structured
  test/assertion annotations — then posts the video and a results summary to the PR
  and tracker issue. Use whenever a UI change needs verifiable evidence that it works,
  instead of prose claims.
compatibility: Requires a GUI environment with screen recording, an authenticated browser session for the app under test, and gh (GitHub CLI) or equivalent for posting evidence.
metadata:
  version: "1.0"
---

# Evidence-Driven Testing

Record annotated screen-recording proof of UI behavior, then attach it to the PR and tracker issue.

## Inputs

- **Test targets** (required): The behaviors/flows to verify, phrased as testable statements.
- **PR / issue** (optional): Where to post the evidence. If omitted, deliver to the requester only.

## Instructions

### 1. Prepare the screen

- Maximize the browser/app window; close popups, notifications, and extra panels.
- Navigate to the starting state (logged in, correct page) BEFORE recording, unless setup itself is under test.

### 2. Start recording

- Begin the screen recording before the first meaningful action.
- Add a `setup` annotation describing the starting context, e.g. "Logged in, navigating to connectors page".

### 3. Annotate as you test

- At each named test's start, add a `test_start` annotation in Jest style: `It should execute the tool directly when permission is 'always'`.
- After each check, add an `assertion` annotation with result `passed`, `failed`, or `untested`.
- Rules for assertions:
  - One assertion per meaningful state change — consolidate, don't annotate per UI label.
  - Use "Precondition: ..." assertions to establish starting state.
  - Keep under ~80 characters, high-signal.
  - If a test cannot run (missing prerequisite, expired auth window), mark it `untested` with the reason — never skip silently.

### 4. Stop and review

- Stop recording after the final assertion.
- Confirm the recording captured the key moments before sharing.

### 5. Post the evidence

- Write a short report: what was tested, environment + exact commit, pass/fail per test, caveats.
- Post the video + summary as a PR comment (embed in the PR description if it's your PR).
- Attach the same video to the tracker issue (Linear/Jira) with a one-line result.
- Send the report + recording to the requester.

### Native GitHub attachment upload

Before uploading, check the installed CLI with `gh pr comment --help` and
`gh issue comment --help`. When the relevant command supports `--attach`, prefer
it over asking the user to sign into a browser. If support is absent or upload
fails, report the specific limitation and use an available authorized fallback.
Keep existing authentication and action-authorization rules.

Use this workflow only for real evidence on the intended PR or issue, never a
throwaway live comment to test CLI support. Review media for secrets and private
data, and preserve the target repository's access boundaries. Do not move private
evidence to a public repository or host to work around an access failure.

For an authorized PR evidence comment, write the report to a body file and upload:

```bash
gh pr comment "$PR_URL" --body-file /tmp/evidence/comment.md \
  --attach '/tmp/evidence/screenshot.png#Verified affected flow' \
  --attach /tmp/evidence/flow.mp4
```

Use `gh issue comment "$ISSUE_URL"` for a GitHub issue. Repeat `--attach` for up
to 50 files. Image alt text follows `path#alt-text`; videos have no alt text.
Local references such as `![Verified affected flow](./screenshot.png)` in the
body are rewritten to uploaded URLs. Body-file paths resolve relative to that
file's directory, falling back to the working directory. Unreferenced attachments
are appended, and existing body references retain their alt text.

Read back the exact resulting comment using its returned URL or comment ID, for
example `gh api "repos/OWNER/REPO/issues/comments/COMMENT_ID" --jq .body`. Obtain
the actual native GitHub upload URLs from that body; never fabricate asset URLs
or substitute the comment permalink for a media URL.

A comment upload alone does not satisfy a repository's PR-description evidence
rule. Read the current PR body, preserve its other content, and put the returned
URLs in its `Evidence` section with `gh pr edit "$PR_URL" --body-file BODY_FILE`.
For UI changes, LaunchHunt requires `UI changes: Yes` plus `Screenshot: ![description](URL)` and/or
`Video: URL`, using actual `https://github.com/user-attachments/assets/...` URLs.
Read back the PR body and run its evidence validator when available. Keep current
post-change test results, tested commit and limitations alongside the media;
successful upload does not prove the changed flow works. Repository files,
release assets and local paths do not replace native attachments when required.

## Guardrails

- Never record a half-covered or tiled window — maximize first.
- When verifying a fix, show or reference the old failure alongside the new success.
- Always state the exact commit/branch/deployment tested against.
