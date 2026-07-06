# Standing fleet rules — <PROJECT> (every seat reads this fully before acting)

<!-- Template: the orchestrator fills the <PLACEHOLDER>s from the project's reality. Keep
     every rule short, numbered, and enforceable — this is the file every dispatch brief
     points workers at, so it must be readable in one pass. Add project-specific "known
     interaction" landmines as they're discovered (they're the highest-value lines). -->

1. DEV SERVER: exactly ONE server runs on port <PORT>, in its own pane (`webserver`). NEVER
   start another, NEVER use another port, NEVER kill the live server. Test against <DEV-URL>.
   If the server must restart, only via `<DEV-SERVER-COMMAND>`, and notify the orchestrator.
   <KNOWN-DEV-SERVER-INTERACTIONS — e.g. commands that corrupt shared caches while the server
   runs, and the recovery procedure>
2. Package manager: <PM> ONLY. Never <THE-OTHERS>.
3. GIT + WORKTREES: you work ONLY in the worktree named in your brief — never another seat's
   worktree, never the main checkout. Branch per ticket, branch name carries the ticket ID
   (<TRACKER-PREFIX>-####). Commit with explicit file paths (`git add <path>` — never `-A`,
   `.`, or `commit -a`). Never push unless your brief explicitly says so. NEVER touch
   <TRUNK-PROTECTION — e.g. main; the operator promotes manually>.
4. LIMITS: <FILE-SIZE/EXPORT/LINT RULES — e.g. max lines per file, naming conventions; run the
   check before committing>.
5. VERIFY before reporting: <TYPECHECK/TEST COMMANDS> clean AND exercise your change live in a
   real browser at <DEV-URL> (interactive features = drive them; visual changes = screenshot
   mobile 390px + desktop). <TEST-LOGIN-CREDENTIALS if any>
6. REPORTING: you report commits to the QA seat (surface noted in your brief) with your commit
   sha + evidence — NOT to the orchestrator. Every inter-pane message goes via
   `.claude/orchestration/cmux-send-verified.sh <surface> "msg"` — never raw cmux send.
   Escalate blockers to the orchestrator.
7. CONTEXT: your seat lives for THIS task. When QA passes your commit, you're done — expect to
   be cleared or closed. Don't start adjacent work you weren't briefed for.
8. DESIGN ORACLE: <COMP-URL + HOW-TO-READ-IT (e.g. claude_design MCP), or "n/a">. The comp is
   the single source of truth — build nothing that isn't in it; escalate gaps instead.
9. FEATURE CONTEXT: <POINTERS TO ACTIVE SPEC/PLAN DOCS + any non-negotiable invariants, e.g.
   security rules that must fail closed>.
