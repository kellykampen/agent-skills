# skill-maker

A toolkit for creating, evaluating, and versioning Claude Code skills.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill skill-maker
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill skill-maker --agent claude-code
```

## What it does

Everything needed to author a skill end to end: scaffold it, edit or improve an existing one, run evals, benchmark performance against a baseline, and tighten a skill's description so it actually triggers when it should.

## Why it exists

A skill is only as good as its description (does it trigger when it should?) and only as trustworthy as its versioning (did the number move when the behavior did?). This is the toolkit that enforces both, instead of leaving them to memory.

## How it works

`init_skill.py` scaffolds a spec-valid `SKILL.md` (semver `x.y.z` from the first commit); `quick_validate.py` hard-fails anything that isn't properly versioned, missing an author, or carrying a malformed `requires`; the eval viewer shows old-vs-new output side by side with arrow-key voting, plus per-eval benchmarks inline.

## Requirements

Requires `python3` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
