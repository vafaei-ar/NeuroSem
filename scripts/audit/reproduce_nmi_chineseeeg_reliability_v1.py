#!/usr/bin/env python3
"""Reproduce the pre-RunRelay ChineseEEG row-mean reliability numbers used in NMI v1.17.

This is a deterministic reproducibility replay of the existing reliability/confound
checkpoint. It performs no model evaluation, semantic analysis, target selection or
manuscript editing. The purpose is to give the historical approximately 0.220 raw LOO
and approximately 0.121 nuisance-residualized LOO values a current RunRelay artifact,
with the exact input-file and script hashes exposed for provenance.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path("outputs/nmi_v118_chineseeeg_reliability_reproduction_v1")
RUNS = ROOT / "runs"
LATEST = ROOT / "latest"
SCRIPT = Path("scripts/analysis/assess_chineseeeg_rowmean_residual_reliability.py")
SUBJECTS = ["sub-04", "sub-05", "sub-06", "sub-07", "sub-08", "sub-10", "sub-13", "sub-14", "sub-15"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_dir(root: Path, required: str) -> Path:
    c = sorted([d for d in root.iterdir() if d.is_dir() and (d / required).is_file()]) if root.exists() else []
    if not c:
        raise FileNotFoundError(f"No directory containing {required} under {root}")
    return c[-1]


def main() -> int:
    LATEST.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    cmd = [
        ".venv/bin/python", str(SCRIPT),
        "--subjects", *SUBJECTS,
        "--permutations", "1000",
        "--seed", "20260819",
        "--output-dir", str(RUNS),
    ]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    run_dir = latest_dir(RUNS, "summary.json")
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    subject_rows = list(csv.DictReader((run_dir / "subject_summary.csv").open(encoding="utf-8")))

    manifest = []
    for row in subject_rows:
        d = Path(row["feature_dir"])
        for name in ["row_mean.npy", "metadata.csv", "channels.txt"]:
            p = d / name
            manifest.append({
                "subject": row["subject"],
                "relative_path": str(p),
                "sha256": sha256(p),
                "size_bytes": p.stat().st_size,
            })
    with (LATEST / "input_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0]))
        w.writeheader(); w.writerows(manifest)

    shutil.copy2(run_dir / "subject_summary.csv", LATEST / "subject_summary.csv")
    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "reproducibility replay of historical model-blind reliability checkpoint",
        "historical_context": "pre-RunRelay 19 Aug 2026 ChineseEEG row-mean reliability reported in manuscript v1.17",
        "script": str(SCRIPT),
        "script_sha256": sha256(SCRIPT),
        "subjects": SUBJECTS,
        "n_subjects": summary["n_subjects"],
        "n_rows": summary["n_rows"],
        "n_channels": summary["n_channels"],
        "representation": summary["representation"],
        "nuisances": summary["nuisances"],
        "raw_pairwise_mean": summary["raw_pairwise_mean"],
        "raw_loo_mean": summary["raw_loo_mean"],
        "residual_pairwise_mean": summary["residual_pairwise_mean"],
        "residual_loo_mean": summary["residual_loo_mean"],
        "circular_shift_null": summary["circular_shift_null"],
        "mean_raw_nuisance_rho": summary["mean_raw_nuisance_rho"],
        "source_run_summary": str(run_dir / "summary.json"),
        "guardrails": {
            "model_embeddings_read": False,
            "semantic_targets_read": False,
            "external_transfer_outcomes_read": False,
            "model_training_performed": False,
            "representation_selection_performed": False,
        },
    }
    (LATEST / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (LATEST / "report.txt").write_text(
        "NeuroSem ChineseEEG reliability reproducibility replay\n\n"
        f"Raw LOO mean: {payload['raw_loo_mean']:.9f}\n"
        f"Residual LOO mean: {payload['residual_loo_mean']:.9f}\n"
        f"Raw pairwise mean: {payload['raw_pairwise_mean']:.9f}\n"
        f"Residual pairwise mean: {payload['residual_pairwise_mean']:.9f}\n"
        f"Subjects: {payload['n_subjects']}\nRows: {payload['n_rows']}\nChannels: {payload['n_channels']}\n"
        "This is a reproducibility replay only; no semantic/model inference was performed.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
