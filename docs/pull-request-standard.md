# Pull request standard

Every pull request, including bot and dependency PRs, must use this title structure:

```text
type(scope): TICKET-123 short description
```

Use a lowercase Conventional Commit type: `feat`, `fix`, `docs`, `style`,
`refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`. The scope is optional.
For a breaking change, put `!` before the colon. Put the uppercase Linear ticket ID
immediately after the colon and space, followed by a description. Examples:

```text
fix(auth): JIF-65 correct session expiry
chore: JIF-65 update dependencies
feat(api)!: JIF-65 require authenticated requests
```

Use the PR template and fill in these level-two headings exactly once, in order:

| Section  | Required content                                                       |
| -------- | ---------------------------------------------------------------------- |
| Summary  | Resulting behavior and a link to the ticket named in the title.        |
| What     | Concrete changes and scope.                                            |
| Why      | The problem, its impact, and the reason for this approach.             |
| Evidence | Actual verification, results, what they prove, and limitations.        |
| Agent    | Agent name, actual session/thread ID, and session link when available. |

Keep the acceptance checklist after Agent. HTML comments, empty sections, and
placeholders such as `TBD`, `N/A`, and `Pending` do not satisfy the standard.

## Linear linkage

In Summary, include exactly one standalone linkage declaration for the ticket in
the title. Choose the declaration that matches the actual scope:

| Declaration          | Use                                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `Fixes JIF-123`      | This PR completes the issue. Linear may apply its configured merged status.                                              |
| `Refs JIF-123`       | This PR is partial work. Other configured workflow automation can still run, but merge does not apply the merged status. |
| `Relates to JIF-123` | An informational relation with no status automation.                                                                     |

The ID may be replaced by the raw full Linear issue URL, for example
`Refs https://linear.app/dojoco/issue/JIF-123/issue-title`. The validator also
accepts Linear's other documented closing, non-closing, and relation keywords,
such as `Closes`, `Implements`, `References`, and `Related to`. Put the declaration
on its own visible line, outside comments or code examples. Keep extra informational
ticket links separate and use a closing word only for work actually completed.
Reviewers assess whether the selected intent matches the PR's scope.

An ordinary Markdown ticket link is useful context but does not declare this
intent. Magic words in PR comments do not create Linear associations. These rules
follow [Linear's GitHub integration documentation](https://linear.app/docs/github#linking-linear-issues-to-github-prs).

Linear also supports IDs in branch names and PR titles. The explicit body statement
records intent; its absence is not proof that a missing native association was
caused by formatting. Native PR linking requires the correct Linear workspace's
GitHub integration with access to the organization/repository and working event
synchronization. Check those independently when a correctly identified PR does not
appear in Linear. GitHub autolink references, Markdown links, GitHub issue-sync
mappings, and Codex PR attachments are separate from Linear's native PR association.

Evidence must include a reviewer-accessible HTTPS link or fenced test, log, or API
output. Explain which checks passed and what the result demonstrates. A bare
"tests passed" statement, local filesystem path, or promise of future testing does
not count. Keep evidence current after material changes and remove private data.
The automated check validates structure and the presence of proof, not the truth
of a result, ticket existence, link permissions, or whether coverage is sufficient.
Reviewers assess those details.

In Evidence, explicitly declare `UI changes: Yes` or `UI changes: No`.
UI changes require screenshots and/or video of the affected flow, uploaded
through GitHub attachments. At least one is required; both are welcome when useful.
Embed screenshots inline and label the proof fields you include:

```markdown
UI changes: Yes

- Screenshot: ![Affected flow](https://github.com/user-attachments/assets/UPLOAD_ID)
- Video: https://github.com/user-attachments/assets/RECORDING_ID
```

The validator inspects changed frontend files, styles, markup, and image assets,
excluding tests and fixtures. Detected UI files require visual proof even
if the declaration says No. Declare Yes for UI changes in other file types too,
such as server-rendered templates in backend code. Use GitHub upload URLs.
Reviewers verify the media actually demonstrate
the affected flow; the validator checks references, not image or video contents.
Backend,
package, and CI changes can use test results, logs, or API output. Do not commit
evidence files to the repository or use them as developer documentation.

In Agent, use these fields:

```markdown
## Agent

- Agent: Codex
- Session/thread ID: actual-thread-id
- Session link: codex://threads/actual-thread-id
```

Agent and Session/thread ID are required, and placeholders fail validation.
Use the actual creating agent/session, not the session of an unrelated reviewer.
For automation, use the bot name, run ID, and workflow/run URL. For human-only
PRs, identify the author and use `human-authored` as the session/thread ID.
Include a session link when available; model/version, GitHub submitter, and a
parent/delegating thread ID are useful optional fields. Record only known values.

The `PR standard` workflow reads current PR metadata on opening, editing,
reopening, pushes, and readiness for review. Invalid PRs receive a failing
`PR standard` commit status and one bot comment listing corrections. Later runs
update that comment; correcting the metadata changes it to a passing message.
PRs remain open so authors can fix them. Maintainers must separately configure and verify required-status protection, subject to repository plan support. It does not replace code review or CI.

The workflow grants explicit contents-read, PR-write, issue-write, and status-write
permissions to fetch metadata/files, update feedback, and publish statuses.
It runs trusted base-branch scripts only, with no PR code execution or
dependency installation. It publishes the status on the PR head SHA explicitly,
so metadata edits can clear a failure without another commit. Operators can use
the workflow's manual PR-number input to revalidate existing PRs or retry an API
failure. Run `NODE_OPTIONS=--max-old-space-size=512 node --test --test-concurrency=1 scripts/pr-standard.test.mjs scripts/enforce-pr-standard.test.mjs` to test the validator and bot behavior.

## CI compute

The metadata job uses `ubicloud-standard-2-ubuntu-2404`, the repository's default
Linux UbiCloud runner. Existing test and deployment jobs keep their configured
UbiCloud sizes. GitHub Actions schedules these workflows; repository Actions and
the UbiCloud integration's repository access must both remain enabled. A queued
job without a runner calls for checking integration access, not changing providers.

`pull_request_target` loads the workflow and trusted checkout from the PR's base
branch. A runner-label migration therefore takes effect for automatic metadata
checks after it reaches that base. Before merge, a maintainer can dispatch the
metadata workflow from the reviewed migration branch against an existing PR to
verify the new runner. After merge, dispatch from main to confirm the normal path.
Verify the actual job's labels, runner name/ID and terminal result through the
Actions jobs API before describing it as a successful UbiCloud run. Metadata
validation keeps its existing permissions, five-minute bound and trusted-code
checkout; it never runs a PR's untrusted head with write permissions.

## Provenance

Imported from JibHQ/jib-factory commit `fae094712705fc1baba55fb4b3cfaaef78041b3a`. Template commands are adapted to this repository. Automatic metadata enforcement activates only after trusted files reach base; first-PR CI does not prove activation or required-status protection.

The unchanged logo is from FantasticDevHQ/fantastic-dev-brand-kit commit `0ce1aebc3e8418d7e59ce171e117cf9793dd2f3a`, `assets/brand/logo-mark.svg`. Existing MIT licensing is preserved.

Local adaptations normalize LF/CRLF/lone-CR bodies and publish a best-effort failure status on API errors while preserving the original exception. The exact README-only `media/fantastic-dev-logo.svg` is excluded from application UI detection; other image assets retain the canonical media requirement.
