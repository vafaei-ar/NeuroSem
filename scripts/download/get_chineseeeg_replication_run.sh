#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-data/raw/chineseeeg}"
RUN_NUMBER="${2:-2}"
DERIVATIVE="${3:-filtered_0.5_30}"
SESSION="ses-LittlePrince"
printf -v RUN "run-%02d" "$RUN_NUMBER"

SUBJECTS=(sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10 sub-13 sub-14 sub-15)

if [[ ! -d "$DATASET/.git" ]]; then
  echo "Not an OpenNeuro/DataLad checkout: $DATASET" >&2
  exit 1
fi

TEXT="derivatives/novels/segmented_novel/LittlePrince/segmented_Chinense_novel_run_${RUN_NUMBER}.xlsx"
AUTHOR_EMBED="derivatives/text_embeddings/LittlePrince_text_embedding/text_embedding_run_${RUN_NUMBER}.npy"

for f in "$TEXT" "$AUTHOR_EMBED"; do
  if ! git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    echo "Required alignment asset is not tracked: $f" >&2
    exit 2
  fi
done

AVAILABLE=()
FILES=("$TEXT" "$AUTHOR_EMBED")
TOTAL=0

echo "ChineseEEG targeted replication retrieval"
echo "Dataset:    $DATASET"
echo "Session:    $SESSION"
echo "Run:        $RUN ($RUN_NUMBER)"
echo "Derivative: $DERIVATIVE"
echo

for subject in "${SUBJECTS[@]}"; do
  prefix="derivatives/${DERIVATIVE}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${RUN}"
  found=0
  subject_files=()
  for ext in eeg vhdr vmrk; do
    f="${prefix}_eeg.${ext}"
    if git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      found=$((found + 1))
      subject_files+=("$f")
    fi
  done
  events="${prefix}_events.tsv"
  if [[ $found -eq 3 ]] && git -C "$DATASET" ls-files --error-unmatch "$events" >/dev/null 2>&1; then
    AVAILABLE+=("$subject")
    FILES+=("${subject_files[@]}")
    echo "  $subject: available"
  else
    echo "  $subject: unavailable for $RUN"
  fi
done

if [[ ${#AVAILABLE[@]} -lt 3 ]]; then
  echo "Too few subjects available for $RUN: ${#AVAILABLE[@]}" >&2
  exit 3
fi

echo
echo "Available subjects (${#AVAILABLE[@]}): ${AVAILABLE[*]}"

for f in "${FILES[@]}"; do
  key=$(git -C "$DATASET" annex lookupkey "$f" 2>/dev/null || true)
  size=$(printf '%s\n' "$key" | sed -n 's/.*-s\([0-9][0-9]*\)--.*/\1/p')
  if [[ -n "$size" ]]; then
    TOTAL=$((TOTAL + size))
  fi
done
if [[ $TOTAL -gt 0 ]]; then
  echo "Logical payload: $(numfmt --to=iec-i --suffix=B "$TOTAL" 2>/dev/null || echo "$TOTAL bytes")"
fi

read -r -p "Retrieve missing $RUN signal and alignment assets? [y/N] " reply
case "$reply" in
  y|Y|yes|YES) ;;
  *) echo "Nothing retrieved."; exit 0 ;;
esac

for f in "${FILES[@]}"; do
  if git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
    echo "Already present: $f"
  else
    echo "Retrieving $f"
    git -C "$DATASET" annex get -- "$f"
  fi
  if [[ ! -e "$DATASET/$f" ]]; then
    echo "FAILED to materialize: $f" >&2
    exit 4
  fi
done

echo
echo "Replication assets ready for $RUN."
echo "Subjects: ${AVAILABLE[*]}"
echo "Next: python scripts/analysis/run_chineseeeg_replication_run.py $DATASET --run-number $RUN_NUMBER"
