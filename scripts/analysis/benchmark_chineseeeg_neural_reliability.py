#!/usr/bin/env python3
"""Benchmark simple ChineseEEG neural representations by cross-subject RDM reliability.

This script does not use semantic embeddings. It compares several prespecified,
transparent neural representations to determine whether the current low cross-subject
RDM reliability is specific to the original flattened 8-bin representation.

Representations:
- relative_flat_corr: flattened relative-bin means, featurewise z-score, correlation distance
- relative_binwise_corr_mean: correlation-distance RDM within each time bin, then mean across bins
- row_mean_corr: whole-row sensor means, featurewise z-score, correlation distance
- row_std_corr: whole-row sensor SD, featurewise z-score, correlation distance
- relative_pca{K}_euclidean: PCA on flattened relative-bin features within subject, Euclidean RDM

PCA is unsupervised and fit independently within each subject. It is used only as a
reliability diagnostic, not as evidence of semantic alignment. No cross-subject or
semantic information is used to fit any representation.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr
from sklearn.decomposition import PCA


DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-10", "sub-13", "sub-14", "sub-15",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_feature_dir(root: Path, subject: str, bins: int) -> Path:
    subject_root = root / subject
    candidates = []
    if subject_root.exists():
        for child in subject_root.iterdir():
            if (
                child.is_dir()
                and (child / f"relative_{bins}bin_mean.npy").exists()
                and (child / "row_mean.npy").exists()
                and (child / "row_std.npy").exists()
                and (child / "metadata.csv").exists()
            ):
                candidates.append(child)
    if not candidates:
        raise FileNotFoundError(f"No complete feature directory for {subject} under {subject_root}")
    return sorted(candidates)[-1]


def zscore_columns(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    mean = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - mean) / sd


def safe_rdm(x: np.ndarray, metric: str) -> np.ndarray:
    rdm = pdist(np.asarray(x, dtype=np.float64), metric=metric)
    if not np.isfinite(rdm).all():
        raise RuntimeError(f"Non-finite RDM using metric={metric}")
    return rdm


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise RuntimeError("Non-finite Spearman correlation")
    return rho


def reliability(rdms: dict[str, np.ndarray], subjects: list[str]) -> dict[str, object]:
    n = len(subjects)
    matrix = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            rho = safe_spearman(rdms[subjects[i]], rdms[subjects[j]])
            matrix[i, j] = rho
            matrix[j, i] = rho

    upper = matrix[np.triu_indices(n, k=1)]
    loo = {}
    for subject in subjects:
        consensus = np.mean(np.stack([rdms[s] for s in subjects if s != subject]), axis=0)
        loo[subject] = safe_spearman(rdms[subject], consensus)
    loo_values = np.array(list(loo.values()), dtype=float)

    return {
        "pairwise_mean": float(np.mean(upper)),
        "pairwise_median": float(np.median(upper)),
        "pairwise_min": float(np.min(upper)),
        "pairwise_max": float(np.max(upper)),
        "loo_mean": float(np.mean(loo_values)),
        "loo_median": float(np.median(loo_values)),
        "loo_min": float(np.min(loo_values)),
        "loo_max": float(np.max(loo_values)),
        "loo_by_subject": loo,
        "matrix": matrix,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark ChineseEEG neural RDM reliability without semantic targets.")
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--relative-bins", type=int, default=8)
    parser.add_argument("--pca-components", nargs="+", type=int, default=[16, 32, 64])
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_neural_reliability_benchmark"))
    args = parser.parse_args()

    subjects = list(args.subjects)
    if len(subjects) < 3:
        raise SystemExit("Need at least 3 subjects")

    relative: dict[str, np.ndarray] = {}
    row_mean: dict[str, np.ndarray] = {}
    row_std: dict[str, np.ndarray] = {}
    feature_dirs: dict[str, str] = {}

    ref_texts = None
    ref_alignment = None
    ref_channels = None

    for subject in subjects:
        feature_dir = latest_feature_dir(args.feature_root, subject, args.relative_bins)
        meta = read_csv(feature_dir / "metadata.csv")
        texts = [r["text"] for r in meta]
        alignment = [r["alignment_index"] for r in meta]
        channels = (feature_dir / "channels.txt").read_text(encoding="utf-8").splitlines()

        if ref_texts is None:
            ref_texts, ref_alignment, ref_channels = texts, alignment, channels
        else:
            if texts != ref_texts:
                raise SystemExit(f"Text ordering mismatch for {subject}")
            if alignment != ref_alignment:
                raise SystemExit(f"Alignment ordering mismatch for {subject}")
            if channels != ref_channels:
                raise SystemExit(f"Channel ordering mismatch for {subject}")

        rel = np.load(feature_dir / f"relative_{args.relative_bins}bin_mean.npy").astype(np.float64)
        mean = np.load(feature_dir / "row_mean.npy").astype(np.float64)
        std = np.load(feature_dir / "row_std.npy").astype(np.float64)
        if not (np.isfinite(rel).all() and np.isfinite(mean).all() and np.isfinite(std).all()):
            raise SystemExit(f"Non-finite mandatory features for {subject}")

        relative[subject] = rel
        row_mean[subject] = mean
        row_std[subject] = std
        feature_dirs[subject] = str(feature_dir)

    variants: dict[str, dict[str, np.ndarray]] = {}

    flat_rdms = {}
    binwise_rdms = {}
    mean_rdms = {}
    std_rdms = {}

    for subject in subjects:
        rel = relative[subject]
        flat = zscore_columns(rel.reshape(rel.shape[0], -1))
        flat_rdms[subject] = safe_rdm(flat, "correlation")

        per_bin = []
        for b in range(rel.shape[1]):
            xb = zscore_columns(rel[:, b, :])
            per_bin.append(safe_rdm(xb, "correlation"))
        binwise_rdms[subject] = np.mean(np.stack(per_bin, axis=0), axis=0)

        mean_rdms[subject] = safe_rdm(zscore_columns(row_mean[subject]), "correlation")
        std_rdms[subject] = safe_rdm(zscore_columns(row_std[subject]), "correlation")

    variants["relative_flat_corr"] = flat_rdms
    variants["relative_binwise_corr_mean"] = binwise_rdms
    variants["row_mean_corr"] = mean_rdms
    variants["row_std_corr"] = std_rdms

    for k in args.pca_components:
        pca_rdms = {}
        for subject in subjects:
            rel = relative[subject]
            flat = zscore_columns(rel.reshape(rel.shape[0], -1))
            max_k = min(flat.shape[0] - 1, flat.shape[1])
            if k > max_k:
                raise SystemExit(f"Requested PCA components {k} exceed maximum {max_k}")
            scores = PCA(n_components=k, svd_solver="full").fit_transform(flat)
            pca_rdms[subject] = safe_rdm(scores, "euclidean")
        variants[f"relative_pca{k}_euclidean"] = pca_rdms

    results = {name: reliability(rdms, subjects) for name, rdms in variants.items()}
    ranking = sorted(results, key=lambda name: results[name]["loo_mean"], reverse=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    with (out / "benchmark.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "rank", "representation", "pairwise_mean", "pairwise_median",
            "pairwise_min", "pairwise_max", "loo_mean", "loo_median", "loo_min", "loo_max"
        ])
        for rank, name in enumerate(ranking, start=1):
            r = results[name]
            writer.writerow([
                rank, name,
                r["pairwise_mean"], r["pairwise_median"], r["pairwise_min"], r["pairwise_max"],
                r["loo_mean"], r["loo_median"], r["loo_min"], r["loo_max"],
            ])

    serializable = {}
    for name, r in results.items():
        serializable[name] = {k: v for k, v in r.items() if k != "matrix"}

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "subjects": subjects,
        "n_subjects": len(subjects),
        "n_rows": len(ref_texts or []),
        "n_channels": len(ref_channels or []),
        "relative_bins": args.relative_bins,
        "pca_components": args.pca_components,
        "ranking_by_loo_mean": ranking,
        "results": serializable,
        "feature_dirs": feature_dirs,
        "notes": [
            "No semantic embeddings or linguistic targets are used.",
            "This is a representation-reliability benchmark, not a semantic test.",
            "PCA is fit separately within each subject and can change RDM geometry through dimensionality reduction.",
            "Orthogonal Procrustes is not included as a way to improve individual Euclidean/cosine RDM reliability because pure rotations preserve those pairwise distances.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Neural reliability benchmark output: {out}")
    print(f"Subjects: {len(subjects)} | rows: {len(ref_texts or [])} | channels: {len(ref_channels or [])}")
    print("Ranking by LOO-consensus Spearman:")
    for rank, name in enumerate(ranking, start=1):
        r = results[name]
        print(
            f"  {rank}. {name}: "
            f"LOO mean={r['loo_mean']:.4f} median={r['loo_median']:.4f} "
            f"| pairwise mean={r['pairwise_mean']:.4f} median={r['pairwise_median']:.4f}"
        )
    print("No semantic inference should be made from this benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
