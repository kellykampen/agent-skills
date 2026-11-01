# Repository instructions

Read docs/worktrees.md and docs/pull-request-standard.md. This is a skill collection, with no app/backend, package install, build, ports or dev services. Do not introduce Convex. Keep lifecycle modules and tests under scripts/worktree/. Never reset, stash or discard user changes. Setup fetches origin and only fast-forwards.

Run focused checks sequentially with NODE_OPTIONS=--max-old-space-size=512 for Node. Full lint/typecheck/build belongs on UbiCloud CI. Use only ubicloud-standard-2-ubuntu-2404 Linux CI runners. Serialize dependency installs/codegen/backend integration with flock -w 3600 /home/cloudagent/.cache/fantastic-heavy.lock.

Write-token metadata jobs must execute trusted base code only. PRs need the owning ticket after the title colon, five ordered sections, actual agent/session identity, accessible evidence and acceptance checklist. Never claim skipped checks passed.

All local Node test suites must hold `/home/cloudagent/.cache/fantastic-heavy.lock` for the entire subprocess tree: `flock -w 3600 /home/cloudagent/.cache/fantastic-heavy.lock env NODE_OPTIONS=--max-old-space-size=512 node --test --test-concurrency=1 <specific test files>`. Do not nest this lock.
