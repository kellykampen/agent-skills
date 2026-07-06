---
name: interview
description: Interview the user in depth (via the AskUserQuestion tool) to turn a rough idea, plan file, or feature request into a concrete spec — then capture the result one of three ways. Use when the user runs /interview, or asks you to "interview me about this plan/feature", "grill me on the details", "flesh this out into a spec", or "turn this into Linear issues". Not for casual clarifying questions — this is a deep, iterative interview.
argument-hint: [plan-file | feature description]
disable-model-invocation: true
metadata:
  author: anonymous
  version: "1.0.0"
---

# Interview

Interview the user thoroughly, then persist the result. The goal is to close the gap between what they have in their head and what's actually written down — surfacing decisions, tradeoffs, and edge cases they haven't thought about yet.

## How to interview

- **Use the AskUserQuestion tool** for every question — never a wall of prose questions. Batch up to 4 at a time, with smart multiple-choice options plus room for free-text.
- Ask about **anything that matters**: technical implementation, UI/UX, data model, edge cases, failure modes, scope, concerns, tradeoffs, non-goals.
- **Make the questions non-obvious.** Don't ask what you could infer from the code or the request. Ask the things that would actually change the design.
- **If you're in a git repo**, read the relevant codebase first and ask questions grounded in it (existing patterns, conventions, where this fits).
- **Keep going** — interview continually, round after round, until the picture is genuinely complete. Don't stop early.

## Modes — pick based on what the user asked for

### 1. Plan file (default)
`/interview <plan-file>` — read the given plan/spec file, interview to fill its gaps, then **write the finished spec back to that same file**.

### 2. Feature → `plans/`
When interviewing about a feature or refactor (a description, a comment, a ticket), write the finished spec to **`./plans/<spec-name>.md`** (create the `plans/` dir if needed). Ground the questions in the current codebase.

### 3. Feature → Linear
When the user wants issues created, after the interview use the **`linear-*` skills** to create:
- A **Linear project** capturing the what / why / how / key features.
- **Issues** under the repo's team (usually named similarly to the repo), each **≤ 3 points** of effort — break anything larger down.
- **Links** between issues for blockers / dependencies.

## Finish

State clearly where you wrote the spec (file path or Linear project/issue links) and give a short summary of the key decisions the interview locked in.
