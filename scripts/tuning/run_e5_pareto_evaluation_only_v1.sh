#!/usr/bin/env bash
set -euo pipefail

PY=.venv/bin/python

if [[ ! -x "$PY" ]]; then
  echo "Missing .venv/bin/python. Run the setup_venv RunRelay task first." >&2
  exit 2
fi

for label in lambda_0p01 lambda_0p03 lambda_0p10 lambda_0p30; do
  root="outputs/e5_neural_tuning_pareto_v1/${label}/neural"
  summary="$(find "$root" -mindepth 2 -maxdepth 2 -type f -name summary.json -print 2>/dev/null | sort | tail -n 1 || true)"
  if [[ -z "$summary" ]]; then
    echo "Missing completed Pareto training summary for ${label}; refusing evaluation-only run." >&2
    exit 3
  fi
  adapter="$(dirname "$summary")/adapter"
  if [[ ! -d "$adapter" ]]; then
    echo "Missing adapter for ${label}: $adapter" >&2
    exit 3
  fi
  echo "Found completed ${label}: $summary"
done

for path in \
  outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter \
  outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter
do
  if [[ ! -d "$path" ]]; then
    echo "Missing frozen Pareto anchor adapter: $path" >&2
    exit 3
  fi
done

echo "=== E5 exploratory Pareto evaluation only ==="
"$PY" scripts/tuning/evaluate_e5_pareto_v1_wrapper.py \
  data/raw/chineseeeg \
  --batch-size 64 \
  --permutations 10000 \
  --workers 16 \
  --chunk-size 50

echo "=== E5 exploratory Pareto evaluation-only run complete ==="
