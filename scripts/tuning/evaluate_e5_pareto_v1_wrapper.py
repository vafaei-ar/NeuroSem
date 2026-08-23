#!/usr/bin/env python3
"""Compatibility wrapper for the exploratory E5 Pareto evaluator.

The validated run-07 RSA helper expects an embedding root containing a timestamp-like
child directory. The Pareto evaluator writes each point directly into its label directory.
This wrapper stages those files one level deeper immediately before RSA, without changing
any model, statistic, nuisance, permutation, or evaluation logic.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts.tuning import evaluate_e5_pareto_v1 as mod

_original_run_rsa = mod.run_rsa


def _run_rsa_with_staging(
    embedding_root: Path,
    feature_root: Path,
    output_root: Path,
    permutations: int,
    workers: int,
    chunk_size: int,
):
    embedding_root = Path(embedding_root)
    if (embedding_root / "embeddings.npy").exists():
        staged = embedding_root / "eval"
        staged.mkdir(parents=True, exist_ok=True)
        for name in ("embeddings.npy", "summary.json", "texts.json"):
            src = embedding_root / name
            if src.exists():
                shutil.copy2(src, staged / name)
    return _original_run_rsa(
        embedding_root,
        feature_root,
        output_root,
        permutations,
        workers,
        chunk_size,
    )


mod.run_rsa = _run_rsa_with_staging

if __name__ == "__main__":
    raise SystemExit(mod.main())
