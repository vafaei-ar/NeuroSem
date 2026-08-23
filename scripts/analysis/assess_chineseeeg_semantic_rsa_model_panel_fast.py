#!/usr/bin/env python3
"""Fast, validation-friendly ChineseEEG model-panel semantic RSA.

This implements the same locked statistic and within-chapter circular-shift null as
assess_chineseeeg_semantic_rsa_model_panel.py, but removes repeated work from the
permutation loop and parallelizes independent permutations across CPU processes.

Key equivalences used for speed:
1. A label permutation only reorders semantic pairwise distances, so the ranked,
   standardized semantic RDM can be computed once and then permuted.
2. Nuisance design matrices are fixed within a subject, so their residual subspace
   basis is computed once.
3. Because the standardized neural residual is already orthogonal to the nuisance
   design, the residualized semantic-neural correlation can be computed from dot
   products plus the semantic residual norm without materializing a full residual
   vector for every subject and permutation.

Use --validate-null with a null array from the legacy implementation before adopting
this script for new confirmatory model-panel runs.
"""

from __future__ import annotations

import os

# Prevent each worker from spawning its own large BLAS thread pool. Parallelism is
# controlled explicitly at the permutation-worker level below.
for _name in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_name, "1")

import argparse
import csv
import json
import math
import multiprocessing as mp
import string
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import rankdata

DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-10", "sub-13", "sub-14", "sub-15",
]

# Globals inherited by forked workers. This avoids repeatedly pickling large arrays.
_G_RANK_SQUARE = None
_G_IU = None
_G_NEURAL = None
_G_Q_BASES = None
_G_PERM_INDICES = None
_G_N_EDGES = None


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


def nuisance_design(nuisances: list[np.ndarray]) -> np.ndarray:
    base = np.ones_like(np.asarray(nuisances[0], dtype=np.float64))
    return np.column_stack([base, *[rank_z(n) for n in nuisances]])


def residualize_ranked(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    """Legacy-equivalent residualization used for observed statistics."""
    yr = rank_z(y)
    X = nuisance_design(nuisances)
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    resid -= resid.mean()
    sd = resid.std()
    if sd == 0:
        raise RuntimeError("Zero-variance residual")
    return resid / sd


def orthonormal_column_basis(X: np.ndarray) -> np.ndarray:
    """Return an orthonormal basis for col(X), robust to rank deficiency."""
    U, s, _ = np.linalg.svd(np.asarray(X, dtype=np.float64), full_matrices=False)
    if len(s) == 0 or s[0] == 0:
        raise RuntimeError("Degenerate nuisance design")
    tol = max(X.shape) * np.finfo(np.float64).eps * s[0]
    keep = s > tol
    if not np.any(keep):
        raise RuntimeError("Nuisance design has zero numerical rank")
    return np.ascontiguousarray(U[:, keep], dtype=np.float64)


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
    idx = np.arange(len(chapters), dtype=np.int32)
    shifted = idx.copy()
    for chapter in np.unique(chapters):
        loc = np.flatnonzero(chapters == chapter).astype(np.int32)
        if len(loc) > 1:
            shift = int(rng.integers(1, len(loc)))
            shifted[loc] = np.roll(loc, shift)
    return shifted


def print_progress(done: int, total: int, started: float, width: int = 36) -> None:
    frac = min(max(done / total, 0.0), 1.0)
    filled = int(round(width * frac))
    bar = "#" * filled + "-" * (width - filled)
    elapsed = time.monotonic() - started
    rate = done / elapsed if elapsed > 0 else 0.0
    eta = (total - done) / rate if rate > 0 else float("nan")
    eta_text = f"{eta / 60:.1f}m" if np.isfinite(eta) else "--"
    print(
        f"\rPermutations [{bar}] {done:>6}/{total} {100 * frac:5.1f}% | "
        f"elapsed {elapsed / 60:.1f}m | ETA {eta_text}",
        end="",
        flush=True,
    )
    if done >= total:
        print(flush=True)


def _fast_stat_from_ranked_semantic(y: np.ndarray) -> float:
    """Mean subject statistic for one already rank-z semantic edge vector."""
    vals = np.empty(_G_NEURAL.shape[0], dtype=np.float64)
    yy = float(np.dot(y, y))
    for s in range(_G_NEURAL.shape[0]):
        q = _G_Q_BASES[s]
        proj = q.T @ y
        resid_ss = yy - float(np.dot(proj, proj))
        # Numerical guard only; a true non-positive residual variance would be invalid.
        resid_var = max(resid_ss / _G_N_EDGES, np.finfo(np.float64).tiny)
        resid_sd = math.sqrt(resid_var)
        vals[s] = float(np.dot(_G_NEURAL[s], y) / _G_N_EDGES / resid_sd)
    return float(vals.mean())


def _worker_chunk(start_stop: tuple[int, int]) -> tuple[int, np.ndarray]:
    start, stop = start_stop
    out = np.empty(stop - start, dtype=np.float64)
    for j, p in enumerate(range(start, stop)):
        perm_idx = _G_PERM_INDICES[p]
        y = _G_RANK_SQUARE[np.ix_(perm_idx, perm_idx)][_G_IU]
        out[j] = _fast_stat_from_ranked_semantic(y)
    return start, out


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast locked ChineseEEG RSA for one model-panel embedding set.")
    parser.add_argument("--embedding-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--workers", type=int, default=min(16, max(1, (os.cpu_count() or 4) // 4)))
    parser.add_argument("--chunk-size", type=int, default=50)
    parser.add_argument("--validate-null", type=Path, default=None,
                        help="Optional legacy within_chapter_shift_null.npy for numerical equivalence validation.")
    parser.add_argument("--validation-tol", type=float, default=1e-10)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.permutations < 1000:
        raise SystemExit("--permutations must be >= 1000")
    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")
    if args.chunk_size < 1:
        raise SystemExit("--chunk-size must be >= 1")

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
    q_bases: dict[str, np.ndarray] = {}
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
        q_bases[subject] = orthonormal_column_basis(nuisance_design(nuisances))
        feature_dirs[subject] = str(d)

    assert ref_embedding_idx is not None and ref_chapters is not None
    idx = np.asarray(ref_embedding_idx, dtype=int)
    if idx.max() >= all_embeddings.shape[0]:
        raise SystemExit("Manifest embedding index exceeds embedding array")
    semantic_rdm = pdist(all_embeddings[idx], metric="cosine")
    if not np.isfinite(semantic_rdm).all():
        raise SystemExit("Non-finite semantic RDM")

    # Observed statistics deliberately use the original implementation path.
    by_subject = {}
    for subject in subjects:
        sr = residualize_ranked(semantic_rdm, nuisance_sets[subject])
        by_subject[subject] = float(np.mean(neural_resid[subject] * sr))
    observed_mean = float(np.mean(list(by_subject.values())))
    observed_median = float(np.median(list(by_subject.values())))

    # Rank once. Every circular shift only permutes these pairwise values, so ranking
    # each permutation again is mathematically redundant.
    semantic_ranked = rank_z(semantic_rdm)
    rank_square = squareform(semantic_ranked)
    iu = np.triu_indices(len(ref_chapters), 1)
    n_edges = len(semantic_ranked)

    # Pre-generate the exact same permutation sequence as the legacy serial code.
    rng = np.random.default_rng(args.seed)
    perm_indices = np.empty((args.permutations, len(ref_chapters)), dtype=np.int32)
    for p in range(args.permutations):
        perm_indices[p] = shifted_indices_within_chapter(ref_chapters, rng)

    # Install read-only-ish globals before forking so workers share pages by copy-on-write.
    global _G_RANK_SQUARE, _G_IU, _G_NEURAL, _G_Q_BASES, _G_PERM_INDICES, _G_N_EDGES
    _G_RANK_SQUARE = np.ascontiguousarray(rank_square, dtype=np.float64)
    _G_IU = iu
    _G_NEURAL = np.ascontiguousarray(np.stack([neural_resid[s] for s in subjects]), dtype=np.float64)
    _G_Q_BASES = [q_bases[s] for s in subjects]
    _G_PERM_INDICES = perm_indices
    _G_N_EDGES = n_edges

    null = np.empty(args.permutations, dtype=np.float64)
    chunks = [(start, min(start + args.chunk_size, args.permutations))
              for start in range(0, args.permutations, args.chunk_size)]
    started = time.monotonic()
    done = 0
    print(
        f"Running {args.permutations:,} optimized within-chapter permutations for run-{run_number:02d} "
        f"with {args.workers} workers...",
        flush=True,
    )
    print_progress(0, args.permutations, started)

    if args.workers == 1:
        for chunk in chunks:
            start, vals = _worker_chunk(chunk)
            null[start:start + len(vals)] = vals
            done += len(vals)
            print_progress(done, args.permutations, started)
    else:
        try:
            ctx = mp.get_context("fork")
        except ValueError:
            ctx = mp.get_context()
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as pool:
            futures = [pool.submit(_worker_chunk, chunk) for chunk in chunks]
            for fut in as_completed(futures):
                start, vals = fut.result()
                null[start:start + len(vals)] = vals
                done += len(vals)
                print_progress(done, args.permutations, started)

    p_value = float((1 + np.sum(null >= observed_mean)) / (args.permutations + 1))
    elapsed = time.monotonic() - started

    validation = None
    if args.validate_null is not None:
        ref = np.load(args.validate_null).astype(np.float64)
        n_compare = min(len(ref), len(null))
        delta = null[:n_compare] - ref[:n_compare]
        max_abs = float(np.max(np.abs(delta))) if n_compare else float("nan")
        mean_abs = float(np.mean(np.abs(delta))) if n_compare else float("nan")
        corr = float(np.corrcoef(null[:n_compare], ref[:n_compare])[0, 1]) if n_compare > 1 else float("nan")
        passed = bool(n_compare == args.permutations and max_abs <= args.validation_tol)
        validation = {
            "reference_null": str(args.validate_null.resolve()),
            "n_compared": int(n_compare),
            "max_abs_difference": max_abs,
            "mean_abs_difference": mean_abs,
            "correlation": corr,
            "tolerance": float(args.validation_tol),
            "passed": passed,
        }
        status = "PASS" if passed else "FAIL"
        print(
            f"Legacy-null validation: {status} | n={n_compare} | max abs diff={max_abs:.3e} | "
            f"mean abs diff={mean_abs:.3e} | r={corr:.12f}",
            flush=True,
        )
        if not passed:
            raise SystemExit(
                "Optimized null did not match the supplied legacy null within tolerance; "
                "do not use this implementation for confirmatory runs yet."
            )

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
        "optimization": {
            "implementation": "pre-ranked semantic RDM + cached nuisance subspaces + process-parallel permutations",
            "workers": int(args.workers),
            "chunk_size": int(args.chunk_size),
            "permutation_elapsed_seconds": float(elapsed),
            "blas_threads_per_worker": 1,
        },
        "validation": validation,
        "feature_dirs": feature_dirs,
        "notes": [
            "Observed statistics use the original residualization path.",
            "Permutation inference is mathematically equivalent to the locked legacy implementation.",
            "Use --validate-null against a legacy null array before first confirmatory use.",
            "Run 07 remains excluded during model screening.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Fast model-panel RSA output: {out}")
    print(f"Model: {emb_summary.get('model_id')}@{emb_summary.get('model_revision')}")
    print(f"Run: {run_number:02d} | subjects: {len(subjects)} | rows: {len(ref_texts or [])}")
    print(
        f"Mean partial-Spearman={observed_mean:.4f} median={observed_median:.4f} | "
        f"null mean={null.mean():.4f} sd={null.std():.4f} p={p_value:.5g}"
    )
    print(f"Permutation time: {elapsed / 60:.2f} min with {args.workers} workers")
    print("  per subject: " + " ".join(f"{s}={by_subject[s]:.4f}" for s in subjects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
