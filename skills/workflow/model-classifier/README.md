# model-classifier

Pick the single best model for a task — scored, not guessed.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill model-classifier
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill model-classifier --agent claude-code
```

## What it does

Classifies any task description into the best underlying AI model to run it on, scored on cost, intelligence, and taste, across a roster of current frontier and budget models.

## Why it exists

"Which model should do this" is a decision people make from habit, not from a consistent standard — which means the same task gets a different (and sometimes wrong) answer depending on who's asking. This gives it one answer, and lets that answer improve over time.

## How it works

Returns a **model**, not a harness or CLI — what actually runs it is a separate decision. Consult it before delegating work to a subagent, casting an Agent/Workflow call, or deciding who implements/reviews/designs a piece of work, rather than picking from memory.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
