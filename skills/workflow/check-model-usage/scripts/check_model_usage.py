#!/usr/bin/env python3
"""Check quota/usage + session & weekly pacing across configured AI coding
harnesses/providers (Claude Code, Codex CLI/OpenAI, Antigravity, GLM/Z.ai,
Kimi/Moonshot, and optional CodexBar-visible OpenRouter/xAI pools).

Usage: python3 check_model_usage.py [--only=claude,codex,agy,glm,kimi,...]
       Aliases: agy=antigravity, glm=zai, grok=xai. Default: core harnesses.

Single data source: the CodexBar CLI (https://github.com/steipete/CodexBar).
This script fetches `codexbar usage --provider <x> --json` for each requested
harness in parallel and formats the result -- it never opens cmux panes,
never drives any harness TUI, never calls provider APIs directly, and is
strictly READ-ONLY against codexbar (no `config enable`, no `set-api-key`;
provider credentials are codexbar's state, configured once via its app -- an
earlier version that pushed keys on every run corrupted a working one).

See ../references/data-sources.md for the JSON shapes this parses and every
assumption baked into the pacing math.
"""

import json
import math
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Snapshot history lives OUTSIDE the skill directory (skill dirs are content,
# not mutable state). One JSONL line per run; auto-pruned. This is what powers
# the "recent" velocity + trend sparklines -- without it every rate is just an
# average since the window started and can't show whether throttling worked.
HISTORY_PATH = Path.home() / ".local" / "share" / "check-model-usage" / "history.jsonl"
HISTORY_RETENTION_DAYS = 14
SPARK_CHARS = "▁▂▃▄▅▆▇█"

SESSIONS_PER_DAY = 4.8  # 24h / 5h session length

DISPLAY_NAMES = {
    "claude": "Claude Code",
    "codex": "Codex CLI",
    "antigravity": "Antigravity (agy)",
    "gemini": "Gemini CLI",
    "zai": "GLM / Z.ai",
    "kimi": "Kimi / Moonshot",
    "openrouter": "OpenRouter",
    "xai": "xAI / Grok",
    "grok": "xAI / Grok",
}
PROVIDER_ORDER = ["claude", "codex", "antigravity", "gemini", "zai", "kimi", "openrouter", "xai", "grok"]

# Gemini's three slots carry no labels in JSON; codexbar's own text output
# labels them Pro / Flash / Flash Lite in slot order.
GEMINI_SLOT_LABELS = {"primary": "Pro (daily)", "secondary": "Flash (daily)", "tertiary": "Flash Lite (daily)"}


def parse_iso(s):
    if not s:
        return None
    s = re.sub(r"\.\d+", "", s).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def human_duration(minutes):
    if minutes is None or minutes < 0:
        return "?"
    m = int(round(minutes))
    d, m = divmod(m, 1440)
    h, m = divmod(m, 60)
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def classify(window_minutes, reset_desc, mins_left):
    """Bucket a window as session/daily/weekly/monthly by actual length.

    codexbar's primary/secondary/tertiary slot names do NOT consistently mean
    session/weekly across providers (z.ai's primary is weekly), so length is
    the only safe classifier.
    """
    if window_minutes:
        if window_minutes <= 360:
            return "session"
        if window_minutes <= 1500:
            return "daily"
        if window_minutes <= 20000:
            return "weekly"
        return "monthly"
    desc = (reset_desc or "").lower()
    if "5 hour" in desc or "5-hour" in desc:
        return "session"
    if "week" in desc:
        return "weekly"
    if "month" in desc:
        return "monthly"
    if mins_left is not None:
        if mins_left <= 12 * 60:
            return "session"
        if mins_left <= 240 * 60:
            return "weekly"
        return "monthly"
    return "weekly"  # documented default; see data-sources.md


ASSUMED_MINUTES = {"session": 300, "daily": 1440, "weekly": 10080, "monthly": 43200}
BUCKET_LABELS = {"session": "Session (5h)", "daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}


def compute_pace(used, window_minutes, mins_left):
    """Same semantics as codexbar's native pace object:
      expected%  = fraction of the window already elapsed * 100
      delta      = used - expected  (positive = deficit / burning too fast)
      runs out   = ETA to 100% at the average rate so far
    Returns dict with keys mirroring codexbar's pace, or None if uncomputable.
    """
    if used is None or mins_left is None or window_minutes is None:
        return None
    elapsed = max(window_minutes - mins_left, 0.01)
    expected = min(elapsed / window_minutes * 100.0, 100.0)
    delta = used - expected
    if used <= 0:
        return {
            "deltaPercent": round(delta),
            "expectedUsedPercent": round(expected),
            "willLastToReset": True,
            "summary": f"fresh quota, 0% used | Expected {round(expected)}% used | Lasts until reset",
        }
    rate = used / elapsed  # % per minute, average since window start
    mins_to_dry = (100.0 - used) / rate if rate > 0 else math.inf
    will_last = mins_to_dry >= mins_left
    if will_last:
        tail = "Lasts until reset"
    else:
        tail = f"Runs out in {human_duration(mins_to_dry)}"
    word = "in reserve" if delta <= 0 else "in deficit"
    return {
        "deltaPercent": round(delta),
        "expectedUsedPercent": round(expected),
        "willLastToReset": will_last,
        "etaSeconds": None if math.isinf(mins_to_dry) else int(mins_to_dry * 60),
        "summary": f"{abs(round(delta))}% {word} | Expected {round(expected)}% used | {tail}",
    }


def burn_rates(w):
    """Actual vs sustainable burn rates for one window, in %/hour.

    actual  = used% / hours elapsed in the window (average since window start)
    safe    = remaining% / hours until reset (lands at exactly 0% at reset)
    ratio   = actual / safe -- the throttle factor: >1 means slow down by that
              multiple to just barely last; <1 means headroom.

    These are the steering numbers: weekly windows must never run dry early
    (throttle to <= safe), while a session window can be spent faster than
    safe within reason -- the actual %/h tells you if you're on track to
    torch it in 2 hours vs pacing real work across the full 5.
    """
    used = w.get("used")
    mins_left = w.get("mins_left")
    wm = w.get("window_minutes")
    if used is None or used <= 0 or not mins_left or mins_left <= 0 or not wm:
        return None
    elapsed_h = max((wm - mins_left) / 60.0, 0.02)
    hours_left = mins_left / 60.0
    remaining = max(100.0 - used, 0.0)
    actual_h = used / elapsed_h
    safe_h = remaining / hours_left
    ratio = (actual_h / safe_h) if safe_h > 0 else math.inf
    return {"actual_h": actual_h, "safe_h": safe_h, "ratio": ratio, "remaining": remaining}


def fmt_rate(x):
    return f"{x:.2f}" if x < 1 else f"{x:.1f}"


def format_burn_line(bucket, r):
    if r["remaining"] <= 0:
        return f"actual {fmt_rate(r['actual_h'])}%/h avg -- quota exhausted"
    if bucket in ("weekly", "monthly"):
        safe_day = r["safe_h"] * 24.0
        return (
            f"actual {fmt_rate(r['actual_h'])}%/h avg -- safe {fmt_rate(r['safe_h'])}%/h "
            f"(= {safe_day:.1f}%/day, {safe_day / SESSIONS_PER_DAY:.1f}%/5h session)"
        )
    return f"actual {fmt_rate(r['actual_h'])}%/h avg -- safe {fmt_rate(r['safe_h'])}%/h to last the window"


def verdict_of(used, pace):
    if used is not None and used <= 0:
        return "fresh"
    if pace is None:
        return "unknown"
    if pace.get("willLastToReset"):
        return "ok"
    # Dead-on pace can mathematically "run out" seconds before the reset;
    # don't scream OVER PACE for a <=2 point deviation from expected.
    if abs(pace.get("deltaPercent") or 0) <= 2:
        return "borderline"
    return "OVER PACE"


def mins_until(reset_iso, now):
    dt = parse_iso(reset_iso)
    if dt is None:
        return None
    return (dt - now).total_seconds() / 60.0


def collect_windows(entry, now):
    """Normalize one codexbar provider entry into a list of window dicts:
    {label, bucket, used, mins_left, window_minutes, pace, pace_native, detail}
    """
    provider = entry.get("provider", "?")
    usage = entry.get("usage") or {}
    native_pace = entry.get("pace") or {}
    windows = []

    # Antigravity tracks two independent pools; the generic slots only carry
    # the "most constrained" one. extraRateWindows has the full breakdown.
    extra = usage.get("extraRateWindows") or []
    if provider == "antigravity" and extra:
        for w in extra:
            win = w.get("window") or {}
            wid = w.get("id", "")
            title = w.get("title")
            if not title:
                pool = "Gemini pool" if "gemini" in wid else "Claude/GPT pool"
                kind = "5h" if wid.endswith("-5h") else "weekly"
                title = f"{pool} {kind}"
            windows.append(_make_window(title, win, None, now))
        return windows

    # Claude's model-specific weekly cap (tertiary) omits resetsAt in JSON but
    # resets together with the all-models weekly window -- inherit its reset so
    # pacing can be computed for it too.
    if provider == "claude":
        tert = usage.get("tertiary")
        if tert and not tert.get("resetsAt"):
            for slot in ("secondary", "primary"):
                other = usage.get(slot) or {}
                if other.get("resetsAt") and classify(
                    other.get("windowMinutes"), other.get("resetDescription"), mins_until(other["resetsAt"], now)
                ) == "weekly":
                    tert["resetsAt"] = other["resetsAt"]
                    break

    seen_weekly = 0
    for slot in ("primary", "secondary", "tertiary"):
        win = usage.get(slot)
        if not win or win.get("usedPercent") is None:
            continue
        mins_left = mins_until(win.get("resetsAt"), now)
        bucket = classify(win.get("windowMinutes"), win.get("resetDescription"), mins_left)
        if provider == "gemini":
            label = GEMINI_SLOT_LABELS.get(slot, slot)
        elif provider == "claude" and slot == "tertiary" and bucket == "weekly":
            # claude.ai API's seven_day_sonnet / seven_day_opus: the
            # model-specific weekly cap (the window Claude Code's own /usage
            # screen shows as e.g. "Current week (Fable)").
            label = "Weekly (model-specific cap)"
        else:
            label = BUCKET_LABELS[bucket]
            if bucket == "weekly":
                seen_weekly += 1
                if seen_weekly > 1:
                    label = f"Weekly ({slot})"
        windows.append(_make_window(label, win, native_pace.get(slot), now, bucket))
    return windows


def _make_window(label, win, pace_native, now, bucket=None):
    used = win.get("usedPercent")
    mins_left = mins_until(win.get("resetsAt"), now)
    wm = win.get("windowMinutes")
    if bucket is None:
        bucket = classify(wm, win.get("resetDescription"), mins_left)
    if not wm:
        wm = ASSUMED_MINUTES[bucket]
        assumed = True
    else:
        assumed = False
    pace = None
    source = None
    if pace_native and pace_native.get("summary"):
        pace = pace_native
        source = "codexbar"
    else:
        pace = compute_pace(used, wm, mins_left)
        source = "computed" + (" (assumed window length)" if assumed else "")
    return {
        "label": label,
        "bucket": bucket,
        "used": used,
        "mins_left": mins_left,
        "window_minutes": wm,
        "resets_at": parse_iso(win.get("resetsAt")),
        "pace": pace,
        "pace_source": source,
        "detail": win.get("resetDescription") or "",
    }


def render_provider(entry, now, lines, summary, history, snapshot):
    provider = entry.get("provider", "?")
    name = DISPLAY_NAMES.get(provider, provider)
    lines.append(f"-- {name} --")

    err = entry.get("error")
    usage = entry.get("usage")
    if err or not usage:
        if isinstance(err, dict):
            detail = err.get("message") or json.dumps(err)
        else:
            detail = err or "no usage data returned"
        lines.append(f"  unavailable ({detail})")
        lines.append("")
        summary.append((name, None))
        return

    ident = usage.get("identity") or {}
    account = ident.get("accountEmail") or usage.get("accountEmail") or ""
    plan = ident.get("loginMethod") or usage.get("loginMethod") or ""
    meta = " | ".join(x for x in (account, f"plan: {plan}" if plan else "", f"source: {entry.get('source', '?')}") if x)
    if meta:
        lines.append(f"  [{meta}]")

    windows = collect_windows(entry, now)
    if not windows:
        lines.append("  no rate windows reported (likely a transient provider hiccup -- rerun in a minute)")
        lines.append("")
        summary.append((name, None))
        return

    verdicts = []
    width = max(len(w["label"]) for w in windows) + 1
    for w in windows:
        used = w["used"]
        used_s = f"{used:.1f}".rstrip("0").rstrip(".") if isinstance(used, float) else str(used)
        reset_s = f"resets in {human_duration(w['mins_left'])}" if w["mins_left"] is not None else "reset time unknown"
        lines.append(f"  {w['label'] + ':':<{width}} {used_s}% used | {reset_s}")
        v = verdict_of(used, w["pace"])
        if w["pace"] and used is not None and used > 0:
            flag = "  << OVER PACE" if v == "OVER PACE" else ""
            lines.append(f"    pace: {w['pace']['summary']}{flag}  [{w['pace_source']}]")
        pts = window_points(history, provider, w["label"], w["resets_at"])
        w["recent"] = recent_velocity(pts, used, now)
        if pts:
            span_h = 24.0 if w["bucket"] in ("weekly", "monthly") else (w["window_minutes"] or 300) / 60.0
            w["spark"] = sparkline(pts, used, now, span_h, buckets=10 if span_h <= 6 else 8)
        rates = burn_rates(w)
        if rates:
            w["rates"] = rates
            burn = format_burn_line(w["bucket"], rates)
            if w["recent"]:
                burn += f" | recent {fmt_rate(max(w['recent']['rate'], 0))}%/h (last {w['recent']['span_h']:.1f}h)"
            lines.append(f"    burn: {burn}")
        snapshot.append((provider, w))
        verdicts.append((w["label"], w["bucket"], v, w))
    lines.append("")
    summary.append((name, verdicts))


def load_history():
    records = []
    try:
        for line in HISTORY_PATH.read_text().splitlines():
            try:
                rec = json.loads(line)
                rec["_ts"] = parse_iso(rec["ts"])
                if rec["_ts"]:
                    records.append(rec)
            except (json.JSONDecodeError, KeyError):
                continue
    except OSError:
        pass
    return sorted(records, key=lambda r: r["_ts"])


def save_history(records, snapshot_windows, now):
    """Append this run's readings, pruning anything past retention. Skip the
    append if the last record is <60s old (back-to-back reruns would just add
    noise points)."""
    if records and (now - records[-1]["_ts"]).total_seconds() < 60:
        return
    cutoff = now - timedelta(days=HISTORY_RETENTION_DAYS)
    kept = [r for r in records if r["_ts"] >= cutoff]
    new = {
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "windows": [
            {
                "provider": p,
                "label": w["label"],
                "bucket": w["bucket"],
                "used": w["used"],
                "resets_at": w["resets_at"].strftime("%Y-%m-%dT%H:%M:%SZ") if w["resets_at"] else None,
            }
            for p, w in snapshot_windows
            if w["used"] is not None
        ],
    }
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({k: v for k, v in r.items() if k != "_ts"}) for r in kept]
    lines.append(json.dumps(new))
    HISTORY_PATH.write_text("\n".join(lines) + "\n")


def same_window_instance(iso, resets_at):
    """Two readings belong to the same window instance when their reset times
    agree (20-min tolerance for provider-side jitter). Trends must never
    straddle a reset -- used% drops to 0 there and a naive delta goes negative
    or, worse, silently wrong."""
    if not iso or not resets_at:
        return False
    dt = parse_iso(iso)
    return dt is not None and abs((dt - resets_at).total_seconds()) < 1200


def window_points(history, provider, label, resets_at):
    """(timestamp, used%) readings of this exact window instance, oldest first."""
    pts = []
    for rec in history:
        for wr in rec.get("windows", []):
            if wr.get("provider") == provider and wr.get("label") == label \
                    and same_window_instance(wr.get("resets_at"), resets_at):
                pts.append((rec["_ts"], wr.get("used")))
    return [(t, u) for t, u in pts if u is not None]


def recent_velocity(pts, used_now, now):
    """Burn rate over the recent past (%/h), from the oldest snapshot within
    the last 3h that is at least 10 minutes old -- recent enough to reflect
    current behavior, spaced enough to not amplify rounding noise. This is the
    'did my throttling work' number the since-window-start average can't give."""
    candidates = [(t, u) for t, u in pts
                  if 600 <= (now - t).total_seconds() <= 3 * 3600]
    if not candidates or used_now is None:
        return None
    t0, u0 = candidates[0]
    span_h = (now - t0).total_seconds() / 3600.0
    return {"rate": (used_now - u0) / span_h, "span_h": span_h}


def sparkline(pts, used_now, now, span_hours, buckets=8):
    """Used% over the trailing span_hours, one char per time bucket (max
    reading in the bucket, scaled 0-100). '·' = no snapshot in that bucket.
    Rendered left=oldest; steep rises show exactly when the burn happened."""
    all_pts = pts + [(now, used_now)] if used_now is not None else pts
    cells = ["·"] * buckets
    start = now - timedelta(hours=span_hours)
    bucket_s = span_hours * 3600 / buckets
    for t, u in all_pts:
        off = (t - start).total_seconds()
        if off < 0:
            continue
        i = min(buckets - 1, int(off / bucket_s))
        level = SPARK_CHARS[min(len(SPARK_CHARS) - 1, int(max(u, 0) / 100.0 * len(SPARK_CHARS)))]
        if cells[i] == "·" or level > cells[i]:
            cells[i] = level
    return "".join(cells)


def local_time(dt, now):
    """Absolute local clock time for a reset: '14:10' today, 'Sat 14:10'
    within a week, 'Jul 11 14:10' beyond."""
    if dt is None:
        return "?"
    loc = dt.astimezone()
    nloc = now.astimezone()
    if loc.date() == nloc.date():
        return loc.strftime("%H:%M")
    if (loc - nloc).days < 2:
        return loc.strftime("%a %H:%M")
    return loc.strftime("%a %b %d %H:%M")


def row_name(provider_name, label):
    """Provider name plus whatever the window label adds beyond its bucket
    (pool name, model cap, ...) so multi-pool providers stay distinct rows."""
    qual = label
    for tok in ("Session (5h)", "5-hour", "Weekly", "weekly", "Daily", "Monthly", "5h"):
        qual = qual.replace(tok, "")
    qual = qual.strip(" -")
    if qual.startswith("(") and qual.endswith(")"):
        qual = qual[1:-1]
    return f"{provider_name} [{qual}]" if qual else provider_name


def format_table(headers, rows, lines):
    widths = [max(len(headers[i]), max((len(r[i]) for r in rows), default=0)) for i in range(len(headers))]
    lines.append("  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    lines.append("  " + "  ".join("-" * w for w in widths))
    for r in rows:
        lines.append("  " + "  ".join(r[i].ljust(widths[i]) for i in range(len(r))))


def table_cells(name, w, v, now, weekly):
    used = w["used"]
    used_s = (f"{used:.1f}".rstrip("0").rstrip(".") if isinstance(used, float) else str(used)) + "%"
    mins_left = w["mins_left"]
    hours_left = mins_left / 60.0 if mins_left and mins_left > 0 else None
    elapsed_h = max((w["window_minutes"] - mins_left) / 60.0, 0.02) if mins_left is not None else None
    actual = fmt_rate(used / elapsed_h) if used and elapsed_h else "-"
    safe = fmt_rate((100.0 - used) / hours_left) if hours_left and used is not None and used < 100 else ("0" if used is not None and used >= 100 else "-")
    if used is not None and used >= 100:
        status = "EXHAUSTED"
    elif v == "OVER PACE":
        r = w.get("rates")
        status = f"OVER PACE {r['ratio']:.1f}x" if r and math.isfinite(r["ratio"]) else "OVER PACE"
    elif v == "borderline":
        status = "~on pace"
    else:
        status = v
    eta = w["pace"].get("etaSeconds") if w["pace"] else None
    dry = human_duration(eta / 60) if eta and v in ("OVER PACE", "borderline") else "-"
    reset_t = local_time(w["resets_at"], now)
    recent = fmt_rate(max(w["recent"]["rate"], 0)) if w.get("recent") else "-"
    spark = w.get("spark") or "-"
    if weekly:
        safe_day = fmt_rate((100.0 - used) / hours_left * 24) if hours_left and used is not None and used < 100 else "-"
        return [name, used_s, actual, recent, safe, safe_day, status, dry, reset_t, spark]
    return [name, used_s, actual, recent, safe, status, dry, reset_t, spark]


def render_summary(summary, lines, now):
    session_rows, weekly_rows, unavailable = [], [], []
    for name, verdicts in summary:
        if verdicts is None:
            unavailable.append(name)
            continue
        for label, bucket, v, w in verdicts:
            if bucket == "session":
                session_rows.append(table_cells(row_name(name, label), w, v, now, weekly=False))
            elif bucket == "weekly":
                weekly_rows.append(table_cells(row_name(name, label), w, v, now, weekly=True))

    lines.append("=== Session (5h) windows ===")
    if session_rows:
        format_table(
            ["Harness", "Used", "Actual %/h", "Recent %/h", "Safe %/h", "Status", "Dry in", "Ends at", "Trend (5h)"],
            session_rows, lines)
    lines.append("")
    lines.append("=== Weekly windows ===")
    if weekly_rows:
        format_table(
            ["Harness", "Used", "Actual %/h", "Recent %/h", "Safe %/h", "Safe %/day", "Status", "Dry in", "Resets", "Trend (24h)"],
            weekly_rows, lines)
    if unavailable:
        lines.append("")
        lines.append("  Unavailable: " + ", ".join(unavailable))
    lines.append("")
    lines.append(
        "Note: pace/burn figures are average-rate-since-window-start from one snapshot, not a live velocity --"
    )
    lines.append(
        "a burst right after a reset can flag OVER PACE even if usage settles; treat it as a prompt to look closer."
    )


DEFAULT_PROVIDERS = ["claude", "codex", "antigravity", "zai", "kimi"]
# OpenRouter/xAI/Grok are opt-in because CodexBar installations may not expose
# those provider IDs yet. Use --only=openrouter,xai or --only=grok to probe them.
ALIASES = {"agy": "antigravity", "glm": "zai", "grok": "xai"}


def parse_args(argv):
    providers = DEFAULT_PROVIDERS
    for arg in argv:
        if arg in ("--help", "-h"):
            print("Usage: check_model_usage.py [--only=claude,codex,agy,glm,kimi,openrouter,xai,...]")
            print("Aliases: agy=antigravity, glm=zai, grok=xai. Default: core harnesses.")
            sys.exit(0)
        if arg.startswith("--only="):
            only = arg[len("--only="):]
            if only and only != "all":
                providers = [ALIASES.get(p.strip(), p.strip()) for p in only.split(",") if p.strip()]
    return providers


def ensure_codexbar():
    if shutil.which("codexbar"):
        return True
    print("codexbar CLI not found -- installing via 'brew install steipete/tap/codexbar'...", file=sys.stderr)
    subprocess.run(["brew", "install", "steipete/tap/codexbar"], capture_output=True)
    return shutil.which("codexbar") is not None


def fetch_provider(provider):
    """One read-only `codexbar usage` call. Returns a list of provider entries
    (codexbar prints a JSON array), or a synthesized error entry."""
    try:
        proc = subprocess.run(
            ["codexbar", "usage", "--provider", provider, "--json"],
            capture_output=True, text=True, timeout=120)
        data = json.loads(proc.stdout)
        return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, subprocess.TimeoutExpired):
        return [{"provider": provider, "error": "codexbar returned no parseable JSON"}]


def has_real_data(entries):
    """True when a fetch produced usable windows or a definitive provider
    error (e.g. a bad key -- retrying won't help). False only for transient
    empty responses, which deserve one retry."""
    for e in entries:
        if e.get("error"):
            return True
        usage = e.get("usage") or {}
        slots = [usage.get(k) for k in ("primary", "secondary", "tertiary")]
        if any(s and s.get("usedPercent") is not None for s in slots) or usage.get("extraRateWindows"):
            return True
    return False


def fetch_all(providers):
    with ThreadPoolExecutor(max_workers=len(providers)) as pool:
        results = dict(zip(providers, pool.map(fetch_provider, providers)))
    # One retry pass for transient empty responses (observed live on Claude
    # when several fetches land in quick succession).
    retry = [p for p, entries in results.items() if not has_real_data(entries)]
    if retry:
        time.sleep(10)
        with ThreadPoolExecutor(max_workers=len(retry)) as pool:
            results.update(zip(retry, pool.map(fetch_provider, retry)))
    return [e for p in providers for e in results[p]]


def main():
    providers = parse_args(sys.argv[1:])
    if not ensure_codexbar():
        print("ERROR: codexbar CLI could not be installed/found. Install manually: brew install steipete/tap/codexbar", file=sys.stderr)
        sys.exit(1)

    entries = fetch_all(providers)
    entries.sort(key=lambda e: (PROVIDER_ORDER.index(e.get("provider")) if e.get("provider") in PROVIDER_ORDER else 99))
    now = datetime.now(timezone.utc)

    lines = ["=== AI Coding Harness Usage & Pacing Report ==="]
    lines.append(f"Generated: {now.astimezone().strftime('%Y-%m-%d %H:%M %Z')} | data: codexbar CLI (no TUI/harness probes, no direct API calls)")
    lines.append("")
    history = load_history()
    summary = []
    snapshot = []
    for entry in entries:
        render_provider(entry, now, lines, summary, history, snapshot)
    render_summary(summary, lines, now)
    save_history(history, snapshot, now)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
