#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import tempfile
import time
import urllib.parse
from pathlib import Path

import mne
import numpy as np
from scipy.stats import rankdata

from scripts.analysis import run_smn4lang_meg_primary_reliability as base

CANDIDATE_BINS = (4, 8, 16)
N_SUBJECTS = 12
N_RUNS = 60
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260828
ALPHA_FAMILY = 0.05
ALPHA_PER_CANDIDATE = ALPHA_FAMILY / len(CANDIDATE_BINS)
FAMILY_CI_LEVEL = 1.0 - ALPHA_PER_CANDIDATE


def report_progress(current: int, total: int, phase: str, message: str = "") -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": max(0.0, min(1.0, current / total)) if total else None,
        "phase": phase,
        "message": message,
        "unit": "files",
        "updated_at_epoch": time.time(),
    }
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


def zscore_1d(x: np.ndarray) -> np.ndarray:
    mu = float(np.mean(x))
    sd = float(np.std(x, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("zero/non-finite within-channel-type temporal SD")
    return (x - mu) / sd


def representations_for_run(fif_path: Path) -> tuple[dict[int, np.ndarray], dict]:
    raw = mne.io.read_raw_fif(fif_path, preload=False, verbose="ERROR")
    mag_picks = mne.pick_types(raw.info, meg="mag", eeg=False, stim=False, eog=False, ecg=False, exclude="bads")
    grad_picks = mne.pick_types(raw.info, meg="grad", eeg=False, stim=False, eog=False, ecg=False, exclude="bads")
    if len(mag_picks) != 102 or len(grad_picks) != 204:
        raise RuntimeError(f"unexpected MEG channel counts: mag={len(mag_picks)}, grad={len(grad_picks)}")
    if not math.isclose(float(raw.info["sfreq"]), 1000.0, rel_tol=0, abs_tol=1e-9):
        raise RuntimeError(f"unexpected sampling rate: {raw.info['sfreq']}")
    if not math.isclose(float(raw.info["highpass"]), 1.0, rel_tol=0, abs_tol=1e-9):
        raise RuntimeError(f"unexpected highpass: {raw.info['highpass']}")
    if not math.isclose(float(raw.info["lowpass"]), 40.0, rel_tol=0, abs_tol=1e-9):
        raise RuntimeError(f"unexpected lowpass: {raw.info['lowpass']}")

    all_picks = np.concatenate([mag_picks, grad_picks])
    n_mag = len(mag_picks)
    data = raw.get_data(picks=all_picks, reject_by_annotation="NaN")
    valid_time = np.isfinite(data).all(axis=0)
    n_valid = int(valid_time.sum())
    if n_valid < max(CANDIDATE_BINS):
        raise RuntimeError(f"too few valid MEG samples for exploratory bins: {n_valid}")
    valid_data = data[:, valid_time]

    reps: dict[int, np.ndarray] = {}
    for n_bins in CANDIDATE_BINS:
        edges = np.linspace(0, n_valid, n_bins + 1, dtype=int)
        mag_vals = np.empty(n_bins, dtype=float)
        grad_vals = np.empty(n_bins, dtype=float)
        for b in range(n_bins):
            start, stop = int(edges[b]), int(edges[b + 1])
            if stop <= start:
                raise RuntimeError(f"valid-sample bin {b} is empty for {n_bins} bins")
            chunk = valid_data[:, start:stop]
            mag_vals[b] = float(np.sqrt(np.mean(np.square(chunk[:n_mag]))))
            grad_vals[b] = float(np.sqrt(np.mean(np.square(chunk[n_mag:]))))
        rep = np.concatenate([zscore_1d(mag_vals), zscore_1d(grad_vals)])
        if rep.shape != (2 * n_bins,) or not np.isfinite(rep).all():
            raise RuntimeError(f"invalid exploratory representation for {n_bins} bins")
        reps[n_bins] = rep

    meta = {
        "n_times": int(raw.n_times),
        "duration_seconds": float(raw.n_times / raw.info["sfreq"]),
        "n_valid_times": n_valid,
        "valid_fraction": float(n_valid / raw.n_times),
        "n_mag": int(len(mag_picks)),
        "n_grad": int(len(grad_picks)),
        "n_bads": int(len(raw.info.get("bads", []))),
        "n_annotations": int(len(raw.annotations)),
    }
    return reps, meta


def corr_distance_rdm(features: np.ndarray, expected_dim: int) -> np.ndarray:
    if features.shape != (N_RUNS, expected_dim):
        raise RuntimeError(f"unexpected feature matrix shape: {features.shape}")
    c = np.corrcoef(features)
    if not np.isfinite(c).all():
        raise RuntimeError("non-finite story correlation matrix")
    return 1.0 - c


def upper(rdm: np.ndarray) -> np.ndarray:
    return rdm[np.triu_indices_from(rdm, k=1)]


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(rankdata(a, method="average"), rankdata(b, method="average"))[0, 1])


def exact_signflip_p(values: np.ndarray) -> float:
    observed = float(np.mean(values))
    ge = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(values)):
        total += 1
        stat = float(np.mean(values * np.asarray(signs)))
        if stat >= observed - 1e-15:
            ge += 1
    return ge / total


def bootstrap_ci(values: np.ndarray, level: float) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.choice(values, size=(BOOTSTRAP_DRAWS, len(values)), replace=True).mean(axis=1)
    tail = (1.0 - level) / 2.0
    lo, hi = np.quantile(draws, [tail, 1.0 - tail])
    return float(lo), float(hi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--format-probe", type=Path, default=Path("outputs/smn4lang_meg_format_probe/latest/summary.json"))
    ap.add_argument("--primary-summary", type=Path, default=Path("outputs/smn4lang_meg_primary_reliability/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_meg_exploratory_granularity/latest"))
    args = ap.parse_args()

    data_root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    probe = json.loads(args.format_probe.read_text(encoding="utf-8"))
    inv = probe.get("full_inventory", {})
    if inv.get("n_fif") != 720 or inv.get("n_subjects") != 12 or inv.get("n_common_runs") != 60 or not inv.get("identical_run_sets"):
        raise RuntimeError("structural readiness probe did not pass")

    primary = json.loads(args.primary_summary.read_text(encoding="utf-8"))
    if primary.get("gate_pass") is not False:
        raise RuntimeError("exploratory granularity task requires the completed failed 32-bin primary gate")
    if primary.get("n_fif_verified_and_processed") != 720:
        raise RuntimeError("primary reliability summary is not the completed 720-file result")

    rows = base.tracked_fifs(data_root)
    base.structural_check(rows)
    features: dict[int, dict[int, dict[int, np.ndarray]]] = {
        n_bins: {s: {} for s in range(1, N_SUBJECTS + 1)} for n_bins in CANDIDATE_BINS
    }
    inventory_rows = []

    report_progress(0, len(rows), "MEG exploratory granularity", "Starting verified file processing")
    with tempfile.TemporaryDirectory(prefix="neurosem_smn4lang_meg_explore_") as td:
        tmp_dir = Path(td)
        for i, row in enumerate(rows, start=1):
            subject, run = row["subject"], row["run"]
            tmp = tmp_dir / f"sub-{subject:02d}_run-{run:02d}.fif"
            key = f"{base.DATASET}/{row['relative_path']}"
            url = base.S3_BASE + urllib.parse.quote(key, safe="/")
            base.download(url, tmp)
            observed_size = tmp.stat().st_size
            if observed_size != row["size_bytes"]:
                raise RuntimeError(f"size mismatch for {row['relative_path']}: {observed_size} vs {row['size_bytes']}")
            observed_md5 = base.md5_file(tmp)
            if observed_md5 != row["expected_md5"]:
                raise RuntimeError(f"MD5 mismatch for {row['relative_path']}")
            reps, meta = representations_for_run(tmp)
            for n_bins, rep in reps.items():
                features[n_bins][subject][run] = rep
            inventory_rows.append({
                "subject": subject,
                "run": run,
                "relative_path": row["relative_path"],
                "size_bytes": observed_size,
                "md5": observed_md5,
                **meta,
            })
            tmp.unlink(missing_ok=True)
            report_progress(i, len(rows), "MEG exploratory granularity", "Verified and reduced one MEG file")
            if i % 10 == 0 or i == len(rows):
                print(f"processed {i}/{len(rows)} verified MEG FIFs", flush=True)

    candidate_rows = []
    subject_rows = []
    feature_cache = {}
    passing = []

    for n_bins in CANDIDATE_BINS:
        mats = np.empty((N_SUBJECTS, N_RUNS, 2 * n_bins), dtype=np.float64)
        rdms: dict[int, np.ndarray] = {}
        for subject in range(1, N_SUBJECTS + 1):
            mat = np.stack([features[n_bins][subject][r] for r in range(1, N_RUNS + 1)], axis=0)
            mats[subject - 1] = mat
            rdms[subject] = corr_distance_rdm(mat, 2 * n_bins)
        feature_cache[f"bins_{n_bins}"] = mats

        vals = []
        for subject in range(1, N_SUBJECTS + 1):
            target = upper(rdms[subject])
            loo = np.mean(np.stack([upper(rdms[s]) for s in range(1, N_SUBJECTS + 1) if s != subject], axis=0), axis=0)
            rho = spearman(target, loo)
            vals.append(rho)
            subject_rows.append({"n_bins": n_bins, "subject": subject, "loo_spearman_rho": rho})

        arr = np.asarray(vals, dtype=float)
        ci95_lo, ci95_hi = bootstrap_ci(arr, 0.95)
        cif_lo, cif_hi = bootstrap_ci(arr, FAMILY_CI_LEVEL)
        p = exact_signflip_p(arr)
        family_pass = bool(float(arr.mean()) > 0 and cif_lo > 0 and p < ALPHA_PER_CANDIDATE)
        if family_pass:
            passing.append(n_bins)
        candidate_rows.append({
            "n_bins": n_bins,
            "feature_dim": 2 * n_bins,
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
            "n_positive": int(np.sum(arr > 0)),
            "bootstrap_95_ci_low": ci95_lo,
            "bootstrap_95_ci_high": ci95_hi,
            "bootstrap_familywise_ci_level": FAMILY_CI_LEVEL,
            "bootstrap_familywise_ci_low": cif_lo,
            "bootstrap_familywise_ci_high": cif_hi,
            "exact_one_sided_signflip_p": p,
            "bonferroni_alpha": ALPHA_PER_CANDIDATE,
            "familywise_reliability_pass": family_pass,
        })

    selected = max(passing) if passing else None

    with (out / "candidate_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(candidate_rows[0].keys()))
        w.writeheader()
        w.writerows(candidate_rows)
    with (out / "subject_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n_bins", "subject", "loo_spearman_rho"])
        w.writeheader()
        w.writerows(subject_rows)
    with (out / "run_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(inventory_rows[0].keys()))
        w.writeheader()
        w.writerows(inventory_rows)
    np.savez_compressed(out / "derived_run_features.npz", **feature_cache)

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "post-confirmatory exploratory MEG temporal-granularity reliability family",
        "exploratory_freeze": "docs/14_SMN4LANG_MEG_EXPLORATORY_GRANULARITY_FREEZE.md",
        "primary_32bin_gate_pass": False,
        "model_blind": True,
        "loads_model_embeddings": False,
        "n_subjects": N_SUBJECTS,
        "n_runs_per_subject": N_RUNS,
        "n_fif_verified_and_processed": len(rows),
        "candidate_bins": list(CANDIDATE_BINS),
        "candidate_metrics": candidate_rows,
        "familywise_alpha": ALPHA_FAMILY,
        "bonferroni_alpha_per_candidate": ALPHA_PER_CANDIDATE,
        "familywise_bootstrap_ci_level": FAMILY_CI_LEVEL,
        "passing_candidates": passing,
        "selected_finest_passing_candidate": selected,
        "next_decision": (
            f"candidate {selected} bins is eligible for the sole exploratory E5 lambda 0.10 versus lambda 0 MEG test"
            if selected is not None
            else "stop MEG branch; no exploratory candidate passed familywise reliability"
        ),
        "guardrails": {
            "post_confirmatory_exploratory_only": True,
            "primary_32bin_failure_unchanged": True,
            "no_model_loaded": True,
            "no_frequency_search": True,
            "no_sensor_subset_search": True,
            "no_latency_search": True,
            "no_source_space_search": True,
            "no_model_outcome_based_candidate_selection": True,
            "selection_rule": "finest passing candidate among 4, 8, 16 bins",
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
