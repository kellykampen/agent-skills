# <PROJECT> runtime regression checklist (known answers)

<!-- Template: QA owns this file. It runs on EVERY reported builder commit and again as a
     mandatory pre-merge gate, executed by the `regr·haiku` tab. The design constraint that
     makes it work: EVERY line is a known-answer check — an exact command or click-path with
     an exact expected value — so a Haiku-class runner can execute it for pennies and any
     deviation is an unambiguous NO-GO (escalated to the QA seat, which routes the failure to
     the owning builder). No judgment calls in this file; judgment lives with QA. -->

Run against <DEV-URL> on the commit under test. All answers are known; any deviation = NO-GO.
<SEQUENCING-CONSTRAINTS — e.g. checks that must not run while the dev server is serving>

1. <EXACT CHECK — e.g. `curl -s <DEV-URL>/api/<endpoint>` → `<exact expected JSON fragment>`>
2. <EXACT CHECK — e.g. page <path> shows <exact element/value>; <element> absent when <state>>
3. <EXACT CHECK — e.g. `<typecheck/test command>` → 0 errors>

Maintained by QA. Every new invariant that ships adds a line; keep every line a known answer.
When a line's expected value legitimately changes, the PR that changes it must update this
file in the same commit — a checklist that drifts from reality trains everyone to ignore
NO-GOs.
