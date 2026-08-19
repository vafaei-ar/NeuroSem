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

echo "Tracked files matching pilot prefix:"
git -C "$DATASET" ls-files "${PREFIX}*" || true

echo

echo "Annexed objects matching pilot prefix:"
MATCHES=$(git -C "$DATASET" annex find --format='${file}\n' | grep -F "$PREFIX" || true)
if [[ -z "$MATCHES" ]]; then
  echo "No annexed files matched the pilot prefix. Stop and report this output."
  exit 2
fi
printf '%s\n' "$MATCHES"

echo

echo "Annex size summary:"
TOTAL=0
COUNT=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  info=$(git -C "$DATASET" annex info "$f" 2>/dev/null || true)
  bytes=$(printf '%s\n' "$info" | awk -F': ' '/^size:/{print $2}' | awk '{print $1}')
  echo "  $f${bytes:+  [reported size: $bytes]}"
  COUNT=$((COUNT + 1))
done <<< "$MATCHES"
echo "Objects: $COUNT"

echo
read -r -p "Retrieve these pilot annex objects now? [y/N] " reply
case "$reply" in
  y|Y|yes|YES)
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      echo "Retrieving $f"
      git -C "$DATASET" annex get "$f"
    done <<< "$MATCHES"
    ;;
  *)
    echo "Nothing retrieved."
    exit 0
    ;;
esac

echo
echo "Pilot retrieval complete. Local presence:"
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  git -C "$DATASET" annex whereis "$f" | head -20
  echo
done <<< "$MATCHES"
