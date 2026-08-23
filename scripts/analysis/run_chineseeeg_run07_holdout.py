#!/usr/bin/env python3
"""Open the frozen ChineseEEG run-07 holdout for the three preselected models.

Requires run-07 EEG row features to have been prepared first. The candidate list,
model revisions, pooling rules, nuisance controls, statistic, and permutation scheme
are fixed before this script is run.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

MODELS = ["bert-base-chinese-final", "multilingual-e5-large", "bge-m3"]


def available_subjects(feature_root: Path) -> list[str]:
    out = []
    if not feature_root.exists():
        return out
    for d in sorted(feature_root.iterdir()):
        if not d.is_dir() or not d.name.startswith("sub-"):
            continue
        if any((child / "row_mean.npy").exists() for child in d.iterdir() if child.is_dir()):
            out.append(d.name)
    return out


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen ChineseEEG run-07 holdout tests.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--chunk-size", type=int, default=50)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    feature_root = Path("outputs/chineseeeg_row_features/run-07")
    subjects = available_subjects(feature_root)
    if len(subjects) < 3:
        raise SystemExit("Run-07 row features are not ready; run preprocessing-only workflow first")

    print("=== OPENING FROZEN RUN-07 HOLDOUT ===")
    print("Candidates: " + ", ".join(MODELS))
    print(f"Subjects ({len(subjects)}): {' '.join(subjects)}")
    print("Run-07 semantic results have not been used for model selection.")

    py = sys.executable
    dataset = args.dataset.expanduser().resolve()
    for model_key in MODELS:
        print(f"\n=== {model_key} | run-07 ===", flush=True)
        emb_root = Path("outputs/chineseeeg_run07_holdout_embeddings") / model_key / "run-07"
        rsa_root = Path("outputs/chineseeeg_run07_holdout_rsa") / model_key / "run-07"

        run([
            py, "scripts/embeddings/generate_chineseeeg_run07_holdout_embeddings.py",
            str(dataset),
            "--model-key", model_key,
            "--batch-size", str(args.batch_size),
            "--device", args.device,
        ])
        run([
            py, "scripts/analysis/assess_chineseeeg_run07_holdout_fast.py",
            "--embedding-root", str(emb_root),
            "--feature-root", str(feature_root),
            "--subjects", *subjects,
            "--permutations", str(args.permutations),
            "--workers", str(args.workers),
            "--chunk-size", str(args.chunk_size),
            "--output-dir", str(rsa_root),
        ])

    print("\nFrozen run-07 holdout complete.")
    print("Models tested: " + ", ".join(MODELS))
    print("Interpret all three results, including negative results, without changing model definitions post hoc.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
