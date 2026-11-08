# Safe label consolidation

Inspect live schemas before using these GraphQL examples. They describe the
public API observed during label cleanup; client wrappers may expose less.
Use [Linear's label documentation](https://linear.app/docs/issue-property#issue-labels) for product
behavior and the connected API schema for current mutation inputs.

## Inventory and pagination

```graphql
query {
  teams(first: 100) {
    nodes { id key name parent { id key } }
    pageInfo { hasNextPage endCursor }
  }
  issueLabels(first: 100) {
    nodes {
      id name description color isGroup groupType retiredAt
      team { id key }
      parent { id name }
      inheritedFrom { id name team { key } }
    }
    pageInfo { hasNextPage endCursor }
  }
  projectLabels(first: 100) {
    nodes {
      id name description color isGroup groupType retiredAt
      team { id key }
      parent { id name }
      inheritedFrom { id name team { key } }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

Continue each connection independently with `after: "END_CURSOR"` until
`hasNextPage` is false. Include archived items in assignment queries where
supported. Paginate nested assignment connections too. Reduce page sizes or
split queries when nested fields exceed the API complexity limit; never
report a truncated inventory as complete.

Record entity IDs, label IDs, and relevant team IDs before changing anything.
Use current metadata to distinguish independent labels from inherited copies.
Record external label references in saved views and templates separately;
do not assume assignment migration also updates every integration or filter.
Multi-team UI filters can match same-named labels across teams, while API calls
still need their separate IDs. Matching results in a view do not prove the
underlying definitions have been consolidated.

## Native same-name replacement

`issueLabelCreate`, `issueLabelUpdate`, `projectLabelCreate`, and
`projectLabelUpdate` support `replaceTeamLabels`. On a workspace label it
replaces same-named team labels with that workspace definition. This is useful
when the meaning should be shared workspace-wide; it is too broad when an
unrelated team uses the name for something different. Inventory all matches
before enabling it. Do not use it to remove legitimate inherited copies.

```graphql
mutation {
  issueLabelUpdate(
    id: "WORKSPACE_LABEL_ID"
    input: { name: "cli" }
    replaceTeamLabels: true
  ) {
    success
    issueLabel { id name team { id } parent { id } }
  }
}
```

For a parent-owned definition, inspect matching names across that parent's
whole subtree before enabling replacement. In an observed project-label
promotion, creating an ungrouped label with the parent's `teamId` and
`replaceTeamLabels: true` resolved a child-name inheritance collision. The
original child ID became inherited from the new parent definition, preserving
its project assignment. This is a distinct path from workspace replacement;
verify the resulting owner, affected subtree, inherited IDs, and assignments.
Do not assume the issue-label and project-label settings expose identical moves.

Grouped children require special handling. The API rejects replacement of an
individual label inside a group. For an approved consolidation, detach the
affected root definitions with `parentId: null`, allow inherited changes to
propagate, perform the replacement while the workspace target is ungrouped,
then attach the result to the intended workspace group. Read back each step.
Do not retire an old group until its children have all been accounted for.

For a confirmed alias such as local `platform:cli` and workspace `cli`, native
replacement matches names, not meanings. One supported approach is to detach
the source and target, temporarily rename the workspace target to the alias
with `replaceTeamLabels: true`, then restore its canonical name and intended
group. Check name collisions and every matching team first. Temporary renames
can affect name-based automation; use an explicit assignment migration when
that risk is unacceptable. Keep an ID mapping and record progress so a partial
failure can resume from live state, without rerunning a creation blindly.

If explicit migration is needed, fetch current assignments and use supported
add/remove operations or `addedLabelIds` / `removedLabelIds` on issue updates.
Do not replace a full label list from a stale snapshot. Preserve estimates and
unrelated labels; fill missing ticket metadata according to the team's rules.
Verify every mapped assignment before retiring the source. Do not collapse
conflicting historical stack positions without resolving their meaning.

## Groups and scope changes

Group selection values are GraphQL enums, not strings:

```graphql
mutation {
  issueLabelCreate(input: {
    name: "Platform"
    isGroup: true
    groupType: multiSelect
  }) {
    success
    issueLabel { id name groupType }
  }
}
```

The public update inputs observed here do not accept `teamId` to change an
existing label's scope. A client save tool's `teamId` may only disambiguate a
name, rather than move it. Confirm the current schema before assuming otherwise.

Linear settings exposes **Move to teams** for workspace labels and groups.
It moves to the teams using the label, rather than letting the caller specify
an arbitrary destination. Inspect usage and the dialog before committing.
Move a coherent group when all its children belong together. Across unrelated
teams, this action can create independent definitions instead of the desired
parent-owned one. Do not claim it implements a chosen owner until readback
shows that owner, its children, and the expected inheritance.

A scope move has been observed to reset a multi-select group to single-select.
When preserving existing combinations, prefer promoting ungrouped leaves first,
then create or reuse a multi-select group at the destination and attach the
owning roots. If moving an existing group is necessary, snapshot combinations
and verify the destination mode before further writes. Restoring multi-select
afterward does not prove combinations survived; compare every assignment.

### Promote sibling definitions to their parent

A subteam label's settings menu can expose **Move to parent team**. For an
approved parent-owned concept, prefer this route over temporarily promoting
the label to workspace scope or recreating it and rewriting issue labels.
Read the confirmation and verify it names the intended parent; the action
makes the definition available to that parent's subteams.

In an observed promotion, matching sibling definitions became inherited copies
of one new parent-owned definition. Their existing child label IDs and issue
assignments survived, and other children received inherited copies. Treat that
as observed behavior to verify, not a guarantee about every name collision,
group configuration, or future version. Inspect matching names and meanings
across the parent's descendants before promotion.

The bulk **Move labels to parent team** action can process labels sequentially.
Navigating away after confirmation has been observed to leave only part of the
selection promoted. Keep the settings page open until every selected label has
moved, then verify each owning root through fresh metadata. On interruption,
resume only the labels still owned by the source team. Do not replay the whole
selection or infer completion from the dialog closing.

After each promotion, fetch fresh metadata. Verify exactly one owning root
under the intended parent and `inheritedFrom` links from the matching children.
Do not mistake those legitimate child copies for remaining duplicates. Compare
all pre-existing assignments, including archived issues, against the snapshot;
keep unrelated labels and estimates intact. Check affected external references
as described above, and report any verification limits.

When grouping several promoted labels, place the owning roots in the intended
parent-owned group and verify group membership propagates to inherited copies.
Check co-occurrences before selecting a single-select mode. Do not move or
regroup inherited children independently.

Scope moves can run asynchronously and replace IDs. Wait for the operation's
completion, fetch fresh metadata, and compare issue/project assignments using
the resulting mapping. Keep uncertain writes sequential and inspect live
state before retrying. Never replay a whole failed batch blindly.

## Verification and handoff

- Confirm requested names, owning teams, groups, and selection modes.
- Confirm inherited copies point to the intended parent definition.
- Compare every pre-existing assignment by issue/project ID, allowing only
  approved replacements. Account for entities created concurrently; counts
  need not be identical. Check archived entities too.
- Verify affected views, templates, and automations within the authorized
  scope. State any references you could not inspect or migrate.
- Confirm retired labels cannot be newly applied and existing history remains
  available. Report semantic conflicts and unresolved ownership separately.
- Put reusable instructions in skills. Put verification evidence in the PR;
  do not commit private inventories, test logs, or evidence reports.
