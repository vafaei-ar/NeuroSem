#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import shutil
import urllib.request
import zipfile
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.io import loadmat, wavfile
from scipy.stats import gamma

OPENNEURO_BASE = "https://s3.amazonaws.com/openneuro.org/ds004078"
LANA_ZIP_URL = "https://ndownloader.figshare.com/files/36524940"
LANA_ZIP_MD5 = "5e981df0866f2522e75a7899f69a00a5"
LANA_REL = "SPM/LanA_n806.nii"
LANA_SHA256 = "3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babca3"
MASK_THRESHOLD = 0.20
TR = 0.71
SUBJECTS = [f"sub-{i:02d}" for i in range(1, 13)]
STORIES = list(range(1, 61))
BOOTSTRAP_SEED = 20260827
N_BOOT = 10_000


def hash_file(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, timeout: int = 600) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        dest.unlink()
    if dest.exists() and dest.stat().st_size > 0:
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem/SMN4Lang-reliability"})
    with urllib.request.urlopen(req, timeout=timeout) as r, tmp.open("wb") as f:
        shutil.copyfileobj(r, f, length=1024 * 1024)
    tmp.replace(dest)


def fetch_text(rel: str) -> str:
    with urllib.request.urlopen(f"{OPENNEURO_BASE}/{rel}", timeout=120) as r:
        return r.read().decode("utf-8-sig", errors="replace")


def canonical_hrf(tr: float, duration: float = 32.0) -> np.ndarray:
    t = np.arange(0.0, duration + tr, tr, dtype=np.float64)
    h = gamma.pdf(t, 6.0, scale=1.0) - gamma.pdf(t, 16.0, scale=1.0) / 6.0
    h[h < 0] = h[h < 0]
    s = float(np.sum(h))
    if not np.isfinite(s) or abs(s) < 1e-12:
        raise RuntimeError("invalid canonical HRF")
    return h / s


def convolve_to_length(x: np.ndarray, h: np.ndarray, n: int) -> np.ndarray:
    return np.convolve(np.asarray(x, dtype=np.float64), h, mode="full")[:n]


def mat_vec(d: dict, key: str) -> np.ndarray:
    return np.asarray(d[key]).reshape(-1)


def preflight_story(root: Path, story: int, n_tp: int, hrf: np.ndarray) -> dict:
    event_rel = f"sub-01/func/sub-01_task-RDR_run-{story}_events.tsv"
    events = list(csv.DictReader(io.StringIO(fetch_text(event_rel)), delimiter="\t"))
    audio_rows = [r for r in events if str(r.get("stim_file", "")).endswith(f"story_{story}.wav")]
    if len(audio_rows) != 1:
        raise RuntimeError(f"story {story}: expected one audio event, got {len(audio_rows)}")
    ev = audio_rows[0]
    onset = float(ev["onset"])
    duration = float(ev["duration"])
    stim_file = str(ev["stim_file"])

    timing_rel = f"derivatives/annotations/time_align/word-level/story_{story}_word_time.mat"
    timing_path = root / timing_rel
    if timing_path.is_symlink():
        timing_path.unlink()
    if not timing_path.exists() or timing_path.stat().st_size == 0:
        download(f"{OPENNEURO_BASE}/{timing_rel}", timing_path)
    td = loadmat(timing_path, simplify_cells=True)
    starts = mat_vec(td, "start").astype(float)
    if len(starts) == 0 or np.any(np.diff(starts) < 0):
        raise RuntimeError(f"story {story}: invalid word timing")

    audio_rel = f"stimuli/{stim_file}"
    audio_path = root / audio_rel
    if audio_path.is_symlink():
        audio_path.unlink()
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        download(f"{OPENNEURO_BASE}/{audio_rel}", audio_path)
    sr, wav = wavfile.read(audio_path)
    wav = np.asarray(wav)
    if wav.ndim == 2:
        wav = wav.astype(np.float64).mean(axis=1)
    else:
        wav = wav.astype(np.float64)
    if np.issubdtype(np.asarray(wavfile.read(audio_path)[1]).dtype, np.integer):
        pass
    maxabs = float(np.max(np.abs(wav))) if wav.size else 0.0
    if maxabs > 0:
        wav = wav / maxabs

    word_counts = np.zeros(n_tp, dtype=np.float64)
    for s in starts:
        idx = int(math.floor(float(s) / TR))
        if 0 <= idx < n_tp:
            word_counts[idx] += 1.0
    word_drive = convolve_to_length(word_counts, hrf, n_tp)

    acoustic = np.zeros(n_tp, dtype=np.float64)
    for i in range(n_tp):
        a = i * TR - onset
        b = (i + 1) * TR - onset
        if b <= 0 or a >= duration:
            continue
        a = max(a, 0.0)
        b = min(b, duration)
        ia = max(0, int(math.floor(a * sr)))
        ib = min(len(wav), int(math.ceil(b * sr)))
        if ib > ia:
            seg = wav[ia:ib]
            acoustic[i] = float(np.sqrt(np.mean(seg * seg)))
    acoustic_drive = convolve_to_length(acoustic, hrf, n_tp)

    start_idx = int(math.ceil(onset / TR - 1e-9))
    valid_idx = np.arange(start_idx, n_tp, dtype=int)
    if valid_idx.size < 100:
        raise RuntimeError(f"story {story}: too few retained TRs: {valid_idx.size}")

    return {
        "onset": onset,
        "duration": duration,
        "stim_file": stim_file,
        "sample_rate": int(sr),
        "n_words": int(len(starts)),
        "valid_idx": valid_idx,
        "word_drive": word_drive[valid_idx],
        "acoustic_drive": acoustic_drive[valid_idx],
        "times": valid_idx.astype(np.float64) * TR,
    }


def corr_rdm_vector_from_bold(img_path: Path, mask: np.ndarray, valid_idx: np.ndarray) -> np.ndarray:
    img = nib.load(str(img_path))
    if tuple(img.shape[:3]) != tuple(mask.shape):
        raise RuntimeError(f"grid mismatch {img_path}: {img.shape[:3]} vs {mask.shape}")
    if img.shape[3] <= int(valid_idx[-1]):
        raise RuntimeError(f"time index out of bounds in {img_path}: {img.shape[3]}")
    data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
    x = data[..., valid_idx][mask, :].T
    del data
    if x.ndim != 2 or x.shape[0] != len(valid_idx):
        raise RuntimeError(f"unexpected extracted shape {x.shape}")
    mu = np.mean(x, axis=0, dtype=np.float64).astype(np.float32)
    sd = np.std(x, axis=0, ddof=0, dtype=np.float64).astype(np.float32)
    keep = np.isfinite(sd) & (sd > 1e-6)
    if int(np.sum(keep)) < 100:
        raise RuntimeError(f"too few nonconstant language voxels: {int(np.sum(keep))}")
    x = (x[:, keep] - mu[keep]) / sd[keep]
    x -= np.mean(x, axis=1, keepdims=True, dtype=np.float64).astype(np.float32)
    norms = np.linalg.norm(x, axis=1)
    if np.any(norms <= 1e-8):
        raise RuntimeError("zero-norm TR pattern after centering")
    x = x / norms[:, None]
    sim = np.clip(x @ x.T, -1.0, 1.0)
    iu = np.triu_indices(len(valid_idx), k=1)
    return (1.0 - sim[iu]).astype(np.float32)


def pair_abs(v: np.ndarray) -> np.ndarray:
    iu = np.triu_indices(len(v), k=1)
    return np.abs(v[iu[0]] - v[iu[1]]).astype(np.float64)


def residualize(y: np.ndarray, nuisance_cols: list[np.ndarray]) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    zcols = []
    for c in nuisance_cols:
        c = np.asarray(c, dtype=np.float64)
        s = float(np.std(c, ddof=0))
        zcols.append((c - float(np.mean(c))) / s if s > 0 else np.zeros_like(c))
    X = np.column_stack([np.ones(len(y), dtype=np.float64)] + zcols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    a = a - np.mean(a)
    b = b - np.mean(b)
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / den) if den > 0 else float("nan")


def fisher_mean(vals: list[float]) -> float:
    a = np.clip(np.asarray(vals, dtype=np.float64), -0.999999, 0.999999)
    return float(np.tanh(np.mean(np.arctanh(a))))


def bootstrap_ci(vals: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(vals)
    means = np.empty(N_BOOT, dtype=np.float64)
    for i in range(N_BOOT):
        means[i] = float(np.mean(vals[rng.integers(0, n, size=n)]))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def exact_signflip_p(vals: np.ndarray) -> float:
    vals = np.asarray(vals, dtype=np.float64)
    obs = float(np.mean(vals))
    n = len(vals)
    ge = 0
    total = 1 << n
    for bits in range(total):
        signs = np.ones(n, dtype=np.float64)
        for j in range(n):
            if (bits >> j) & 1:
                signs[j] = -1.0
        if float(np.mean(vals * signs)) >= obs - 1e-15:
            ge += 1
    return ge / total


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_fmri_reliability/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    atlas_zip = root / "external/lana/SPM_Atlas.zip"
    download(LANA_ZIP_URL, atlas_zip)
    if hash_file(atlas_zip, "md5") != LANA_ZIP_MD5:
        raise RuntimeError("LanA archive MD5 mismatch")
    atlas_dir = root / "external/lana/spm_atlas"
    atlas_path = atlas_dir / LANA_REL
    if not atlas_path.exists():
        atlas_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(atlas_zip) as zf:
            zf.extractall(atlas_dir)
    if hash_file(atlas_path, "sha256") != LANA_SHA256:
        raise RuntimeError("LanA atlas SHA256 mismatch")
    atlas_img = nib.load(str(atlas_path))
    atlas = np.asarray(atlas_img.get_fdata(dtype=np.float32), dtype=np.float32)
    mask = np.isfinite(atlas) & (atlas >= MASK_THRESHOLD)
    n_mask_voxels = int(np.sum(mask))
    if n_mask_voxels < 100:
        raise RuntimeError(f"LanA mask unexpectedly small: {n_mask_voxels}")

    hrf = canonical_hrf(TR)

    # Preflight all small stimulus materials before any neural outcome is computed.
    n_tp_by_story: dict[int, int] = {}
    nuisance_by_story: dict[int, dict] = {}
    for story in STORIES:
        rep_rel = f"derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-{story}_bold.nii.gz"
        rep_path = root / rep_rel
        if rep_path.is_symlink():
            rep_path.unlink()
        if not rep_path.exists() or rep_path.stat().st_size == 0:
            download(f"{OPENNEURO_BASE}/{rep_rel}", rep_path)
        rep_img = nib.load(str(rep_path))
        if tuple(rep_img.shape[:3]) != tuple(mask.shape):
            raise RuntimeError(f"story {story}: representative MNI grid mismatch")
        n_tp = int(rep_img.shape[3])
        n_tp_by_story[story] = n_tp
        nuisance_by_story[story] = preflight_story(root, story, n_tp, hrf)

    story_rows: list[dict] = []
    per_subject_primary: dict[str, list[float]] = {s: [] for s in SUBJECTS}
    per_subject_raw: dict[str, list[float]] = {s: [] for s in SUBJECTS}

    for story in STORIES:
        info = nuisance_by_story[story]
        valid_idx = info["valid_idx"]
        rdms: list[np.ndarray] = []
        for sub in SUBJECTS:
            rel = f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"
            p = root / rel
            if p.is_symlink():
                p.unlink()
            if not p.exists() or p.stat().st_size == 0:
                download(f"{OPENNEURO_BASE}/{rel}", p, timeout=1200)
            img = nib.load(str(p))
            if int(img.shape[3]) != n_tp_by_story[story]:
                raise RuntimeError(f"{sub} story {story}: timepoint mismatch {img.shape[3]} vs {n_tp_by_story[story]}")
            rdms.append(corr_rdm_vector_from_bold(p, mask, valid_idx))

        stack = np.stack(rdms, axis=0).astype(np.float64)
        total = np.sum(stack, axis=0)
        nuis = [
            pair_abs(info["times"]),
            pair_abs(info["word_drive"]),
            pair_abs(info["acoustic_drive"]),
        ]
        n_pairs = int(stack.shape[1])
        for i, sub in enumerate(SUBJECTS):
            target = stack[i]
            loo = (total - target) / (len(SUBJECTS) - 1)
            raw_r = pearson(target, loo)
            target_res = residualize(target, nuis)
            loo_res = residualize(loo, nuis)
            primary_r = pearson(target_res, loo_res)
            if not np.isfinite(primary_r) or not np.isfinite(raw_r):
                raise RuntimeError(f"nonfinite reliability for {sub} story {story}")
            per_subject_primary[sub].append(primary_r)
            per_subject_raw[sub].append(raw_r)
            story_rows.append({
                "subject": sub,
                "story": story,
                "n_timepoints": int(len(valid_idx)),
                "n_pairs": n_pairs,
                "primary_residual_reliability": primary_r,
                "raw_reliability": raw_r,
            })

    participant_rows = []
    primary_vals = []
    raw_vals = []
    for sub in SUBJECTS:
        primary = fisher_mean(per_subject_primary[sub])
        raw = fisher_mean(per_subject_raw[sub])
        primary_vals.append(primary)
        raw_vals.append(raw)
        participant_rows.append({
            "subject": sub,
            "n_stories": len(per_subject_primary[sub]),
            "primary_residual_reliability": primary,
            "raw_reliability": raw,
        })

    primary_arr = np.asarray(primary_vals, dtype=np.float64)
    raw_arr = np.asarray(raw_vals, dtype=np.float64)
    ci_lo, ci_hi = bootstrap_ci(primary_arr)
    p_one = exact_signflip_p(primary_arr)
    gate = bool(float(np.mean(primary_arr)) > 0.0 and ci_lo > 0.0)

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "fMRI neural geometry reliability",
        "model_blind": True,
        "computes_model_outcomes": False,
        "n_subjects": len(SUBJECTS),
        "n_stories": len(STORIES),
        "n_runs": len(SUBJECTS) * len(STORIES),
        "tr_seconds": TR,
        "spatial_representation": {
            "atlas": LANA_REL,
            "atlas_sha256": LANA_SHA256,
            "mask_threshold_probability": MASK_THRESHOLD,
            "n_mask_voxels": n_mask_voxels,
            "grid_exact_match": True,
            "voxelwise_preprocessing": "featurewise z-score across retained TRs, ddof=0",
            "rdm": "correlation distance across LanA-mask multivoxel patterns",
        },
        "temporal_items": "TRs from story audio onset through end of scan",
        "nuisance_controls": [
            "absolute temporal separation in seconds",
            "absolute difference in canonical-HRF-convolved word-onset density",
            "absolute difference in canonical-HRF-convolved acoustic RMS envelope",
        ],
        "reference": "within-story leave-one-participant-out mean neural RDM across other 11 participants",
        "participant_aggregation": "unweighted Fisher-z mean across 60 stories, then tanh",
        "primary_mean": float(np.mean(primary_arr)),
        "primary_median": float(np.median(primary_arr)),
        "primary_n_positive": int(np.sum(primary_arr > 0)),
        "primary_bootstrap_95_ci": [ci_lo, ci_hi],
        "primary_exact_one_sided_signflip_p": p_one,
        "raw_mean_sensitivity": float(np.mean(raw_arr)),
        "raw_median_sensitivity": float(np.median(raw_arr)),
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "reliability_gate_pass": gate,
        "guardrails": {
            "no_model_embeddings_loaded": True,
            "no_roi_threshold_search": True,
            "no_lag_or_hrf_search": True,
            "no_participant_or_story_selection": True,
            "no_result_driven_rescue": True,
        },
    }

    write_csv(out / "story_results.csv", story_rows)
    write_csv(out / "participant_results.csv", participant_rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "gate": gate, "mean": summary["primary_mean"], "ci": summary["primary_bootstrap_95_ci"], "n_mask_voxels": n_mask_voxels}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
