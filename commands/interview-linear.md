---
description: Interview me about a feature and make a linear project & issues
argument-hint: [plan]
model: opus
---

Read this comment $1 and interview me in detail using the AskUserQuestionTool about literally anything: technical implementation, UI & UX, concerns, tradeoffs, etc. 
but make sure the questions are not obvious.

If you are in a git repo, then be sure to check the current codebase and ask relevante questions, as this is likely a feature or refacotor of the current codebase.

Be very in-depth and continue interviewing me continually until it’s complete, then use the linear-cli skills to create a project, with issues with in the repo team (the team is usually similiar named to the repo). the linear project should be the what, why, how and key features. Each issue should be no larger than 3 points of effort. If you have an issue that larger, you need to break it down. Be sure to link issues with blockers/dependencies.

**Also link PROJECT-level dependencies.** After the project exists, check the team's other projects and link the ones this new project depends on (`projectRelationCreate` via `linear-cli api mutate` — the Linear MCP and `linear-cli rel` only do *issue* relations, not project↔project). Nearly every project depends on at least one other; only a genuinely foundational project is a legitimate solo. **Orientation is load-bearing:** `type: "dependency"`, prerequisite anchored `end`, dependent anchored `start` (`{ projectId: <prereq>, anchorType: "end", relatedProjectId: <this project>, relatedAnchorType: "start" }`). The reverse anchor order (`start`→`end`) silently fails to render in the roadmap/Dependencies column.

Each issue MUST have detailed acceptance criteria written as **markdown checkboxes** — one `- [ ]` per criterion, never plain bullets (`-`/`*`), a numbered list, or prose. The format is load-bearing: Linear renders `- [ ]` as tickable checkboxes, and bullet AC can't be checked off, so it can't be verified or closed out. One observable, testable assertion per box.

**Definition of Done (enforce this, always):** an issue is NOT Done until **every** acceptance-criteria checkbox is checked. And a checkbox may ONLY be checked after an **independent agent has verified that specific criterion against the actual codebase** (via the `linear-ac-verification` skill or an independent reviewer that ran the real tests/build) — never self-checked, never checked on a claim. Moving an issue to Done with unchecked or bullet-point AC is a defect: the issue is not done. Use `linear-ac-verification` before closing anything.