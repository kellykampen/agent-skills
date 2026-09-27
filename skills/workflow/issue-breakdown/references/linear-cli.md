# Creating the breakdown in Linear (linear-cli)

Read this when you're actually creating the epic + issues via `linear-cli`. It maps each rule in the main skill to the command that enforces it. If a family of `linear-*` skills is installed (e.g. `linear-create`, `linear-projects`, `linear-relations`, `linear-labels`, `linear-attachments`), those are the authoritative reference for exact flags — invoke the relevant one; this file is the orientation.

> Command names below use `linear-cli`'s short subcommands (`i` = issues, `p`/`proj` = projects, `l` = labels, `rel` = relations). Confirm flags with `linear-cli <sub> --help` before a bulk run — the CLI evolves.

## Order of operations

1. **Create the epic (project) first.** You need its ID to parent everything.
2. **Create each issue**, parented to the project, with estimate + labels + user-story body + AC, in one pass.
3. **Second pass: add issue dependency relations** — you can only link `A blocks B` once both issue IDs exist.
4. **Attach design PNGs** to any design/UI issues.
5. **Wire project-level dependencies** — link this epic to the *other projects* it depends on (see "Project dependencies" below). Skipping this is the most common miss.
6. **If the user specified a visible order, set and verify it** in the project's issue view (see "Visible issue order" below). Dependency links alone do not do this.
7. **Verify** every issue against the completion checklist (see main skill) before calling it done.

## Rule → command

| Rule | How |
|---|---|
| Epic (project) | Create a project in the target team; capture its ID/slug. Put the what/why/how/key-features/non-goals in the project description. |
| Issue in the epic | Create the issue **with the project set** — never create then forget to parent. Confirm the team is correct. |
| User story + AC | Goes in the issue **description** (markdown). Use the template from the main skill so AC is always present. |
| Fibonacci estimate | Set the estimate field to 1/2/3. If your tempted value is 5+, don't store it — split the issue and estimate the pieces. |
| Labels | Apply ≥1 label per issue (domain + type). If a needed label doesn't exist, create it, don't skip. |
| Issue dependencies | `linear-cli rel add <A> -r blocks <B>` — A blocks B. Do these after all issues exist. |
| Visible issue order | Read the view's rank field through raw GraphQL; update that field if the user specified an order. `priority` is urgency, not rank. |
| Project dependencies | Link the epic to other projects it depends on via `projectRelationCreate` (raw GraphQL — see below). **Not** `linear-cli rel`; that's issues only. |
| Design PNG | Attach the exported screenshot to the design/UI issue (attachment/upload), plus an optional prototype/Figma/Claude Design URL in the body. |

## Verified command patterns (orientation, not exhaustive)

```bash
# inspect / find (grounding before you create)
linear-cli i get <ISSUE-ID> --output json          # read one issue
linear-cli i list -t <TEAM> -o json                # list a team's issues
linear-cli s issues "<query>" -o json              # search issues
linear-cli l list --type issue -o json             # list labels

# relations (dependency wiring — second pass)
linear-cli rel add <A-ID> -r blocks <B-ID>         # A blocks B
```

For creating projects/issues, setting estimates, applying labels, and uploading attachments, defer to the installed `linear-create` / `linear-projects` / `linear-labels` / `linear-attachments` skills (or `linear-cli <sub> --help`) rather than guessing flags — getting the team/project/estimate fields right the first time is worth the lookup.

## Visible issue order

Linear stores issue urgency in `priority` (0 = none). A project view ordered by **Priority** uses `prioritySortOrder` for the relative order within a priority level; its value is distinct from `sortOrder`. A manually ordered view may use `sortOrder`. Check the view's display option and compare live ranks with the order shown in the UI before writing either field. Ranking affects the issue's position across the workspace, not just this project. [Linear's priority ordering](https://linear.app/docs/priority) and [display options](https://linear.app/docs/display-options) describe the view behavior.

The ordinary `linear-cli i list` output defaults to identifier order, and `i update` has no rank flag. The Linear MCP issue list/save tools do not expose these rank fields. Use raw GraphQL through `linear-cli api` when the user has asked for the project list itself to follow an execution sequence:

```bash
linear-cli api query '{ project(id:"PROJECT_ID") { issues(first:100) { nodes { id identifier priority sortOrder prioritySortOrder } } } }' --output json
```

Sort the returned issues by the field that matches the view (ascending `prioritySortOrder` in a Priority-ordered view), rather than trusting the API's node order. `IssueUpdateInput` accepts both `prioritySortOrder` and `sortOrder`. For a Priority-ordered view, update a specific issue with raw `issueUpdate` after choosing a rank from its current neighbors:

```graphql
mutation {
  issueUpdate(id: "ISSUE_UUID", input: { prioritySortOrder: -123456.5 }) {
    success
    issue { identifier priority prioritySortOrder }
  }
}
```

The rank above is illustrative; read current ranks before calculating a new one. Preserve `priority` and avoid changing unrelated issues. Requery after each batch and verify the requested top-to-bottom sequence. If the user requested a single forward chain, also verify that adjacent tickets have the matching `blocks` links, with one entrance and one exit. If the available client cannot write rank, say the visible order remains unset instead of treating dependency links as sufficient.

## Project dependencies (project ↔ project)

Project-level dependencies are a **separate mechanism** from issue relations, and there's no convenience wrapper: the **Linear MCP exposes no project-relation tool** and `linear-cli rel` only does *issue* relations. Create them with raw GraphQL via `linear-cli api mutate` (`projectRelationCreate`). Every new epic should get **≥1** of these unless it's genuinely foundational.

**Orientation is load-bearing and silently fails if wrong.** A dependency is a **finish-to-start** link: the prerequisite's `end` connects to the dependent's `start`. `type` has exactly one valid value, `"dependency"`; anchors are `start | end | milestone`.

```bash
# "<dependent> depends on <prerequisite>"  ==  prerequisite blocks dependent
linear-cli api mutate -v p=<PREREQUISITE_ID> -v r=<DEPENDENT_ID> '
  mutation($p:String!,$r:String!){
    projectRelationCreate(input:{
      type:"dependency",
      projectId:$p, anchorType:"end",          # prerequisite, anchored at END
      relatedProjectId:$r, relatedAnchorType:"start"   # dependent, anchored at START
    }){ success projectRelation{ id } }
  }'
```

- **Get the anchors right.** `end → start` (above) is the normal "blocks" dependency and is the ONLY orientation that renders on the roadmap and in the projects-list **Dependencies** column. The reverse, `start → end`, is a valid *start-to-finish* relation that the mutation happily accepts but which **never shows up in the column** — a silent no-op that looks done but isn't. If a link isn't appearing, this is almost always why.
- **Pairs are deduped / undirected.** Creating A↔B when a relation already exists in *either* direction fails with "a dependency of the same type already exists between the two projects." Read the existing one first (`project{ relations{ nodes{ id anchorType relatedProject{ name } } } }`) — it may be stored on the other project's `relations` list.
- **Reversible:** `mutation{ projectRelationDelete(id:"<REL_ID>"){ success } }`.
- **Only one project has no dependency in a healthy tree — the foundation.** If several new projects come out solo, you probably skipped this step.

## Gotchas specific to the CLI

- **Convex/Linear team vs project:** the *team* (e.g. `FTD`, `DOJO`) is the top namespace; the *project* is the epic inside it. Create issues against the right **team** AND set the **project** — an issue can be in a team but orphaned from any project, which violates the parent rule.
- **Estimate scales cap silently.** Some Fibonacci presets store 13 as 8 (or similar). That's a display artifact — it does not license a >3-point issue. Split anyway.
- **Attachments must actually upload**, not just be linked in text. A design issue needs the image on the ticket; verify it rendered.
