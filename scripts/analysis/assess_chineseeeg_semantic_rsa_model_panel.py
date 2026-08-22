#!/usr/bin/env python3
"""Run locked ChineseEEG semantic RSA for one model-panel embedding set.

This mirrors the nuisance control and inference used for the pinned BERT analysis.
Only the semantic embedding source changes. No neural representation, nuisance set,
statistic, or permutation scheme is altered.
"""

from __future__ import annotations

import argparse
import csv
import json
import string
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import rankdata

DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-10", "sub-13", "sub-14", "sub-15",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_dir(root: Path, required: str) -> Path:
    candidates = [d for d in root.iterdir() if d.is_dir() and (d / required).exists()] if root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No directory containing {required} under {root}")
    return sorted(candidates)[-1]


def latest_feature_dir(root: Path, subject: str) -> Path:
    return latest_dir(root / subject, "row_mean.npy")


def zscore_columns(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    mean = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - mean) / sd


def rank_z(x: np.ndarray) -> np.ndarray:
    r = rankdata(np.asarray(x, dtype=np.float64), method="average")
    r -= r.mean()
    sd = r.std()
    if sd == 0:
        raise RuntimeError("Zero-variance ranked vector")
    return r / sd


def residualize_ranked(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    X = np.column_stack([np.ones_like(yr), *[rank_z(n) for n in nuisances]])
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    resid -= resid.mean()
    sd = resid.std()
    if sd == 0:
        raise RuntimeError("Zero-variance residual")
    return resid / sd


def char_set_jaccard_rdm(texts: list[str]) -> np.ndarray:
    sets = [set(t) for t in texts]
    out = []
    for i in range(len(sets) - 1):
        for j in range(i + 1, len(sets)):
            union = len(sets[i] | sets[j])
            sim = len(sets[i] & sets[j]) / union if union else 1.0
            out.append(1.0 - sim)
    return np.asarray(out, dtype=np.float64)


def punctuation_count(text: str) -> int:
    punct = set(string.punctuation) | set("，。！？；：、“”‘’（）《》〈〉【】…—·")
    return sum(ch in punct for ch in text)


def shifted_indices_within_chapter(chapters: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    idx = np.arange(len(chapters))
    shifted = idx.copy()
    for chapter in np.unique(chapters):
        loc = np.flatnonzero(chapters == chapter)
        if len(loc) > 1:
            shift = int(rng.integers(1, len(loc)))
            shifted[loc] = np.roll(loc, shift)
    return shifted


def print_progress(done: int, total: int, started: float, width: int = 36) -> None:
    """Print a lightweight terminal progress bar with elapsed time and ETA."""
    frac = min(max(done / total, 0.0), 1.0)
    filled = int(round(width * frac))
    bar = "#" * filled + "-" * (width - filled)
    elapsed = time.monotonic() - started
    rate = done / elapsed if elapsed > 0 else 0.0
    eta = (total - done) / rate if rate > 0 else float("nan")
    eta_text = f"{eta / 60:.1f}m" if np.isfinite(eta) else "--"
    line = f"\rPermutations [{bar}] {done:>6}/{total} {100 * frac:5.1f}% | elapsed {elapsed / 60:.1f}m | ETA {eta_text}"
    print(line, end="", flush=True)
    if done >= total:
        print(flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Locked ChineseEEG RSA for one model-panel embedding set.")
    parser.add_argument("--embedding-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.permutations < 1000:
        raise SystemExit("--permutations must be >= 1000")

    emb_dir = latest_dir(args.embedding_root, "embeddings.npy")
    all_embeddings = np.load(emb_dir / "embeddings.npy").astype(np.float64)
    emb_summary = json.loads((emb_dir / "summary.json").read_text(encoding="utf-8"))
    run_number = int(emb_summary["run_number"])
    if run_number == 7:
        raise SystemExit("Run 07 is sealed for cross-model holdout")

    subjects = list(args.subjects)
    ref_texts = None
    ref_embedding_idx = None
    ref_chapters = None
    orth_rdm = None
    punct_rdm = None
    neural_resid: dict[str, np.ndarray] = {}
    nuisance_sets: dict[str, list[np.ndarray]] = {}
    feature_dirs: dict[str, str] = {}

    for subject in subjects:
        d = latest_feature_dir(args.feature_root, subject)
        meta = read_csv(d / "metadata.csv")
        x = np.load(d / "row_mean.npy").astype(np.float64)
        texts = [r["text"] for r in meta]
        embedding_idx = [int(r["embedding_index"]) for r in meta]
        chapters = np.array([int((r["chapter_marker_context"] or "CH00")[2:]) for r in meta], dtype=int)

        if ref_texts is None:
            ref_texts = texts
            ref_embedding_idx = embedding_idx
            ref_chapters = chapters
            orth_rdm = char_set_jaccard_rdm(texts)
            punct = np.array([punctuation_count(t) for t in texts], dtype=float)
            punct_rdm = pdist(punct[:, None], metric="cityblock")
        else:
            if texts != ref_texts or embedding_idx != ref_embedding_idx or not np.array_equal(chapters, ref_chapters):
                raise SystemExit(f"Canonical row identity mismatch for {subject}")

        neural = pdist(zscore_columns(x), metric="correlation")
        position = np.array([float(r["run_position_fraction"]) for r in meta], dtype=float)
        duration = np.array([float(r["duration_sec"]) for r in meta], dtype=float)
        char_count = np.array([float(r["char_count"]) for r in meta], dtype=float)
        nuisances = [
            pdist(position[:, None], metric="cityblock"),
            pdist(duration[:, None], metric="cityblock"),
            pdist(char_count[:, None], metric="cityblock"),
            pdist(chapters[:, None], metric="hamming"),
            orth_rdm,
            punct_rdm,
        ]
        neural_resid[subject] = residualize_ranked(neural, nuisances)
        nuisance_sets[subject] = nuisances
        feature_dirs[subject] = str(d)

    assert ref_embedding_idx is not None and ref_chapters is not None
    idx = np.asarray(ref_embedding_idx, dtype=int)
    if idx.max() >= all_embeddings.shape[0]:
        raise SystemExit("Manifest embedding index exceeds embedding array")
    semantic_rdm = pdist(all_embeddings[idx], metric="cosine")
    if not np.isfinite(semantic_rdm).all():
        raise SystemExit("Non-finite semantic RDM")

    by_subject = {}
    for subject in subjects:
        sr = residualize_ranked(semantic_rdm, nuisance_sets[subject])
        by_subject[subject] = float(np.mean(neural_resid[subject] * sr))
    observed_mean = float(np.mean(list(by_subject.values())))
    observed_median = float(np.median(list(by_subject.values())))

    rng = np.random.default_rng(args.seed)
    iu = np.triu_indices(len(ref_chapters), 1)
    square = squareform(semantic_rdm)
    null = np.empty(args.permutations, dtype=np.float64)
    progress_every = max(1, args.permutations // 100)
    started = time.monotonic()
    print(f"Running {args.permutations:,} within-chapter permutations for run-{run_number:02d}...", flush=True)
    print_progress(0, args.permutations, started)
    for p in range(args.permutations):
        perm_idx = shifted_indices_within_chapter(ref_chapters, rng)
        shifted = square[np.ix_(perm_idx, perm_idx)][iu]
        vals = []
        for subject in subjects:
            sr = residualize_ranked(shifted, nuisance_sets[subject])
            vals.append(float(np.mean(neural_resid[subject] * sr)))
        null[p] = float(np.mean(vals))
        done = p + 1
        if done == args.permutations or done % progress_every == 0:
            print_progress(done, args.permutations, started)

    p_value = float((1 + np.sum(null >= observed_mean)) / (args.permutations + 1))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    np.save(out / "within_chapter_shift_null.npy", null)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "embedding_dir": str(emb_dir),
        "embedding_provenance": emb_summary,
        "subjects": subjects,
        "n_subjects": len(subjects),
        "n_rows": len(ref_texts or []),
        "neural_representation": "row_mean, featurewise z-score, correlation-distance RDM",
        "nuisances": [
            "run_position_lag", "duration_difference", "character_count_difference",
            "chapter_mismatch", "character_set_jaccard_distance", "punctuation_count_difference",
        ],
        "statistic": "partial Spearman: Pearson correlation between residualized rank-z RDM vectors",
        "permutations": args.permutations,
        "seed": args.seed,
        "observed": {"mean": observed_mean, "median": observed_median, "by_subject": by_subject},
        "inference": {
            "null_mean": float(null.mean()),
            "null_sd": float(null.std()),
            "p_ge_observed": p_value,
        },
        "feature_dirs": feature_dirs,
        "notes": [
            "All neural and nuisance analysis choices are locked to the original BERT analysis.",
            "Only the prespecified model-family embedding source changes.",
            "Run 07 is excluded during model screening.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Model-panel RSA output: {out}")
    print(f"Model: {emb_summary.get('model_id')}@{emb_summary.get('model_revision')}")
    print(f"Run: {run_number:02d} | subjects: {len(subjects)} | rows: {len(ref_texts or [])}")
    print(f"Mean partial-Spearman={observed_mean:.4f} median={observed_median:.4f} | null mean={null.mean():.4f} sd={null.std():.4f} p={p_value:.5g}")
    print("  per subject: " + " ".join(f"{s}={by_subject[s]:.4f}" for s in subjects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
