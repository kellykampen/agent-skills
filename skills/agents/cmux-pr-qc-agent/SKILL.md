---
name: cmux-pr-qc-agent
description: >-
  Spin up an independent, autonomous Claude Code instance in a separate cmux pane
  that watches a GitHub PR end-to-end: it polls for new review comments and CI
  status, drives every check to green (fixing failures with tests, not just
  waiting), fixes each review comment with a failing-test-first change, and replies
  to each comment individually with the fixing commit — looping until the PR is
  green and every thread is answered. Use this whenever you open or push a PR and
  want it shepherded to mergeable, when the user says "watch this PR", "QC PR #N",
  "handle the review comments", "make the checks pass and reply to CodeRabbit",
  "babysit my PR", or wants a separate Claude / QC bot to own a PR. Reach for it
  even if the user just says "I opened a PR, take it from here" — that's this skill.
compatibility: Requires cmux, the GitHub CLI (`gh`), and git.
metadata:
  author: kellykampen
  version: "1.1.0"
  requires: "cmux, gh, git"
---

# PR QC Bot

## What this is

A delegated, long-running PR shepherd. The **orchestrator** (you) spawns a
**separate Claude Code instance** in its own cmux pane and hands it one PR. That
instance — the *bot* — owns the PR: it watches for review comments and CI
results, fixes what's needed (tests first), replies to each comment, and keeps
looping until the PR is green and every thread is answered, then reports back.

Why a separate instance rather than doing it inline: a PR review cycle is
*bursty and slow* — CodeRabbit and humans drop comments minutes or hours apart,
CI takes a while, and each round is mechanical. Tying up your main session to
poll a PR is wasteful; a dedicated instance can sit on it, react as things
arrive, and ping you only when it's done or genuinely stuck. It's also cleanly
independent — a fresh agent re-reads each comment without your authoring bias.

This skill pairs with [`linear-ac-verification`](../linear-ac-verification/SKILL.md)
(verify acceptance criteria) — same delegation pattern, different target.

## Don't reinvent the cmux plumbing

This machine has the cmux skill suite. **Invoke the installed `cmux-workspace`
skill** for everything about creating the pane and talking to the bot — reading
the caller context (`$CMUX_WORKSPACE_ID` / `$CMUX_SURFACE_ID`), `cmux new-pane …
--focus false`, the two-step `cmux send` + `cmux send-key … enter`, reading the
pane back, and its non-interfering focus rules. Use `cmux` for topology/surface
discovery. Don't hardcode socket paths or surface IDs. This skill only adds the
PR-watching layer on top.

## Spawning the bot

Via `cmux-workspace`: capture your own surface (`$CMUX_SURFACE_ID` — the bot
reports back here), create a helper pane to the right with `--focus false` so
your focus is undisturbed, and start Claude Code in it (`ccc` by convention; fall
back to `claude` if `ccc` isn't on PATH — check with `command -v ccc`). Wait for
the prompt, then send the brief (text, then Enter as a separate `send-key`, since
an agent stages input until Enter arrives). The brief tells the bot to run *this
skill* on the PR — you don't decompose the work yourself; the bot does.

Brief template:

```
You are an autonomous PR QC bot. Own PR #<N> in <repo path> (cd there) until it
is green and every review comment is answered. Use the `cmux-pr-qc-agent` skill — run
its watch loop. You did NOT need to have written this code; verify and fix
honestly. Work only on this PR's branch. Report back to surface <$CMUX_SURFACE_ID>
(a one-line "PR#<N>: <status>") and fire a desktop notification when you reach
green+all-replied, or if you get stuck on anything ambiguous or destructive.
```

## The watch loop (what the bot runs)

The bot repeats this until the exit condition. Each pass:

1. **Read state.**
   - CI: `gh pr checks <N>` (or `gh pr view <N> --json statusCheckRollup`).
   - Unreplied review threads: `scripts/unreplied_threads.py <N>` — this lists
     only the top-level review comments with no reply yet, so you fix/answer each
     exactly once instead of re-handling threads already closed.
2. **Drive CI to green.** For each failing check, pull the cause and fix it like
   any bug — `gh run view <run-id> --log-failed`, reproduce, write a failing test,
   fix, run the project's test/typecheck/lint/build locally to confirm, push. A
   red check is a defect, not a status to report and move past.
3. **Handle each unreplied comment**, one at a time:
   - **Triage first.** Decide if it's a real issue. Valid → fix it. Wrong or
     not-applicable → that's fine, but you still owe the reviewer a reply
     explaining *why* you're declining, not silence.
   - **Fix test-first.** Reproduce the issue with a failing test, then fix, then
     run the relevant tests + typecheck/lint/build green. The test is what proves
     the comment is actually addressed and stops it regressing.
   - **Reply individually, after the fix is pushed**, referencing the commit:
     ```
     gh api repos/{owner}/{repo}/pulls/<N>/comments/<comment-id>/replies \
       -f body="Fixed in <short-sha> — <what changed and why>."
     ```
     One reply per thread — the reviewer should see a specific response to *their*
     point, not a lump comment. Never post "fixed" before the fix is actually
     pushed (see guardrails).
4. **Commit + push** the round's work with a clear message. Batch a round's fixes
   into sensible commits; don't push half-built states.
5. **Decide.** CI-green + zero unreplied threads is necessary but **not sufficient**
   for "done." A PR is *mergeable-clean* only when ALL of: CI green · zero unreplied
   threads · an **independent different-model review** posted on the PR · and every
   **acceptance criterion of the linked issue independently verified with its `- [ ]`
   checkbox checked** (see "The Done gate" below). If all hold, report back and exit or
   drop to a light watch. Otherwise sleep a sensible interval and loop.

### Polling cadence

Poll on the order of 1–3 minutes, not seconds — CI and human comments move slowly,
and a tight loop just burns tokens for no faster result. Use `sleep` between
passes. Crucially: **the moment you reach green + all-replied, report back** — the
user shouldn't have to wonder whether you're still working. If nothing new arrives
for a couple of cycles after that, exit cleanly (a merged/closed PR also ends the
loop).

## The Done gate — AC verification & independent review

Green CI and answered comments are necessary but **not sufficient**. The failure this
prevents (learned the hard way): PRs and their linked Linear issues marked **Done** while the
acceptance criteria were never actually confirmed — because the AC were bullet points nobody
could tick, or checkboxes checked on a "looks done" claim. Before you call a PR mergeable-clean:

- **AC must be `- [ ]` checkboxes.** If the linked issue's acceptance criteria are plain
  bullets/prose, they can't be verified or ticked — convert them to markdown `- [ ]` checkboxes
  first, one observable, testable assertion per box. A bullet is uncheckable, so it can never be
  confirmed or closed — which is exactly how "Done" issues end up holding unverified work.
- **Verify each AC against the running code, THEN check its box.** For every criterion, actually
  confirm it — run the test, hit the endpoint, drive the UI, trace the code path — via the
  [`linear-ac-verification`](../linear-ac-verification/SKILL.md) skill. A box is checked **only
  after** that specific criterion is verified against reality. Never self-check, never tick a box
  on a claim. An issue is **not Done until every box is checked**, and a PR that closes an issue
  isn't clean until they are.
- **Independent, different-model review — evidenced ON the PR.** The review must come from a
  **different model** than whoever wrote the code (fresh eyes, no authoring bias), and it must be
  **posted as a comment on the PR**. A review that lives only in a log or a chat message does not
  count; the same goes for AC-verification — leave the evidence on the PR/issue where the next
  person can see it.

Shorthand: *"verified locally" ≠ done · "reviewed" ≠ done unless it's a different model and it's
on the PR · "CI green" ≠ done unless the AC are independently checked.* All three, evidenced, or
it isn't mergeable-clean.

## Gotchas

- **Invoking a non-Claude reviewer.** Getting a *different-model* review cheaply means reaching
  for non-Claude harnesses — `claudekimi` / `claudeglm` (Kimi / GLM) or `agy` (Gemini). But
  `claudekimi`/`claudeglm` are shell functions whose `_claude_provider_token` helper and API keys
  load **only in an interactive shell**, so a bare non-interactive call fails with
  `command not found: _claude_provider_token`. Always invoke them through an interactive login
  shell: `zsh -ic 'claudekimi -p "<review prompt>"'`. **Never print the resolved token** — it's a
  secret (echoing an unset-guard like `${KEY:-…}` will leak it).
- **Pick the reviewer model by what's actually up.** Provider pools go down or dry out; before
  leaning on one, a trivial probe (`zsh -ic 'claudekimi -p "reply OK"'`) tells you it responds.
  Fall back across Kimi / GLM / Gemini rather than silently substituting the *same* model that
  wrote the code (that defeats the independence the gate exists for).

## Guardrails (because it pushes and posts on its own)

This bot acts autonomously — that's the point — so its limits matter:

- **Only its own PR's branch.** Never touch other branches, never `git push
  --force` (a review bot rebasing/force-pushing under a reviewer is how work gets
  lost). Append commits.
- **No fabricated replies.** Only reply "fixed in <sha>" when that commit exists
  and is pushed and its test passes. A reply that claims a fix that isn't there is
  worse than no reply — it tells the reviewer to stop looking.
- **A declined comment gets a reasoned reply, not a silent skip.** "I don't think
  this applies because …" is a valid outcome; ignoring the thread is not.
- **Escalate, don't guess.** Anything ambiguous (a comment you can't interpret), a
  failure you can't fix after a couple of honest attempts, a merge conflict, or
  anything destructive → stop, report to the orchestrator surface with specifics,
  and wait. Looping forever or making a risky guess is worse than asking.
- **Don't merge** unless explicitly told to — getting to green + replied is the
  job; the human (or branch protection) decides on merge.

## Reporting back

The orchestrator's surface id is in the bot's `$CMUX_SURFACE_ID` at spawn (passed
in the brief). When the bot reaches green+all-replied, or gets stuck, it sends a
one-line status to that surface (via `cmux-workspace`) and fires a desktop
notification (`printf '\e]777;notify;PR #<N>;<status>\a'`). The orchestrator reads
the report and tells the user — and never claims the PR is clean unless the bot
reported green + all threads answered.
