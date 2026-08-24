#!/usr/bin/env python3
"""Overnight model-blind ChineseEEG representation benchmark.

This implements docs/eeg_representation_overnight_protocol_v2.md.
It deliberately never loads language-model embeddings or adapters.

Subjobs:
1. existing amplitude baselines;
2. deterministic spatial amplitude variants;
3. theta/alpha/beta relative spectral power;
4. low-gamma relative power when 0.5-80 Hz signal is available;
5. row-onset Fourier-phase feasibility at 5.5 and 10 Hz;
6. run-06 EEG-only winner selection;
7. locked winner evaluation on run-07;
8. exploratory run-07 full panel after the winner has been frozen.

Failures of optional candidate families are isolated and recorded so one unavailable
feature does not waste an overnight run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import string
import traceback
from datetime import datetime, timezone
from pathlib import Path

import mne
import numpy as np
from scipy.signal import periodogram
from scipy.spatial.distance import pdist
from scipy.stats import rankdata, spearmanr


DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-09", "sub-10", "sub-13", "sub-14", "sub-15",
]

PRIMARY_ELIGIBLE_ORDER = [
    "row_mean_all",
    "row_std_all",
    "relative_8bin_all",
    "row_mean_nonfrontal",
    "row_mean_posterior",
    "row_mean_lateral_posterior",
    "theta_relative_power",
    "alpha_relative_power",
    "beta_relative_power",
    "low_gamma_relative_power",
]

PHASE_CANDIDATES = ["theta_phase_5p5hz", "alpha_phase_10hz"]

PUNCT = set(string.punctuation) | set("，。！？；：、“”‘’（）《》〈〉【】…—·")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_feature_dir(root: Path, run: str, subject: str) -> Path:
    base = root / run / subject
    candidates = [
        d for d in base.iterdir()
        if d.is_dir() and (d / "metadata.csv").exists() and (d / "row_mean.npy").exists()
    ] if base.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No row features for {run}/{subject} under {base}")
    return sorted(candidates)[-1]


def find_derivative_vhdr(data_root: Path, derivative: str, subject: str, run: str) -> Path:
    filename = f"{subject}_ses-LittlePrince_task-reading_{run}_eeg.vhdr"
    candidates = [
        data_root / "derivatives" / "preproc" / derivative / subject / "ses-LittlePrince" / "eeg" / filename,
        data_root / "derivatives" / derivative / subject / "ses-LittlePrince" / "eeg" / filename,
    ]
    for p in candidates:
        if p.exists():
            # Keep the DataLad/git-annex worktree path instead of resolving the
            # .vhdr symlink into .git/annex/objects. BrainVision headers refer to
            # their .vmrk/.eeg companions by relative filename; resolving the
            # symlink makes MNE look for those companions inside the annex object
            # directory even though they are correctly materialized beside the
            # worktree header.
            return p.absolute()
    globbed = sorted(data_root.glob(f"derivatives/**/{derivative}/{subject}/ses-LittlePrince/eeg/{filename}"))
    for p in globbed:
        if p.exists():
            return p.absolute()
    raise FileNotFoundError(f"No materialized {derivative} BrainVision header for {subject} {run}")


def zscore_columns(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError(f"Feature matrix must be finite 2D, got {x.shape}")
    mean = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - mean) / sd


def rank_z(x: np.ndarray) -> np.ndarray:
    r = rankdata(np.asarray(x, dtype=np.float64), method="average")
    r -= r.mean()
    sd = r.std()
    if sd == 0 or not np.isfinite(sd):
        raise ValueError("Degenerate ranked vector")
    return r / sd


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise ValueError("Non-finite Spearman correlation")
    return rho


def residualize(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    cols = [np.ones_like(yr)] + [rank_z(n) for n in nuisances]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    resid -= resid.mean()
    sd = resid.std()
    if sd == 0 or not np.isfinite(sd):
        raise ValueError("Degenerate residual RDM")
    return resid / sd


def rdm_from_features(x: np.ndarray) -> np.ndarray:
    rdm = pdist(zscore_columns(x), metric="correlation")
    if not np.isfinite(rdm).all():
        raise ValueError("Non-finite correlation-distance RDM")
    return rdm


def char_set_jaccard_rdm(texts: list[str]) -> np.ndarray:
    sets = [set(t) for t in texts]
    vals = []
    for i in range(len(sets) - 1):
        for j in range(i + 1, len(sets)):
            union = len(sets[i] | sets[j])
            sim = len(sets[i] & sets[j]) / union if union else 1.0
            vals.append(1.0 - sim)
    return np.asarray(vals, dtype=np.float64)


def punctuation_count(text: str) -> int:
    return sum(ch in PUNCT for ch in text)


def nuisance_rdms(meta: list[dict[str, str]], indices: np.ndarray | None = None) -> list[np.ndarray]:
    if indices is None:
        selected = meta
    else:
        selected = [meta[int(i)] for i in indices]
    position = np.asarray([float(r["run_position_fraction"]) for r in selected], dtype=float)
    duration = np.asarray([float(r["duration_sec"]) for r in selected], dtype=float)
    char_count = np.asarray([float(r["char_count"]) for r in selected], dtype=float)
    chapters = np.asarray([int((r.get("chapter_marker_context") or "CH00")[2:]) for r in selected], dtype=int)
    texts = [r.get("text", "") for r in selected]
    punct = np.asarray([punctuation_count(t) for t in texts], dtype=float)
    return [
        pdist(position[:, None], metric="cityblock"),
        pdist(duration[:, None], metric="cityblock"),
        pdist(char_count[:, None], metric="cityblock"),
        pdist(chapters[:, None], metric="hamming"),
        char_set_jaccard_rdm(texts),
        pdist(punct[:, None], metric="cityblock"),
    ]


def canonical_identity(meta: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    return [
        (str(r.get("alignment_index", "")), str(r.get("embedding_index", "")), str(r.get("text", "")))
        for r in meta
    ]


def reliability_metrics(
    rdms: dict[str, np.ndarray],
    residual_rdms: dict[str, np.ndarray],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    subjects = sorted(rdms)
    raw_loo: dict[str, float] = {}
    resid_loo: dict[str, float] = {}
    for s in subjects:
        raw_consensus = np.mean(np.stack([rdms[o] for o in subjects if o != s], axis=0), axis=0)
        resid_consensus = np.mean(np.stack([residual_rdms[o] for o in subjects if o != s], axis=0), axis=0)
        raw_loo[s] = safe_spearman(rdms[s], raw_consensus)
        resid_loo[s] = safe_spearman(residual_rdms[s], resid_consensus)

    raw_pair = []
    resid_pair = []
    for i, s1 in enumerate(subjects):
        for s2 in subjects[i + 1:]:
            raw_pair.append(safe_spearman(rdms[s1], rdms[s2]))
            resid_pair.append(safe_spearman(residual_rdms[s1], residual_rdms[s2]))

    aggregate = {
        "raw_loo_mean": float(np.mean(list(raw_loo.values()))),
        "raw_loo_median": float(np.median(list(raw_loo.values()))),
        "residual_loo_mean": float(np.mean(list(resid_loo.values()))),
        "residual_loo_median": float(np.median(list(resid_loo.values()))),
        "raw_pairwise_mean": float(np.mean(raw_pair)),
        "residual_pairwise_mean": float(np.mean(resid_pair)),
        "fraction_positive_residual_loo": float(np.mean([v > 0 for v in resid_loo.values()])),
    }
    return aggregate, raw_loo, resid_loo


def standard_sensor_groups(channels: list[str]) -> dict[str, list[int]]:
    montage = mne.channels.make_standard_montage("GSN-HydroCel-128")
    pos = montage.get_positions()["ch_pos"]
    matched = [(i, pos[ch]) for i, ch in enumerate(channels) if ch in pos]
    if len(matched) < max(80, int(0.7 * len(channels))):
        raise ValueError(f"Only {len(matched)}/{len(channels)} channels match GSN-HydroCel-128 montage")
    idx = np.asarray([i for i, _ in matched], dtype=int)
    xyz = np.asarray([p for _, p in matched], dtype=float)
    y = xyz[:, 1]
    x = xyz[:, 0]
    nonfrontal_cut = float(np.quantile(y, 0.60))
    posterior_cut = float(np.median(y))
    lateral_cut = float(np.quantile(np.abs(x), 0.35))
    groups = {
        "row_mean_nonfrontal": idx[y <= nonfrontal_cut].tolist(),
        "row_mean_posterior": idx[y <= posterior_cut].tolist(),
        "row_mean_lateral_posterior": idx[(y <= posterior_cut) & (np.abs(x) >= lateral_cut)].tolist(),
    }
    for name, vals in groups.items():
        if len(vals) < 12:
            raise ValueError(f"Sensor group {name} unexpectedly small: {len(vals)}")
    return groups


def load_existing_features(feature_dir: Path) -> tuple[list[dict[str, str]], list[str], dict[str, np.ndarray]]:
    meta = read_csv(feature_dir / "metadata.csv")
    channels = (feature_dir / "channels.txt").read_text(encoding="utf-8").splitlines()
    out: dict[str, np.ndarray] = {}
    out["row_mean_all"] = np.load(feature_dir / "row_mean.npy").astype(np.float64)
    std_path = feature_dir / "row_std.npy"
    if std_path.exists():
        out["row_std_all"] = np.load(std_path).astype(np.float64)
    rel_path = feature_dir / "relative_8bin_mean.npy"
    if rel_path.exists():
        rel = np.load(rel_path).astype(np.float64)
        if rel.ndim != 3:
            raise ValueError(f"Unexpected relative_8bin shape {rel.shape}")
        out["relative_8bin_all"] = rel.reshape(rel.shape[0], -1)
    return meta, channels, out


def align_raw_to_channels(raw: mne.io.BaseRaw, channels: list[str]) -> mne.io.BaseRaw:
    missing = [ch for ch in channels if ch not in raw.ch_names]
    if missing:
        raise ValueError(f"Raw derivative missing {len(missing)} expected channels, first={missing[:5]}")
    return raw.copy().pick(channels)


def segment_samples(row: dict[str, str], sfreq: float, n_times: int) -> tuple[int, int]:
    start = int(round(float(row["start_sec"]) * sfreq))
    stop = int(round(float(row["end_sec"]) * sfreq))
    start = max(0, min(start, n_times))
    stop = max(0, min(stop, n_times))
    if stop <= start:
        raise ValueError(f"Invalid segment {start}:{stop}")
    return start, stop


def relative_bandpower_features(
    raw: mne.io.BaseRaw,
    meta: list[dict[str, str]],
    band: tuple[float, float],
    total: tuple[float, float],
    nfft: int = 512,
) -> np.ndarray:
    sfreq = float(raw.info["sfreq"])
    n_ch = len(raw.ch_names)
    feats = np.empty((len(meta), n_ch), dtype=np.float64)
    eps = np.finfo(np.float64).tiny
    for i, row in enumerate(meta):
        start, stop = segment_samples(row, sfreq, raw.n_times)
        data = raw.get_data(start=start, stop=stop)
        if data.shape[1] < 2:
            raise ValueError(f"Too few samples for PSD at row {i}")
        f, pxx = periodogram(data, fs=sfreq, axis=1, detrend="constant", scaling="density", nfft=max(nfft, data.shape[1]))
        bmask = (f >= band[0]) & (f <= band[1])
        tmask = (f >= total[0]) & (f <= total[1])
        if not bmask.any() or not tmask.any():
            raise ValueError(f"No frequency bins for band={band}, total={total}, sfreq={sfreq}")
        bp = np.trapz(pxx[:, bmask], f[bmask], axis=1)
        tp = np.trapz(pxx[:, tmask], f[tmask], axis=1)
        feats[i] = np.log((bp + eps) / (tp + eps))
    if not np.isfinite(feats).all():
        raise ValueError("Non-finite relative power features")
    return feats


def phase_features(
    raw: mne.io.BaseRaw,
    meta: list[dict[str, str]],
    frequency: float,
    window_sec: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    sfreq = float(raw.info["sfreq"])
    n_win = int(round(window_sec * sfreq))
    valid = np.asarray([
        (float(r["end_sec"]) - float(r["start_sec"])) >= window_sec
        for r in meta
    ], dtype=bool)
    idx = np.flatnonzero(valid)
    if len(idx) < 30:
        raise ValueError(f"Only {len(idx)} rows are >= {window_sec:g}s for phase")
    feats = np.empty((len(idx), len(raw.ch_names) * 2), dtype=np.float64)
    t = np.arange(n_win, dtype=np.float64) / sfreq
    kernel = np.exp(-2j * np.pi * frequency * t)
    for j, row_i in enumerate(idx):
        start, _ = segment_samples(meta[int(row_i)], sfreq, raw.n_times)
        stop = min(raw.n_times, start + n_win)
        data = raw.get_data(start=start, stop=stop)
        if data.shape[1] != n_win:
            raise ValueError(f"Phase window clipped at row {row_i}")
        coeff = data @ kernel
        mag = np.abs(coeff)
        unit = coeff / np.where(mag > 0, mag, 1.0)
        feats[j, :len(raw.ch_names)] = unit.real
        feats[j, len(raw.ch_names):] = unit.imag
    if not np.isfinite(feats).all():
        raise ValueError("Non-finite phase features")
    return feats, idx


def inspect_ica_metadata(data_root: Path, subjects: list[str], runs: list[str]) -> dict[str, object]:
    records = []
    for run in runs:
        for subject in subjects:
            patterns = [
                f"derivatives/preproc/**/{subject}/ses-LittlePrince/eeg/*{run}*ica*json",
                f"derivatives/**/{subject}/ses-LittlePrince/eeg/*{run}*ica*json",
            ]
            found = []
            for pat in patterns:
                found.extend(data_root.glob(pat))
            unique = sorted({p.resolve() for p in found if p.is_file()})
            if not unique:
                records.append({"run": run, "subject": subject, "status": "not_found"})
                continue
            p = unique[0]
            try:
                content = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                content = {"parse_error": traceback.format_exc(limit=1)}
            records.append({"run": run, "subject": subject, "path": str(p), "content": content})
    return {"n_records": len(records), "n_metadata_files_found": sum("path" in r for r in records), "records": records}


def evaluate_candidate(
    run: str,
    stage: str,
    candidate: str,
    features_by_subject: dict[str, tuple[np.ndarray, np.ndarray | None]],
    meta_by_subject: dict[str, list[dict[str, str]]],
    primary_selection_eligible: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    subjects = sorted(features_by_subject)
    if len(subjects) < 3:
        raise ValueError(f"Candidate {candidate} available for only {len(subjects)} subjects")

    identities = None
    rdms: dict[str, np.ndarray] = {}
    residual_rdms: dict[str, np.ndarray] = {}
    used_rows = None
    for subject in subjects:
        x, indices = features_by_subject[subject]
        meta = meta_by_subject[subject]
        if indices is None:
            indices = np.arange(len(meta), dtype=int)
        else:
            indices = np.asarray(indices, dtype=int)
        current_identity = [canonical_identity(meta)[int(i)] for i in indices]
        if identities is None:
            identities = current_identity
            used_rows = indices.copy()
        elif current_identity != identities:
            raise ValueError(f"Canonical row identity mismatch for {candidate}: {subject}")
        nuisances = nuisance_rdms(meta, indices)
        rdm = rdm_from_features(x)
        rdms[subject] = rdm
        residual_rdms[subject] = residualize(rdm, nuisances)

    aggregate, raw_loo, resid_loo = reliability_metrics(rdms, residual_rdms)
    row = {
        "run": run,
        "stage": stage,
        "candidate": candidate,
        "primary_selection_eligible": bool(primary_selection_eligible),
        "n_subjects": len(subjects),
        "n_rows": len(identities or []),
        **aggregate,
    }
    subject_rows = [
        {
            "run": run,
            "stage": stage,
            "candidate": candidate,
            "subject": s,
            "raw_loo": raw_loo[s],
            "residual_loo": resid_loo[s],
        }
        for s in subjects
    ]
    return row, subject_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Model-blind ChineseEEG EEG representation benchmark.")
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--discovery-run", default="run-06")
    parser.add_argument("--holdout-run", default="run-07")
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_eeg_representation_overnight/latest"))
    args = parser.parse_args()

    data_root = args.data_root.expanduser().resolve()
    feature_root = args.feature_root.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    runs = [args.discovery_run, args.holdout_run]
    subjects = list(args.subjects)
    subjobs: dict[str, dict[str, object]] = {}
    all_candidate_metrics: list[dict[str, object]] = []
    all_subject_metrics: list[dict[str, object]] = []
    sensor_group_records: dict[str, object] = {}
    candidate_store: dict[str, dict[str, dict[str, tuple[np.ndarray, np.ndarray | None]]]] = {r: {} for r in runs}
    meta_store: dict[str, dict[str, list[dict[str, str]]]] = {r: {} for r in runs}

    ica_audit = inspect_ica_metadata(data_root, subjects, runs)
    subjobs["ica_metadata_audit"] = {"status": "completed", "n_found": ica_audit["n_metadata_files_found"]}

    for run in runs:
        for subject in subjects:
            meta = None
            channels = None
            try:
                fdir = latest_feature_dir(feature_root, run, subject)
                meta, channels, existing = load_existing_features(fdir)
                meta_store[run][subject] = meta
                for name, x in existing.items():
                    candidate_store[run].setdefault(name, {})[subject] = (x, None)
                subjobs[f"{run}:{subject}:existing_features"] = {
                    "status": "completed", "feature_dir": str(fdir), "candidates": sorted(existing),
                }
            except Exception:
                subjobs[f"{run}:{subject}:existing_features"] = {"status": "failed", "error": traceback.format_exc(limit=2)}
                continue

            try:
                groups = standard_sensor_groups(channels)
                sensor_group_records[f"{run}:{subject}"] = {
                    name: [channels[i] for i in idx] for name, idx in groups.items()
                }
                row_mean = existing["row_mean_all"]
                for name, idx in groups.items():
                    candidate_store[run].setdefault(name, {})[subject] = (row_mean[:, idx], None)
                subjobs[f"{run}:{subject}:spatial"] = {
                    "status": "completed", "group_sizes": {k: len(v) for k, v in groups.items()},
                }
            except Exception:
                subjobs[f"{run}:{subject}:spatial"] = {"status": "failed", "error": traceback.format_exc(limit=2)}

            try:
                p30 = find_derivative_vhdr(data_root, "filtered_0.5_30", subject, run)
                raw30 = mne.io.read_raw_brainvision(p30, preload=True, verbose="ERROR")
                raw30 = align_raw_to_channels(raw30, channels)
                bands = {
                    "theta_relative_power": (4.0, 7.0),
                    "alpha_relative_power": (8.0, 12.0),
                    "beta_relative_power": (13.0, 30.0),
                }
                for name, band in bands.items():
                    x = relative_bandpower_features(raw30, meta, band=band, total=(1.0, 30.0))
                    candidate_store[run].setdefault(name, {})[subject] = (x, None)
                for name, frequency in [("theta_phase_5p5hz", 5.5), ("alpha_phase_10hz", 10.0)]:
                    x, idx = phase_features(raw30, meta, frequency=frequency, window_sec=1.0)
                    candidate_store[run].setdefault(name, {})[subject] = (x, idx)
                subjobs[f"{run}:{subject}:30hz_signal"] = {
                    "status": "completed", "path": str(p30), "sfreq": float(raw30.info["sfreq"]),
                }
            except Exception:
                subjobs[f"{run}:{subject}:30hz_signal"] = {"status": "unavailable", "error": traceback.format_exc(limit=2)}

            try:
                p80 = find_derivative_vhdr(data_root, "filtered_0.5_80", subject, run)
                raw80 = mne.io.read_raw_brainvision(p80, preload=True, verbose="ERROR")
                raw80 = align_raw_to_channels(raw80, channels)
                x = relative_bandpower_features(raw80, meta, band=(30.0, 45.0), total=(1.0, 45.0))
                candidate_store[run].setdefault("low_gamma_relative_power", {})[subject] = (x, None)
                subjobs[f"{run}:{subject}:low_gamma_relative_power"] = {
                    "status": "completed", "path": str(p80), "sfreq": float(raw80.info["sfreq"]),
                }
            except Exception:
                subjobs[f"{run}:{subject}:low_gamma_relative_power"] = {"status": "unavailable", "error": traceback.format_exc(limit=2)}

    # Run-06 discovery evaluation and freeze the primary winner using EEG-only criteria.
    for name in PRIMARY_ELIGIBLE_ORDER + PHASE_CANDIDATES:
        try:
            metric, subject_rows = evaluate_candidate(
                args.discovery_run,
                "discovery",
                name,
                candidate_store[args.discovery_run].get(name, {}),
                meta_store[args.discovery_run],
                primary_selection_eligible=name in PRIMARY_ELIGIBLE_ORDER,
            )
            all_candidate_metrics.append(metric)
            all_subject_metrics.extend(subject_rows)
            subjobs[f"{args.discovery_run}:evaluate:{name}"] = {"status": "completed"}
        except Exception as exc:
            subjobs[f"{args.discovery_run}:evaluate:{name}"] = {"status": "failed", "error": str(exc)}

    eligible = [m for m in all_candidate_metrics if m["run"] == args.discovery_run and m["primary_selection_eligible"]]
    if not eligible:
        raise SystemExit("No primary-eligible candidate completed on discovery run")
    rank_order = {name: i for i, name in enumerate(PRIMARY_ELIGIBLE_ORDER)}
    eligible.sort(
        key=lambda m: (
            -float(m["residual_loo_mean"]),
            -float(m["raw_loo_mean"]),
            -float(m["residual_pairwise_mean"]),
            -float(m["fraction_positive_residual_loo"]),
            rank_order.get(str(m["candidate"]), 999),
        )
    )
    winner = str(eligible[0]["candidate"])
    frozen_at = datetime.now(timezone.utc).isoformat()

    # Locked run-07 evaluation of the run-06 winner happens before the exploratory panel.
    locked_metric, locked_subject_rows = evaluate_candidate(
        args.holdout_run,
        "locked_winner_holdout",
        winner,
        candidate_store[args.holdout_run].get(winner, {}),
        meta_store[args.holdout_run],
        primary_selection_eligible=True,
    )
    all_candidate_metrics.append(locked_metric)
    all_subject_metrics.extend(locked_subject_rows)
    subjobs[f"{args.holdout_run}:locked_winner:{winner}"] = {"status": "completed"}

    # Only after the winner has been locked do we evaluate the remaining run-07 panel.
    for name in PRIMARY_ELIGIBLE_ORDER + PHASE_CANDIDATES:
        if name == winner:
            continue
        try:
            metric, subject_rows = evaluate_candidate(
                args.holdout_run,
                "exploratory_holdout_panel",
                name,
                candidate_store[args.holdout_run].get(name, {}),
                meta_store[args.holdout_run],
                primary_selection_eligible=name in PRIMARY_ELIGIBLE_ORDER,
            )
            all_candidate_metrics.append(metric)
            all_subject_metrics.extend(subject_rows)
            subjobs[f"{args.holdout_run}:exploratory:{name}"] = {"status": "completed"}
        except Exception as exc:
            subjobs[f"{args.holdout_run}:exploratory:{name}"] = {"status": "failed", "error": str(exc)}

    phase_metrics = [m for m in all_candidate_metrics if m["candidate"] in PHASE_CANDIDATES]
    phase_eligible = False
    if phase_metrics:
        run06_phase = [m for m in phase_metrics if m["run"] == args.discovery_run]
        if run06_phase:
            phase_eligible = max(float(m["residual_loo_mean"]) for m in run06_phase) > 0.05

    fields = [
        "run", "stage", "candidate", "primary_selection_eligible", "n_subjects", "n_rows",
        "raw_loo_mean", "raw_loo_median", "residual_loo_mean", "residual_loo_median",
        "raw_pairwise_mean", "residual_pairwise_mean", "fraction_positive_residual_loo",
    ]
    with (out / "candidate_metrics.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in all_candidate_metrics:
            writer.writerow({k: row.get(k, "") for k in fields})

    subject_fields = ["run", "stage", "candidate", "subject", "raw_loo", "residual_loo"]
    with (out / "subject_metrics.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=subject_fields)
        writer.writeheader()
        for row in all_subject_metrics:
            writer.writerow({k: row.get(k, "") for k in subject_fields})

    (out / "sensor_groups.json").write_text(
        json.dumps(sensor_group_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/eeg_representation_overnight_protocol_v2.md",
        "analysis_status": "model-blind EEG representation development",
        "model_blind": True,
        "neural_model_rsa_computed": False,
        "discovery_run": args.discovery_run,
        "holdout_run": args.holdout_run,
        "discovery_subjects": subjects,
        "holdout_subjects": subjects,
        "nuisances": [
            "run_position_lag", "duration_difference", "character_count_difference",
            "chapter_mismatch", "character_set_jaccard_distance", "punctuation_count_difference",
        ],
        "winner_selection": {
            "primary_statistic": "nuisance-residualized leave-one-subject-out RDM reliability on run-06",
            "tie_breakers": [
                "raw leave-one-subject-out reliability",
                "nuisance-residualized pairwise reliability",
                "fraction positive residual LOO",
            ],
            "phase_candidates_eligible": phase_eligible,
            "winner": winner,
            "winner_metrics_run06": eligible[0],
            "frozen_at_utc_before_run07_evaluation": frozen_at,
        },
        "locked_run07_winner_holdout": locked_metric,
        "ica_metadata_audit": ica_audit,
        "candidate_metrics": all_candidate_metrics,
        "subjob_status": subjobs,
        "guardrails": {
            "language_model_embeddings_loaded": False,
            "language_model_adapter_loaded": False,
            "model_correspondence_used_for_selection": False,
            "nature_validation_modified": False,
            "phase_primary_selection_eligible": False,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Model-blind EEG representation benchmark complete: {out}")
    print(f"Run-06 winner: {winner} | residual LOO mean={eligible[0]['residual_loo_mean']:.4f}")
    print(f"Locked run-07 winner residual LOO mean={locked_metric['residual_loo_mean']:.4f}")
    print(f"Phase feasibility eligible: {phase_eligible}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
