#!/usr/bin/env bash
set -euo pipefail

ACCESSION="ds004952"
DESTINATION="${1:-data/raw/chineseeeg}"

if ! command -v openneuro >/dev/null 2>&1; then
  echo "OpenNeuro CLI not found."
  echo "Install Deno, then run:"
  echo "  deno install -A --global jsr:@openneuro/cli -n openneuro"
  exit 1
fi

mkdir -p "$(dirname "$DESTINATION")"

echo "Downloading OpenNeuro dataset ${ACCESSION} to ${DESTINATION}"
openneuro download "$ACCESSION" "$DESTINATION"

echo
cat <<'EOF'
The OpenNeuro CLI creates a DataLad/git-annex dataset. Large annexed files may still need retrieval.
From the dataset directory, use DataLad or git-annex, for example:

  datalad get <path>

Do not commit downloaded neural data to the NeuroSem Git repository.
Record the exact OpenNeuro snapshot/tag used before analysis. The ChineseEEG paper cites snapshot v1.2.0.
EOF
