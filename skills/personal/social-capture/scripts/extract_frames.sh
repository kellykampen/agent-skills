#!/usr/bin/env bash
# extract_frames.sh — extract JPG frames from a video for visual analysis.
#
# Usage:
#   extract_frames.sh <video_path> [options]
#
# Options:
#   --max-frames N        target ~N frames (auto-calculates fps from duration)
#   --fps F               fixed frames per second (overrides --max-frames)
#   --scene-threshold T   scene-change detection (0.0-1.0, lower = more sensitive)
#   --width W             output width in px (default 1280, height auto-scaled)
#   --quality Q           (unused — output is lossless PNG)
#   --output-dir D        output directory (default: mktemp -d)
#   -h, --help            show this help
#
# Output: prints a JSON object on stdout with output_dir, frames[], frame_count,
# video_duration_seconds, and the chosen strategy. Errors print JSON on stderr
# and exit 1.

set -euo pipefail

print_help() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; }

err_json() {
  printf '{"error": "%s"}\n' "$1" >&2
  exit 1
}

VIDEO_PATH=""
MAX_FRAMES=""
FPS=""
SCENE_THRESHOLD=""
WIDTH="1280"
QUALITY="4"
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-frames) MAX_FRAMES="${2:-}"; shift 2 ;;
    --fps) FPS="${2:-}"; shift 2 ;;
    --scene-threshold) SCENE_THRESHOLD="${2:-}"; shift 2 ;;
    --width) WIDTH="${2:-}"; shift 2 ;;
    --quality) QUALITY="${2:-}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    --) shift; VIDEO_PATH="${1:-}"; shift || true ;;
    -*) err_json "unknown flag: $1" ;;
    *) VIDEO_PATH="$1"; shift ;;
  esac
done

[[ -z "$VIDEO_PATH" ]] && err_json "missing video path; usage: extract_frames.sh <video> [options]"
command -v ffmpeg  >/dev/null 2>&1 || err_json "ffmpeg not found on PATH (install: 'brew install ffmpeg' on macOS)"
command -v ffprobe >/dev/null 2>&1 || err_json "ffprobe not found on PATH (ships with ffmpeg)"
[[ -f "$VIDEO_PATH" ]] || err_json "video file not found: $VIDEO_PATH"

# Filename safety: copy to a path with no spaces / colons / unicode quirks.
# This avoids shell-escaping issues that have repeatedly bitten ad-hoc ffmpeg invocations.
EXT="${VIDEO_PATH##*.}"
SAFE_PATH="$(mktemp -t watch-video).${EXT}"
cp "$VIDEO_PATH" "$SAFE_PATH"
trap 'rm -f "$SAFE_PATH"' EXIT

DURATION_RAW="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$SAFE_PATH" || echo "0")"
DURATION="$(awk -v d="$DURATION_RAW" 'BEGIN { printf "%.2f", d+0 }')"
DURATION_INT="${DURATION%.*}"
[[ "$DURATION_INT" -le 0 ]] && err_json "could not read video duration (corrupt or unsupported codec?)"

if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$(mktemp -d -t watch-video-frames)"
fi
mkdir -p "$OUTPUT_DIR"

# Pick extraction strategy. Precedence: --scene-threshold > --fps > --max-frames > auto.
STRATEGY=""
VF=""
EFFECTIVE_FPS=""

if [[ -n "$SCENE_THRESHOLD" ]]; then
  STRATEGY="scene"
  # eq(n,0) guarantees the first frame is always included, even if no scene changes are detected.
  VF="select='eq(n,0)+gt(scene,${SCENE_THRESHOLD})',scale=${WIDTH}:-2"
elif [[ -n "$FPS" ]]; then
  STRATEGY="fps"
  EFFECTIVE_FPS="$FPS"
  VF="fps=${FPS},scale=${WIDTH}:-2"
elif [[ -n "$MAX_FRAMES" ]]; then
  STRATEGY="max_frames"
  EFFECTIVE_FPS="$(awk -v n="$MAX_FRAMES" -v d="$DURATION" 'BEGIN { f = n / d; if (f > 30) f = 30; printf "%.6f", f }')"
  VF="fps=${EFFECTIVE_FPS},scale=${WIDTH}:-2"
else
  STRATEGY="auto"
  # Adaptive: aim for 8-25 frames depending on duration.
  EFFECTIVE_FPS="$(awk -v d="$DURATION" 'BEGIN {
    if (d <= 10)        f = 1.0;
    else if (d <= 30)   f = 0.5;
    else if (d <= 60)   f = 0.333;
    else if (d <= 120)  f = 0.2;
    else if (d <= 300)  f = 0.125;
    else                f = 0.0667;
    printf "%.4f", f
  }')"
  VF="fps=${EFFECTIVE_FPS},scale=${WIDTH}:-2"
fi

# Run ffmpeg. -vsync vfr keeps scene-detection from duplicating frames.
ffmpeg -y -hide_banner -loglevel error \
  -i "$SAFE_PATH" \
  -vf "$VF" \
  -vsync vfr \
  "$OUTPUT_DIR/frame_%03d.png" \
  || err_json "ffmpeg extraction failed"

# Collect frames.
FRAMES=()
shopt -s nullglob
for f in "$OUTPUT_DIR"/frame_*.png; do
  FRAMES+=("$f")
done
shopt -u nullglob
COUNT="${#FRAMES[@]}"

[[ "$COUNT" -eq 0 ]] && err_json "no frames extracted (filter may have rejected all frames)"

# Get output resolution from the first frame.
RES_W=0; RES_H=0
if [[ "$COUNT" -gt 0 ]]; then
  RES_W="$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of default=noprint_wrappers=1:nokey=1 "${FRAMES[0]}" 2>/dev/null || echo 0)"
  RES_H="$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "${FRAMES[0]}" 2>/dev/null || echo 0)"
fi

# Emit JSON. Paths are quoted; we rely on mktemp output not containing quotes.
{
  printf '{\n'
  printf '  "output_dir": "%s",\n' "$OUTPUT_DIR"
  printf '  "video_duration_seconds": %s,\n' "$DURATION"
  printf '  "strategy": "%s",\n' "$STRATEGY"
  printf '  "effective_fps": %s,\n' "${EFFECTIVE_FPS:-null}"
  printf '  "frame_width": %s,\n' "${RES_W:-0}"
  printf '  "frame_height": %s,\n' "${RES_H:-0}"
  printf '  "frame_count": %s,\n' "$COUNT"
  printf '  "frames": [\n'
  for i in "${!FRAMES[@]}"; do
    if [[ $i -lt $((COUNT - 1)) ]]; then
      printf '    "%s",\n' "${FRAMES[$i]}"
    else
      printf '    "%s"\n' "${FRAMES[$i]}"
    fi
  done
  printf '  ]\n'
  printf '}\n'
}
