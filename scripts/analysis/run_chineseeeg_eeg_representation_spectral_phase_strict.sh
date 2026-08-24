#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-data/raw/chineseeeg}"
FEATURE_ROOT="${2:-outputs/chineseeeg_row_features}"
OUTPUT_DIR="${3:-outputs/chineseeeg_eeg_representation_overnight/latest}"
SESSION="ses-LittlePrince"
CANDIDATE_SUBJECTS=(sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10 sub-13 sub-14 sub-15)
RUNS=(run-06 run-07)
DERIVATIVES=(filtered_0.5_30 filtered_0.5_80)

if [[ ! -d "$DATASET/.git" ]]; then
  echo "Not a DataLad/OpenNeuro checkout: $DATASET" >&2
  exit 2
fi

tracked_subjects=()
excluded_not_tracked=()

# Phase 1: determine the common TRACKED subject intersection across every
# required run x derivative x BrainVision companion combination. NOT TRACKED is
# a dataset-availability condition, not something git-annex can repair.
for subject in "${CANDIDATE_SUBJECTS[@]}"; do
  subject_ok=1
  for derivative in "${DERIVATIVES[@]}"; do
    for run in "${RUNS[@]}"; do
      prefix="derivatives/preproc/${derivative}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${run}_eeg"
      for ext in vhdr vmrk eeg; do
        f="${prefix}.${ext}"
        if ! git -C "$DATASET" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
          echo "DATASET UNAVAILABLE / NOT TRACKED: $f" >&2
          subject_ok=0
        fi
      done
    done
  done
  if [[ $subject_ok -eq 1 ]]; then
    tracked_subjects+=("$subject")
  else
    excluded_not_tracked+=("$subject")
  fi
done

if [[ ${#tracked_subjects[@]} -lt 3 ]]; then
  echo "Too few subjects in common tracked intersection: ${#tracked_subjects[@]}" >&2
  exit 4
fi

echo "Common tracked cohort (${#tracked_subjects[@]}): ${tracked_subjects[*]}"
if [[ ${#excluded_not_tracked[@]} -gt 0 ]]; then
  echo "Excluded because required files are not tracked: ${excluded_not_tracked[*]}"
fi

# Phase 2: materialize every required BrainVision companion for each tracked
# subject. A subject enters the frozen cohort only if all required assets are
# actually materializable. Preserve worktree paths; do not resolve .vhdr annex
# symlinks into .git/annex/objects.
materialized=0
already=0
COMMON_SUBJECTS=()
excluded_not_materializable=()

for subject in "${tracked_subjects[@]}"; do
  subject_ok=1
  for derivative in "${DERIVATIVES[@]}"; do
    for run in "${RUNS[@]}"; do
      prefix="derivatives/preproc/${derivative}/${subject}/${SESSION}/eeg/${subject}_${SESSION}_task-reading_${run}_eeg"
      for ext in vhdr vmrk eeg; do
        f="${prefix}.${ext}"
        if git -C "$DATASET" annex find --in here --format='${file}\n' -- "$f" 2>/dev/null | grep -Fxq "$f"; then
          already=$((already + 1))
        else
          echo "Materializing: $f"
          if git -C "$DATASET" annex get -- "$f"; then
            materialized=$((materialized + 1))
          else
            echo "NOT MATERIALIZABLE: $f" >&2
            subject_ok=0
            continue
          fi
        fi
        if [[ ! -e "$DATASET/$f" ]]; then
          echo "NOT MATERIALIZABLE AFTER GET: $f" >&2
          subject_ok=0
        fi
      done
    done
  done
  if [[ $subject_ok -eq 1 ]]; then
    COMMON_SUBJECTS+=("$subject")
  else
    excluded_not_materializable+=("$subject")
  fi
done

if [[ ${#COMMON_SUBJECTS[@]} -lt 3 ]]; then
  echo "Too few subjects in common tracked+materializable intersection: ${#COMMON_SUBJECTS[@]}" >&2
  exit 5
fi

echo "Frozen common tracked+materializable cohort (${#COMMON_SUBJECTS[@]}): ${COMMON_SUBJECTS[*]}"
if [[ ${#excluded_not_materializable[@]} -gt 0 ]]; then
  echo "Excluded because required files were not materializable: ${excluded_not_materializable[*]}"
fi
echo "Materialization complete. newly_materialized=$materialized already_present=$already"

# Freeze the cohort before analysis and use it identically for every candidate,
# including the amplitude mean baseline.
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
FROZEN_COHORT_CSV=$(IFS=,; echo "${COMMON_SUBJECTS[*]}")
EXCLUDED_TRACKED_CSV=$(IFS=,; echo "${excluded_not_tracked[*]-}")
EXCLUDED_MATERIALIZABLE_CSV=$(IFS=,; echo "${excluded_not_materializable[*]-}")
.venv/bin/python - "$OUTPUT_DIR/frozen_common_cohort.json" "$FROZEN_COHORT_CSV" "$EXCLUDED_TRACKED_CSV" "$EXCLUDED_MATERIALIZABLE_CSV" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
def split_csv(value):
    return [x for x in value.split(",") if x]

payload = {
    "schema_version": 1,
    "cohort_rule": "common tracked and materializable intersection across run-06/run-07 and filtered_0.5_30/filtered_0.5_80 BrainVision vhdr/vmrk/eeg companions",
    "frozen_subjects": split_csv(sys.argv[2]),
    "excluded_not_tracked": split_csv(sys.argv[3]),
    "excluded_not_materializable": split_csv(sys.argv[4]),
}
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

.venv/bin/python scripts/analysis/run_chineseeeg_eeg_representation_overnight.py \
  --data-root "$DATASET" \
  --feature-root "$FEATURE_ROOT" \
  --discovery-run run-06 \
  --holdout-run run-07 \
  --subjects "${COMMON_SUBJECTS[@]}" \
  --output-dir "$OUTPUT_DIR"

# Strict completeness check: all intended representation families must execute
# on both runs, and every candidate must use exactly the frozen common cohort.
.venv/bin/python - "$OUTPUT_DIR/summary.json" "$OUTPUT_DIR/frozen_common_cohort.json" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
cohort_path = Path(sys.argv[2])
if not summary_path.exists():
    raise SystemExit(f"Missing benchmark summary: {summary_path}")
if not cohort_path.exists():
    raise SystemExit(f"Missing frozen cohort record: {cohort_path}")

s = json.loads(summary_path.read_text(encoding="utf-8"))
cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
frozen = list(cohort.get("frozen_subjects", []))
if len(frozen) < 3:
    raise SystemExit(f"Invalid frozen cohort: {frozen}")

required = [
    "row_mean_all",
    "row_std_all",
    "relative_8bin_all",
    "row_mean_nonfrontal",
    "row_mean_posterior",
    "row_mean_lateral_posterior",
    "theta_relative_power",
    "alpha_relative_power",
    "beta_relative_power",
    "low_gamma_relative_power",
    "theta_phase_5p5hz",
    "alpha_phase_10hz",
]
status = s.get("subjob_status", {})
problems = []
for name in required:
    for key in (f"run-06:evaluate:{name}", f"run-07:exploratory:{name}"):
        rec = status.get(key)
        if not isinstance(rec, dict) or str(rec.get("status", "")).lower() != "completed":
            problems.append((key, rec))

# Confirm the analysis itself used the frozen cohort for both runs.
for field in ("discovery_subjects", "holdout_subjects"):
    observed = list(s.get(field, []))
    if observed != frozen:
        problems.append((field, {"expected": frozen, "observed": observed}))

# Require one candidate-metric row for every intended family/run and enforce
# identical n_subjects for all of them.
rows = [r for r in s.get("candidate_metrics", []) if isinstance(r, dict)]
by_key = {(str(r.get("run")), str(r.get("candidate"))): r for r in rows}
for name in required:
    for run in ("run-06", "run-07"):
        rec = by_key.get((run, name))
        if rec is None:
            problems.append((f"candidate_metrics:{run}:{name}", "absent"))
            continue
        if int(rec.get("n_subjects", -1)) != len(frozen):
            problems.append((f"candidate_metrics:{run}:{name}", {"expected_n": len(frozen), "observed_n": rec.get("n_subjects")}))

if problems:
    raise SystemExit(f"Strict common-cohort benchmark incomplete: {problems}")
print("STRICT_COMMON_COHORT_SPECTRAL_PHASE_COMPLETENESS_OK")
PY

echo "Strict common-cohort spectral/phase benchmark completed successfully."
