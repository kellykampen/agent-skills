#!/usr/bin/env bash
# cmux-send-verified.sh — send a message to a cmux surface and VERIFY it actually submitted.
#
# Why this exists: raw `cmux send` + `send-key Enter` can silently leave the message sitting
# unsubmitted in the pane's input line (TUI focus quirks, palettes, timing). An unsubmitted
# directive looks sent but never runs — the field-tested failure mode this script closes.
#
# Usage:
#   cmux-send-verified.sh [--flush] <surface-ref> "<message>"
#     <surface-ref>  e.g. surface:85 or 85 (whatever your cmux accepts)
#     --flush        clear a stale input draft first via ctrl+c. OFF by default: ctrl+c on a
#                    BUSY agent aborts its current turn — only flush when you know the pane is
#                    idle and holds a stray draft.
#
# Exit codes: 0 = submitted (or queued behind a busy turn, which is normal); 1 = could not
# verify submission — the capture is printed so you can see what's stuck.
set -uo pipefail

CMUX="${CMUX_BIN:-}"
if [[ -z "$CMUX" ]]; then
  CMUX="$(command -v cmux || true)"
fi
if [[ -z "$CMUX" ]]; then
  for c in "$HOME/Applications/cmux.app/Contents/Resources/bin/cmux" \
           "/Applications/cmux.app/Contents/Resources/bin/cmux"; do
    [[ -x "$c" ]] && CMUX="$c" && break
  done
fi
if [[ -z "$CMUX" ]]; then
  echo "FAIL: cmux binary not found (set CMUX_BIN)" >&2
  exit 1
fi

FLUSH=0
if [[ "${1:-}" == "--flush" ]]; then
  FLUSH=1
  shift
fi

if [[ $# -lt 2 ]]; then
  echo "usage: cmux-send-verified.sh [--flush] <surface-ref> \"<message>\"" >&2
  exit 1
fi

SURFACE="$1"
shift
MSG="$*"
# A distinctive snippet from the head of the message, for detecting it stuck in the input line.
SNIPPET="${MSG:0:40}"

# Claude Code's spinner glyphs (✻ ✶ ✢ ✽ and friends) precede every "<verb>ing… (Ns)" busy
# line while a turn is actively running. Their presence is positive proof the message was
# submitted and picked up — far more reliable than looking for the message text itself, which
# either scrolls out of a short capture window or gets collapsed into a "[Pasted text #N]"
# placeholder that never matches a raw-text snippet.
SPINNER_RE='[✻✶✢✽✳]'

if [[ $FLUSH -eq 1 ]]; then
  "$CMUX" send-key --surface "$SURFACE" ctrl+c >/dev/null 2>&1 || true
  sleep 0.5
fi

"$CMUX" send --surface "$SURFACE" "$MSG" || { echo "FAIL: cmux send errored" >&2; exit 1; }
"$CMUX" send-key --surface "$SURFACE" Enter || { echo "FAIL: cmux send-key errored" >&2; exit 1; }

# Verify submission. Two independent signals, checked in order:
#   1. Positive evidence of processing (a spinner glyph, or a "queued" marker for a busy pane)
#      -> success immediately, regardless of any stray echoed text elsewhere in the capture.
#   2. Otherwise, search the WHOLE capture (not just the last few lines — long/wrapped messages
#      routinely scroll past a narrow tail) for the raw snippet OR a "[Pasted text #N]"
#      placeholder, either of which means the draft is still sitting unsubmitted -> retry Enter.
#   3. If neither signal fires, the turn most likely already completed (fast, short reply)
#      before this check ran -> treat as success.
CAP=""
for attempt in 1 2 3; do
  sleep 2
  CAP="$("$CMUX" capture-pane --surface "$SURFACE" --lines 30 2>/dev/null || true)"
  if [[ -z "$CAP" ]]; then
    # Pane mid-render/unreadable; try a smaller capture once more.
    CAP="$("$CMUX" capture-pane --surface "$SURFACE" --lines 6 2>/dev/null || true)"
  fi
  if printf '%s' "$CAP" | grep -qi 'queued'; then
    echo "OK: queued on $SURFACE (agent busy; will process at end of its turn)"
    exit 0
  fi
  if printf '%s' "$CAP" | grep -qE "$SPINNER_RE"; then
    echo "OK: sent to $SURFACE (confirmed processing)"
    exit 0
  fi
  if printf '%s' "$CAP" | grep -qF -- "$SNIPPET" || printf '%s' "$CAP" | grep -qF '[Pasted text #'; then
    # Draft still visible somewhere in the pane with no processing signal — nudge submit again.
    "$CMUX" send-key --surface "$SURFACE" Enter >/dev/null 2>&1 || true
    continue
  fi
  echo "OK: sent to $SURFACE"
  exit 0
done

echo "FAIL: message may be unsubmitted on $SURFACE — last capture:" >&2
printf '%s\n' "$CAP" >&2
exit 1
