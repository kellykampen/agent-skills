#!/usr/bin/env bash
# Converts a rendered mp4 to a palette-optimized GIF for inline README/social previews.
# Usage: make-gif.sh <input.mp4> <output.gif> [fps] [width]
#
# GOTCHA: always pass -nostdin. Without it, ffmpeg reads from the shared
# stdin — if this runs inside a `while read` loop (e.g. converting several
# videos in one script), ffmpeg silently steals characters meant for the
# loop's `read`, corrupting later filenames. Costly to debug; cheap to avoid.
set -euo pipefail

IN="${1:?Usage: make-gif.sh <input.mp4> <output.gif> [fps] [width]}"
OUT="${2:?Usage: make-gif.sh <input.mp4> <output.gif> [fps] [width]}"
FPS="${3:-14}"
WIDTH="${4:-900}"

ffmpeg -nostdin -y -i "$IN" \
  -vf "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
  -loglevel error "$OUT"

echo "✓ $OUT"
