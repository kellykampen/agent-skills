#!/usr/bin/env bash
# Thin wrapper so `pnpm test:e2e:remote*` works from any shell without exporting keys.
# Loads provider credentials, then execs crabbox with whatever args were passed.
# Reusable almost verbatim across projects — no per-project changes usually needed.
set -euo pipefail
cd "$(dirname "$0")/.."

# E2B: reuse the team API key the e2b CLI already cached at login — never copied into
# the repo, and picks up rotations automatically. An existing $E2B_API_KEY wins.
if [ -z "${E2B_API_KEY:-}" ] && [ -f "$HOME/.e2b/config.json" ]; then
  E2B_API_KEY="$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.e2b/config.json'))).get('teamApiKey',''))" 2>/dev/null || true)"
  [ -n "$E2B_API_KEY" ] && export E2B_API_KEY
fi

# Everything else (DAYTONA_API_KEY, overrides) from a gitignored env file.
if [ -f crabbox/.env.local ]; then
  set -a; . crabbox/.env.local; set +a
fi

exec crabbox "$@"
