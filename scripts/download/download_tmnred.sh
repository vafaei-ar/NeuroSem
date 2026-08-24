#!/usr/bin/env bash
set -euo pipefail

ACCESSION="ds005383"
EXPECTED_SNAPSHOT="1.0.0"
DESTINATION="${1:-data/raw/tmnred}"

if ! command -v openneuro >/dev/null 2>&1; then
  echo "OpenNeuro CLI not found." >&2
  echo "Install the OpenNeuro CLI before running this task." >&2
  exit 2
fi

mkdir -p "$(dirname "$DESTINATION")"

if [[ -d "$DESTINATION/.git" ]]; then
  echo "TMNRED OpenNeuro checkout already exists: $DESTINATION"
else
  echo "Creating OpenNeuro DataLad/git-annex checkout for ${ACCESSION} at ${DESTINATION}"
  openneuro download "$ACCESSION" "$DESTINATION"
fi

if [[ ! -d "$DESTINATION/.git" ]]; then
  echo "Expected DataLad/git-annex checkout was not created: $DESTINATION" >&2
  exit 3
fi

# The Scientific Data descriptor pins OpenNeuro ds005383 v1.0.0. Prefer that
# snapshot when the tag is present locally. Do not fetch annexed EEG payloads
# here; signal materialization is a later, explicitly scoped step after audit.
if git -C "$DESTINATION" rev-parse -q --verify "refs/tags/${EXPECTED_SNAPSHOT}" >/dev/null 2>&1; then
  git -C "$DESTINATION" checkout --detach "$EXPECTED_SNAPSHOT"
  echo "Pinned TMNRED snapshot: ${EXPECTED_SNAPSHOT}"
else
  echo "WARNING: expected snapshot tag ${EXPECTED_SNAPSHOT} not found locally." >&2
  echo "Current HEAD will be recorded by the audit; do not begin confirmatory signal analysis until version provenance is resolved." >&2
fi

echo "TMNRED metadata checkout prepared without recursive annex materialization."
echo "HEAD=$(git -C "$DESTINATION" rev-parse HEAD)"
git -C "$DESTINATION" tag --points-at HEAD || true
