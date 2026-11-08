---
name: issue-breakdown
description: "Break a feature or initiative into a Linear epic (project) plus small, review-ready issues that meet a strict quality bar: every issue is a user story ('as a role, I want an action, so a result') with explicit acceptance criteria, a Fibonacci estimate of 3 points or less (anything larger is split), a parent epic/project, blocker and dependency links, and labels; design issues also carry a screenshot/PNG export of the design plus an optional prototype/Figma/Claude Design link. Use whenever the user wants to break down, scope, or plan a feature/epic/initiative into tickets, write Linear issues, create an epic, turn work into user stories, estimate or split tickets, or enforce ticket-quality standards — even if they don't say 'Linear' explicitly. Works whether issues are created via linear-cli, the Linear MCP, or drafted as specs first."
metadata:
  author: kellykampen
  version: "1.7.0"
---

# Issue Breakdown

Turn a feature, epic, or rough initiative into **one Linear project (the epic) and a set of small, review-ready issues** that all clear a fixed quality bar. The value here is *predictability*: the same feature, broken down by anyone on any day, comes out as the same shape of tickets — small user stories with acceptance criteria, estimates, parents, dependency links, and (for design work) a picture of the target. A backlog built this way is estimable, parallelizable, and reviewable; a backlog of vague 8-point "build the thing" tickets is none of those.

Apply this whether you're creating the issues live (linear-cli or the Linear MCP) or just drafting specs to paste in later — the standard is the same; only the last "how to create it" step changes.

## The shape you're producing

```
Epic (Linear project)  ──  what / why / how / key features
  ├─ Issue  (≤3 pts, user story, AC, labels, parent, links)
  ├─ Issue  (≤3 pts, …)  ──blocks──▶ Issue
  └─ Issue  (≤3 pts, …)
```

Work top-down: first frame the **epic**, then decompose it into **issues**, then **wire the dependencies** between them. Don't create issues before the epic exists — an unparented issue is a rule violation and loses the "why."

## Step 1 — Frame the epic (project)

The epic is the container and the narrative. Give it four things so anyone landing on it understands the work without reading every child:

- **What** — the feature in one or two sentences.
- **Why** — the user/business outcome it drives.
- **How** — the approach and the key decisions already locked.
- **Key features / scope** — a short bullet list of what's in, and an explicit **non-goals** line for what's out.

- **Project-level dependencies** — which *other existing projects* in the team must this epic build on? Check the team's project list and link the ones it depends on. Nearly every project depends on ≥1 other; only a genuinely foundational epic is a legitimate solo. These are **project↔project** relations, distinct from the issue links in Step 2.5 — see the tool note in Step 4.

If the "why/how" isn't clear yet, that's a signal to interview the user before decomposing — you can't write good stories against a fuzzy goal. (The `interview` skill is the tool for that; this skill assumes the goal is understood and focuses on the breakdown.)

## Step 2 — Decompose into issues (the quality bar)

**Every** issue must clear all of these. Treat them as a checklist you verify before the issue is "done being written," not aspirations.

### 2.1 Written as a user story

Format: **"As a role, I want to action, so result."** The role is a real actor (end user, admin, reviewer, the system, an integrating developer), the action is one concrete capability, the result is the payoff. This keeps tickets outcome-focused instead of task-focused — "As an admin, I want to bulk-archive members, so I can clean up churned accounts fast" tells a reviewer what success *means*, where "Add archive button" does not.

If you can't phrase it as one clean story, the issue is probably doing two things — split it.

### 2.2 Explicit acceptance criteria — as markdown checkboxes

Every issue carries an **Acceptance Criteria** section written as a **markdown task list — one `- [ ]` checkbox per condition** — never plain bullets (`-`, `*`), a numbered list, or a prose paragraph. The format is load-bearing, not cosmetic: Linear (and GitHub) render `- [ ]` as **interactive checkboxes** a reviewer/QA ticks off one at a time, and the `linear-ac-verification` flow literally checks these boxes as it confirms each criterion against the running code. A criterion written as a bare bullet can't be ticked, so it drops out of that verification loop — the AC stops being a tracked contract and becomes decoration.

Make each box one **observable, testable** condition — something you could hand to QA for an unambiguous pass/fail ("archived members disappear from the active list and appear under Archived", "the endpoint returns 403 for non-admins"), not vague ("works correctly"). Keep it to **one assertion per box** — don't staple three conditions together with "and", or you can't tick them independently. AC is the contract: it's what the reviewer/QA checks against and what tells the implementer when to stop. No AC — or AC that isn't checkboxes — means not ready to work.

```markdown
### Acceptance criteria
- [ ] archived members disappear from the active list and appear under Archived
- [ ] the bulk-archive action is admin-only (button hidden for members)
- [ ] the archive endpoint returns 403 for non-admin callers
```

**These boxes are the child's Definition of Done.** Each box must be verified against actual code or behavior by an independent reviewer or the `linear-ac-verification` flow. Record the evidence; do not check a box from an unsupported claim. Complete this verification before merging the child's PR so that merge can close the ticket. Do not copy project-wide build, deployment, integration or sibling requirements into a child unless that PR actually delivers them. Parent acceptance remains open independently.

### 2.3 Fibonacci estimate, 3 points or less

Estimate in Fibonacci (1, 2, 3, …). **If an issue is larger than 3 points, it is too large — split it** until each piece is ≤3. **Prefer 1–2 point issues**: they're faster to build, far faster to review, merge sooner, and cause fewer conflicts. A 1-point ticket that ships today beats a 5-point ticket that's "in review" for a week. When in doubt, split smaller. (See Step 3 for how.)

### 2.4 Parented to the epic

Every issue belongs to the epic/project from Step 1. No orphan issues — a loose issue can't be tracked, filtered, or reasoned about as part of the feature.

### 2.5 Dependency links

Wire the real relationships: if issue A must land before B, record **A blocks B** (equivalently, B is blocked by A). This makes the build order explicit, lets work parallelize safely, and stops someone picking up a ticket whose groundwork doesn't exist yet. Link every dependency you know — a dependency graph you can see beats one that lives in someone's head.

When the user specifies a top-to-bottom execution order, also arrange the project's visible issue list in that order. `blocks` links do not move rows. Do not change issue urgency (`priority`) to position tickets; the view's ordering field is separate. See [references/linear-cli.md](references/linear-cli.md) for reading and setting the rank when using Linear CLI. If the user requests one forward chain, verify that only adjacent requested tickets are linked, with exactly one entrance and one exit.

### 2.6 Labels

Label each issue enough to filter and route it — area/domain, type (feature/bug/chore/spike), and any workflow labels your team uses. Unlabeled issues get lost. At minimum every issue should be findable by its domain.

Inspect the issue-label catalog and team hierarchy before creating a label.
Reuse workspace and inherited parent-team definitions; do not create a local
variant such as `platform:cli` when an applicable workspace `cli` exists.
Project labels are a separate catalog and do not satisfy an issue's labels.
Respect existing groups and selection modes. Use the `linear-labels` skill,
when available, for ownership decisions or consolidation; it is not required
for ordinary issue authoring.

On every ticket created or revised, verify relevant labels and a non-empty
provisional estimate on the team's configured scale. Fill missing fields before
handoff. Resolve a disabled estimation scale with the owner rather than silently
changing team settings. Do not bulk-create new labels to avoid that discovery.

### 2.7 Design issues carry the design

If an issue is a **design/UI ticket**, it must include a **screenshot or PNG export of the target design** attached to the issue — the implementer builds to match a picture, not a paragraph. Optionally add a link to the source (prototype, Figma, or Claude Design). A UI ticket without the visual is not ready; the copy and layout live in the design, and "build it like the mock" only works if the mock is on the ticket.

### 2.8 One implementation ticket, one PR

Scope each implementation ticket to one small, reviewable PR. Associate that PR with only its owning implementation ticket, and associate the ticket with only that PR. Before opening or linking a PR, check for an existing association in both directions. A parent/project can contain many child tickets, but it does not own their PRs. Keep dependency and parent references as context, separate from PR ownership and closing declarations.

The PR must satisfy every acceptance criterion of its owning ticket. Use the repository's completion linkage for that ticket, such as `Fixes TICKET-123`, so a verified merge can close it. Read the saved Linear association and status back; a missing integration or automation is not a reason to leave delivered work In Progress. When authorized, reconcile the status with the merge evidence.

If the work needs another PR, create another focused ticket before that work starts. If a requirement remains unfinished, give it a separate follow-up ticket with its own acceptance criteria, estimate and dependencies. Never reuse a delivery ticket for a series of partial PRs or hold it open until its parent passes.

### 2.9 Independent child completion and parent traceability

Each child delivers one finite outcome and states which parent criterion it advances. Close the child when its own verified PR merges. Mark a parent criterion complete only when the child's evidence proves that entire criterion; otherwise record the delivered part and leave the remaining parent work unchecked. A source-retention PR, for example, can complete its retention ticket while runtime qualification remains a separate ticket. Do not represent an unexecuted suite or a failing graph as passing.

When cleaning up an existing backlog, inspect the actual PR and acceptance evidence. Separate delivered work from unfinished requirements, create or identify focused follow-ups, and link them in both directions before closing the delivery ticket. Preserve the original scope and evidence as history. Do not simply delete unmet criteria, lower an estimate to disguise a large task, or keep a completed child open for parent acceptance. Parent or umbrella records organize work; decompose their implementation into independently closable tickets of at most three points, preferably one or two.

## Step 3 — Splitting anything over 3 points

When an issue estimates above 3, split along a real seam rather than slicing arbitrarily. Good seams, roughly in order of preference:

- **By vertical slice** — a thin end-to-end path first (one entity, one happy path), then broaden. Each slice ships and is demoable.
- **By CRUD / capability** — read path vs write path; create vs edit vs delete as separate stories.
- **By state / variant** — empty state, loaded state, error state; or per-role behavior.
- **By layer only as a last resort** — backend endpoint vs frontend wiring. Layer splits don't ship independently, so prefer vertical slices when you can.

After splitting, re-estimate each piece and wire the dependencies between them (the slice that lays the foundation usually **blocks** the others). If a "split" piece is still >3, split again — keep going until everything is ≤3.

Check the merge boundary as well as the estimate: each piece must fit one PR whose merge can close that ticket. Move later integration, additional test families or deployment into their own tickets when they cannot be delivered in that PR. State entry prerequisites explicitly instead of inheriting every parent requirement as a child exit condition.

## Requirements standards: STE100, EARS, Gherkin, traceability, 29148

Every issue uses the same standards. The user story (2.1) stays as the first line: it gives the "why". The numbered REQs give the exact behavior. The Gherkin AC (2.2) check each REQ.

- **Wording: ASD-STE100.** Write all text in Linear (titles, descriptions, AC, comments, updates, procedures/SOPs) in Simplified Technical English. We use it as a style guide, not a certified process. Do not rewrite text that you quote verbatim. See [references/ste-writing.md](references/ste-writing.md).
- **Requirements: EARS.** Number them `REQ-001` and up, one requirement per ID. Use the ubiquitous, event-driven ("When X, the system shall Y"), state-driven, unwanted-behavior, or optional-feature pattern. See [references/requirements-ears.md](references/requirements-ears.md).
- **Quality: ISO/IEC/IEEE 29148.** Each REQ is necessary, appropriate, unambiguous, complete, singular, feasible, verifiable, correct, and conforming. Same file.
- **AC: Gherkin.** One Given/When/Then scenario per AC, still as a `- [ ]` checkbox, with ≥1 AC per REQ. Every Then is testable.
- **Traceability: REQ → AC → TEST.** Each issue has a table that maps each REQ to its AC and test. Nothing gets built without a check. See [references/traceability.md](references/traceability.md).
- **Diagrams: Mermaid.** Use a Mermaid flowchart for issue dependencies in the epic, and a REQ → AC → TEST graph for complex issues. Same file.
- **Structure.** Project = epic = one feature (Step 1). Parent and dependency links already apply (2.4, 2.5). Add to each issue an **Entry** condition (what must be true to start, e.g. "ENG-101 is Done") and an **Exit** condition (the Definition of Done in 2.2, plus the traceability tests pass). The Mermaid dependency flowchart shows both.
- **Risky change:** put **WARNING:** (injury, data loss, security) or **CAUTION:** (damage to systems, money, schedule) first. Write the command, then the risk.

## Output format

When drafting an issue (before creating it), use this template so nothing in the bar gets skipped:

```markdown
**Title:** Bulk-archive members from the members table

As a <role>, I want to <action>, so <result>.

### Requirements
- **REQ-001:** When <trigger>, the <system> shall <response>.
- **REQ-002:** …

### Acceptance criteria
- [ ] **AC-001 (REQ-001)** Given <state>, When <action>, Then <observable result>.
- [ ] **AC-002 (REQ-002)** …

### Traceability
| REQ | AC | Test |
| --- | --- | --- |
| REQ-001 | AC-001 | <test file › test name> |

### Notes / design
- Design: <screenshot attached> · <optional prototype/Figma/Claude Design link>   (design issues only)

**Estimate:** 1|2|3   **Labels:** area, type   **Epic:** project
**Depends on / blocks:** issue refs, or "none"
**Parent criterion advanced:** parent REQ/AC ID and the exact part this child delivers
**PR ownership:** one owning ticket ↔ one PR; URL when available
**Follow-ups / excluded parent work:** separate ticket refs, or "none"
**Entry:** what must be true to start   **Exit:** this child's AC verified, traceability tests pass, and its sole PR merges
```

And for the epic:

```markdown
**Project:** name
**What:** …  **Why:** …  **How:** …
**Key features:** …
**Non-goals:** …
**Project dependencies:** other projects this epic builds on (`projectRelationCreate`), or "foundational"
**Issue dependencies:** Mermaid flowchart of the issues (A --> B means A blocks B), with Entry/Exit per issue
```

## Step 4 — Create it (tool notes)

The standard above is tool-agnostic — it holds whether you create issues via `linear-cli`, the Linear MCP, or hand the drafts to someone. The concrete "how the fleet runs it" (linear-cli invocations for creating the project, creating issues, setting estimates, adding relations, attaching design PNGs, and applying labels) lives in **[references/linear-cli.md](references/linear-cli.md)** — read it when you're actually creating issues in Linear via the CLI. If you're using the Linear MCP or another client, map the same fields; the bar doesn't change.

Whatever the tool: create the **epic first**, then the issues (parented as you go), then add the **issue dependency relations** in a second pass once all issue IDs exist — and finally wire the **project-level dependencies** (this epic → the other projects it depends on). If the user requested a visible execution order, set and verify that order after the issues exist. Project↔project relations are a different mechanism from issue relations: the Linear MCP and `linear-cli rel` don't create them; use `projectRelationCreate` via `linear-cli api mutate`, and get the anchor orientation right (finish-to-start — prerequisite `end` → dependent `start`). Details in [references/linear-cli.md](references/linear-cli.md).

**Description body is content, not a path (FLT-61).** When using `linear-cli`, `-d` / `--description`
takes the markdown text itself. Stage drafts under `/tmp` if useful, then always pass contents:
`-d "$(cat /tmp/body.md)"` or (on create) `-d - < /tmp/body.md`. Never `-d /tmp/body.md` — that
stores the path string as the ticket body. The body must include the user story and `- [ ]` AC
checkboxes. See [references/linear-cli.md](references/linear-cli.md) for the full pattern.

## Completion criteria

The breakdown is done when **every** issue satisfies all of:

- [ ] Phrased as a user story (as a role / I want / so that)
- [ ] Has an Acceptance Criteria list written as `- [ ]` checkboxes (observable + testable, one assertion per box)
- [ ] Estimated in Fibonacci and **≤3 points** (prefer 1–2)
- [ ] Parented to the epic/project
- [ ] Has dependency links wired (or explicitly "none")
- [ ] If an execution order was requested, the project's visible issue order matches it
- [ ] Has ≥1 label
- [ ] If a design/UI issue: has a design screenshot/PNG attached (+ optional source link)
- [ ] Has numbered EARS requirements (`REQ-001`…, one per ID) that pass the 29148 checks
- [ ] Has ≥1 Gherkin AC checkbox per REQ, each tagged with its REQ ID
- [ ] Has a traceability row for every REQ (REQ → AC → TEST), with no gaps
- [ ] States an Entry condition and an Exit condition
- [ ] Fits one PR with exactly one owning implementation ticket; neither side has another PR/ticket association
- [ ] Child acceptance is finite and independent of unfinished parent or sibling acceptance
- [ ] Identifies the parent criterion advanced and assigns remaining work to separate focused tickets
- [ ] The child's verified PR merge can close its ticket without waiting for parent completion
- [ ] Text follows ASD-STE100 style ([references/ste-writing.md](references/ste-writing.md))

…and the epic itself has what/why/how/key-features/non-goals **and its project-level dependencies wired** (linked to the other projects it depends on, or explicitly a foundational solo). If any box is unchecked, the breakdown isn't finished — fix it before calling it done.

## Gotchas

- **Merged delivery tickets must not become permanent integration buckets.** Close the verified one-PR delivery; put remaining requirements in separate small tickets and keep parent acceptance accurate.
- **One PR does not close a parent and its child.** Link it to its single implementation owner. Update parent acceptance through the child's verified evidence, not a second PR ownership association.
- **The estimate cap is an authoring rule, not a display setting.** "≤3 points" means *split the work*, even if your Linear estimate scale technically allows 5/8. A stored 3 that's really an 8 lies to everyone planning against it.
- **Parent + label are non-negotiable and easy to forget** when creating issues fast. An issue with no project or no label is effectively invisible later. Verify both on every issue.
- **Design tickets fail silently without the image.** The implementer will guess copy/spacing and it'll bounce at review. Attach the PNG even when a prototype link exists — links rot and require auth; the attached image always renders on the ticket.
- **Wire dependencies in a second pass.** You usually can't link A→B until both exist, so create all issues first, then add relations. Skipping this leaves a backlog that looks parallelizable but isn't.
- **Don't over-split into meaningless fragments.** ≤3 and "prefer 1–2" is about review-ability, not turning one story into ten half-point slivers. Each issue should still be an independently valuable, demoable slice with its own AC.
- **Project dependencies ≠ issue dependencies, and they're easy to skip.** Issue `blocks` links (Step 2.5) live *inside* the epic; project↔project links tie this epic to *other* epics. Both matter. The project one is the one people forget — and because the Linear MCP / `linear-cli rel` can't create it, it gets silently dropped. Wire it with `projectRelationCreate` (see the reference), and mind the anchor orientation: the reverse order still "succeeds" but never shows up in the Dependencies column — a silent no-op.
