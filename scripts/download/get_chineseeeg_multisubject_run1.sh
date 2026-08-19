#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-data/raw/chineseeeg}"
SESSION="${2:-ses-LittlePrince}"
RUN="${3:-run-01}"
DERIVATIVE="${4:-filtered_0.5_30}"

SUBJECTS=(sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10 sub-13 sub-14 sub-15)

if [[ ! -d "$DATASET/.git" ]]; then
  echo "Not an OpenNeuro/DataLad checkout: $DATASET" >&2
  exit 1
fi

echo "ChineseEEG targeted multi-subject retrieval"
echo "Dataset:    $DATASET"
echo "Session:    $SESSION"
echo "Run:        $RUN"
echo "Derivative: $DERIVATIVE"
echo "Subjects:   ${SUBJECTS[*]}"
echo

FILES=()
TOTAL=0
UNAVAILABLE=()
PARTIAL=()
for subject in "${SUBJECTS[@]}"; do
  prefix="derivatives/${DERIVATIVE}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${RUN}"
  found=0
  for ext in eeg vhdr vmrk; do
    f="${prefix}_eeg.${ext}"
    if git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      FILES+=("$f")
      found=$((found + 1))
      key=$(git -C "$DATASET" annex lookupkey "$f" 2>/dev/null || true)
      size=$(printf '%s\n' "$key" | sed -n 's/.*-s\([0-9][0-9]*\)--.*/\1/p')
      if [[ -n "$size" ]]; then
        TOTAL=$((TOTAL + size))
      fi
    fi
  done
  if [[ $found -eq 0 ]]; then
    UNAVAILABLE+=("$subject")
    echo "UNAVAILABLE: $subject has no tracked BrainVision triplet for $SESSION $RUN" >&2
  elif [[ $found -ne 3 ]]; then
    PARTIAL+=("$subject")
    echo "ERROR: $subject has only $found/3 expected BrainVision annex files for $SESSION $RUN" >&2
  fi
done

if [[ ${#PARTIAL[@]} -gt 0 ]]; then
  echo "Partial tracked triplets are a dataset/integrity error: ${PARTIAL[*]}" >&2
  exit 2
fi
if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No matching annex files found." >&2
  exit 2
fi

echo "Target annex files: ${#FILES[@]}"
if [[ $TOTAL -gt 0 ]]; then
  echo "Total logical payload: $(numfmt --to=iec-i --suffix=B "$TOTAL" 2>/dev/null || echo "$TOTAL bytes")"
fi
if [[ ${#UNAVAILABLE[@]} -gt 0 ]]; then
  echo "Structurally unavailable for this run: ${UNAVAILABLE[*]}"
fi

echo
for subject in "${SUBJECTS[@]}"; do
  echo "$subject:"
  prefix="derivatives/${DERIVATIVE}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${RUN}"
  found=0
  for ext in eeg vhdr vmrk; do
    f="${prefix}_eeg.${ext}"
    if git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      found=$((found + 1))
      present=no
      if git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
        present=yes
      fi
      key=$(git -C "$DATASET" annex lookupkey "$f" 2>/dev/null || true)
      size=$(printf '%s\n' "$key" | sed -n 's/.*-s\([0-9][0-9]*\)--.*/\1/p')
      human="unknown"
      if [[ -n "$size" ]]; then
        human=$(numfmt --to=iec-i --suffix=B "$size" 2>/dev/null || echo "${size} bytes")
      fi
      echo "  ${ext}: $human local=$present"
    fi
  done
  if [[ $found -eq 0 ]]; then
    echo "  unavailable in dataset for this run"
  fi
done

echo
read -r -p "Retrieve all missing available run-01 BrainVision objects now? [y/N] " reply
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
done

echo
FAILED=0
echo "Final verification:"
for subject in "${SUBJECTS[@]}"; do
  prefix="derivatives/${DERIVATIVE}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${RUN}"
  tracked=0
  subject_ok=yes
  for ext in eeg vhdr vmrk; do
    f="${prefix}_eeg.${ext}"
    if git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      tracked=$((tracked + 1))
      if ! git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
        subject_ok=no
      elif [[ ! -e "$DATASET/$f" ]]; then
        subject_ok=no
      fi
    fi
  done
  if [[ $tracked -eq 0 ]]; then
    echo "  $subject: unavailable"
  elif [[ $tracked -eq 3 && "$subject_ok" == "yes" ]]; then
    echo "  $subject: yes"
  else
    echo "  $subject: no"
    FAILED=1
  fi
done

if [[ $FAILED -ne 0 ]]; then
  echo "One or more available subjects are incomplete." >&2
  exit 3
fi

echo "All available requested subjects have materialized run-01 BrainVision triplets."
