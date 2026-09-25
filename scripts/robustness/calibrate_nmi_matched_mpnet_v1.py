#!/usr/bin/env python3
"""Calibrate the genuine-neural E5 displacement on source-side ChineseEEG text only.

This pre-matched-surrogate calibration reads no ZuCo or SMN4Lang stimuli, neural data,
or transfer outcomes. It reuses the three frozen text-only and genuine-neural E5
adapters and measures model-space displacement on the canonical ChineseEEG source
texts from runs 01-06 that were already materialized for the MPNet surrogate target.
The sole purpose is to fix the genuine-arm displacement reference and its observed
seed variability before the displacement-matched surrogate protocol is finalized.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from scripts.robustness.run_nmi_mpnet_model_space_comparison_v1 import (
    compare,
    encode_adapter,
    latest_adapter,
)

SEEDS = [20260829, 20260830, 20260831]
RUNS = [1, 2, 3, 4, 5, 6]
CONTROL_ROOT = Path("outputs/nmi_multiseed_e5_v1")
SOURCE_TEXT_ROOT = Path("outputs/nmi_alternative_signal_mpnet_targets_v1/latest")
OUT = Path("outputs/nmi_matched_mpnet_calibration_v1/latest")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_progress(current: int, total: int, phase: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else 0.0,
        "phase": phase,
        "message": message,
        "unit": "adapter encodings",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    tmp.replace(p)


def load_source_texts() -> tuple[list[str], list[dict]]:
    texts_all: list[str] = []
    manifest: list[dict] = []
    for run in RUNS:
        p = SOURCE_TEXT_ROOT / f"run_{run:02d}" / "texts.json"
        if not p.is_file():
            raise FileNotFoundError(f"missing frozen source text file: {p}")
        obj = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(obj, list) or not obj or not all(isinstance(x, str) for x in obj):
            raise RuntimeError(f"unexpected source text payload: {p}")
        clean = [x.strip() for x in obj]
        if any(not x for x in clean):
            raise RuntimeError(f"blank source text in {p}")
        manifest.append({
            "run": run,
            "path": str(p),
            "sha256": sha256(p),
            "n_items": len(clean),
        })
        texts_all.extend(clean)
    return texts_all, manifest


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    import torch

    OUT.mkdir(parents=True, exist_ok=True)
    texts, source_manifest = load_source_texts()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows: list[dict] = []
    total = len(SEEDS) * 2
    done = 0
    write_progress(0, total, "encode", "starting source-side displacement calibration")

    for seed in SEEDS:
        seed_root = CONTROL_ROOT / f"seed_{seed}"
        text_adapter = latest_adapter(seed_root / "text_only")
        genuine_adapter = latest_adapter(seed_root / "neural")

        et = encode_adapter(text_adapter, texts, device)
        done += 1
        write_progress(done, total, "encode", f"text-only seed {seed}")
        eg = encode_adapter(genuine_adapter, texts, device)
        done += 1
        write_progress(done, total, "encode", f"genuine-neural seed {seed}")

        if et.shape != eg.shape or et.shape[0] != len(texts):
            raise RuntimeError(f"seed {seed}: embedding shape mismatch")
        metrics = compare(et, eg)
        cka = float(metrics["linear_centered_cka"])
        rows.append({
            "seed": seed,
            "text_adapter": str(text_adapter),
            "genuine_adapter": str(genuine_adapter),
            "n_items": len(texts),
            **metrics,
            "delta_1_minus_cka": 1.0 - cka,
        })

    write_csv(OUT / "seed_metrics.csv", rows)
    write_csv(OUT / "source_text_manifest.csv", source_manifest)

    deltas = np.asarray([float(r["delta_1_minus_cka"]) for r in rows], dtype=float)
    mean_delta = float(np.mean(deltas))
    max_abs_dev = float(np.max(np.abs(deltas - mean_delta)))
    relative_floor = 0.25 * mean_delta
    tolerance_half_width = max(max_abs_dev, relative_floor)
    band = [mean_delta - tolerance_half_width, mean_delta + tolerance_half_width]

    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "pre-matched-surrogate source-side calibration",
        "purpose": "Fix genuine-neural displacement reference and observed seed variability before matched-surrogate protocol freeze.",
        "stimulus_set": "canonical ChineseEEG source texts from runs 01-06 materialized for the frozen surrogate target",
        "n_items": len(texts),
        "runs": RUNS,
        "seeds": SEEDS,
        "primary_metric": "delta = 1 - linear centered CKA(genuine-neural, seed-matched text-only)",
        "seed_delta_values": deltas.tolist(),
        "mean_delta": mean_delta,
        "max_absolute_seed_deviation": max_abs_dev,
        "relative_floor_25pct": relative_floor,
        "candidate_tolerance_half_width": tolerance_half_width,
        "candidate_tolerance_band": band,
        "secondary_metrics": [
            "corresponding_item_cosine_similarity_mean",
            "pairwise_cosine_distance_pearson",
            "pairwise_cosine_distance_spearman",
            "mean_knn_jaccard_overlap",
        ],
        "guardrails": {
            "zuco_stimuli_read": False,
            "zuco_neural_data_read": False,
            "smn4lang_stimuli_read": False,
            "smn4lang_neural_data_read": False,
            "external_transfer_outcomes_read": False,
            "surrogate_grid_trained": False,
            "dose_selected": False,
        },
        "source_text_manifest": source_manifest,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.txt").write_text(
        "NeuroSem matched-MPNet source-side calibration\n\n"
        f"Items: {len(texts)} across ChineseEEG runs 01-06\n"
        f"Seeds: {SEEDS}\n"
        f"Per-seed 1-CKA: {deltas.tolist()}\n"
        f"Mean 1-CKA: {mean_delta:.10g}\n"
        f"Observed max absolute seed deviation: {max_abs_dev:.10g}\n"
        f"25% relative floor: {relative_floor:.10g}\n"
        f"Candidate tolerance half-width: {tolerance_half_width:.10g}\n"
        f"Candidate tolerance band: [{band[0]:.10g}, {band[1]:.10g}]\n"
        "No external target stimuli, neural data, or transfer outcomes were read.\n",
        encoding="utf-8",
    )
    write_progress(total, total, "complete", "source-side displacement calibration complete")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
