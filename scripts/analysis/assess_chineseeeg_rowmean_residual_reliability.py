#!/usr/bin/env python3
"""Assess whether the strongest ChineseEEG row-mean geometry survives simple nuisance control.

This remains a reliability/confound checkpoint, not a semantic RSA test.

Primary neural geometry:
- row_mean.npy, shape [rows, channels]
- featurewise z-score across rows within each subject, matching the benchmark
- correlation-distance RDM across rows within each subject

Nuisance RDMs:
- absolute run-position difference (temporal lag/order)
- absolute row-duration difference
- absolute character-count difference
- chapter mismatch (0 same, 1 different)

We rank-transform all RDM vectors and residualize each subject's neural RDM against
an intercept plus the nuisance RDMs using least squares. We then recompute pairwise
and leave-one-subject-out (LOO) Spearman reliability on the residualized vectors.

A circular-shift null is also computed for the residualized LOO mean by independently
rotating each subject's row labels. This preserves each subject's within-run geometry
and coarse autocorrelation while breaking row identity across subjects.

No semantic/model embeddings are loaded anywhere in this script.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
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


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise RuntimeError("Non-finite Spearman correlation")
    return rho


def rank_z(x: np.ndarray) -> np.ndarray:
    r = rankdata(x, method="average").astype(np.float64)
    r -= r.mean()
    sd = r.std()
    if sd == 0:
        raise RuntimeError("Zero-variance ranked vector")
    return r / sd


def residualize(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    cols = [np.ones_like(yr)] + [rank_z(n) for n in nuisances]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    sd = resid.std()
    if sd == 0:
        raise RuntimeError("Zero-variance residual RDM")
    return resid / sd


def loo_mean(rdms: dict[str, np.ndarray], subjects: list[str]) -> tuple[dict[str, float], float]:
    out: dict[str, float] = {}
    for subject in subjects:
        others = [rdms[s] for s in subjects if s != subject]
        consensus = np.mean(np.stack(others, axis=0), axis=0)
        out[subject] = safe_spearman(rdms[subject], consensus)
    return out, float(np.mean(list(out.values())))


def pairwise_mean(rdms: dict[str, np.ndarray], subjects: list[str]) -> float:
    vals = []
    for i in range(len(subjects)):
        for j in range(i + 1, len(subjects)):
            vals.append(safe_spearman(rdms[subjects[i]], rdms[subjects[j]]))
    return float(np.mean(vals))


def condensed_reindex_from_shift(n_rows: int, shift: int) -> np.ndarray:
    """Return indices mapping pdist condensed vector after a circular row shift."""
    labels = np.roll(np.arange(n_rows), shift)
    idx = np.empty((n_rows, n_rows), dtype=np.int64)
    k = 0
    for i in range(n_rows - 1):
        width = n_rows - i - 1
        idx[i, i + 1:] = np.arange(k, k + width)
        idx[i + 1:, i] = np.arange(k, k + width)
        k += width
    iu = np.triu_indices(n_rows, 1)
    return idx[labels[iu[0]], labels[iu[1]]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess nuisance-controlled reliability of ChineseEEG row-mean neural geometry.")
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_rowmean_residual_reliability"))
    args = parser.parse_args()

    if args.permutations < 100:
        raise SystemExit("--permutations must be >= 100")

    subjects = list(args.subjects)
    raw_rdms: dict[str, np.ndarray] = {}
    residual_rdms: dict[str, np.ndarray] = {}
    nuisance_rhos: dict[str, dict[str, float]] = {}
    feature_dirs: dict[str, str] = {}

    ref_texts = None
    ref_alignment = None
    ref_channels = None
    n_rows = None

    for subject in subjects:
        d = latest_feature_dir(args.feature_root, subject)
        meta = read_csv(d / "metadata.csv")
        x = np.load(d / "row_mean.npy").astype(np.float64)
        channels = (d / "channels.txt").read_text(encoding="utf-8").splitlines()

        texts = [r["text"] for r in meta]
        alignment = [r["alignment_index"] for r in meta]
        if ref_texts is None:
            ref_texts = texts
            ref_alignment = alignment
            ref_channels = channels
            n_rows = len(meta)
        else:
            if texts != ref_texts:
                raise SystemExit(f"Text order mismatch for {subject}")
            if alignment != ref_alignment:
                raise SystemExit(f"Alignment order mismatch for {subject}")
            if channels != ref_channels:
                raise SystemExit(f"Channel order mismatch for {subject}")

        if x.shape != (len(meta), len(channels)):
            raise SystemExit(f"Unexpected row_mean shape for {subject}: {x.shape}")
        if not np.isfinite(x).all():
            raise SystemExit(f"Non-finite row_mean values for {subject}")

        # Match benchmark_chineseeeg_neural_reliability.py exactly: standardize
        # each sensor feature across rows within subject before correlation distance.
        xz = zscore_columns(x)
        neural = pdist(xz, metric="correlation")
        position = np.array([float(r["run_position_fraction"]) for r in meta])
        duration = np.array([float(r["duration_sec"]) for r in meta])
        char_count = np.array([float(r["char_count"]) for r in meta])
        chapter = np.array([int((r["chapter_marker_context"] or "CH00")[2:]) for r in meta])

        pos_rdm = pdist(position[:, None], metric="cityblock")
        dur_rdm = pdist(duration[:, None], metric="cityblock")
        char_rdm = pdist(char_count[:, None], metric="cityblock")
        chap_rdm = pdist(chapter[:, None], metric="hamming")

        raw_rdms[subject] = neural
        residual_rdms[subject] = residualize(neural, [pos_rdm, dur_rdm, char_rdm, chap_rdm])
        nuisance_rhos[subject] = {
            "position": safe_spearman(neural, pos_rdm),
            "duration": safe_spearman(neural, dur_rdm),
            "char_count": safe_spearman(neural, char_rdm),
            "chapter": safe_spearman(neural, chap_rdm),
        }
        feature_dirs[subject] = str(d)

    raw_loo_by, raw_loo = loo_mean(raw_rdms, subjects)
    resid_loo_by, resid_loo = loo_mean(residual_rdms, subjects)
    raw_pair = pairwise_mean(raw_rdms, subjects)
    resid_pair = pairwise_mean(residual_rdms, subjects)

    rng = np.random.default_rng(args.seed)
    shift_maps = {}
    assert n_rows is not None
    for shift in range(n_rows):
        shift_maps[shift] = condensed_reindex_from_shift(n_rows, shift)

    null = np.empty(args.permutations, dtype=float)
    for p in range(args.permutations):
        shifted: dict[str, np.ndarray] = {}
        for subject in subjects:
            shift = int(rng.integers(0, n_rows))
            shifted[subject] = residual_rdms[subject][shift_maps[shift]]
        _, null[p] = loo_mean(shifted, subjects)

    p_value = float((1 + np.sum(null >= resid_loo)) / (args.permutations + 1))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    with (out / "subject_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["subject", "raw_loo", "residual_loo", "rho_position", "rho_duration", "rho_char_count", "rho_chapter", "feature_dir"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for s in subjects:
            writer.writerow({
                "subject": s,
                "raw_loo": raw_loo_by[s],
                "residual_loo": resid_loo_by[s],
                "rho_position": nuisance_rhos[s]["position"],
                "rho_duration": nuisance_rhos[s]["duration"],
                "rho_char_count": nuisance_rhos[s]["char_count"],
                "rho_chapter": nuisance_rhos[s]["chapter"],
                "feature_dir": feature_dirs[s],
            })

    np.save(out / "circular_shift_null_loo_mean.npy", null)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "subjects": subjects,
        "n_subjects": len(subjects),
        "n_rows": n_rows,
        "n_channels": len(ref_channels or []),
        "representation": "featurewise-z-scored row_mean, correlation-distance RDM",
        "nuisances": ["run_position_lag", "duration_difference", "character_count_difference", "chapter_mismatch"],
        "raw_pairwise_mean": raw_pair,
        "raw_loo_mean": raw_loo,
        "residual_pairwise_mean": resid_pair,
        "residual_loo_mean": resid_loo,
        "residual_loo_by_subject": resid_loo_by,
        "circular_shift_null": {
            "permutations": args.permutations,
            "seed": args.seed,
            "mean": float(null.mean()),
            "sd": float(null.std()),
            "p_ge_observed": p_value,
        },
        "mean_raw_nuisance_rho": {
            key: float(np.mean([nuisance_rhos[s][key] for s in subjects]))
            for key in ["position", "duration", "char_count", "chapter"]
        },
        "notes": [
            "This is not a semantic test.",
            "Sensor features are z-scored across rows within subject before correlation-distance RDM construction, exactly matching the row_mean_corr benchmark definition.",
            "Residualization is performed on rank-transformed RDM vectors.",
            "Circular shifts preserve within-subject row geometry but break cross-subject row identity.",
            "Additional visual/ocular/lexical nuisance controls are still required before semantic inference.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Row-mean residual reliability output: {out}")
    print(f"Subjects: {len(subjects)} | rows: {n_rows} | channels: {len(ref_channels or [])}")
    print(f"Raw row-mean reliability: pairwise mean={raw_pair:.4f} | LOO mean={raw_loo:.4f}")
    print(f"Residual reliability: pairwise mean={resid_pair:.4f} | LOO mean={resid_loo:.4f}")
    print("Mean raw nuisance correlations:")
    for key in ["position", "duration", "char_count", "chapter"]:
        val = np.mean([nuisance_rhos[s][key] for s in subjects])
        print(f"  {key}: {val:.4f}")
    print(
        "Circular-shift null for residual LOO mean: "
        f"mean={null.mean():.4f} sd={null.std():.4f} observed={resid_loo:.4f} p={p_value:.4g}"
    )
    print("Interpretation: reliability/confound checkpoint only; no semantic inference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
