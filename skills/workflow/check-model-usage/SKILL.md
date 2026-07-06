---
name: check-model-usage
description: Checks quota/usage and session + weekly pacing across all 5 AI coding harnesses in one command -- Claude Code, Codex CLI, Antigravity (agy), GLM/Z.ai, and Kimi/Moonshot -- using only the CodexBar CLI (no TUI probes, no direct provider API calls). Use this whenever the user asks "how much quota do I have left", "am I going to run out before the weekly reset", "check my usage/limits across tools", "how's my burn rate", or wants a consolidated view of AI coding-tool usage and whether current usage is sustainable until the next reset. Also use proactively before recommending heavy usage of any of these 5 tools if recent usage hasn't been checked.
context: fork
model: sonnet
effort: medium
---

# Check Model Usage

Runs `scripts/check_model_usage.py` (a single self-contained Python script, stdlib only), which prints one
consolidated report covering current usage plus **session (5h) and weekly pacing** across all 5 harnesses.
Just run it (takes ~20s; most of that is codexbar's Claude fetch):

```bash
python3 scripts/check_model_usage.py
```

Use `--only=` to check a subset (comma-separated): `--only=claude,codex`, `--only=glm,kimi`, etc. Accepted
names: `claude`, `codex`, `agy` (alias for `antigravity`), `glm` (alias for `zai`), `kimi` -- plus any other
codexbar provider id (e.g. `gemini`) if explicitly requested.

## How it works

The **only** data source is [CodexBar](https://github.com/steipete/CodexBar)
(`brew install steipete/tap/codexbar`), a community-maintained CLI that reaches each provider's usage data
itself (OAuth token files, provider web APIs, API tokens) and returns clean JSON. This skill never opens cmux
panes, never drives any harness TUI, never calls provider APIs directly, and **never writes codexbar config**
(no `config enable`, no `set-api-key` -- all 5 providers are already configured in codexbar; a piped
`set-api-key` from an earlier version once corrupted a working stored key). If you're tempted to do any of
those to fill a gap, stop: fix it inside codexbar instead (see `references/data-sources.md`). The script:

1. Installs `codexbar` via Homebrew if missing (the only mutation it ever performs, and only when absent).
2. Fetches `codexbar usage --provider <x> --json` for each requested harness **in parallel** -- read-only.
3. Renders the report: each returned window (`primary`/`secondary`/`tertiary`, or
   Antigravity's `extraRateWindows`) is classified into session / daily / weekly / monthly buckets by **actual
   window length** -- not by slot name, because codexbar's slot naming doesn't map consistently across providers
   (z.ai's `primary` is weekly; see `references/data-sources.md`).

Claude's model-specific weekly cap (what Claude Code's own `/usage` screen shows as e.g. "Current week
(Fable)") is now read directly from codexbar's Claude `tertiary` window (sourced from the claude.ai API's
`seven_day_sonnet`/`seven_day_opus` field) -- the old supplemental cmux/TUI probe is gone.

## Pacing

Every window with usage gets a pace line in codexbar's own format
(`N% in reserve/deficit | Expected M% used | Lasts until reset / Runs out in ...`):

- Tagged `[codexbar]`: codexbar's **native** pace calculation, used verbatim when present (currently Claude and
  Codex, primary+secondary windows only).
- Tagged `[computed]`: the same math reproduced by the script for providers/windows codexbar doesn't
  cover (Antigravity, GLM, Kimi, Claude's model cap): expected% = elapsed fraction of the window; deficit means
  usage is ahead of schedule; "Runs out in" projects the average rate so far to 100%.

Every window with usage also gets a **burn line** -- the steering numbers for deciding how hard to throttle:

```
burn: actual 2.6%/h avg -- safe 0.40%/h (= 9.7%/day, 2.0%/5h session)   <- weekly
burn: actual 14.4%/h avg -- safe 21.2%/h to last the window             <- session
```

- **actual %/h** = used% / hours elapsed in the window (average since window start).
- **safe %/h** = remaining% / hours until reset -- the rate that lands at exactly 0% when the reset hits.
  Weekly/monthly windows also show it per day and per 5h session (= safe/day ÷ 4.8).

The intent: weekly windows must **never** run dry early (throttle actual to ≤ safe), while a 5h session may
be spent faster than safe within reason -- comparing actual vs safe %/h shows whether you're pacing real work
across the full session or about to torch it in 2 hours.

The report ends with **two summary tables** (one per window type) with separate Actual/Recent/Safe %/h
columns, a Status column carrying the throttle factor (`OVER PACE 6.4x` = cut usage to ~1/6.4 of current to
just barely last; `EXHAUSTED` = 100% used), projected Dry-in, the **absolute local clock time** when each
session ends / weekly window resets, and a trend sparkline:

```
=== Session (5h) windows ===
  Harness      Used  Actual %/h  Recent %/h  Safe %/h  Status          Dry in  Ends at  Trend (5h)
  Codex CLI    52%   20.6        8.2         19.4      ~on pace        2h 20m  11:54    ··▂▃▅▅▆▆▇▇

=== Weekly windows ===
  Harness      Used  Actual %/h  Recent %/h  Safe %/h  Safe %/day  Status          Dry in   Resets            Trend (24h)
  Codex CLI    38%   2.6         0.9         0.40      9.7         OVER PACE 6.4x  23h 48m  Sat Jul 11 18:49  ····▂▃▄▄
```

When relaying results to the user, present these tables (or a faithful condensation) rather than re-deriving
your own -- the columns were chosen deliberately for throttling decisions.

**Execution model:** this skill runs as a forked subagent on Haiku (`context: fork`, `model: haiku`,
`effort: low` in the frontmatter) because the work is pure script execution + table relay -- no reasoning
that needs a bigger model, and the fork keeps a heavyweight session's model and context untouched when the
skill fires mid-task. Don't remove those frontmatter fields.

## Output format (required)

The fork's final message is all the calling session sees. Run the script ONCE, then reply with exactly this
structure -- each section appears exactly once, in this order, and nothing else:

```
<1-2 sentences: the single most urgent pacing risk right now>

=== Session (5h) windows ===
<that table, copied character-for-character from the script output>

=== Weekly windows ===
<that table, copied character-for-character from the script output>

<any "unavailable (...)" provider lines from the script output, verbatim -- omit this block if none>
```

No preamble ("the check has completed..."), no extra headings, no "URGENT PACING ALERTS" section, no prose
restating of what the tables already show, and never write a section or sentence twice. The tables are the
deliverable; your only added value is the 1-2 sentence risk call at the top.

## Trending (snapshot history)

Every run appends its readings to `~/.local/share/check-model-usage/history.jsonl` (one small JSONL line per
run, auto-pruned after 14 days, deduped for back-to-back reruns). That history powers two things the
single-snapshot averages cannot:

- **Recent %/h** -- burn rate measured between snapshots over the last ≤3h (needs a prior snapshot ≥10 min
  old, so it appears from the second run onwards). This is the "did my throttling work" number: Actual %/h
  is an average since the window started and stays inflated for hours after a burst, while Recent shows what
  you're burning *now*. Actual high + Recent low = burst already over, relax. Recent ≥ Actual = still
  burning, act.
- **Trend sparkline** -- used% over the trailing 24h (weekly) or 5h (session), one char per time bucket,
  `·` = no snapshot then. Steep rises show exactly when the burn happened. Snapshots only exist when the
  skill runs, so sparse dots just mean it wasn't checked -- run it more often during heavy fleet work for a
  denser picture.

Trends are matched to the same window *instance* by reset time, so they never straddle a reset. If Recent
and Trend show `-`, there's simply no prior snapshot for this window yet -- normal right after a reset or on
a machine where the skill just got installed.

A window is flagged `OVER PACE` when its projected run-dry time is before its reset. Deviations of ≤2 points
from expected are reported as `borderline` instead of screaming. All of this is an **average rate since the
window started**, computed from one snapshot -- a burst right after a reset can flag OVER PACE even if usage
settles; treat the flag as a prompt to look closer, not gospel.

## When something looks wrong

If a harness reports "unavailable", the report includes the provider's own error message. Common cases and
fixes (all fixes happen **in codexbar**, never in this script):

- Missing/invalid API key (z.ai, Kimi): re-add the key via the CodexBar app (Settings > Providers) or one
  by-hand `codexbar config set-api-key --provider <x> --api-key "..."`. This script must never write keys --
  its earlier piped `set-api-key --stdin` step is exactly what corrupted a working Kimi key once (see
  `references/data-sources.md`).
- Rate-limited Claude usage endpoint from polling too frequently: wait a few minutes and rerun.
- Empty transient responses: the script already retries these once automatically.

For anything else, read `references/data-sources.md` first: it documents the exact codexbar JSON shapes this
was built against and how to debug codexbar itself. Do not fall back to driving TUIs or hitting provider APIs
directly, and do not add config writes back to the script.
