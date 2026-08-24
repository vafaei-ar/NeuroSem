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
            return p.resolve()
    globbed = sorted(data_root.glob(f"derivatives/**/{derivative}/{subject}/ses-LittlePrince/eeg/{filename}"))
    for p in globbed:
        if p.exists():
            return p.resolve()
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
            pattern = f"derivatives/**/filtered_0.5_30/{subject}/ses-LittlePrince/eeg/{subject}_ses-LittlePrince_task-reading_{run}_ica_components.json"
            matches = sorted(data_root.glob(pattern))
            row = {"run": run, "subject": subject, "path": None, "content": None}
            if matches:
                p = matches[0]
                row["path"] = str(p)
                try:
                    row["content"] = json.loads(p.read_text(encoding="utf-8"))
                except Exception as exc:
                    row["content"] = {"parse_error": str(exc)}
            records.append(row)
    return {
        "n_records": len(records),
        "n_metadata_files_found": sum(r["path"] is not None for r in records),
        "records": records,
        "interpretation": "Author preprocessed derivatives already incorporate ICA/artifact cleaning; metadata are audited here, but ICA sources are not treated as semantic components.",
    }


def build_run_features(
    run: str,
    subjects: list[str],
    feature_root: Path,
    data_root: Path,
    status: dict[str, dict[str, object]],
) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, list[dict[str, str]]], dict[str, list[str]], dict[str, list[int]]]:
    features: dict[str, dict[str, np.ndarray]] = {}
    metas: dict[str, list[dict[str, str]]] = {}
    channels_by_subject: dict[str, list[str]] = {}
    sensor_groups_ref: dict[str, list[int]] = {}

    for subject in subjects:
        key_prefix = f"{run}:{subject}"
        d = latest_feature_dir(feature_root, run, subject)
        meta, channels, base = load_existing_features(d)
        features[subject] = dict(base)
        metas[subject] = meta
        channels_by_subject[subject] = channels
        status[f"{key_prefix}:existing_features"] = {"status": "completed", "feature_dir": str(d), "candidates": sorted(base)}

        try:
            groups = standard_sensor_groups(channels)
            if not sensor_groups_ref:
                sensor_groups_ref = groups
            row_mean = base["row_mean_all"]
            for name, indices in groups.items():
                features[subject][name] = row_mean[:, np.asarray(indices, dtype=int)]
            status[f"{key_prefix}:spatial"] = {
                "status": "completed",
                "group_sizes": {k: len(v) for k, v in groups.items()},
            }
        except Exception as exc:
            status[f"{key_prefix}:spatial"] = {"status": "unavailable", "error": str(exc)}

        raw30 = None
        try:
            p30 = find_derivative_vhdr(data_root, "filtered_0.5_30", subject, run)
            raw30 = mne.io.read_raw_brainvision(p30, preload=True, verbose="ERROR")
            raw30 = align_raw_to_channels(raw30, channels)
            for name, band in [
                ("theta_relative_power", (4.0, 7.0)),
                ("alpha_relative_power", (8.0, 12.0)),
                ("beta_relative_power", (13.0, 30.0)),
            ]:
                try:
                    features[subject][name] = relative_bandpower_features(raw30, meta, band, (1.0, 30.0))
                    status[f"{key_prefix}:{name}"] = {"status": "completed", "source": str(p30)}
                except Exception as exc:
                    status[f"{key_prefix}:{name}"] = {"status": "failed", "error": str(exc)}
            for name, freq in [("theta_phase_5p5hz", 5.5), ("alpha_phase_10hz", 10.0)]:
                try:
                    pf, pidx = phase_features(raw30, meta, freq)
                    features[subject][name] = pf
                    features[subject][name + "__indices"] = pidx.astype(np.int64)
                    status[f"{key_prefix}:{name}"] = {
                        "status": "completed",
                        "source": str(p30),
                        "n_rows": int(len(pidx)),
                    }
                except Exception as exc:
                    status[f"{key_prefix}:{name}"] = {"status": "failed", "error": str(exc)}
        except Exception as exc:
            status[f"{key_prefix}:30hz_signal"] = {"status": "unavailable", "error": str(exc)}
        finally:
            if raw30 is not None:
                try:
                    raw30.close()
                except Exception:
                    pass

        raw80 = None
        try:
            p80 = find_derivative_vhdr(data_root, "filtered_0.5_80", subject, run)
            raw80 = mne.io.read_raw_brainvision(p80, preload=True, verbose="ERROR")
            raw80 = align_raw_to_channels(raw80, channels)
            features[subject]["low_gamma_relative_power"] = relative_bandpower_features(raw80, meta, (30.0, 45.0), (1.0, 45.0))
            status[f"{key_prefix}:low_gamma_relative_power"] = {"status": "completed", "source": str(p80)}
        except Exception as exc:
            status[f"{key_prefix}:low_gamma_relative_power"] = {"status": "unavailable", "error": str(exc)}
        finally:
            if raw80 is not None:
                try:
                    raw80.close()
                except Exception:
                    pass

    return features, metas, channels_by_subject, sensor_groups_ref


def check_canonical_metas(metas: dict[str, list[dict[str, str]]]) -> tuple[str, list[dict[str, str]]]:
    subjects = sorted(metas)
    ref_subject = subjects[0]
    ref_meta = metas[ref_subject]
    ref_id = canonical_identity(ref_meta)
    for s in subjects[1:]:
        if canonical_identity(metas[s]) != ref_id:
            raise ValueError(f"Canonical row identity mismatch between {ref_subject} and {s}")
    return ref_subject, ref_meta


def evaluate_candidate(
    candidate: str,
    subjects: list[str],
    features: dict[str, dict[str, np.ndarray]],
    metas: dict[str, list[dict[str, str]]],
    phase: bool = False,
) -> tuple[dict[str, float], dict[str, float], dict[str, float], int]:
    _, ref_meta = check_canonical_metas(metas)
    eval_subjects = [s for s in subjects if candidate in features.get(s, {})]
    if len(eval_subjects) < 4:
        raise ValueError(f"Candidate {candidate} available for only {len(eval_subjects)} subjects")

    if phase:
        index_sets = []
        for s in eval_subjects:
            key = candidate + "__indices"
            if key not in features[s]:
                raise ValueError(f"Missing phase indices for {s}")
            index_sets.append(set(int(x) for x in features[s][key]))
        common = sorted(set.intersection(*index_sets))
        if len(common) < 30:
            raise ValueError(f"Only {len(common)} common rows for phase candidate {candidate}")
        common_arr = np.asarray(common, dtype=int)
        rdms: dict[str, np.ndarray] = {}
        residual: dict[str, np.ndarray] = {}
        nuis = nuisance_rdms(ref_meta, common_arr)
        for s in eval_subjects:
            idx = features[s][candidate + "__indices"].astype(int)
            lookup = {int(row): j for j, row in enumerate(idx)}
            rows = np.asarray([lookup[int(row)] for row in common_arr], dtype=int)
            rdm = rdm_from_features(features[s][candidate][rows])
            rdms[s] = rdm
            residual[s] = residualize(rdm, nuis)
        agg, raw_loo, resid_loo = reliability_metrics(rdms, residual)
        return agg, raw_loo, resid_loo, len(common)

    arrays = [features[s][candidate] for s in eval_subjects]
    n_rows = len(ref_meta)
    for s, x in zip(eval_subjects, arrays):
        if x.shape[0] != n_rows:
            raise ValueError(f"Candidate {candidate} row count mismatch for {s}: {x.shape[0]} != {n_rows}")
    nuis = nuisance_rdms(ref_meta)
    rdms = {}
    residual = {}
    for s in eval_subjects:
        rdm = rdm_from_features(features[s][candidate])
        rdms[s] = rdm
        residual[s] = residualize(rdm, nuis)
    agg, raw_loo, resid_loo = reliability_metrics(rdms, residual)
    return agg, raw_loo, resid_loo, n_rows


def candidate_sort_key(row: dict[str, object]) -> tuple[float, float, float, float]:
    return (
        float(row["residual_loo_mean"]),
        float(row["raw_loo_mean"]),
        float(row["residual_pairwise_mean"]),
        float(row["fraction_positive_residual_loo"]),
    )


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run overnight model-blind ChineseEEG EEG representation benchmark.")
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    parser.add_argument("--feature-root", type=Path, default=Path("outputs/chineseeeg_row_features"))
    parser.add_argument("--discovery-run", default="run-06")
    parser.add_argument("--holdout-run", default="run-07")
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_eeg_representation_overnight/latest"))
    args = parser.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    status: dict[str, dict[str, object]] = {}
    candidate_rows: list[dict[str, object]] = []
    subject_rows: list[dict[str, object]] = []
    sensor_groups: dict[str, object] = {}

    # Determine usable subjects from already-completed row features for both stages independently.
    discovery_subjects = []
    holdout_subjects = []
    for s in args.subjects:
        try:
            latest_feature_dir(args.feature_root, args.discovery_run, s)
            discovery_subjects.append(s)
        except Exception:
            pass
        try:
            latest_feature_dir(args.feature_root, args.holdout_run, s)
            holdout_subjects.append(s)
        except Exception:
            pass

    if len(discovery_subjects) < 4:
        raise SystemExit(f"Need >=4 discovery subjects; found {discovery_subjects}")
    if len(holdout_subjects) < 4:
        raise SystemExit(f"Need >=4 holdout subjects; found {holdout_subjects}")

    ica_audit = inspect_ica_metadata(args.data_root, sorted(set(discovery_subjects + holdout_subjects)), [args.discovery_run, args.holdout_run])
    status["ica_metadata_audit"] = {"status": "completed", "n_found": ica_audit["n_metadata_files_found"]}

    print(f"[1/4] Building discovery candidate features for {args.discovery_run}: {discovery_subjects}", flush=True)
    discovery_features, discovery_metas, discovery_channels, discovery_groups = build_run_features(
        args.discovery_run, discovery_subjects, args.feature_root, args.data_root, status
    )
    if discovery_groups:
        sensor_groups[args.discovery_run] = {
            name: {
                "indices": idx,
                "channels_reference_subject": [discovery_channels[sorted(discovery_channels)[0]][i] for i in idx],
            }
            for name, idx in discovery_groups.items()
        }

    # Evaluate all run-06 candidates. Only all-row candidates are winner-eligible.
    print("[2/4] Evaluating run-06 EEG-only candidate reliability", flush=True)
    discovery_metric_by_candidate: dict[str, dict[str, object]] = {}
    for candidate in PRIMARY_ELIGIBLE_ORDER + PHASE_CANDIDATES:
        is_phase = candidate in PHASE_CANDIDATES
        try:
            agg, raw_loo, resid_loo, n_rows = evaluate_candidate(
                candidate, discovery_subjects, discovery_features, discovery_metas, phase=is_phase
            )
            row = {
                "run": args.discovery_run,
                "stage": "discovery",
                "candidate": candidate,
                "primary_selection_eligible": not is_phase,
                "n_subjects": len(raw_loo),
                "n_rows": n_rows,
                **agg,
            }
            candidate_rows.append(row)
            discovery_metric_by_candidate[candidate] = row
            for s in sorted(raw_loo):
                subject_rows.append({
                    "run": args.discovery_run,
                    "stage": "discovery",
                    "candidate": candidate,
                    "subject": s,
                    "raw_loo": raw_loo[s],
                    "residual_loo": resid_loo[s],
                    "n_rows": n_rows,
                })
            status[f"{args.discovery_run}:evaluate:{candidate}"] = {"status": "completed"}
            print(f"  {candidate}: residual LOO={agg['residual_loo_mean']:.4f} raw LOO={agg['raw_loo_mean']:.4f}", flush=True)
        except Exception as exc:
            status[f"{args.discovery_run}:evaluate:{candidate}"] = {
                "status": "failed",
                "error": str(exc),
                "traceback": traceback.format_exc(limit=3),
            }
            print(f"  {candidate}: unavailable/failed: {exc}", flush=True)

    eligible = [
        discovery_metric_by_candidate[c]
        for c in PRIMARY_ELIGIBLE_ORDER
        if c in discovery_metric_by_candidate
    ]
    if not eligible:
        raise SystemExit("No primary-selection-eligible run-06 candidate completed")
    winner = max(eligible, key=candidate_sort_key)
    winner_name = str(winner["candidate"])
    winner_frozen_at_utc = datetime.now(timezone.utc).isoformat()
    print(f"Frozen run-06 EEG-only winner: {winner_name}", flush=True)

    # Build run-07 candidates only after winner is frozen.
    print(f"[3/4] Building locked holdout features for {args.holdout_run}: {holdout_subjects}", flush=True)
    holdout_features, holdout_metas, holdout_channels, holdout_groups = build_run_features(
        args.holdout_run, holdout_subjects, args.feature_root, args.data_root, status
    )
    if holdout_groups:
        sensor_groups[args.holdout_run] = {
            name: {
                "indices": idx,
                "channels_reference_subject": [holdout_channels[sorted(holdout_channels)[0]][i] for i in idx],
            }
            for name, idx in holdout_groups.items()
        }

    print(f"[4/4] Locked holdout evaluation of frozen winner {winner_name}", flush=True)
    holdout_winner_result: dict[str, object]
    try:
        agg, raw_loo, resid_loo, n_rows = evaluate_candidate(
            winner_name, holdout_subjects, holdout_features, holdout_metas, phase=False
        )
        row = {
            "run": args.holdout_run,
            "stage": "locked_winner_holdout",
            "candidate": winner_name,
            "primary_selection_eligible": True,
            "n_subjects": len(raw_loo),
            "n_rows": n_rows,
            **agg,
        }
        candidate_rows.append(row)
        for s in sorted(raw_loo):
            subject_rows.append({
                "run": args.holdout_run,
                "stage": "locked_winner_holdout",
                "candidate": winner_name,
                "subject": s,
                "raw_loo": raw_loo[s],
                "residual_loo": resid_loo[s],
                "n_rows": n_rows,
            })
        holdout_winner_result = row
        status[f"{args.holdout_run}:locked_winner:{winner_name}"] = {"status": "completed"}
        print(f"Locked holdout residual LOO={agg['residual_loo_mean']:.4f}", flush=True)
    except Exception as exc:
        holdout_winner_result = {"candidate": winner_name, "status": "failed", "error": str(exc)}
        status[f"{args.holdout_run}:locked_winner:{winner_name}"] = {
            "status": "failed", "error": str(exc), "traceback": traceback.format_exc(limit=3)
        }

    # Only now, after the locked winner holdout, evaluate the rest of run 07 for exploratory comparison.
    for candidate in PRIMARY_ELIGIBLE_ORDER + PHASE_CANDIDATES:
        if candidate == winner_name:
            continue
        is_phase = candidate in PHASE_CANDIDATES
        try:
            agg, raw_loo, resid_loo, n_rows = evaluate_candidate(
                candidate, holdout_subjects, holdout_features, holdout_metas, phase=is_phase
            )
            row = {
                "run": args.holdout_run,
                "stage": "post_lock_exploratory_panel",
                "candidate": candidate,
                "primary_selection_eligible": False,
                "n_subjects": len(raw_loo),
                "n_rows": n_rows,
                **agg,
            }
            candidate_rows.append(row)
            for s in sorted(raw_loo):
                subject_rows.append({
                    "run": args.holdout_run,
                    "stage": "post_lock_exploratory_panel",
                    "candidate": candidate,
                    "subject": s,
                    "raw_loo": raw_loo[s],
                    "residual_loo": resid_loo[s],
                    "n_rows": n_rows,
                })
            status[f"{args.holdout_run}:exploratory:{candidate}"] = {"status": "completed"}
        except Exception as exc:
            status[f"{args.holdout_run}:exploratory:{candidate}"] = {"status": "failed", "error": str(exc)}

    candidate_fields = [
        "run", "stage", "candidate", "primary_selection_eligible", "n_subjects", "n_rows",
        "raw_loo_mean", "raw_loo_median", "residual_loo_mean", "residual_loo_median",
        "raw_pairwise_mean", "residual_pairwise_mean", "fraction_positive_residual_loo",
    ]
    subject_fields = ["run", "stage", "candidate", "subject", "raw_loo", "residual_loo", "n_rows"]
    write_csv(out / "candidate_metrics.csv", candidate_rows, candidate_fields)
    write_csv(out / "subject_metrics.csv", subject_rows, subject_fields)
    (out / "sensor_groups.json").write_text(json.dumps(sensor_groups, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/eeg_representation_overnight_protocol_v2.md",
        "analysis_status": "model-blind EEG representation development",
        "model_blind": True,
        "neural_model_rsa_computed": False,
        "discovery_run": args.discovery_run,
        "holdout_run": args.holdout_run,
        "discovery_subjects": discovery_subjects,
        "holdout_subjects": holdout_subjects,
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
            "phase_candidates_eligible": False,
            "winner": winner_name,
            "winner_metrics_run06": winner,
            "frozen_at_utc_before_run07_evaluation": winner_frozen_at_utc,
        },
        "locked_run07_winner_holdout": holdout_winner_result,
        "ica_metadata_audit": ica_audit,
        "candidate_metrics": candidate_rows,
        "subjob_status": status,
        "guardrails": {
            "no_model_embeddings_loaded": True,
            "nature_null_unchanged": True,
            "sensor_groups_are_not_localization_claims": True,
            "phase_is_feasibility_only": True,
            "eye_tracking_not_materialized_in_prior_audit": True,
            "run07_nonwinner_panel_is_post_lock_exploratory": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Output: {out}")
    print(f"Run-06 winner: {winner_name}")
    if holdout_winner_result.get("residual_loo_mean") is not None:
        print(f"Run-07 locked winner residual LOO: {holdout_winner_result['residual_loo_mean']:.4f}")
    else:
        print(f"Run-07 locked winner evaluation failed: {holdout_winner_result.get('error')}")
    print("No model embeddings were loaded; this is EEG-only representation development.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
