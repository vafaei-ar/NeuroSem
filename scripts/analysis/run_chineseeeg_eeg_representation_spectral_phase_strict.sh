#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-data/raw/chineseeeg}"
FEATURE_ROOT="${2:-outputs/chineseeeg_row_features}"
OUTPUT_DIR="${3:-outputs/chineseeeg_eeg_representation_overnight/latest}"
SESSION="ses-LittlePrince"
SUBJECTS=(sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10 sub-13 sub-14 sub-15)
RUNS=(run-06 run-07)
DERIVATIVES=(filtered_0.5_30 filtered_0.5_80)

if [[ ! -d "$DATASET/.git" ]]; then
  echo "Not a DataLad/OpenNeuro checkout: $DATASET" >&2
  exit 2
fi

materialized=0
already=0
missing_tracked=0

for derivative in "${DERIVATIVES[@]}"; do
  for run in "${RUNS[@]}"; do
    for subject in "${SUBJECTS[@]}"; do
      prefix="derivatives/${derivative}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${run}_eeg"
      for ext in vhdr vmrk eeg; do
        f="${prefix}.${ext}"
        if ! git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
          echo "NOT TRACKED: $f" >&2
          missing_tracked=$((missing_tracked + 1))
          continue
        fi
        if git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
          already=$((already + 1))
        else
          echo "Materializing: $f"
          git -C "$DATASET" annex get -- "$f"
          materialized=$((materialized + 1))
        fi
        if [[ ! -e "$DATASET/$f" ]]; then
          echo "FAILED TO MATERIALIZE: $f" >&2
          exit 3
        fi
      done
    done
  done
done

if [[ $missing_tracked -gt 0 ]]; then
  echo "Required tracked assets missing from dataset index: $missing_tracked" >&2
  exit 4
fi

echo "Materialization complete. newly_materialized=$materialized already_present=$already"

rm -rf "$OUTPUT_DIR"
.venv/bin/python scripts/analysis/run_chineseeeg_eeg_representation_overnight.py \
  --data-root "$DATASET" \
  --feature-root "$FEATURE_ROOT" \
  --discovery-run run-06 \
  --holdout-run run-07 \
  --output-dir "$OUTPUT_DIR"

.venv/bin/python - "$OUTPUT_DIR/summary.json" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
if not p.exists():
    raise SystemExit(f"Missing benchmark summary: {p}")
s = json.loads(p.read_text(encoding="utf-8"))
text = json.dumps(s)
required = [
    "theta_relative_power",
    "alpha_relative_power",
    "beta_relative_power",
    "low_gamma_relative_power",
    "theta_phase_5p5hz",
    "alpha_phase_10hz",
]
missing = [name for name in required if name not in text]
if missing:
    raise SystemExit(f"Strict benchmark incomplete; candidate names absent from summary: {missing}")

# Fail if any required family is explicitly reported with zero usable subjects or unavailable status.
def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)

bad = []
for d in walk(s):
    name = d.get("candidate") or d.get("name") or d.get("representation")
    if name in required:
        n = d.get("n_subjects")
        status = str(d.get("status", "")).lower()
        if n == 0 or status in {"unavailable", "failed", "error", "skipped"}:
            bad.append((name, n, status))
if bad:
    raise SystemExit(f"Strict benchmark incomplete for required spectral/phase candidates: {bad}")
print("STRICT_SPECTRAL_PHASE_COMPLETENESS_OK")
PY

echo "Strict spectral/phase benchmark completed successfully."
