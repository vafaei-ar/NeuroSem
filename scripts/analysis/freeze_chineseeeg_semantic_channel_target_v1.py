#!/usr/bin/env python3
"""Freeze a channel-level contribution target for the established ChineseEEG semantic RSA.

This stage is deliberately AHBA-blind. It uses the already-fixed ChineseEEG
row_mean representation, pinned bert-base-chinese final-layer embeddings, and the
same nuisance-controlled partial-Spearman statistic as the established held-out
semantic RSA. For each held-out run, subject, and channel, contribution is the
change in residual semantic RSA when that channel is removed:

    contribution(e) = RSA_full - RSA_without_e

Positive values therefore mean that retaining the channel supports the established
semantic alignment. Participant maps are the unweighted mean contribution across
held-out runs 01-06. The population target is the unweighted mean across common
participants. No AHBA expression, molecular sensitivity matrix, gene set, or
molecular association is loaded or computed here.
"""
from __future__ import annotations

import argparse
import csv
import json
import string
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import rankdata

DEFAULT_RUNS = [1, 2, 3, 4, 5, 6]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_dir(root: Path, required: str) -> Path:
    candidates = [d for d in root.iterdir() if d.is_dir() and (d / required).exists()] if root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No directory containing {required} under {root}")
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
        raise RuntimeError("zero-variance ranked vector")
    return r / sd


def residualize_ranked(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    X = np.column_stack([np.ones_like(yr), *[rank_z(n) for n in nuisances]])
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    resid -= resid.mean()
    sd = resid.std()
    if sd == 0:
        raise RuntimeError("zero-variance residual")
    return resid / sd


def pearson_standardized(a: np.ndarray, b: np.ndarray) -> float:
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


def feature_container_for_run(run_number: int, feature_root: Path) -> Path:
    """Resolve the frozen feature layout, including legacy unscoped run-01."""
    scoped = feature_root / f"run-{run_number:02d}"
    if scoped.exists():
        return scoped
    if run_number == 1 and feature_root.exists():
        return feature_root
    raise FileNotFoundError(f"missing feature root for run-{run_number:02d}: {scoped}")


def embedding_container_for_run(run_number: int, embedding_root: Path) -> Path:
    """Resolve the frozen embedding layout, including legacy unscoped run-01."""
    scoped = embedding_root / f"run-{run_number:02d}"
    if scoped.exists():
        return scoped
    if run_number == 1 and embedding_root.exists():
        return embedding_root
    raise FileNotFoundError(f"missing embedding root for run-{run_number:02d}: {scoped}")


def load_run(run_number: int, feature_root: Path, embedding_root: Path):
    run_label = f"run-{run_number:02d}"
    fr = feature_container_for_run(run_number, feature_root)
    subjects = sorted([d.name for d in fr.iterdir() if d.is_dir() and d.name.startswith("sub-")])
    subject_dirs = {}
    for subject in subjects:
        try:
            subject_dirs[subject] = latest_dir(fr / subject, "row_mean.npy")
        except FileNotFoundError:
            pass
    if len(subject_dirs) < 3:
        raise RuntimeError(f"{run_label}: fewer than 3 subjects with row_mean features under {fr}")

    er = embedding_container_for_run(run_number, embedding_root)
    emb_dir = latest_dir(er, "bert_base_chinese_final_mean.npy")
    emb = np.load(emb_dir / "bert_base_chinese_final_mean.npy").astype(np.float64)
    return run_label, subject_dirs, emb_dir, emb


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", type=int, default=DEFAULT_RUNS)
    ap.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    ap.add_argument("--embedding-root", type=Path, default=Path("outputs/chineseeeg_pinned_embeddings"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_semantic_channel_target_v1/latest"))
    args = ap.parse_args()

    if args.runs != DEFAULT_RUNS:
        raise SystemExit(f"frozen run set is {DEFAULT_RUNS}, got {args.runs}")

    run_payloads = []
    subject_sets = []
    for run_number in args.runs:
        run_label, subject_dirs, emb_dir, emb = load_run(run_number, args.feature_root, args.embedding_root)
        run_payloads.append((run_number, run_label, subject_dirs, emb_dir, emb))
        subject_sets.append(set(subject_dirs))
    common_subjects = sorted(set.intersection(*subject_sets))
    if len(common_subjects) < 3:
        raise RuntimeError("fewer than 3 subjects common to held-out runs 01-06")

    canonical_channels = None
    run_subject_rows = []
    participant_maps = {s: [] for s in common_subjects}
    full_rsa = {s: [] for s in common_subjects}
    source_dirs = {}

    for run_number, run_label, subject_dirs, emb_dir, emb in run_payloads:
        ref_texts = None
        ref_embedding_idx = None
        ref_channels = None
        source_dirs[run_label] = {"embedding_dir": str(emb_dir), "feature_dirs": {}}

        for subject in common_subjects:
            d = subject_dirs[subject]
            source_dirs[run_label]["feature_dirs"][subject] = str(d)
            meta = read_csv(d / "metadata.csv")
            x = np.load(d / "row_mean.npy").astype(np.float64)
            channels = [line.strip() for line in (d / "channels.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
            texts = [r["text"] for r in meta]
            embedding_idx = [int(r["embedding_index"]) for r in meta]
            chapters = np.array([int((r["chapter_marker_context"] or "CH00")[2:]) for r in meta], dtype=int)

            if x.ndim != 2 or x.shape[1] != len(channels):
                raise RuntimeError(f"{run_label} {subject}: feature/channel shape mismatch")
            if len(channels) != 128:
                raise RuntimeError(f"{run_label} {subject}: expected 128 channels, got {len(channels)}")
            if not np.isfinite(x).all():
                raise RuntimeError(f"{run_label} {subject}: non-finite row_mean")

            if ref_texts is None:
                ref_texts, ref_embedding_idx, ref_channels = texts, embedding_idx, channels
            elif texts != ref_texts or embedding_idx != ref_embedding_idx or channels != ref_channels:
                raise RuntimeError(f"{run_label}: canonical row/channel mismatch for {subject}")
            if canonical_channels is None:
                canonical_channels = channels
            elif channels != canonical_channels:
                raise RuntimeError(f"channel order differs across runs: {run_label} {subject}")

            idx = np.asarray(embedding_idx, dtype=int)
            if idx.max() >= emb.shape[0]:
                raise RuntimeError(f"{run_label}: embedding index exceeds array")
            sem_rdm = pdist(emb[idx], metric="cosine")
            if not np.isfinite(sem_rdm).all():
                raise RuntimeError(f"{run_label}: non-finite semantic RDM")

            orth = char_set_jaccard_rdm(texts)
            punct = np.array([punctuation_count(t) for t in texts], dtype=float)
            position = np.array([float(r["run_position_fraction"]) for r in meta], dtype=float)
            duration = np.array([float(r["duration_sec"]) for r in meta], dtype=float)
            char_count = np.array([float(r["char_count"]) for r in meta], dtype=float)
            nuisances = [
                pdist(position[:, None], metric="cityblock"),
                pdist(duration[:, None], metric="cityblock"),
                pdist(char_count[:, None], metric="cityblock"),
                pdist(chapters[:, None], metric="hamming"),
                orth,
                pdist(punct[:, None], metric="cityblock"),
            ]
            sem_resid = residualize_ranked(sem_rdm, nuisances)

            xz = zscore_columns(x)
            full_neural = pdist(xz, metric="correlation")
            full_neural_resid = residualize_ranked(full_neural, nuisances)
            full = pearson_standardized(full_neural_resid, sem_resid)
            full_rsa[subject].append(full)

            contributions = np.empty(128, dtype=np.float64)
            for ci in range(128):
                keep = np.ones(128, dtype=bool)
                keep[ci] = False
                reduced = pdist(xz[:, keep], metric="correlation")
                reduced_resid = residualize_ranked(reduced, nuisances)
                reduced_rsa = pearson_standardized(reduced_resid, sem_resid)
                contributions[ci] = full - reduced_rsa
                run_subject_rows.append({
                    "run": run_label,
                    "subject": subject,
                    "channel": channels[ci],
                    "full_residual_rsa": full,
                    "leave_channel_out_residual_rsa": reduced_rsa,
                    "contribution": contributions[ci],
                })
            participant_maps[subject].append(contributions)

    assert canonical_channels is not None
    participant_mean = {}
    for subject in common_subjects:
        arr = np.vstack(participant_maps[subject])
        if arr.shape != (6, 128) or not np.isfinite(arr).all():
            raise RuntimeError(f"unexpected contribution stack for {subject}: {arr.shape}")
        participant_mean[subject] = arr.mean(axis=0)

    population = np.mean(np.vstack([participant_mean[s] for s in common_subjects]), axis=0)
    if population.shape != (128,) or not np.isfinite(population).all():
        raise RuntimeError("invalid population channel target")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    with (out / "run_subject_channel_contributions.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(run_subject_rows[0]))
        w.writeheader(); w.writerows(run_subject_rows)

    with (out / "participant_channel_target.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subject", "channel", "mean_contribution_runs_01_06"])
        for subject in common_subjects:
            for channel, value in zip(canonical_channels, participant_mean[subject]):
                w.writerow([subject, channel, float(value)])

    with (out / "population_channel_target.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["channel", "mean_contribution_across_subjects", "n_subjects"])
        for channel, value in zip(canonical_channels, population):
            w.writerow([channel, float(value), len(common_subjects)])

    payload = {
        "schema_version": 1,
        "analysis": "AHBA-blind ChineseEEG semantic channel contribution target freeze v1",
        "loads_ahba_expression": False,
        "loads_molecular_sensitivity": False,
        "loads_gene_sets": False,
        "computes_molecular_associations": False,
        "runs": [f"run-{r:02d}" for r in args.runs],
        "subjects_common_to_all_runs": common_subjects,
        "n_subjects": len(common_subjects),
        "n_channels": 128,
        "channel_order": canonical_channels,
        "neural_representation": "row_mean; featurewise z-score within run/subject; correlation-distance RDM",
        "semantic_target": "pinned bert-base-chinese final-layer mean-pooled embedding cosine-distance RDM",
        "nuisances": ["run_position_lag", "duration_difference", "character_count_difference", "chapter_mismatch", "character_set_jaccard_distance", "punctuation_count_difference"],
        "rsa_statistic": "partial Spearman implemented as Pearson correlation between separately residualized rank-z neural and semantic RDM vectors",
        "channel_contribution": "full residual RSA minus leave-one-channel-out residual RSA; positive means retaining the channel supports semantic alignment",
        "participant_aggregation": "unweighted arithmetic mean of the 128-channel contribution map across held-out runs 01-06",
        "population_aggregation": "unweighted arithmetic mean of participant maps across subjects common to all six runs",
        "population_target_min": float(population.min()),
        "population_target_max": float(population.max()),
        "population_target_mean": float(population.mean()),
        "population_target_sd": float(population.std()),
        "mean_full_residual_rsa_by_subject": {s: float(np.mean(full_rsa[s])) for s in common_subjects},
        "planned_molecular_inference": {
            "participant_unit": "subject",
            "primary_association": "for each frozen gene set, Spearman correlation across the 128 matched channels between the gene-set molecular weight vector and each participant's frozen channel-contribution map",
            "participant_summary": "Fisher-z transform each participant channel correlation; report mean/median and exact two-sided sign-flip p across participants",
            "multiplicity": "Benjamini-Hochberg FDR across the frozen primary gene-set family; retain unadjusted p as descriptive",
            "required_controls_before_claim": ["AHBA donor LODO", "no-mirror bilateral sensitivity", "gene-set-size-matched random sets", "spatial-autocorrelation-preserving null maps", "broad cortical-gradient/nonspecific spatial control"],
        },
        "ready_for_frozen_molecular_association": True,
        "blockers": [],
        "source_dirs": source_dirs,
        "guardrails": [
            "Do not alter the channel target after inspecting any AHBA molecular association.",
            "Do not select runs, subjects, channels, semantic model layers, nuisances, or contribution definitions based on molecular results.",
            "Treat subject-level inference as primary; channels are not independent inferential units.",
            "A positive association is spatial correspondence with a population transcriptomic prior, not causal receptor evidence.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ready", "n_subjects": len(common_subjects), "n_channels": 128, "ready_for_frozen_molecular_association": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
