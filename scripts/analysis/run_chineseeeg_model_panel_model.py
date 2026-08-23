#!/usr/bin/env python3
"""Run one prespecified model family across ChineseEEG LittlePrince runs 01-06.

Run 07 is intentionally blocked. This script reuses already extracted neural features,
generates model embeddings for each run, and executes the locked nuisance-controlled RSA.
The RSA stage uses the validated optimized parallel implementation.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


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


def run_cmd(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one NeuroSem model-panel family across runs 01-06.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--model-key", required=True, choices=[
        "xlm-roberta-large", "multilingual-e5-large", "bge-m3", "qwen3-embedding-0.6b"
    ])
    parser.add_argument("--runs", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6])
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--chunk-size", type=int, default=50)
    args = parser.parse_args()

    if any(r < 1 or r > 6 for r in args.runs):
        raise SystemExit("Model screening is restricted to runs 01-06; run 07 remains sealed")

    python = sys.executable
    dataset = args.dataset.resolve()
    for run_number in args.runs:
        run_label = f"run-{run_number:02d}"
        feature_root = Path("outputs/chineseeeg_row_features") if run_number == 1 else Path("outputs/chineseeeg_row_features") / run_label
        subjects = available_subjects(feature_root)
        if not subjects:
            raise SystemExit(f"No extracted row features found for {run_label} under {feature_root}")

        emb_root = Path("outputs/chineseeeg_model_panel_embeddings") / args.model_key / run_label
        rsa_root = Path("outputs/chineseeeg_model_panel_rsa") / args.model_key / run_label

        run_cmd([
            python, "scripts/embeddings/generate_chineseeeg_model_panel_embeddings.py",
            str(dataset), "--run-number", str(run_number), "--model-key", args.model_key,
            "--batch-size", str(args.batch_size), "--device", args.device,
        ])
        run_cmd([
            python, "scripts/analysis/assess_chineseeeg_semantic_rsa_model_panel_fast.py",
            "--embedding-root", str(emb_root),
            "--feature-root", str(feature_root),
            "--subjects", *subjects,
            "--permutations", str(args.permutations),
            "--workers", str(args.workers),
            "--chunk-size", str(args.chunk_size),
            "--output-dir", str(rsa_root),
        ])

    print("Model-panel family run complete.")
    print(f"Model key: {args.model_key} | runs: {' '.join(f'run-{r:02d}' for r in args.runs)}")
    print(f"Fast RSA: workers={args.workers} | chunk_size={args.chunk_size}")
    print("Run-07 was not accessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
