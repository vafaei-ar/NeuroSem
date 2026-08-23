#!/usr/bin/env bash
set -euo pipefail

PY=.venv/bin/python

if [[ ! -x "$PY" ]]; then
  echo "Missing .venv/bin/python. Run the setup_venv RunRelay task first." >&2
  exit 2
fi

$PY - <<'PY'
import importlib.util
mods = ["torch", "transformers", "peft", "datasets", "scipy", "numpy", "openpyxl"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
print(f"E5 Pareto preflight missing={missing}")
if missing:
    raise SystemExit("Missing required Python packages: " + ", ".join(missing))
PY

for spec in \
  "0.01 lambda_0p01" \
  "0.03 lambda_0p03" \
  "0.10 lambda_0p10" \
  "0.30 lambda_0p30"
do
  read -r weight label <<< "$spec"
  out="outputs/e5_neural_tuning_pareto_v1/${label}"
  if find "$out" -type f -name summary.json -print -quit 2>/dev/null | grep -q .; then
    echo "Refusing to overwrite or mix with prior Pareto training output under $out" >&2
    exit 3
  fi
  echo "=== E5 Pareto training lambda=${weight} ==="
  "$PY" scripts/tuning/train_e5_neurosem_lora.py \
    --arm neural \
    --neural-loss-weight "$weight" \
    --output-dir "$out"
done

echo "=== E5 exploratory Pareto evaluation ==="
"$PY" scripts/tuning/evaluate_e5_pareto_v1.py \
  data/raw/chineseeeg \
  --batch-size 64 \
  --permutations 10000 \
  --workers 16 \
  --chunk-size 50

echo "=== E5 exploratory Pareto experiment complete ==="
