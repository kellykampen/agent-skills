---
name: issue-breakdown
description: "Break a feature or initiative into a Linear epic (project) plus small, review-ready issues that meet a strict quality bar: every issue is a user story ('as a role, I want an action, so a result') with explicit acceptance criteria, a Fibonacci estimate of 3 points or less (anything larger is split), a parent epic/project, blocker and dependency links, and labels; design issues also carry a screenshot/PNG export of the design plus an optional prototype/Figma/Claude Design link. Use whenever the user wants to break down, scope, or plan a feature/epic/initiative into tickets, write Linear issues, create an epic, turn work into user stories, estimate or split tickets, or enforce ticket-quality standards — even if they don't say 'Linear' explicitly. Works whether issues are created via linear-cli, the Linear MCP, or drafted as specs first."
metadata:
  author: kellykampen
  version: "1.0.0"
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

If the "why/how" isn't clear yet, that's a signal to interview the user before decomposing — you can't write good stories against a fuzzy goal. (The `interview` skill is the tool for that; this skill assumes the goal is understood and focuses on the breakdown.)

## Step 2 — Decompose into issues (the quality bar)

**Every** issue must clear all of these. Treat them as a checklist you verify before the issue is "done being written," not aspirations.

### 2.1 Written as a user story

Format: **"As a role, I want to action, so result."** The role is a real actor (end user, admin, reviewer, the system, an integrating developer), the action is one concrete capability, the result is the payoff. This keeps tickets outcome-focused instead of task-focused — "As an admin, I want to bulk-archive members, so I can clean up churned accounts fast" tells a reviewer what success *means*, where "Add archive button" does not.

If you can't phrase it as one clean story, the issue is probably doing two things — split it.

### 2.2 Explicit acceptance criteria

Every issue carries an **Acceptance Criteria** section: a checkable list of conditions that must be true for the issue to be accepted. Make them observable and testable ("archived members disappear from the active list and appear under Archived", "the endpoint returns 403 for non-admins"), not vague ("works correctly"). AC is the contract — it's what the reviewer/QA checks against and what tells the implementer when to stop. No AC = not ready to work.

### 2.3 Fibonacci estimate, 3 points or less

Estimate in Fibonacci (1, 2, 3, …). **If an issue is larger than 3 points, it is too large — split it** until each piece is ≤3. **Prefer 1–2 point issues**: they're faster to build, far faster to review, merge sooner, and cause fewer conflicts. A 1-point ticket that ships today beats a 5-point ticket that's "in review" for a week. When in doubt, split smaller. (See Step 3 for how.)

### 2.4 Parented to the epic

Every issue belongs to the epic/project from Step 1. No orphan issues — a loose issue can't be tracked, filtered, or reasoned about as part of the feature.

### 2.5 Dependency links

Wire the real relationships: if issue A must land before B, record **A blocks B** (equivalently, B is blocked by A). This makes the build order explicit, lets work parallelize safely, and stops someone picking up a ticket whose groundwork doesn't exist yet. Link every dependency you know — a dependency graph you can see beats one that lives in someone's head.

### 2.6 Labels

Label each issue enough to filter and route it — area/domain, type (feature/bug/chore/spike), and any workflow labels your team uses. Unlabeled issues get lost. At minimum every issue should be findable by its domain.

### 2.7 Design issues carry the design

If an issue is a **design/UI ticket**, it must include a **screenshot or PNG export of the target design** attached to the issue — the implementer builds to match a picture, not a paragraph. Optionally add a link to the source (prototype, Figma, or Claude Design). A UI ticket without the visual is not ready; the copy and layout live in the design, and "build it like the mock" only works if the mock is on the ticket.

## Step 3 — Splitting anything over 3 points

When an issue estimates above 3, split along a real seam rather than slicing arbitrarily. Good seams, roughly in order of preference:

- **By vertical slice** — a thin end-to-end path first (one entity, one happy path), then broaden. Each slice ships and is demoable.
- **By CRUD / capability** — read path vs write path; create vs edit vs delete as separate stories.
- **By state / variant** — empty state, loaded state, error state; or per-role behavior.
- **By layer only as a last resort** — backend endpoint vs frontend wiring. Layer splits don't ship independently, so prefer vertical slices when you can.

After splitting, re-estimate each piece and wire the dependencies between them (the slice that lays the foundation usually **blocks** the others). If a "split" piece is still >3, split again — keep going until everything is ≤3.

## Output format

When drafting an issue (before creating it), use this template so nothing in the bar gets skipped:

```markdown
**Title:** Bulk-archive members from the members table

As a <role>, I want to <action>, so <result>.

### Acceptance criteria
- [ ] observable, testable condition
- [ ] …

### Notes / design
- Design: <screenshot attached> · <optional prototype/Figma/Claude Design link>   (design issues only)

**Estimate:** 1|2|3   **Labels:** area, type   **Epic:** project
**Depends on / blocks:** issue refs, or "none"
```

And for the epic:

```markdown
**Project:** name
**What:** …  **Why:** …  **How:** …
**Key features:** …
**Non-goals:** …
```

## Step 4 — Create it (tool notes)

The standard above is tool-agnostic — it holds whether you create issues via `linear-cli`, the Linear MCP, or hand the drafts to someone. The concrete "how the fleet runs it" (linear-cli invocations for creating the project, creating issues, setting estimates, adding relations, attaching design PNGs, and applying labels) lives in **[references/linear-cli.md](references/linear-cli.md)** — read it when you're actually creating issues in Linear via the CLI. If you're using the Linear MCP or another client, map the same fields; the bar doesn't change.

Whatever the tool: create the **epic first**, then the issues (parented as you go), then add the **dependency relations** in a second pass once all issue IDs exist.

## Completion criteria

The breakdown is done when **every** issue satisfies all of:

- [ ] Phrased as a user story (as a role / I want / so that)
- [ ] Has an Acceptance Criteria list (observable + testable)
- [ ] Estimated in Fibonacci and **≤3 points** (prefer 1–2)
- [ ] Parented to the epic/project
- [ ] Has dependency links wired (or explicitly "none")
- [ ] Has ≥1 label
- [ ] If a design/UI issue: has a design screenshot/PNG attached (+ optional source link)

…and the epic itself has what/why/how/key-features/non-goals. If any box is unchecked, the breakdown isn't finished — fix it before calling it done.

## Gotchas

- **The estimate cap is an authoring rule, not a display setting.** "≤3 points" means *split the work*, even if your Linear estimate scale technically allows 5/8. A stored 3 that's really an 8 lies to everyone planning against it.
- **Parent + label are non-negotiable and easy to forget** when creating issues fast. An issue with no project or no label is effectively invisible later. Verify both on every issue.
- **Design tickets fail silently without the image.** The implementer will guess copy/spacing and it'll bounce at review. Attach the PNG even when a prototype link exists — links rot and require auth; the attached image always renders on the ticket.
- **Wire dependencies in a second pass.** You usually can't link A→B until both exist, so create all issues first, then add relations. Skipping this leaves a backlog that looks parallelizable but isn't.
- **Don't over-split into meaningless fragments.** ≤3 and "prefer 1–2" is about review-ability, not turning one story into ten half-point slivers. Each issue should still be an independently valuable, demoable slice with its own AC.
