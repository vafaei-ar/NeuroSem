#!/usr/bin/env python3
"""Exploratory nuisance-controlled semantic RSA for ChineseEEG LittlePrince run-01.

This is the first semantic checkpoint after establishing cross-subject reliability of
row-mean neural geometry. It intentionally uses the distributed author embeddings only
as an exploratory semantic target because their generation provenance is not yet fully
resolved. A positive result here is not sufficient for the NeuroSem primary claim.

Neural geometry per subject:
- row_mean.npy
- featurewise z-score across rows within subject
- correlation-distance RDM

Semantic geometry:
- distributed LittlePrince run-01 embedding array
- select the 391 semantic-eligible rows by embedding_index
- cosine-distance RDM

Nuisance RDMs per subject:
- run-position lag
- row-duration difference
- character-count difference
- chapter mismatch
- character-set Jaccard distance (orthographic overlap control)
- punctuation-count difference

Both neural and semantic RDMs are rank-transformed and residualized against the same
nuisance design before Spearman association. Inference uses within-chapter circular
shifts of semantic row labels, preserving chapter membership and coarse serial structure
while breaking exact neural-text alignment.
"""

from __future__ import annotations

import argparse
import csv
import json
import string
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import rankdata, spearmanr


DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-10", "sub-13", "sub-14", "sub-15",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_feature_dir(root: Path, subject: str) -> Path:
    subject_root = root / subject
    candidates = []
    if subject_root.exists():
        for child in subject_root.iterdir():
            if child.is_dir() and (child / "row_mean.npy").exists() and (child / "metadata.csv").exists():
                candidates.append(child)
    if not candidates:
        raise FileNotFoundError(f"No completed row_mean feature output for {subject} under {subject_root}")
    return sorted(candidates)[-1]


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


def residualize(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    X = np.column_stack([np.ones_like(yr), *[rank_z(n) for n in nuisances]])
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    sd = resid.std()
    if sd == 0:
        raise RuntimeError("Zero-variance residual RDM")
    return resid / sd


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise RuntimeError("Non-finite Spearman correlation")
    return rho


def char_set_jaccard_rdm(texts: list[str]) -> np.ndarray:
    sets = [set(t) for t in texts]
    n = len(sets)
    out = np.empty(n * (n - 1) // 2, dtype=np.float64)
    k = 0
    for i in range(n - 1):
        a = sets[i]
        for j in range(i + 1, n):
            b = sets[j]
            union = len(a | b)
            sim = (len(a & b) / union) if union else 1.0
            out[k] = 1.0 - sim
            k += 1
    return out


def punctuation_count(text: str) -> int:
    ascii_punct = set(string.punctuation)
    chinese_punct = set("，。！？；：、“”‘’（）《》〈〉【】…—·")
    return sum((ch in ascii_punct) or (ch in chinese_punct) for ch in text)


def shifted_indices_within_chapter(chapters: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    idx = np.arange(len(chapters))
    shifted = idx.copy()
    for chapter in np.unique(chapters):
        loc = np.flatnonzero(chapters == chapter)
        if len(loc) <= 1:
            continue
        shift = int(rng.integers(1, len(loc)))
        shifted[loc] = np.roll(loc, shift)
    return shifted


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploratory nuisance-controlled semantic RSA for ChineseEEG.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--run-number", type=int, default=1)
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_semantic_rsa_exploratory"))
    args = parser.parse_args()

    if args.permutations < 100:
        raise SystemExit("--permutations must be >= 100")

    dataset = args.dataset.expanduser().resolve()
    embed_path = dataset / "derivatives" / "text_embeddings" / "LittlePrince_text_embedding" / f"text_embedding_run_{args.run_number}.npy"
    if not embed_path.exists():
        raise SystemExit(f"Embedding file not materialized: {embed_path}")

    subjects = list(args.subjects)
    ref_texts = None
    ref_alignment = None
    ref_embedding_idx = None
    ref_chapters = None

    neural_rdms: dict[str, np.ndarray] = {}
    nuisance_sets: dict[str, list[np.ndarray]] = {}
    neural_resid: dict[str, np.ndarray] = {}
    raw_rhos: dict[str, float] = {}
    residual_rhos: dict[str, float] = {}
    feature_dirs: dict[str, str] = {}

    author_embeddings = np.load(embed_path, mmap_mode="r")
    if author_embeddings.ndim != 2:
        raise SystemExit(f"Unexpected embedding shape: {author_embeddings.shape}")

    orthographic_rdm = None
    punctuation_rdm = None
    semantic_rdm = None

    for subject in subjects:
        d = latest_feature_dir(args.feature_root, subject)
        meta = read_csv(d / "metadata.csv")
        x = np.load(d / "row_mean.npy").astype(np.float64)
        texts = [r["text"] for r in meta]
        alignment = [int(r["alignment_index"]) for r in meta]
        embedding_idx = [int(r["embedding_index"]) for r in meta]
        chapters = np.array([int((r["chapter_marker_context"] or "CH00")[2:]) for r in meta], dtype=int)

        if ref_texts is None:
            ref_texts = texts
            ref_alignment = alignment
            ref_embedding_idx = embedding_idx
            ref_chapters = chapters
            if max(embedding_idx) >= author_embeddings.shape[0]:
                raise SystemExit("Embedding index exceeds distributed embedding array")
            selected_embeddings = np.asarray(author_embeddings[embedding_idx], dtype=np.float64)
            semantic_rdm = pdist(selected_embeddings, metric="cosine")
            if not np.isfinite(semantic_rdm).all():
                raise SystemExit("Non-finite semantic RDM")
            orthographic_rdm = char_set_jaccard_rdm(texts)
            punct = np.array([punctuation_count(t) for t in texts], dtype=float)
            punctuation_rdm = pdist(punct[:, None], metric="cityblock")
        else:
            if texts != ref_texts:
                raise SystemExit(f"Text ordering mismatch for {subject}")
            if alignment != ref_alignment:
                raise SystemExit(f"Alignment-index ordering mismatch for {subject}")
            if embedding_idx != ref_embedding_idx:
                raise SystemExit(f"Embedding-index ordering mismatch for {subject}")
            if not np.array_equal(chapters, ref_chapters):
                raise SystemExit(f"Chapter ordering mismatch for {subject}")

        if x.shape[0] != len(meta):
            raise SystemExit(f"Feature/metadata row mismatch for {subject}")
        if not np.isfinite(x).all():
            raise SystemExit(f"Non-finite row_mean values for {subject}")

        neural = pdist(zscore_columns(x), metric="correlation")
        position = np.array([float(r["run_position_fraction"]) for r in meta], dtype=float)
        duration = np.array([float(r["duration_sec"]) for r in meta], dtype=float)
        char_count = np.array([float(r["char_count"]) for r in meta], dtype=float)

        nuisances = [
            pdist(position[:, None], metric="cityblock"),
            pdist(duration[:, None], metric="cityblock"),
            pdist(char_count[:, None], metric="cityblock"),
            pdist(chapters[:, None], metric="hamming"),
            orthographic_rdm,
            punctuation_rdm,
        ]

        neural_rdms[subject] = neural
        nuisance_sets[subject] = nuisances
        neural_resid[subject] = residualize(neural, nuisances)
        raw_rhos[subject] = safe_spearman(neural, semantic_rdm)
        sem_resid = residualize(semantic_rdm, nuisances)
        residual_rhos[subject] = safe_spearman(neural_resid[subject], sem_resid)
        feature_dirs[subject] = str(d)

    assert semantic_rdm is not None
    assert ref_chapters is not None

    observed_raw = float(np.mean(list(raw_rhos.values())))
    observed_resid = float(np.mean(list(residual_rhos.values())))

    semantic_square = squareform(semantic_rdm)
    iu = np.triu_indices(len(ref_chapters), k=1)
    rng = np.random.default_rng(args.seed)
    null = np.empty(args.permutations, dtype=np.float64)

    for p in range(args.permutations):
        perm_idx = shifted_indices_within_chapter(ref_chapters, rng)
        shifted_sem = semantic_square[np.ix_(perm_idx, perm_idx)][iu]
        vals = []
        for subject in subjects:
            shifted_sem_resid = residualize(shifted_sem, nuisance_sets[subject])
            vals.append(safe_spearman(neural_resid[subject], shifted_sem_resid))
        null[p] = float(np.mean(vals))

    p_ge = float((1 + np.sum(null >= observed_resid)) / (args.permutations + 1))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    with (out / "subject_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["subject", "raw_rho", "residual_rho", "feature_dir"])
        writer.writeheader()
        for subject in subjects:
            writer.writerow({
                "subject": subject,
                "raw_rho": raw_rhos[subject],
                "residual_rho": residual_rhos[subject],
                "feature_dir": feature_dirs[subject],
            })

    np.save(out / "within_chapter_shift_null_mean_rho.npy", null)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "subjects": subjects,
        "n_subjects": len(subjects),
        "n_rows": len(ref_texts or []),
        "embedding_path": str(embed_path),
        "embedding_shape": list(author_embeddings.shape),
        "neural_representation": "row_mean featurewise-zscored, correlation-distance RDM",
        "semantic_representation": "distributed author embedding, cosine-distance RDM",
        "nuisances": [
            "run_position_lag",
            "duration_difference",
            "character_count_difference",
            "chapter_mismatch",
            "character_set_jaccard_distance",
            "punctuation_count_difference",
        ],
        "raw_rho_mean": observed_raw,
        "residual_rho_mean": observed_resid,
        "raw_rho_by_subject": raw_rhos,
        "residual_rho_by_subject": residual_rhos,
        "within_chapter_circular_shift_null": {
            "permutations": args.permutations,
            "seed": args.seed,
            "mean": float(null.mean()),
            "sd": float(null.std()),
            "p_ge_observed": p_ge,
        },
        "notes": [
            "Exploratory only: distributed embedding-generation provenance is unresolved and must not be treated as the primary semantic target.",
            "Both neural and semantic RDMs are rank-residualized against the same nuisance design per subject.",
            "Within-chapter circular shifts preserve chapter membership and coarse serial structure while breaking exact row alignment.",
            "A positive result requires replication with independently generated pinned language-model embeddings and stronger lexical/visual/ocular nuisance controls before supporting H1.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Exploratory semantic RSA output: {out}")
    print(f"Subjects: {len(subjects)} | rows: {len(ref_texts or [])}")
    print(f"Author embedding shape: {tuple(author_embeddings.shape)}")
    print(f"Raw semantic-neural Spearman mean: {observed_raw:.4f}")
    print(f"Residual semantic-neural Spearman mean: {observed_resid:.4f}")
    print(
        "Within-chapter circular-shift null: "
        f"mean={null.mean():.4f} sd={null.std():.4f} observed={observed_resid:.4f} p={p_ge:.4g}"
    )
    print("Per-subject residual rho:")
    for subject in subjects:
        print(f"  {subject}: {residual_rhos[subject]:.4f}")
    print("Interpretation: exploratory semantic checkpoint only; author embedding provenance remains unresolved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
