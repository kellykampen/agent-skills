---
name: convex-domain-folder
description: >-
  Reorganize a Convex backend into per-domain folders — the pattern where each
  domain owns convex/DOMAIN/schema.ts (exporting DOMAINTables, spread into
  the root schema) plus optional queries.ts / mutations.ts / model.ts, further
  split into internal/private/public trust-tier subfolders once a domain has
  more than one trust boundary, and an optional convex/DOMAIN/http.ts exporting
  a registerDomainRoutes(app) composed into the root http.ts the same way
  domain schemas compose into root schema.ts. Use this whenever moving a flat
  convex/NAME.ts into a convex/NAME/ subdirectory, splitting a growing Convex
  function file by trust tier (internal vs private vs public), extracting table
  definitions out of a monolithic schema.ts, moving HTTP routes into a domain
  folder, or when the user says things like "move X into a subdir like we did
  for tasks/users", "break this Convex file up", "follow the same structure",
  "split into internal/private/public", or "modularize the schema/http routes".
  Covers the Convex function-path changes (api.DOMAIN.TIER.queries.*),
  relative-import repointing, and the convex-test glob re-rooting that
  co-located tests need. Reach for it even when the request sounds like a
  trivial file move — the api-path and test-resolution consequences are easy
  to get wrong.
compatibility: Requires a Convex project with the `convex` CLI available (for codegen).
metadata:
  author: kellykampen
  version: "1.2.0"
  requires: "convex"
---

# Convex domain-folder structure

## The mental model

A Convex backend tends to start flat: `convex/tasks.ts`, `convex/users.ts`, one
giant `convex/schema.ts`. As it grows, the clean end state is one folder per
domain, where each domain owns its tables and its functions:

```
convex/
  schema.ts              # just spreads: ...usersTables, ...tasksTables, ...
  http.ts                # thin composition root: calls each registerXRoutes(app)
  tasks/
    schema.ts            # exports tasksTables (table defs, NOT defineSchema)
    queries.ts           # api.tasks.queries.*  (single-tier domain, no trust split needed)
    mutations.ts         # api.tasks.mutations.*
    model.ts             # shared helpers/validators (no Convex functions)
    tasks.test.ts        # co-located test (needs glob re-rooting, see below)
  companies/
    schema.ts            # data-only domain -> schema.ts is the ONLY file
  users/
    schema.ts            # exports usersTables
    helpers.ts            # shared helpers, used across ALL tiers below (not tiered itself)
    validators.ts          # shared validators, ditto
    triggers.ts            # Convex triggers, ditto
    internal/
      queries.ts          # api path: internal.users.internal.queries.*  (internalQuery)
      mutations.ts        # internalMutation — convex-only, never client-callable
    private/
      queries.ts          # api.users.private.queries.*  (query, requires an authed user)
      mutations.ts        # api.users.private.mutations.*
      actions.ts           # action, also requires an authed user
    public/
      queries.ts           # api.users.public.queries.*  (query, no auth required)
```

The root `schema.ts` becomes a thin composition root — a few imports and spreads,
zero inline table definitions. Adding a new domain then costs one import + one
spread, with no central file to keep editing.

**The single most important fact:** moving a file into a subfolder *changes its
Convex function paths*, because Convex derives module names from the file path.
`convex/tasks.ts` → `api.tasks.*`; `convex/tasks/queries.ts` → `api.tasks.queries.*`.
Every call site must be repointed. This is not a pure rename — plan for the blast
radius before you start.

## Before you touch anything: map the blast radius

Moving a domain touches more than the files you move. Enumerate first:

```bash
# Functions being moved (their api paths are about to change):
grep -nE "export const [a-zA-Z]+ = (query|mutation|action|internalQuery|internalMutation)" convex/<domain>.ts

# Who imports the helpers you're about to relocate:
grep -rn 'from "\.\./<domain>"\|from "\./<domain>"' convex --include="*.ts" | grep -v _generated

# Frontend + test call sites (paths that will change):
grep -rnE "api\.<domain>\." apps packages --include="*.ts" --include="*.tsx" | grep -v _generated
```

If a helper like `requireUser` is imported all over the codebase, that's the real
work — the file move is the easy part.

## Step 1 — Extract the table(s) into `<domain>/schema.ts`

Create `convex/<domain>/schema.ts` exporting a **plain object** of table
definitions named `<domain>Tables`. Note: this is `defineTable`, NOT
`defineSchema` — the wrapping into a schema happens once, in the root.

```ts
// convex/tasks/schema.ts
import { defineTable } from "convex/server";
import { v } from "convex/values";

export const tasksTables = {
  tasks: defineTable({
    text: v.string(),
    userId: v.id("users"),
  }).index("by_user", ["userId"]),
};
```

Then the root schema just spreads each domain's tables:

```ts
// convex/schema.ts
import { defineSchema } from "convex/server";
import { usersTables } from "./users/schema";
import { tasksTables } from "./tasks/schema";

export default defineSchema({
  ...usersTables,
  ...tasksTables,
});
```

`defineSchema` takes a plain record of `name -> defineTable(...)`, so `...spread`
is ordinary object spread — no Convex-specific machinery. Generated types
(`Doc<"tasks">`, `Id<"tasks">`) are keyed by the *table name*, not the file, so
moving definitions between files changes nothing downstream. After extracting,
delete now-unused imports (`defineTable`, `v`) from the root schema so it stays
clean.

**A schema-only extraction is a no-op on the deployment** — identical table
names, identical indexes. Confirm this at push time (see Verification); a "no
index add/remove" push is the proof you did a pure reorg with no data impact.

## Step 2 — Split the functions (skip for data-only domains)

Data-only domains (tables nothing queries directly) get *only* `schema.ts`. If
the domain has functions, split by kind so the api surface is predictable:

- `convex/<domain>/queries.ts` → the `query(...)` exports
- `convex/<domain>/mutations.ts` → the `mutation(...)` / `internalMutation(...)` exports
- `convex/<domain>/model.ts` → shared helpers and validators used by both

`model.ts` is the key to avoiding duplication. It holds the pure, non-registered
pieces — return-shape validators, sort helpers, auth gates like `requireUser`.
Convex only registers exports that are `query`/`mutation`/etc., so a module of
plain functions and validators registers nothing; it's just a helper module (the
same reason a `schema.ts` full of `defineTable` calls doesn't create functions).
The name itself isn't load-bearing — some domains call it `model.ts`, this
codebase's convention is `helpers.ts` (plus a separate `validators.ts` when
validators outgrow the helpers file); match whatever the surrounding domains
already use rather than introducing a third name.

Relative imports shift one level deeper: `./_generated/server` →
`../_generated/server`, `./constants` → `../constants`, and a sibling helper
becomes `./model`.

## Step 2b — Split by trust tier (once a domain has more than one)

Kind-first (`queries.ts`/`mutations.ts` at the domain root) is the right default
for a domain with one trust boundary. Once a domain's functions actually span
more than one — some convex-only, some requiring a logged-in user, some open to
anyone — nest the kind files one level deeper, under a tier folder instead:

- `<domain>/internal/` — `internalQuery` / `internalMutation` / `internalAction`.
  Convex-only: callable by triggers, other server functions, and scheduled jobs,
  **never** from client code. This is Convex's own built-in privacy boundary —
  the framework enforces it, nothing to double-check.
- `<domain>/private/` — plain `query` / `mutation` / `action`, client-callable,
  but every handler starts by resolving and checking an authenticated user (e.g.
  a `getAuthUserId`/`requireUser`-style gate from the domain's `helpers.ts` or
  `model.ts`). Convex does **not** enforce this tier for you — it's a naming +
  code-review convention, not a framework guarantee, so the auth check inside
  the handler is the real boundary, not the folder name.
- `<domain>/public/` — plain `query` / `mutation`, reachable by authenticated
  *and* unauthenticated clients. Generally queries — read paths that are safe to
  expose with no auth (username availability, public profile lookups) — but a
  domain can have public mutations too (e.g. an unauthenticated support-ticket
  submission) when the operation is genuinely meant to be open.

Shared pieces that don't belong to any one tier — `helpers.ts`, `validators.ts`,
`triggers.ts`, `model.ts` — stay flat at the domain root, *not* inside a tier
folder, exactly like before. They register no Convex functions, so they have no
tier of their own; every tier imports from them.

**Don't force every domain into three tiers.** A domain with only convex-only
helpers and one authenticated CRUD surface needs `internal/` + `private/`, not
an empty `public/` folder. Nest by tier only when a domain genuinely has more
than one trust boundary in play — otherwise Step 2's flat `queries.ts`/
`mutations.ts` is still correct and simpler.

## Step 3 — Repoint every call site

The api paths changed. Fix them:

- Backend importers of relocated helpers: `from "../users"` → `from "../users/helpers"`
- Frontend + tests, kind-only split: `api.<domain>.<fn>` → `api.<domain>.queries.<fn>` or
  `api.<domain>.mutations.<fn>`
- Frontend + tests, tiered split: `api.<domain>.<fn>` → `api.<domain>.<tier>.queries.<fn>`,
  e.g. `api.<domain>.private.mutations.<fn>` or, for convex-only callers,
  `internal.<domain>.internal.queries.<fn>`

**Example**

Input: a component calling `useQuery(api.tasks.list)` and `useMutation(api.tasks.create)`
Output (kind-only): `useQuery(api.tasks.queries.list)` and `useMutation(api.tasks.mutations.create)`
Output (tiered, e.g. users): `useQuery(api.users.public.queries.getUserByUsername)` and
`useMutation(api.users.private.mutations.updateProfile)`

Then delete the old flat file (`rm convex/<domain>.ts`).

## The `index.ts` trap

Convex does **not** special-case `index.ts`. `convex/tasks/index.ts` becomes the
module `tasks/index` — api path `api.tasks.index.*`, CLI `tasks/index:fn`. That
`.index` segment is almost never what you want. Use named files (`queries.ts`,
`mutations.ts`) instead. If you ever must confirm a path, check the generated
`convex/_generated/api.d.ts` — the module keys are literal file paths.

## Spreading `http.ts` the same way as `schema.ts`

HTTP routes (Hono/`httpRouter` endpoints, as opposed to Convex functions) get
the same domain-folder treatment as tables — with one mechanical difference.
`defineSchema` takes a plain object, so domain schemas compose by literal
`...spread`. Hono's `app.route()`/`app.openapi()` register routes as a *side
effect* on a shared app instance — there's no plain-object form to spread —
so the composition seam is a **function call**, not a spread, even though the
intent (root file is a thin list of domain imports, zero inline route
definitions) is identical:

```ts
// convex/tasks/http.ts
import type { OpenAPIHono } from "@hono/zod-openapi";
import type { ConvexEnv } from "../lib/honoHelpers";

export function registerTasksRoutes(app: OpenAPIHono<ConvexEnv>) {
  app.openapi(someRoute, async (c) => { /* ... */ });
}
```

```ts
// convex/http.ts
import { registerTasksRoutes } from "./tasks/http";
import { registerUsersRoutes } from "./users/http";

registerTasksRoutes(app);
registerUsersRoutes(app);
```

Conventions:

- The domain file is always named `http.ts` (matching `schema.ts`'s naming),
  exporting a single `register<Domain>Routes(app)` function. Older domains in
  this codebase may still use `api.ts` with a differently-named export — that's
  a naming inconsistency from before this convention existed; match it when
  extending an existing file, but write new domain HTTP files as `http.ts` +
  `register<Domain>Routes`.
- Only domains that actually expose raw HTTP endpoints (webhooks, beacon/tracking
  pixels, non-Convex-client integrations) need an `http.ts`. Most domains are
  reached purely through `query`/`mutation`/`action` and have no HTTP surface at
  all — don't manufacture an empty one.
- `http.ts` is independent of the internal/private/public split above — HTTP
  routes have their own auth story (a route handler checks a header, webhook
  signature, or session cookie directly; it isn't gated by which folder it's
  defined in), so don't try to force HTTP routes into a tier folder.

## Co-located tests: re-root the convex-test glob

If a test lives *inside* a domain folder (e.g. `convex/tasks/tasks.test.ts`) and
uses `convex-test`, the naive `import.meta.glob("../**/*.ts")` breaks with
`Could not find module for: "tasks/mutations"`.

Why: `convex-test` resolves modules by a *single common prefix* it derives from
the `_generated` path, which only works when every glob key is relative to the
convex root. From inside a domain folder, vite emits mixed-depth keys —
`./mutations.ts` for siblings but `../schema.ts` for the root — so the prefix
arithmetic misses. Re-root each key to be convex-root-relative before handing the
map to `convexTest`:

```ts
const rawModules = import.meta.glob("../**/*.ts");
const modules = Object.fromEntries(
  Object.entries(rawModules).map(([path, loader]) => [
    // "./mutations.ts" -> "./tasks/mutations.ts"; "../schema.ts" -> "./schema.ts"
    "./" + path.replace(/^\.\.\//, "").replace(/^\.\//, "tasks/"),
    loader,
  ]),
);
```

A separate glob for a component that doesn't share the test's directory (e.g.
`import.meta.glob("../betterAuth/**/*.ts")`) needs no re-rooting — all its keys
already share one prefix.

## Verification

Run these after the move; they catch the mistakes that matter:

```bash
# 1. Types — the fastest signal that a call site or import was missed.
pnpm --filter @repo/backend check-types

# 2. Push. For a schema-only reorg, expect NO "Added/removed table indexes"
#    lines — that empty diff proves identical schema, zero data impact.
pnpm --filter @repo/backend dev:once

# 3. No stale paths left behind.
grep -rnE "api\.<domain>\.(<oldfn1>|<oldfn2>)\b" apps packages --include="*.ts" --include="*.tsx" | grep -v _generated
grep -rn 'from "\.\./<domain>"' convex --include="*.ts" | grep -v _generated

# 4. Tests + web types (frontend call sites changed).
pnpm --filter @repo/backend test
pnpm --filter web check-types
```

The generated `convex/_generated/api.d.ts` is the source of truth for the new
module keys — grep it for `<domain>/queries`, `<domain>/mutations` to confirm
registration and that the old flat `<domain>` module is gone.

## Why this holds together

- The **spread seam** (`...<domain>Tables`) is why schema files compose without
  friction — it's plain JS, and types key off table names not files. `http.ts`
  wants the same seam but Hono forces a function-call composition instead —
  same intent (thin root, one line per domain), different mechanism.
- The **no-op push** is your safety proof: a structural reorg must not change the
  deployed schema, and Convex tells you by showing no index churn.
- Splitting **model.ts/helpers.ts** out keeps `queries.ts`/`mutations.ts` thin
  and lets other domains — and every trust tier within the same domain — reuse
  gates like `requireUser` without a circular dependency, because helper
  modules register no functions.
- The **internal/private/public split** makes the trust boundary visible in the
  file tree instead of buried in each handler's first line — but only Convex's
  own `internal*` functions are actually enforced by the framework; `private`
  vs `public` is a convention the auth-check code inside the handler has to
  honor, so reviewing a "private" file means checking the auth gate is really
  there, not just trusting the folder name.
