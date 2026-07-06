# Data sources and assumptions

This documents exactly what `scripts/check_model_usage.py` parses against, so a
future session can fix it fast instead of re-deriving everything when a provider starts reporting
"unavailable" or a number looks wrong.

**Ground rule: CodexBar is the only data source.** This skill must not open cmux panes, drive any harness TUI
(`claude /usage`, `codex /status`, `agy /usage`), or call provider HTTP APIs directly. If codexbar can't reach
a provider, debug codexbar (`codexbar usage --provider <x> --verbose`, try `--source cli|oauth|api|web`,
`codexbar config validate` / `dump`) or upgrade it (`brew upgrade codexbar`) -- don't route around it.

## CodexBar JSON shape

[CodexBar](https://github.com/steipete/CodexBar) (`brew install steipete/tap/codexbar`) tracks usage across
50+ AI coding providers. `codexbar usage --provider <x> --json` prints a JSON **array** with one entry per
provider/account:

```json
[{
  "provider": "codex",
  "source": "oauth",
  "version": "0.142.5",
  "usage": {
    "identity": { "accountEmail": "...", "loginMethod": "plus", "providerID": "codex" },
    "primary":   { "usedPercent": 28, "windowMinutes": 300,   "resetsAt": "2026-07-05T04:54:03Z", "resetDescription": "..." },
    "secondary": { "usedPercent": 35, "windowMinutes": 10080, "resetsAt": "2026-07-11T11:49:50Z" },
    "tertiary": null
  },
  "pace": {
    "primary":   { "deltaPercent": -11, "expectedUsedPercent": 39, "willLastToReset": true,  "stage": "behind",   "summary": "11% in reserve | Expected 39% used | Lasts until reset" },
    "secondary": { "deltaPercent": 27,  "expectedUsedPercent": 8,  "willLastToReset": false, "etaSeconds": 93098, "stage": "farAhead", "summary": "27% in deficit | Expected 8% used | Runs out in 1d 1h" }
  }
}]
```

On failure the entry has an `error` object instead of `usage`:
`{"kind": "provider", "code": 1, "message": "Kimi Code API key is invalid or expired. ..."}` -- the renderer
prints `error.message` verbatim.

### Native `pace` -- who has it

As of CodexBar 0.39.0, only **Codex and Claude** entries carry a native `pace` object, and only for
`primary`/`secondary` slots. Sign convention: **positive `deltaPercent` = deficit = burning ahead of
schedule = bad** (stage `ahead`/`farAhead`); negative = reserve (stage `behind`/`farBehind`).
The script uses native pace verbatim when present (tag `[codexbar]`) and reproduces identical math
otherwise (tag `[computed]`).

### Slot mapping is NOT consistent -- classify by window length

Observed mapping as of CodexBar 0.39.0:

| Provider | primary | secondary | tertiary |
|---|---|---|---|
| codex | 5h (300 min) | weekly (10080 min) | null |
| claude (claude.ai API source) | 5h (300 min) | weekly, all models (10080 min) | **model-specific weekly cap** (10080 min, from the API's `seven_day_sonnet`/`seven_day_opus` field; the window Claude Code's `/usage` TUI shows as "Current week (Fable)"). Has `usedPercent` + `windowMinutes` but **no `resetsAt`** -- the renderer inherits the reset time from the all-models weekly window, which the TUI confirms is identical |
| zai | **weekly** (10080 min) | **monthly** (`resetDescription: "Monthly"`, no windowMinutes) | **5h** (300 min) |
| kimi | weekly (no windowMinutes at all -- classified by reset distance; `resetDescription` like "37/100 requests") | 5h (300 min) | null |
| gemini | Pro **daily** (1440 min) | Flash daily | Flash Lite daily (labels only exist in codexbar's text output, hardcoded in the renderer) |
| antigravity | "most constrained" pool only | its 5h window | null -- **use `extraRateWindows` instead, see below** |

The script therefore classifies by **actual length**, never slot name:
- `windowMinutes <= 360` -> session (5h); `<= 1500` -> daily; `<= 20000` -> weekly; else monthly.
- Missing `windowMinutes`: match `resetDescription` text ("5 hour"/"week"/"month"), else by time-to-reset
  (`<=12h` session, `<=10d` weekly, else monthly), defaulting to weekly. Assumed lengths (300/1440/10080/43200
  min) feed the pacing math and are flagged `(assumed window length)` in the output.

### Antigravity: use `extraRateWindows`, not primary/secondary

Antigravity tracks two fully independent pools (Gemini models; Claude+GPT models), each with its own 5h +
weekly window. The generic slots only surface the single "most constrained" pool (per CodexBar's own
`docs/antigravity.md`). The full breakdown is `usage.extraRateWindows[]`, keyed by stable ids:

```json
"extraRateWindows": [
  { "id": "antigravity-quota-summary-gemini-5h",     "title": "Gemini 5-hour",     "window": {...} },
  { "id": "antigravity-quota-summary-gemini-weekly", "title": "Gemini weekly",     "window": {...} },
  { "id": "antigravity-quota-summary-3p-5h",         "title": "Claude/GPT 5-hour", "window": {...} },
  { "id": "antigravity-quota-summary-3p-weekly",     "title": "Claude/GPT weekly", "window": {...} }
]
```

The renderer uses `title` when present, deriving a label from the id otherwise, and falls back to the generic
slots only when `extraRateWindows` is absent (older CodexBar/agy payloads).

## Provider configuration lives in codexbar, NOT in this skill

The script performs **zero** codexbar config mutation -- no `config enable`, no `set-api-key`. All 5
providers are configured once in codexbar itself (`~/.config/codexbar/config.json`, managed via the CodexBar
menubar app's Settings > Providers, or one-off `codexbar config` commands by hand):

- Codex: OAuth tokens from `~/.codex/auth.json` -- no key needed.
- Claude: talks to the claude.ai usage API via Claude Code's OAuth credentials -- no key needed. Slowest
  fetch (~10-20s).
- Antigravity: CodexBar auto-discovers the `agy` binary and talks to its embedded local HTTPS quota server --
  no key needed.
- z.ai and Kimi: API keys stored in codexbar's config (set up once via the app or
  `codexbar config set-api-key --provider <x> --api-key "..."`).

### Why the script must never write keys (incident, 2026-07-05)

An earlier version of this script re-pushed `ZAI_API_KEY`/`KIMI_API_KEY` from `~/.zshrc.local` into codexbar
config via `printf | codexbar config set-api-key --stdin` on **every run**. Observed live: Kimi worked at the
start of a session, then broke with `Kimi Code API key is invalid or expired` immediately after runs of that
script -- the stored key in config.json had been corrupted to 51 chars (source key: 72 chars), consistent
with overlapping config writes racing against codexbar's shared config file. The key itself was still valid
(proved by passing it read-only via codexbar's native `KIMI_CODE_API_KEY` env var). Fix was one clean
`set-api-key` by hand. Lesson: provider credentials are codexbar's state, set once by a human/app -- a
report script that rewrites them on every invocation adds a failure mode and no value. If a key error
appears, tell the user to re-add the key in codexbar; don't automate it here.

### "Claude CLI usage endpoint is rate limited right now"

Seen live 2026-07-05 after ~8 Claude fetches within a few minutes (a test loop): the Claude usage endpoint
rate-limits repeated polling. Normal usage -- one script run at a time, minutes apart -- never triggers this.
If it appears, just wait a few minutes and rerun; don't add tighter retry loops (they make it worse). The
script's built-in retry pass deliberately skips definitive provider errors like this one and only retries
*empty* transient responses.

## Pacing math assumptions

- **Expected% / deficit / run-dry** are computed from real `windowMinutes` + `resetsAt` when present -- no
  cycle-length guessing. Only windows missing `windowMinutes` (kimi weekly, zai monthly) use the assumed
  lengths above.
- **Burn line rates**: `actual %/h = used% / hours-elapsed-in-window`; `safe %/h = remaining% /
  hours-to-reset` (0% exactly at reset). Weekly/monthly also show safe per day (`safe%/h * 24`) and per 5h
  session (safe/day ÷ 4.8). The summary's `Nx safe rate` multiplier = actual ÷ safe -- the throttle factor.
  Late in a window `safe %/h` can exceed 100 (e.g. 88% remaining with 53 min left) -- correct, just means
  "cannot realistically run out".
- All rates are **averages since the window started**, from a single snapshot -- not a live velocity. A burst
  right after a reset inflates the average and can flag a false `OVER PACE`; deviations of ≤2 points from
  expected are reported as `borderline` rather than `OVER PACE` to reduce that noise.
- `resetsAt` is plain UTC ISO-8601 (with or without fractional seconds).
- **Recent %/h (trending)** = Δused / Δtime against the oldest snapshot within the last 3h that is ≥10 min
  old, read from `~/.local/share/check-model-usage/history.jsonl`. Snapshots are matched to the same window
  instance by `resetsAt` (±20 min jitter tolerance) so a delta never straddles a reset. History is appended
  on every run, deduped when <60s apart, pruned past 14 days. The sparkline buckets used% over the trailing
  24h (weekly) / window length (session); `·` marks buckets with no snapshot.
