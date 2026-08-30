#!/usr/bin/env python3
"""Build the frozen model-blind SMN4Lang fMRI source targets for bidirectional transfer."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from scripts.analysis.run_smn4lang_fmri_reliability import (
    SUBJECTS,
    STORIES,
    TR,
    MASK_THRESHOLD,
    canonical_hrf,
    corr_rdm_vector_from_bold,
    residualize,
)
from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import (
    LANA_SHA256,
    fresh_lana_mask,
    story_context,
)

TRAIN_STORIES = [1, 3, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24, 25, 27, 28, 29, 30, 31, 32, 33, 35, 36, 39, 40, 42, 43, 44, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]
VALIDATION_STORIES = [2, 7, 11, 16, 22, 26, 34, 37, 38, 41, 45, 50]


def report_progress(current: int, total: int, phase: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else None,
        "phase": phase,
        "unit": "stories",
        "updated_at_epoch": time.time(),
    }
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


def zstd(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    sd = float(x.std(ddof=0))
    if not np.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError("cannot standardize constant/non-finite vector")
    return (x - float(x.mean())) / sd


def main() -> int:
    root = Path("data/raw/smn4lang").resolve()
    reliability_path = Path("outputs/smn4lang_fmri_reliability/latest/summary.json")
    out = Path("outputs/nmi_bidirectional_fmri_source_v1/latest").resolve()
    target_dir = out / "targets"
    out.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    reliability = json.loads(reliability_path.read_text(encoding="utf-8"))
    if not reliability.get("reliability_gate_pass"):
        raise RuntimeError("SMN4Lang fMRI reliability gate did not pass")
    if int(reliability.get("n_subjects", -1)) != 12 or int(reliability.get("n_stories", -1)) != 60:
        raise RuntimeError("unexpected frozen SMN4Lang reliability cohort")
    spatial = reliability.get("spatial_representation", {})
    if spatial.get("atlas_sha256") != LANA_SHA256 or float(spatial.get("mask_threshold_probability", -1)) != MASK_THRESHOLD:
        raise RuntimeError("frozen LanA specification mismatch")

    if sorted(TRAIN_STORIES + VALIDATION_STORIES) != list(STORIES) or set(TRAIN_STORIES) & set(VALIDATION_STORIES):
        raise RuntimeError("invalid frozen story split")

    split_payload = {
        "schema_version": 1,
        "split_method": "SHA256 ordering of literal smn4lang-story-XX; lowest 48 train, remaining 12 validation",
        "train_stories": TRAIN_STORIES,
        "validation_stories": VALIDATION_STORIES,
        "n_train": len(TRAIN_STORIES),
        "n_validation": len(VALIDATION_STORIES),
    }
    (out / "split.json").write_text(json.dumps(split_payload, indent=2) + "\n", encoding="utf-8")

    hrf = canonical_hrf(TR)
    mask = fresh_lana_mask(root, out / "runtime_atlas")
    story_rows = []

    for idx, story in enumerate(STORIES, start=1):
        ctx = story_context(root, story, hrf)
        participant_rankz = []
        for sub in SUBJECTS:
            path = root / f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"
            neural = corr_rdm_vector_from_bold(path, mask, ctx["valid_idx"])
            resid = residualize(neural, ctx["nuisance"])
            ranked = rankdata(np.asarray(resid, dtype=np.float64), method="average")
            participant_rankz.append(zstd(ranked))

        mat = np.vstack(participant_rankz)
        group = zstd(mat.mean(axis=0))
        target_path = target_dir / f"story_{story:02d}.npz"
        np.savez_compressed(
            target_path,
            target=group.astype(np.float32),
            valid_idx=np.asarray(ctx["valid_idx"], dtype=np.int32),
            n_timepoints=np.asarray([ctx["n_items"]], dtype=np.int32),
            n_pairs=np.asarray([ctx["n_pairs"]], dtype=np.int64),
        )
        story_rows.append({
            "story": story,
            "split": "train" if story in TRAIN_STORIES else "validation",
            "n_timepoints": int(ctx["n_items"]),
            "n_pairs": int(ctx["n_pairs"]),
            "group_target_mean": float(group.mean()),
            "group_target_sd": float(group.std(ddof=0)),
            "mean_participant_edgewise_sd": float(mat.std(axis=0, ddof=0).mean()),
        })
        print(f"Frozen fMRI source target story {story:02d}/60", flush=True)
        report_progress(idx, len(STORIES), "Freeze fMRI source geometry")

    n_tp = np.asarray([r["n_timepoints"] for r in story_rows], dtype=float)
    n_pairs = np.asarray([r["n_pairs"] for r in story_rows], dtype=float)
    summary = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory bidirectional transfer source freeze",
        "protocol": "docs/17_NMI_BIDIRECTIONAL_FMRI_SOURCE_FREEZE_V1.md",
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "n_subjects": len(SUBJECTS),
        "n_stories": len(STORIES),
        "train_stories": TRAIN_STORIES,
        "validation_stories": VALIDATION_STORIES,
        "spatial_representation": {
            "mask": "LanA probabilistic language-network atlas",
            "mask_threshold_probability": MASK_THRESHOLD,
            "atlas_sha256": LANA_SHA256,
            "n_mask_voxels": int(mask.sum()),
        },
        "group_target_rule": "participant residual RDM -> average ranks -> within-participant z -> edgewise mean across 12 -> group z",
        "nuisance_controls": [
            "absolute temporal separation in seconds",
            "absolute difference in canonical-HRF-convolved word-onset density",
            "absolute difference in canonical-HRF-convolved acoustic RMS envelope",
        ],
        "timepoint_count": {
            "min": int(n_tp.min()),
            "median": float(np.median(n_tp)),
            "max": int(n_tp.max()),
            "mean": float(n_tp.mean()),
        },
        "pair_count": {
            "min": int(n_pairs.min()),
            "median": float(np.median(n_pairs)),
            "max": int(n_pairs.max()),
            "mean": float(n_pairs.mean()),
        },
        "story_summaries": story_rows,
        "guardrails": {
            "language_model_loaded": False,
            "external_eeg_read": False,
            "representation_search": False,
            "split_frozen_before_model_training": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": str(out), "n_stories": 60}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
