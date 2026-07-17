#!/usr/bin/env bash
# Optimizes plotter SVGs with vpype: linemerge + linesort (+ linesimplify).
# Usage:
#   ./optimize.sh file1.svg file2.svg ...     # individual files
#   ./optimize.sh directory/                  # every .svg in the directory
# Results land in <same directory>/optimized/ with the same filename.
set -euo pipefail

MERGE_TOL="0.5mm"     # max gap merged into a single stroke
SIMPLIFY_TOL="0.05mm" # point reduction, invisible with a 0.4mm pen

# Find vpype: installed binary, else uvx (runs without installing)
if command -v vpype >/dev/null 2>&1; then
  VPYPE=(vpype)
elif command -v uvx >/dev/null 2>&1; then
  VPYPE=(uvx vpype)
else
  echo "Found neither vpype nor uvx." >&2
  echo "Install one of them:" >&2
  echo "  brew install uv          # the script then uses 'uvx vpype' automatically" >&2
  echo "  pipx install vpype       # or a permanent install" >&2
  exit 1
fi

# Collect the file list
files=()
for arg in "$@"; do
  if [[ -d "$arg" ]]; then
    while IFS= read -r f; do files+=("$f"); done \
      < <(find "$arg" -maxdepth 1 -name '*.svg' | sort)
  elif [[ -f "$arg" ]]; then
    files+=("$arg")
  else
    echo "Skipping (does not exist): $arg" >&2
  fi
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No SVG files to process. Usage: $0 <files or directory>" >&2
  exit 1
fi

for f in "${files[@]}"; do
  dir=$(dirname "$f")
  name=$(basename "$f")
  outdir="$dir/optimized"
  mkdir -p "$outdir"
  out="$outdir/$name"

  echo "── $name"
  "${VPYPE[@]}" \
    read "$f" \
    linemerge --tolerance "$MERGE_TOL" \
    linesort \
    linesimplify --tolerance "$SIMPLIFY_TOL" \
    write "$out"

  # Show the gain: pen lifts and total travel before/after
  # "Length" = drawn stroke (should be ~unchanged), "Pen-up" = travel in the air
  echo "  Before:"
  "${VPYPE[@]}" read "$f" stat 2>/dev/null | grep -E '^\s*(Length|Pen-up length|Path count)' | uniq | sed 's/^/    /' || true
  echo "  After:"
  "${VPYPE[@]}" read "$out" stat 2>/dev/null | grep -E '^\s*(Length|Pen-up length|Path count)' | uniq | sed 's/^/    /' || true
done

echo
echo "Done. Optimized files in */optimized/."
