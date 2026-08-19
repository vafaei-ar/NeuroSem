#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-data/raw/chineseeeg}"
SUBJECT="${2:-sub-04}"
SESSION="${3:-ses-LittlePrince}"
RUN="${4:-run-01}"
DERIVATIVE="${5:-filtered_0.5_30}"

if [[ ! -d "$DATASET/.git" ]]; then
  echo "Not an OpenNeuro/DataLad checkout: $DATASET" >&2
  exit 1
fi

PREFIX="derivatives/${DERIVATIVE}/${SUBJECT}/${SESSION}/eeg/${SUBJECT}_${SESSION}_task-reading_${RUN}"

echo "Dataset:    $DATASET"
echo "Pilot:      $SUBJECT / $SESSION / $RUN"
echo "Derivative: $DERIVATIVE"
echo "Prefix:     $PREFIX"
echo

mapfile -t TRACKED < <(git -C "$DATASET" ls-files "${PREFIX}*")

if [[ ${#TRACKED[@]} -eq 0 ]]; then
  echo "No tracked files matched the pilot prefix."
  exit 2
fi

echo "Tracked files matching pilot prefix:"
printf '%s\n' "${TRACKED[@]}"

echo
CURRENT_UUID=$(git -C "$DATASET" annex uuid 2>/dev/null || true)
echo "Current annex repository UUID: ${CURRENT_UUID:-unknown}"

echo
echo "Annex-backed files among tracked pilot files:"
ANNEXED=()
for f in "${TRACKED[@]}"; do
  if key=$(git -C "$DATASET" annex lookupkey "$f" 2>/dev/null); then
    if [[ -n "$key" ]]; then
      ANNEXED+=("$f")
      echo "  $f"
      echo "    key: $key"
    fi
  fi
done

if [[ ${#ANNEXED[@]} -eq 0 ]]; then
  echo
  echo "No annex-backed pilot files were detected with 'git annex lookupkey'."
  exit 2
fi

echo
echo "Annex object sizes and local availability:"
TOTAL=0
for f in "${ANNEXED[@]}"; do
  key=$(git -C "$DATASET" annex lookupkey "$f")
  size=$(printf '%s\n' "$key" | sed -n 's/.*-s\([0-9][0-9]*\)--.*/\1/p')
  if git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
    present="yes"
  else
    present="no"
  fi
  if [[ -n "$size" ]]; then
    TOTAL=$((TOTAL + size))
    human=$(numfmt --to=iec-i --suffix=B "$size" 2>/dev/null || echo "${size} bytes")
    echo "  $f  [$human, local=$present]"
  else
    echo "  $f  [size unknown from key, local=$present]"
  fi
done

if [[ $TOTAL -gt 0 ]]; then
  echo "Total annex payload: $(numfmt --to=iec-i --suffix=B "$TOTAL" 2>/dev/null || echo "$TOTAL bytes")"
fi

echo
read -r -p "Retrieve these pilot annex objects now? [y/N] " reply
case "$reply" in
  y|Y|yes|YES)
    for f in "${ANNEXED[@]}"; do
      echo "Retrieving $f"
      git -C "$DATASET" annex get -- "$f"
    done
    ;;
  *)
    echo "Nothing retrieved."
    exit 0
    ;;
esac

echo
echo "Pilot retrieval verification:"
FAILED=0
for f in "${ANNEXED[@]}"; do
  full="$DATASET/$f"
  annex_here="no"
  path_ok="no"
  if git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
    annex_here="yes"
  fi
  if [[ -e "$full" ]]; then
    path_ok="yes"
  fi
  echo "  $f  [annex-here=$annex_here, path-resolves=$path_ok]"
  if [[ "$annex_here" != "yes" || "$path_ok" != "yes" ]]; then
    FAILED=1
    echo "    whereis:"
    git -C "$DATASET" annex whereis "$f" 2>/dev/null | sed 's/^/      /' || true
  fi
done

if [[ $FAILED -ne 0 ]]; then
  echo
  echo "One or more annex objects are not materialized in this checkout."
  echo "Do not run the MNE validator yet. Report this output."
  exit 3
fi

echo
echo "All pilot annex objects are materialized and their symlink paths resolve."
