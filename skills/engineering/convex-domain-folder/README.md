# convex-domain-folder

Reorganize a Convex backend into per-domain folders without breaking anything.

## Install

Install just this skill from the collection:

```bash
npx skills add kellykampen/agent-skills --skill convex-domain-folder
```

Or try it without installing:

```bash
npx skills use kellykampen/agent-skills --skill convex-domain-folder --agent claude-code
```

## What it does

Moves a flat `convex/<name>.ts` into a `convex/<name>/` directory where each domain owns its own `schema.ts` (exporting `<domain>Tables`, spread into the root schema) plus optional `queries.ts` / `mutations.ts` / `model.ts`.

## Why it exists

A growing Convex backend tends to accumulate one giant schema/functions file. The move to per-domain folders looks trivial — it isn't. The `api.<domain>.*` function paths and the `convex-test` glob resolution for co-located tests are easy to get wrong by hand.

## How it works

Splits table definitions out of the monolithic schema, repoints every relative import, updates the generated `api.<domain>.queries.*` / `api.<domain>.mutations.*` call sites, and re-roots the `convex-test` glob so co-located tests keep resolving correctly.

## Requirements

Requires `convex` on `PATH`.

---

Source: [`SKILL.md`](./SKILL.md) · [Back to all skills](../../../README.md)
