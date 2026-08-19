#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-data/raw/chineseeeg}"
RUN="${2:-1}"

if [[ ! -d "$DATASET/.git" ]]; then
  echo "Not an OpenNeuro/DataLad checkout: $DATASET" >&2
  exit 1
fi

TEXT="derivatives/novels/segmented_novel/LittlePrince/segmented_Chinense_novel_run_${RUN}.xlsx"
DISPLAY="derivatives/novels/segmented_novel/LittlePrince/segmented_Chinense_novel_run_${RUN}_display.xlsx"
EMBED="derivatives/text_embeddings/LittlePrince_text_embedding/text_embedding_run_${RUN}.npy"
FILES=("$TEXT" "$DISPLAY" "$EMBED")

echo "ChineseEEG text/alignment pilot"
echo "Dataset: $DATASET"
echo "Run:     $RUN"
echo

for f in "${FILES[@]}"; do
  if ! git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    echo "Tracked file not found: $f" >&2
    exit 2
  fi
  key=$(git -C "$DATASET" annex lookupkey "$f" 2>/dev/null || true)
  if [[ -n "$key" ]]; then
    size=$(printf '%s\n' "$key" | sed -n 's/.*-s\([0-9][0-9]*\)--.*/\1/p')
    human="unknown"
    if [[ -n "$size" ]]; then
      human=$(numfmt --to=iec-i --suffix=B "$size" 2>/dev/null || echo "${size} bytes")
    fi
    if [[ -e "$DATASET/$f" ]]; then
      local_state="yes"
    else
      local_state="no"
    fi
    echo "$f [$human, local=$local_state]"
  else
    echo "$f [not annex-backed]"
  fi
done

echo
read -r -p "Retrieve text, display, and author embedding for run ${RUN}? [y/N] " reply
case "$reply" in
  y|Y|yes|YES)
    for f in "${FILES[@]}"; do
      echo "Retrieving $f"
      git -C "$DATASET" annex get -- "$f" 2>/dev/null || true
      if [[ ! -e "$DATASET/$f" ]]; then
        echo "FAILED to materialize: $f" >&2
        exit 3
      fi
    done
    ;;
  *)
    echo "Nothing retrieved."
    exit 0
    ;;
esac

echo
for f in "${FILES[@]}"; do
  if [[ -e "$DATASET/$f" ]]; then
    echo "PRESENT: $f ($(du -h "$DATASET/$f" | awk '{print $1}'))"
  else
    echo "MISSING: $f"
  fi
done
