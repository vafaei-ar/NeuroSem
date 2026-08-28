#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import mne
import numpy as np
from scipy.stats import rankdata

S3_BASE = "https://s3.amazonaws.com/openneuro.org/"
DATASET = "ds004078"
FIF_RE = re.compile(
    r"^derivatives/preprocessed_data/sub-(?P<subject>\d+)/MEG/"
    r"sub-\d+_task-RDR_run-(?P<run>\d+)_meg\.fif$"
)
ANNEX_RE = re.compile(r"MD5E-s(?P<size>\d+)--(?P<md5>[0-9a-f]{32})\.fif$")
N_BINS = 32
N_SUBJECTS = 12
N_RUNS = 60
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260828


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dst: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem-SMN4Lang-MEG-reliability/1"})
    with urllib.request.urlopen(req, timeout=180) as r, dst.open("wb") as f:
        while True:
            chunk = r.read(8 * 1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def annex_metadata(path: Path) -> tuple[int, str]:
    if not path.is_symlink():
        raise RuntimeError(f"expected git-annex symlink: {path}")
    target = os.readlink(path)
    m = ANNEX_RE.search(target)
    if not m:
        raise RuntimeError(f"could not parse git-annex MD5E key from {path}: {target}")
    return int(m.group("size")), m.group("md5")


def tracked_fifs(data_root: Path) -> list[dict]:
    import subprocess

    cp = subprocess.run(
        ["git", "-C", str(data_root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = []
    for rel in cp.stdout.splitlines():
        m = FIF_RE.match(rel)
        if not m:
            continue
        path = data_root / rel
        size, md5 = annex_metadata(path)
        rows.append(
            {
                "subject": int(m.group("subject")),
                "run": int(m.group("run")),
                "relative_path": rel,
                "size_bytes": size,
                "expected_md5": md5,
            }
        )
    rows.sort(key=lambda x: (x["subject"], x["run"]))
    return rows


def structural_check(rows: list[dict]) -> None:
    if len(rows) != N_SUBJECTS * N_RUNS:
        raise RuntimeError(f"expected {N_SUBJECTS*N_RUNS} FIFs, found {len(rows)}")
    by_subject: dict[int, set[int]] = {}
    for r in rows:
        by_subject.setdefault(r["subject"], set()).add(r["run"])
    if set(by_subject) != set(range(1, N_SUBJECTS + 1)):
        raise RuntimeError(f"unexpected participant set: {sorted(by_subject)}")
    expected_runs = set(range(1, N_RUNS + 1))
    for subject, runs in sorted(by_subject.items()):
        if runs != expected_runs:
            raise RuntimeError(f"participant {subject} run set mismatch")


def zscore_1d(x: np.ndarray) -> np.ndarray:
    mu = float(np.mean(x))
    sd = float(np.std(x, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("zero/non-finite within-channel-type temporal SD")
    return (x - mu) / sd


def run_representation(fif_path: Path) -> tuple[np.ndarray, dict]:
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

    # The prospective freeze specifies 32 equal bins over the full VALID run
    # duration after excluding released bad annotations. First mark samples
    # covered by released bad annotations as NaN, concatenate only time samples
    # that remain finite across all retained MEG channels, and divide that
    # valid-sample sequence into 32 equal normalized-time bins. This is a
    # literal implementation of the frozen rule and uses no outcome information.
    data = raw.get_data(picks=all_picks, reject_by_annotation="NaN")
    valid_time = np.isfinite(data).all(axis=0)
    n_valid = int(valid_time.sum())
    if n_valid < N_BINS:
        raise RuntimeError(f"too few valid MEG samples for {N_BINS} bins: {n_valid}")
    valid_data = data[:, valid_time]
    edges = np.linspace(0, n_valid, N_BINS + 1, dtype=int)
    mag_vals = np.empty(N_BINS, dtype=float)
    grad_vals = np.empty(N_BINS, dtype=float)

    for b in range(N_BINS):
        start, stop = int(edges[b]), int(edges[b + 1])
        if stop <= start:
            raise RuntimeError(f"valid-sample bin {b} is empty")
        chunk = valid_data[:, start:stop]
        mag = chunk[:n_mag]
        grad = chunk[n_mag:]
        mag_vals[b] = float(np.sqrt(np.mean(np.square(mag))))
        grad_vals[b] = float(np.sqrt(np.mean(np.square(grad))))

    rep = np.concatenate([zscore_1d(mag_vals), zscore_1d(grad_vals)])
    if rep.shape != (64,) or not np.isfinite(rep).all():
        raise RuntimeError("invalid frozen 64-dimensional MEG representation")
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
    return rep, meta


def corr_distance_rdm(features: np.ndarray) -> np.ndarray:
    if features.shape != (N_RUNS, 64):
        raise RuntimeError(f"unexpected feature matrix shape: {features.shape}")
    c = np.corrcoef(features)
    if not np.isfinite(c).all():
        raise RuntimeError("non-finite story correlation matrix")
    return 1.0 - c


def upper(rdm: np.ndarray) -> np.ndarray:
    idx = np.triu_indices_from(rdm, k=1)
    return rdm[idx]


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = rankdata(a, method="average")
    rb = rankdata(b, method="average")
    return float(np.corrcoef(ra, rb)[0, 1])


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


def bootstrap_ci(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.choice(values, size=(BOOTSTRAP_DRAWS, len(values)), replace=True).mean(axis=1)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(lo), float(hi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--format-probe", type=Path, default=Path("outputs/smn4lang_meg_format_probe/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_meg_primary_reliability/latest"))
    args = ap.parse_args()

    data_root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    probe = json.loads(args.format_probe.read_text(encoding="utf-8"))
    inv = probe.get("full_inventory", {})
    if inv.get("n_fif") != 720 or inv.get("n_subjects") != 12 or inv.get("n_common_runs") != 60 or not inv.get("identical_run_sets"):
        raise RuntimeError("frozen structural readiness probe did not pass")
    reps = probe.get("representatives", [])
    if len(reps) != 12 or not all(r.get("integrity_verified") for r in reps):
        raise RuntimeError("representative materialization/integrity readiness did not pass")

    rows = tracked_fifs(data_root)
    structural_check(rows)
    features: dict[int, dict[int, np.ndarray]] = {s: {} for s in range(1, 13)}
    inventory_rows = []

    with tempfile.TemporaryDirectory(prefix="neurosem_smn4lang_meg_") as td:
        tmp_dir = Path(td)
        for i, row in enumerate(rows, start=1):
            subject, run = row["subject"], row["run"]
            tmp = tmp_dir / f"sub-{subject:02d}_run-{run:02d}.fif"
            key = f"{DATASET}/{row['relative_path']}"
            url = S3_BASE + urllib.parse.quote(key, safe="/")
            download(url, tmp)
            observed_size = tmp.stat().st_size
            if observed_size != row["size_bytes"]:
                raise RuntimeError(f"size mismatch for {row['relative_path']}: {observed_size} vs {row['size_bytes']}")
            observed_md5 = md5_file(tmp)
            if observed_md5 != row["expected_md5"]:
                raise RuntimeError(f"MD5 mismatch for {row['relative_path']}")
            rep, meta = run_representation(tmp)
            features[subject][run] = rep
            inventory_rows.append(
                {
                    "subject": subject,
                    "run": run,
                    "relative_path": row["relative_path"],
                    "size_bytes": observed_size,
                    "md5": observed_md5,
                    **meta,
                }
            )
            tmp.unlink(missing_ok=True)
            if i % 10 == 0 or i == len(rows):
                print(f"processed {i}/{len(rows)} verified MEG FIFs", flush=True)

    subject_rdms: dict[int, np.ndarray] = {}
    for subject in range(1, 13):
        mat = np.stack([features[subject][r] for r in range(1, 61)], axis=0)
        subject_rdms[subject] = corr_distance_rdm(mat)

    subject_metrics = []
    reliabilities = []
    for subject in range(1, 13):
        target = upper(subject_rdms[subject])
        loo = np.mean(np.stack([upper(subject_rdms[s]) for s in range(1, 13) if s != subject], axis=0), axis=0)
        rho = spearman(target, loo)
        reliabilities.append(rho)
        subject_metrics.append({"subject": subject, "loo_spearman_rho": rho})

    vals = np.asarray(reliabilities, dtype=float)
    ci_lo, ci_hi = bootstrap_ci(vals)
    p = exact_signflip_p(vals)
    gate_pass = bool(float(vals.mean()) > 0 and ci_lo > 0 and p < 0.05)

    with (out / "subject_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["subject", "loo_spearman_rho"])
        w.writeheader()
        w.writerows(subject_metrics)
    with (out / "run_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        fields = list(inventory_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(inventory_rows)

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "frozen model-blind primary MEG reliability gate",
        "representation_freeze": "docs/13_SMN4LANG_MEG_REPRESENTATION_FREEZE.md",
        "model_blind": True,
        "loads_model_embeddings": False,
        "n_subjects": 12,
        "n_runs_per_subject": 60,
        "n_fif_verified_and_processed": 720,
        "representation": {
            "released_band_hz": [1.0, 40.0],
            "n_normalized_time_bins": 32,
            "magnetometers": 102,
            "planar_gradiometers": 204,
            "feature_dim": 64,
            "within_type_standardization": "z-score 32 RMS bins separately for magnetometers and gradiometers",
            "story_rdm": "correlation distance between 64-dimensional story vectors",
            "bad_annotation_handling": "released bad-annotation samples excluded, then remaining valid samples concatenated in temporal order and divided into 32 equal normalized-time bins",
        },
        "reliability": {
            "metric": "participant leave-one-out Spearman correlation of upper-triangle story-RDM edges",
            "mean": float(vals.mean()),
            "median": float(np.median(vals)),
            "n_positive": int(np.sum(vals > 0)),
            "participant_values": [float(x) for x in vals],
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_95_ci": [ci_lo, ci_hi],
            "exact_one_sided_signflip_p": p,
        },
        "gate_rule": "pass iff mean > 0, participant-bootstrap 95% CI entirely > 0, and exact one-sided sign-flip p < 0.05, after structural readiness",
        "gate_pass": gate_pass,
        "next_decision": "run the single frozen E5 lambda 0.10 versus lambda 0 MEG transfer test" if gate_pass else "stop MEG model evaluation; report MEG reliability failure without rescue analysis",
        "guardrails": {
            "no_model_loaded": True,
            "no_bin_search": True,
            "no_frequency_search": True,
            "no_sensor_subset_search": True,
            "no_latency_search": True,
            "no_source_space_search": True,
            "no_reliability_rescue_if_gate_fails": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
