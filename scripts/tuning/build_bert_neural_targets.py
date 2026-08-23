#!/usr/bin/env python3
"""Build frozen run-level residual neural geometry targets for BERT tuning.

The implementation mirrors the locked ChineseEEG RSA preprocessing. It never uses
language-model embeddings and therefore can be run before tuning without leaking model
performance into target construction.
"""

from __future__ import annotations

import argparse
import csv
import json
import string
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import rankdata


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
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - x.mean(axis=0)) / sd


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
    out: list[float] = []
    for i in range(len(sets) - 1):
        for j in range(i + 1, len(sets)):
            union = len(sets[i] | sets[j])
            sim = len(sets[i] & sets[j]) / union if union else 1.0
            out.append(1.0 - sim)
    return np.asarray(out, dtype=np.float64)


def punctuation_count(text: str) -> int:
    punct = set(string.punctuation) | set("，。！？；：、“”‘’（）《》〈〉【】…—·")
    return sum(ch in punct for ch in text)


def feature_root_for_run(base: Path, run_number: int) -> Path:
    return base if run_number == 1 else base / f"run-{run_number:02d}"


def build_one(run_number: int, feature_base: Path, subjects: list[str], seed: int, out_root: Path) -> Path:
    feature_root = feature_root_for_run(feature_base, run_number)
    ref_texts: list[str] | None = None
    ref_embedding_idx: list[int] | None = None
    ref_chapters: np.ndarray | None = None
    orth_rdm: np.ndarray | None = None
    punct_rdm: np.ndarray | None = None
    subject_residuals: list[np.ndarray] = []
    used_subjects: list[str] = []
    feature_dirs: dict[str, str] = {}

    for subject in subjects:
        try:
            d = latest_feature_dir(feature_root, subject)
        except FileNotFoundError:
            continue
        meta = read_csv(d / "metadata.csv")
        x = np.load(d / "row_mean.npy").astype(np.float64)
        texts = [r["text"] for r in meta]
        embedding_idx = [int(r["embedding_index"]) for r in meta]
        chapters = np.asarray([int((r["chapter_marker_context"] or "CH00")[2:]) for r in meta], dtype=int)

        if ref_texts is None:
            ref_texts = texts
            ref_embedding_idx = embedding_idx
            ref_chapters = chapters
            orth_rdm = char_set_jaccard_rdm(texts)
            punct = np.asarray([punctuation_count(t) for t in texts], dtype=float)
            punct_rdm = pdist(punct[:, None], metric="cityblock")
        elif texts != ref_texts or embedding_idx != ref_embedding_idx or not np.array_equal(chapters, ref_chapters):
            raise SystemExit(f"Canonical row identity mismatch for run-{run_number:02d} {subject}")

        neural = pdist(zscore_columns(x), metric="correlation")
        position = np.asarray([float(r["run_position_fraction"]) for r in meta], dtype=float)
        duration = np.asarray([float(r["duration_sec"]) for r in meta], dtype=float)
        char_count = np.asarray([float(r["char_count"]) for r in meta], dtype=float)
        nuisances = [
            pdist(position[:, None], metric="cityblock"),
            pdist(duration[:, None], metric="cityblock"),
            pdist(char_count[:, None], metric="cityblock"),
            pdist(chapters[:, None], metric="hamming"),
            orth_rdm,
            punct_rdm,
        ]
        subject_residuals.append(residualize_ranked(neural, nuisances))
        used_subjects.append(subject)
        feature_dirs[subject] = str(d)

    if ref_texts is None or ref_embedding_idx is None or ref_chapters is None or len(subject_residuals) < 3:
        raise SystemExit(f"Need >=3 aligned subjects for run-{run_number:02d}")

    target = np.mean(np.stack(subject_residuals, axis=0), axis=0)
    target -= target.mean()
    target /= target.std()

    rng = np.random.default_rng(seed + run_number)
    shuffled = target[rng.permutation(len(target))].copy()
    shuffled -= shuffled.mean()
    shuffled /= shuffled.std()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (out_root / f"run-{run_number:02d}" / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    np.save(out / "neural_target.npy", target.astype(np.float32))
    np.save(out / "shuffled_neural_target.npy", shuffled.astype(np.float32))
    np.save(out / "subject_residuals.npy", np.stack(subject_residuals).astype(np.float32))
    (out / "texts.json").write_text(json.dumps(ref_texts, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "embedding_indices.json").write_text(json.dumps(ref_embedding_idx), encoding="utf-8")
    (out / "chapters.json").write_text(json.dumps(ref_chapters.tolist()), encoding="utf-8")
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_number": run_number,
        "subjects": used_subjects,
        "n_subjects": len(used_subjects),
        "n_rows": len(ref_texts),
        "n_edges": len(target),
        "seed": seed,
        "shuffle_seed": seed + run_number,
        "neural_representation": "row_mean, featurewise z-score, correlation-distance RDM",
        "target": "mean across subjects of nuisance-residualized rank-z neural RDM; final run target z-standardized",
        "nuisances": [
            "run_position_lag", "duration_difference", "character_count_difference",
            "chapter_mismatch", "character_set_jaccard_distance", "punctuation_count_difference"
        ],
        "shuffled_control": "fixed permutation of run-level target values; same marginal distribution, pair identity destroyed",
        "feature_dirs": feature_dirs,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Run-{run_number:02d} tuning target: {out}")
    print(f"  subjects={len(used_subjects)} rows={len(ref_texts)} edges={len(target)}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build frozen residual neural targets for NeuroSem BERT tuning.")
    parser.add_argument("--runs", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6])
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--subjects", nargs="+", default=[
        "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
        "sub-09", "sub-10", "sub-13", "sub-14", "sub-15",
    ])
    parser.add_argument("--seed", type=int, default=20260823)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/bert_neural_tuning_targets_v1"))
    args = parser.parse_args()

    if any(r < 1 or r > 7 for r in args.runs):
        raise SystemExit("Runs must be in 1..7")
    for run_number in args.runs:
        build_one(run_number, args.feature_root, list(args.subjects), args.seed, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
