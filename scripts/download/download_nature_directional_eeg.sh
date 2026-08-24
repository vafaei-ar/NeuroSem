#!/usr/bin/env bash
set -euo pipefail

ROOT="data/raw/nature_directional_eeg"
ZIP="$ROOT/Inner_Speech_Dataset.zip"
EXTRACTED="$ROOT/extracted"
URL="https://zenodo.org/records/20374418/files/Inner%20Speech%20Dataset.zip?download=1"
EXPECTED_MD5="5ce82e9b48fd441b136eea141c45f769"

mkdir -p "$ROOT" "$EXTRACTED"

if [[ -f "$ZIP" ]]; then
  echo "Archive already exists: $ZIP"
else
  echo "Downloading pinned Zenodo record 20374418 (~5 GB)..."
  curl -L --fail --retry 3 --retry-delay 5 -C - -o "$ZIP" "$URL"
fi

actual_md5="$(md5sum "$ZIP" | awk '{print $1}')"
echo "MD5: $actual_md5"
if [[ "$actual_md5" != "$EXPECTED_MD5" ]]; then
  echo "Checksum mismatch for $ZIP" >&2
  echo "Expected: $EXPECTED_MD5" >&2
  echo "Observed: $actual_md5" >&2
  exit 3
fi

marker="$EXTRACTED/.extract_complete_${EXPECTED_MD5}"
if [[ -f "$marker" ]]; then
  echo "Extraction already verified: $EXTRACTED"
else
  echo "Extracting dataset..."
  unzip -q -o "$ZIP" -d "$EXTRACTED"
  touch "$marker"
fi

echo "Nature directional EEG dataset prepared under: $ROOT"
find "$EXTRACTED" -maxdepth 3 -type d | sort | head -n 80
