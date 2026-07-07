#!/usr/bin/env bash
# Renders a composition to a NEW versioned file — never overwrites a previous render.
# Usage: render-version.sh <compositionId> <outputNamePrefix>
#
# GOTCHA: the version-detection glob below uses `find`, not `ls`. An `ls
# out/versions/foo-v*.mp4` on a prefix with no existing matches returns
# non-zero, and under `set -o pipefail` that aborts the WHOLE script before
# the render ever starts — silently, with no useful output. `find` returns
# empty successfully instead, so don't "simplify" this back to `ls`.
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSITION="${1:?Usage: render-version.sh <compositionId> <outputNamePrefix>}"
PREFIX="${2:?Usage: render-version.sh <compositionId> <outputNamePrefix>}"

mkdir -p out/versions
LAST=$(find out/versions -maxdepth 1 -name "${PREFIX}-v*.mp4" 2>/dev/null | sed -E "s/.*-v([0-9]+)\.mp4/\1/" | sort -n | tail -1)
NEXT=$(( ${LAST:-0} + 1 ))
OUT="out/versions/${PREFIX}-v${NEXT}.mp4"

echo "Rendering $COMPOSITION to $OUT ..."
npx remotion render "$COMPOSITION" "$OUT"
echo "✓ Saved $OUT (never overwrites — next render will be v$((NEXT + 1)))"
