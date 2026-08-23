#!/usr/bin/env bash
set -euo pipefail

PY=.venv/bin/python

if [[ ! -x "$PY" ]]; then
  echo "Missing .venv/bin/python. Run the setup_venv RunRelay task first." >&2
  exit 2
fi

$PY - <<'PY'
import importlib
mods = ["torch", "transformers", "peft", "datasets", "scipy", "numpy", "openpyxl"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Missing required Python packages: " + ", ".join(missing))
PY

echo "=== E5 training: text_only ==="
$PY scripts/tuning/train_e5_neurosem_lora.py --arm text_only

echo "=== E5 training: neural ==="
$PY scripts/tuning/train_e5_neurosem_lora.py --arm neural

echo "=== E5 training: shuffled_neural ==="
$PY scripts/tuning/train_e5_neurosem_lora.py --arm shuffled_neural

echo "=== E5 run-07 neural holdout ==="
$PY scripts/tuning/evaluate_e5_neurosem_run07.py \
  data/raw/chineseeeg \
  --batch-size 64 \
  --permutations 10000 \
  --workers 16 \
  --chunk-size 50

echo "=== E5 frozen external C-MTEB STS benchmark ==="
$PY scripts/tuning/evaluate_e5_neurosem_cmteb_sts.py --batch-size 64

echo "=== E5 replication complete ==="
