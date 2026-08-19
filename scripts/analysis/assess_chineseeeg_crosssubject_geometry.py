#!/usr/bin/env python3
"""Assess cross-subject reliability of ChineseEEG row-level neural geometry.

This is a reliability/confound diagnostic, not a semantic RSA test. It discovers the
latest per-subject feature outputs, verifies identical row/channel ordering, constructs
one neural RDM per subject from relative-time sensor features, and reports pairwise and
leave-one-subject-out RDM agreement. It also reports correlations with simple position
and duration nuisance geometries.

Primary representation for this checkpoint:
- relative_8bin_mean.npy, flattened to [rows, 8*channels]
- each feature dimension standardized across rows within subject
- correlation distance between rows
- Spearman correlation between vectorized subject RDMs
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


DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-10", "sub-13", "sub-14", "sub-15",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_feature_dir(root: Path, subject: str, bins: int) -> Path:
    candidates = []
    subject_root = root / subject
    if subject_root.exists():
        for child in subject_root.iterdir():
            if child.is_dir() and (child / f"relative_{bins}bin_mean.npy").exists() and (child / "metadata.csv").exists():
                candidates.append(child)
    if not candidates:
        raise FileNotFoundError(f"No completed feature output found for {subject} under {subject_root}")
    return sorted(candidates)[-1]


def zscore_features(x: np.ndarray) -> np.ndarray:
    mean = np.mean(x, axis=0, dtype=np.float64)
    sd = np.std(x, axis=0, dtype=np.float64)
    sd[sd == 0] = 1.0
    return ((x - mean) / sd).astype(np.float64, copy=False)


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    result = spearmanr(a, b)
    rho = float(result.statistic)
    if not np.isfinite(rho):
        raise RuntimeError("Non-finite Spearman correlation")
    return rho


def write_matrix_csv(path: Path, subjects: list[str], matrix: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["subject", *subjects])
        for subject, row in zip(subjects, matrix):
            writer.writerow([subject, *[f"{float(v):.8f}" for v in row]])


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess cross-subject ChineseEEG neural RDM reliability.")
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--relative-bins", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_crosssubject_geometry"))
    args = parser.parse_args()

    subjects: list[str] = []
    feature_dirs: dict[str, Path] = {}
    metadata: dict[str, list[dict[str, str]]] = {}
    channels: dict[str, list[str]] = {}
    rdms: dict[str, np.ndarray] = {}
    nuisance: dict[str, dict[str, float]] = {}

    ref_texts: list[str] | None = None
    ref_alignment: list[str] | None = None
    ref_channels: list[str] | None = None

    for subject in args.subjects:
        feature_dir = latest_feature_dir(args.feature_root, subject, args.relative_bins)
        meta = read_csv(feature_dir / "metadata.csv")
        if not meta:
            raise SystemExit(f"Empty metadata for {subject}: {feature_dir}")

        text_order = [row["text"] for row in meta]
        alignment_order = [row["alignment_index"] for row in meta]
        ch = (feature_dir / "channels.txt").read_text(encoding="utf-8").splitlines()

        if ref_texts is None:
            ref_texts = text_order
            ref_alignment = alignment_order
            ref_channels = ch
        else:
            if text_order != ref_texts:
                raise SystemExit(f"Text row ordering mismatch for {subject}")
            if alignment_order != ref_alignment:
                raise SystemExit(f"Alignment-index ordering mismatch for {subject}")
            if ch != ref_channels:
                raise SystemExit(f"Channel ordering mismatch for {subject}")

        x = np.load(feature_dir / f"relative_{args.relative_bins}bin_mean.npy")
        if x.ndim != 3:
            raise SystemExit(f"Unexpected relative feature shape for {subject}: {x.shape}")
        if x.shape[0] != len(meta):
            raise SystemExit(f"Feature/metadata row mismatch for {subject}: {x.shape[0]} vs {len(meta)}")
        if not np.isfinite(x).all():
            raise SystemExit(f"Non-finite relative features for {subject}")

        flat = x.reshape(x.shape[0], -1).astype(np.float64)
        flat = zscore_features(flat)
        rdm = pdist(flat, metric="correlation")
        if not np.isfinite(rdm).all():
            raise SystemExit(f"Non-finite neural RDM for {subject}")

        position = np.array([float(row["run_position_fraction"]) for row in meta], dtype=float)
        duration = np.array([float(row["duration_sec"]) for row in meta], dtype=float)
        position_rdm = pdist(position[:, None], metric="cityblock")
        duration_rdm = pdist(duration[:, None], metric="cityblock")

        subjects.append(subject)
        feature_dirs[subject] = feature_dir
        metadata[subject] = meta
        channels[subject] = ch
        rdms[subject] = rdm
        nuisance[subject] = {
            "rho_position": safe_spearman(rdm, position_rdm),
            "rho_duration": safe_spearman(rdm, duration_rdm),
        }

    if len(subjects) < 3:
        raise SystemExit("Need at least 3 completed subjects for cross-subject reliability")

    n = len(subjects)
    pairwise = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            rho = safe_spearman(rdms[subjects[i]], rdms[subjects[j]])
            pairwise[i, j] = rho
            pairwise[j, i] = rho

    loo: dict[str, float] = {}
    for subject in subjects:
        others = [rdms[s] for s in subjects if s != subject]
        consensus = np.mean(np.stack(others, axis=0), axis=0)
        loo[subject] = safe_spearman(rdms[subject], consensus)

    upper = pairwise[np.triu_indices(n, k=1)]
    loo_values = np.array(list(loo.values()), dtype=float)
    pos_values = np.array([nuisance[s]["rho_position"] for s in subjects], dtype=float)
    dur_values = np.array([nuisance[s]["rho_duration"] for s in subjects], dtype=float)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    write_matrix_csv(out / "pairwise_rdm_spearman.csv", subjects, pairwise)

    with (out / "subject_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "subject", "loo_consensus_rho", "rho_position", "rho_duration", "feature_dir"
        ])
        writer.writeheader()
        for subject in subjects:
            writer.writerow({
                "subject": subject,
                "loo_consensus_rho": loo[subject],
                "rho_position": nuisance[subject]["rho_position"],
                "rho_duration": nuisance[subject]["rho_duration"],
                "feature_dir": str(feature_dirs[subject]),
            })

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "subjects": subjects,
        "n_subjects": n,
        "n_rows": len(ref_texts or []),
        "n_channels": len(ref_channels or []),
        "relative_bins": args.relative_bins,
        "representation": "relative-time sensor means flattened, within-subject feature z-score, correlation-distance RDM",
        "rdm_comparison": "Spearman correlation of vectorized upper triangles",
        "pairwise_rdm_rho": {
            "mean": float(np.mean(upper)),
            "median": float(np.median(upper)),
            "min": float(np.min(upper)),
            "max": float(np.max(upper)),
        },
        "loo_consensus_rho": {
            "mean": float(np.mean(loo_values)),
            "median": float(np.median(loo_values)),
            "min": float(np.min(loo_values)),
            "max": float(np.max(loo_values)),
            "by_subject": loo,
        },
        "nuisance_rdm_rho": {
            "position_mean": float(np.mean(pos_values)),
            "position_range": [float(np.min(pos_values)), float(np.max(pos_values))],
            "duration_mean": float(np.mean(dur_values)),
            "duration_range": [float(np.min(dur_values)), float(np.max(dur_values))],
        },
        "notes": [
            "This is a reliability diagnostic, not evidence of semantic alignment.",
            "Shared narrative order, stimulus duration, visual structure, and temporal autocorrelation can induce cross-subject RDM agreement.",
            "Semantic inference requires nuisance-controlled RSA and dependence-preserving nulls.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Cross-subject geometry output: {out}")
    print(f"Subjects: {n} -> {' '.join(subjects)}")
    print(f"Rows: {summary['n_rows']} | channels: {summary['n_channels']} | relative bins: {args.relative_bins}")
    print(
        "Pairwise neural-RDM Spearman: "
        f"mean={np.mean(upper):.4f} median={np.median(upper):.4f} "
        f"range={np.min(upper):.4f}..{np.max(upper):.4f}"
    )
    print(
        "LOO-consensus Spearman: "
        f"mean={np.mean(loo_values):.4f} median={np.median(loo_values):.4f} "
        f"range={np.min(loo_values):.4f}..{np.max(loo_values):.4f}"
    )
    print(
        "Position-RDM correlation: "
        f"mean={np.mean(pos_values):.4f} range={np.min(pos_values):.4f}..{np.max(pos_values):.4f}"
    )
    print(
        "Duration-RDM correlation: "
        f"mean={np.mean(dur_values):.4f} range={np.min(dur_values):.4f}..{np.max(dur_values):.4f}"
    )
    print("Interpretation: reliability checkpoint only; do not call this semantic alignment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
