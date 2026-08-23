#!/usr/bin/env bash
set -euo pipefail

# Frozen independent-seed replication of the BERT NeuroSem tuning experiment.
# Only the random seed differs from v1. All targets, hyperparameters, splits,
# evaluators, and benchmark definitions are reused unchanged.

PYTHON="${PYTHON:-python}"
CONFIG="configs/bert_neural_tuning_v1_seed2.json"
TARGET_ROOT="outputs/bert_neural_tuning_targets_v1"
TUNING_ROOT="outputs/bert_neural_tuning_v1_seed2"

for arm in text_only neural shuffled_neural; do
  echo
  echo "=== seed2 training: ${arm} ==="
  "${PYTHON}" scripts/tuning/train_bert_neurosem_lora.py \
    --arm "${arm}" \
    --config "${CONFIG}" \
    --target-root "${TARGET_ROOT}" \
    --output-dir "${TUNING_ROOT}" \
    --geometry-batch-size 128
done

echo
echo "=== seed2 run-07 neural holdout ==="
"${PYTHON}" scripts/tuning/evaluate_bert_neurosem_run07.py \
  data/raw/chineseeeg \
  --tuning-root "${TUNING_ROOT}" \
  --embedding-output outputs/bert_neurosem_run07_embeddings_v1_seed2 \
  --rsa-output outputs/bert_neurosem_run07_rsa_v1_seed2 \
  --batch-size 128 \
  --permutations 10000 \
  --workers 16 \
  --chunk-size 50

echo
echo "=== seed2 frozen external C-MTEB STS benchmark ==="
"${PYTHON}" scripts/tuning/evaluate_bert_neurosem_cmteb_sts.py \
  --tuning-root "${TUNING_ROOT}" \
  --output-dir outputs/bert_neurosem_cmteb_sts_v1_seed2 \
  --batch-size 128

echo
echo "Seed-2 replication complete. No v1 hyperparameters were changed."
