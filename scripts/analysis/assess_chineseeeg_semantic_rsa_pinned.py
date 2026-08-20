#!/usr/bin/env python3
"""Replicate ChineseEEG semantic RSA with independently generated pinned embeddings.

Primary statistic: partial Spearman correlation, implemented as Pearson correlation
between rank-transformed residualized neural and semantic RDM vectors.

Primary semantic target: pinned BERT final-layer mean-pooled embeddings.
Sensitivity target: pinned BERT mean-of-last-four-layers embeddings.

Inference uses within-chapter circular shifts and 10,000 permutations by default.
No representation selection is performed against the semantic result.
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


def pearson_standardized(a: np.ndarray, b: np.ndarray) -> float:
    # Inputs are centered and standardized residualized ranks.
    return float(np.mean(a * b))


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Pinned-embedding replication of ChineseEEG semantic RSA.")
    parser.add_argument("--embedding-root", type=Path, default=Path("outputs/chineseeeg_pinned_embeddings"))
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_semantic_rsa_pinned"))
    args = parser.parse_args()

    if args.permutations < 1000:
        raise SystemExit("--permutations must be >= 1000")

    emb_dir = latest_dir(args.embedding_root, "bert_base_chinese_final_mean.npy")
    final_all = np.load(emb_dir / "bert_base_chinese_final_mean.npy").astype(np.float64)
    last4_all = np.load(emb_dir / "bert_base_chinese_last4_mean.npy").astype(np.float64)
    emb_summary = json.loads((emb_dir / "summary.json").read_text(encoding="utf-8"))

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
    if idx.max() >= final_all.shape[0] or idx.max() >= last4_all.shape[0]:
        raise SystemExit("Manifest embedding index exceeds generated embedding arrays")

    targets = {
        "final_mean": pdist(final_all[idx], metric="cosine"),
        "last4_mean": pdist(last4_all[idx], metric="cosine"),
    }
    if not all(np.isfinite(v).all() for v in targets.values()):
        raise SystemExit("Non-finite semantic RDM")

    observed: dict[str, dict[str, object]] = {}
    sem_resid_by_target: dict[str, dict[str, np.ndarray]] = {}
    for name, sem_rdm in targets.items():
        by_subject = {}
        sem_resids = {}
        for subject in subjects:
            sr = residualize_ranked(sem_rdm, nuisance_sets[subject])
            sem_resids[subject] = sr
            by_subject[subject] = pearson_standardized(neural_resid[subject], sr)
        sem_resid_by_target[name] = sem_resids
        observed[name] = {
            "mean": float(np.mean(list(by_subject.values()))),
            "median": float(np.median(list(by_subject.values()))),
            "by_subject": by_subject,
        }

    rng = np.random.default_rng(args.seed)
    iu = np.triu_indices(len(ref_chapters), 1)
    squares = {name: squareform(rdm) for name, rdm in targets.items()}
    nulls = {name: np.empty(args.permutations, dtype=np.float64) for name in targets}

    for p in range(args.permutations):
        perm_idx = shifted_indices_within_chapter(ref_chapters, rng)
        for name, square in squares.items():
            shifted = square[np.ix_(perm_idx, perm_idx)][iu]
            vals = []
            for subject in subjects:
                sr = residualize_ranked(shifted, nuisance_sets[subject])
                vals.append(pearson_standardized(neural_resid[subject], sr))
            nulls[name][p] = float(np.mean(vals))

    inference = {}
    for name in targets:
        obs = float(observed[name]["mean"])
        null = nulls[name]
        inference[name] = {
            "null_mean": float(null.mean()),
            "null_sd": float(null.std()),
            "p_ge_observed": float((1 + np.sum(null >= obs)) / (args.permutations + 1)),
        }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name, null in nulls.items():
        np.save(out / f"{name}_within_chapter_shift_null.npy", null)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "embedding_dir": str(emb_dir),
        "embedding_provenance": emb_summary,
        "subjects": subjects,
        "n_subjects": len(subjects),
        "n_rows": len(ref_texts or []),
        "neural_representation": "row_mean, featurewise z-score, correlation-distance RDM",
        "semantic_targets": {
            "primary": "final_mean",
            "sensitivity": "last4_mean",
        },
        "nuisances": [
            "run_position_lag", "duration_difference", "character_count_difference",
            "chapter_mismatch", "character_set_jaccard_distance", "punctuation_count_difference",
        ],
        "statistic": "partial Spearman: Pearson correlation between residualized rank-z RDM vectors",
        "permutations": args.permutations,
        "seed": args.seed,
        "observed": observed,
        "inference": inference,
        "feature_dirs": feature_dirs,
        "notes": [
            "Primary neural representation was selected on cross-subject reliability before semantic testing.",
            "The final-layer mean-pooled embedding is the prespecified primary independently generated semantic target.",
            "The last-four-layer target is sensitivity analysis and should not replace the primary result post hoc.",
            "Within-chapter circular shifts preserve chapter membership and coarse serial organization while breaking exact row identity.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Pinned semantic RSA output: {out}")
    print(f"Subjects: {len(subjects)} | rows: {len(ref_texts or [])} | permutations: {args.permutations}")
    print(f"Embedding model: {emb_summary.get('model_id')}@{emb_summary.get('model_revision')}")
    for name in ["final_mean", "last4_mean"]:
        o = observed[name]
        inf = inference[name]
        label = "PRIMARY" if name == "final_mean" else "SENSITIVITY"
        print(
            f"{label} {name}: mean partial-Spearman={o['mean']:.4f} median={o['median']:.4f} | "
            f"null mean={inf['null_mean']:.4f} sd={inf['null_sd']:.4f} p={inf['p_ge_observed']:.5g}"
        )
        print("  per subject: " + " ".join(f"{s}={o['by_subject'][s]:.4f}" for s in subjects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
