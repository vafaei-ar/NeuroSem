#!/usr/bin/env bash
set -euo pipefail

PY=.venv/bin/python

if [[ ! -x "$PY" ]]; then
  echo "Missing .venv/bin/python" >&2
  exit 2
fi

for path in \
  outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter \
  outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter
do
  if [[ ! -d "$path" ]]; then
    echo "Missing frozen E5 adapter: $path" >&2
    exit 3
  fi
done

if ! find outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural -mindepth 2 -maxdepth 2 -type f -name summary.json -print -quit 2>/dev/null | grep -q .; then
  echo "Missing completed lambda=0.10 Pareto adapter" >&2
  exit 3
fi

"$PY" scripts/tuning/evaluate_nature_directional_eeg_v1.py \
  data/raw/nature_directional_eeg/extracted/inner_speech_v2 \
  --output-dir outputs/nature_directional_neurosem_v1/latest \
  --device auto
