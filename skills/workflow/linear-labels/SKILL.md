---
name: linear-labels
description: Audit, create, group, and consolidate Linear issue and project labels across workspace, parent teams, and subteams. Use for label ownership, duplicates, inherited labels, or taxonomy cleanup; ordinary issue authoring should reuse existing labels first.
metadata:
  author: kellykampen
  version: "1.0.0"
---

# Linear labels

Use the connected Linear tools when they expose the required operation. Use
`linear-cli api` for missing fields or mutations, and Linear settings for scope
moves that the public API cannot perform. Inspect current tool schemas or CLI
help before writing; supported fields differ between clients.

## Discover before creating

Issue labels and project labels are separate catalogs. A project label named
`cli` does not label an issue. Inspect both when the request covers all labels.
Read the team hierarchy and each label's ID, owning team, parent group,
`inheritedFrom`, retirement state, and group selection mode. Follow every page.
Do not assume a client's default workspace list includes team-owned labels.

Reuse an existing workspace or inherited label before creating a local variant.
Resolve by ID and scope when names are ambiguous. A child team's separate ID
with `inheritedFrom` is an inherited definition, not evidence of accidental
duplication. Do not edit or remove inherited copies independently.

For cleanup, capture label metadata and current assignments, including archived
issues and projects. Check affected views, templates, filters, and automations
when they reference labels. Keep snapshots outside the repository and out of
public PR evidence if they contain private workspace data.

## Choose the owner and group

| Scope | Use |
| --- | --- |
| Workspace | Concepts with the same meaning across unrelated teams. |
| Parent team | Concepts shared within that parent's descendants. Let subteams inherit them. |
| Product team | Components or delivery terms unique to that product. |

Follow the user's established taxonomy. For example, a workspace may use
`Platform` with `cli`, `web`, `desktop`, `mobile`, `cloud`, `extension`, `shared`,
`backend`, and `frontend`; and `Type` with `Bug`, `Feature`, `Improvement`,
`Task`, `Story`, and `spike`. These are examples, not a requirement to create
missing labels in every workspace. Keep short child names where available;
do not add a local `platform:cli` when the workspace already provides `cli`.

Groups organize a dimension; their scope determines who can use it. Use
multi-select when multiple children can apply to one item. Check existing
co-occurrences before introducing single-select, which can remove another
selection. A group itself cannot be applied as a label.

Ask about ambiguous ownership one family at a time, with a recommendation
grounded in actual usage. If the user wants only workspace and parent-team
choices, exclude leaf teams from the choices. Continue independent approved
work while waiting; do not treat silence as a decision.

Similar names do not establish equivalent meaning. For example, `stack-4`
and `Stack 04` can describe different historical sequences. Inspect the work
and conflicting assignments before merging. No current usage or a null
`lastAppliedAt` does not prove a label was never used.

## Consolidate and verify

Read [references/consolidation.md](references/consolidation.md) before bulk
replacement, alias merging, group changes, or moving a label between scopes.
It covers native replacement constraints and settings moves.

Prefer a supported native consolidation over rewriting each issue's complete
label list. Preserve unrelated labels and existing multi-label combinations.
For authorized unused-label cleanup, prefer retirement when it provides the
requested result and keeps history recoverable.

After each batch, read back names, scopes, group membership, inheritance, and
retirement states. A successful mutation is not proof every requested field
changed. Compare assignments by entity ID against the snapshot, accounting
for replacement IDs and concurrent new work. A smaller label count alone is
not evidence of a successful cleanup. Report completed changes, unresolved
ownership, semantic conflicts, and verification limits separately.

When creating or revising tickets as part of this work, apply relevant existing
labels and a non-empty provisional estimate on the team's configured scale.
Read both fields back before handoff. If estimation is disabled or the scale
cannot express the intended estimate, resolve that with the owner rather than
silently changing team settings or leaving the estimate empty.
