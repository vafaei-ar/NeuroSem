#!/usr/bin/env python3
"""Frozen ChineseEEG-to-SMN4Lang fMRI multilingual-E5 transfer test.

Confirmatory contrast only: ChineseEEG-trained lambda=0.10 neural-guided adapter
minus matched lambda=0 text-only adapter. The fMRI representation, LanA mask,
HRF, nuisance controls, participants, stories, and inference are inherited from the
prospectively frozen SMN4Lang reliability analysis. No SMN4Lang tuning or search is
performed here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.io import loadmat
from scipy.signal import fftconvolve
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analysis.run_smn4lang_fmri_reliability import (
    SUBJECTS,
    STORIES,
    TR,
    MASK_THRESHOLD,
    canonical_hrf,
    corr_rdm_vector_from_bold,
    pair_abs,
    preflight_story,
    residualize,
    fisher_mean,
    bootstrap_ci,
    exact_signflip_p,
)
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import (
    MODEL_ID,
    MODEL_REVISION,
    PREFIX,
    TEXT_ONLY_ADAPTER,
    LAMBDA_010_ROOT,
    latest_completed_adapter,
    load_adapter,
    encode_texts,
)

LANA_ZIP_MD5 = "5e981df0866f2522e75a7899f69a00a5"
LANA_REL = "SPM/LanA_n806.nii"
LANA_SHA256 = "3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babcaa3"
FINAL_PUNCT = set("。！？!?")
ARMS = ("lambda_0", "lambda_0p10")
WORD_DRIVE_EPS = 0.0


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    r = float(spearmanr(np.asarray(a, float), np.asarray(b, float)).statistic)
    if not np.isfinite(r):
        raise RuntimeError("non-finite residual Spearman RSA")
    return r


def as_1d_strings(v) -> list[str]:
    arr = np.asarray(v, dtype=object).reshape(-1)
    return [str(x) for x in arr]


def as_1d_float(v) -> np.ndarray:
    return np.asarray(v, dtype=float).reshape(-1)


def causal_sentence_prefixes(words: list[str]) -> list[str]:
    prefixes: list[str] = []
    current = ""
    for raw in words:
        token = str(raw).strip()
        if not token:
            raise RuntimeError("empty released word token")
        current += token
        prefixes.append(current)
        if any(ch in FINAL_PUNCT for ch in token):
            current = ""
    return prefixes


def load_word_annotation(root: Path, story: int) -> tuple[np.ndarray, list[str], list[str]]:
    path = root / f"derivatives/annotations/time_align/word-level/story_{story}_word_time.mat"
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    d = loadmat(path, simplify_cells=True)
    for key in ("start", "end", "word"):
        if key not in d:
            raise RuntimeError(f"story {story}: missing word annotation key {key}")
    starts = as_1d_float(d["start"])
    ends = as_1d_float(d["end"])
    words = as_1d_strings(d["word"])
    if len(starts) != len(ends) or len(starts) != len(words) or len(words) == 0:
        raise RuntimeError(f"story {story}: inconsistent word annotation lengths")
    if np.any(~np.isfinite(starts)) or np.any(~np.isfinite(ends)) or np.any(np.diff(starts) < 0):
        raise RuntimeError(f"story {story}: invalid word timings")
    if np.any(ends < starts):
        raise RuntimeError(f"story {story}: word end precedes start")
    prefixes = causal_sentence_prefixes(words)
    return starts, words, prefixes


def fresh_lana_mask(source_root: Path, runtime_dir: Path) -> np.ndarray:
    source_zip = source_root / "external/lana/SPM_Atlas.zip"
    if not source_zip.exists() or digest(source_zip, "md5") != LANA_ZIP_MD5:
        raise RuntimeError("verified LanA archive missing or MD5 mismatch")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = runtime_dir / LANA_REL
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    atlas_path.unlink(missing_ok=True)
    with zipfile.ZipFile(source_zip) as zf:
        with zf.open(LANA_REL) as src, atlas_path.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    observed = digest(atlas_path, "sha256")
    if observed != LANA_SHA256:
        raise RuntimeError(f"LanA atlas SHA256 mismatch: {observed}")
    img = nib.load(str(atlas_path))
    atlas = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
    mask = np.isfinite(atlas) & (atlas >= MASK_THRESHOLD)
    if int(mask.sum()) != 25137:
        raise RuntimeError(f"unexpected LanA >=0.20 mask size: {int(mask.sum())}")
    return mask


def story_context(root: Path, story: int, hrf: np.ndarray) -> dict:
    rep = root / f"derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-{story}_bold.nii.gz"
    if not rep.exists() or rep.stat().st_size == 0:
        raise FileNotFoundError(rep)
    n_tp = int(nib.load(str(rep)).shape[3])
    info = preflight_story(root, story, n_tp, hrf)
    starts, words, prefixes = load_word_annotation(root, story)
    if len(starts) != int(info["n_words"]):
        raise RuntimeError(f"story {story}: annotation/preflight word-count mismatch")

    positive = np.asarray(info["word_drive"], float) > WORD_DRIVE_EPS
    if int(positive.sum()) < 100:
        raise RuntimeError(f"story {story}: too few positive-word-drive TRs: {int(positive.sum())}")
    valid_idx = np.asarray(info["valid_idx"], int)[positive]
    times = np.asarray(info["times"], float)[positive]
    word_drive = np.asarray(info["word_drive"], float)[positive]
    acoustic_drive = np.asarray(info["acoustic_drive"], float)[positive]
    nuisance = [pair_abs(times), pair_abs(word_drive), pair_abs(acoustic_drive)]

    return {
        "story": story,
        "n_tp": n_tp,
        "starts": starts,
        "words": words,
        "prefixes": prefixes,
        "valid_idx": valid_idx,
        "times": times,
        "word_drive": word_drive,
        "acoustic_drive": acoustic_drive,
        "nuisance": nuisance,
        "n_items": int(len(valid_idx)),
        "n_pairs": int(len(valid_idx) * (len(valid_idx) - 1) // 2),
    }


def model_residual_rdm(model, tokenizer, ctx: dict, device: str, hrf: np.ndarray) -> np.ndarray:
    emb = encode_texts(model, tokenizer, ctx["prefixes"], device)
    if emb.ndim != 2 or emb.shape[0] != len(ctx["starts"]):
        raise RuntimeError(f"story {ctx['story']}: unexpected embedding shape {emb.shape}")
    events = np.zeros((ctx["n_tp"], emb.shape[1]), dtype=np.float64)
    for start, vec in zip(ctx["starts"], emb, strict=True):
        idx = int(math.floor(float(start) / TR))
        if 0 <= idx < ctx["n_tp"]:
            events[idx] += vec
    drive = fftconvolve(events, hrf[:, None], mode="full", axes=0)[: ctx["n_tp"]]
    x = np.asarray(drive[ctx["valid_idx"]], dtype=np.float64)
    norms = np.linalg.norm(x, axis=1)
    if np.any(~np.isfinite(norms)) or np.any(norms <= 1e-12):
        raise RuntimeError(f"story {ctx['story']}: zero/nonfinite HRF semantic state")
    rdm = pdist(x, metric="cosine")
    if len(rdm) != ctx["n_pairs"] or not np.isfinite(rdm).all():
        raise RuntimeError(f"story {ctx['story']}: invalid model RDM")
    return residualize(rdm, ctx["nuisance"])


def build_model_rdms(contexts: dict[int, dict], device: str, hrf: np.ndarray) -> tuple[dict, dict]:
    import torch

    adapter_010 = latest_completed_adapter(LAMBDA_010_ROOT)
    specs = {
        "lambda_0": TEXT_ONLY_ADAPTER,
        "lambda_0p10": adapter_010,
    }
    output: dict[str, dict[int, np.ndarray]] = {a: {} for a in ARMS}
    provenance: dict[str, str] = {}
    for arm in ARMS:
        adapter = specs[arm]
        print(f"Loading frozen model arm {arm}: {adapter}", flush=True)
        tokenizer, model = load_adapter(adapter, device)
        for story in STORIES:
            print(f"Encoding {arm} story {story:02d}/60", flush=True)
            output[arm][story] = model_residual_rdm(model, tokenizer, contexts[story], device, hrf)
        provenance[arm] = str(adapter.resolve())
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return output, provenance


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--reliability-summary", type=Path, default=Path("outputs/smn4lang_fmri_reliability/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_fmri_e5_transfer_v1/latest"))
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    import torch

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    reliability = json.loads(args.reliability_summary.read_text(encoding="utf-8"))
    if not reliability.get("reliability_gate_pass"):
        raise RuntimeError("SMN4Lang fMRI reliability gate did not pass")
    if int(reliability.get("n_subjects", -1)) != 12 or int(reliability.get("n_stories", -1)) != 60:
        raise RuntimeError("unexpected frozen SMN4Lang reliability cohort")
    spatial = reliability.get("spatial_representation", {})
    if spatial.get("atlas_sha256") != LANA_SHA256 or float(spatial.get("mask_threshold_probability", -1)) != MASK_THRESHOLD:
        raise RuntimeError("reliability-stage LanA specification mismatch")

    hrf = canonical_hrf(TR)
    mask = fresh_lana_mask(root, out.parent / "runtime_atlas")

    print("Freezing story contexts before model loading", flush=True)
    contexts = {story: story_context(root, story, hrf) for story in STORIES}

    print("Building the two prospectively frozen model geometries", flush=True)
    model_rdms, model_provenance = build_model_rdms(contexts, device, hrf)

    story_rows: list[dict] = []
    by_subject: dict[str, dict[str, list[float]]] = {
        sub: {arm: [] for arm in ARMS} for sub in SUBJECTS
    }

    print("Evaluating neural-model alignment across 12 participants x 60 stories", flush=True)
    for story in STORIES:
        ctx = contexts[story]
        for sub in SUBJECTS:
            path = root / f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"
            if not path.exists() or path.stat().st_size == 0:
                raise FileNotFoundError(path)
            neural = corr_rdm_vector_from_bold(path, mask, ctx["valid_idx"])
            neural_resid = residualize(neural, ctx["nuisance"])
            vals = {
                arm: safe_spearman(neural_resid, model_rdms[arm][story])
                for arm in ARMS
            }
            for arm in ARMS:
                by_subject[sub][arm].append(vals[arm])
            story_rows.append({
                "subject": sub,
                "story": story,
                "n_timepoints": ctx["n_items"],
                "n_pairs": ctx["n_pairs"],
                "lambda_0_residual_rsa": vals["lambda_0"],
                "lambda_0p10_residual_rsa": vals["lambda_0p10"],
                "delta_0p10_minus_0": vals["lambda_0p10"] - vals["lambda_0"],
            })
        print(f"Completed neural-model RSA for story {story:02d}/60", flush=True)

    participant_rows: list[dict] = []
    deltas: list[float] = []
    arm_means: dict[str, list[float]] = {arm: [] for arm in ARMS}
    for sub in SUBJECTS:
        if any(len(by_subject[sub][arm]) != 60 for arm in ARMS):
            raise RuntimeError(f"{sub}: expected 60 story RSAs per model arm")
        a0 = fisher_mean(by_subject[sub]["lambda_0"])
        a1 = fisher_mean(by_subject[sub]["lambda_0p10"])
        delta = a1 - a0
        arm_means["lambda_0"].append(a0)
        arm_means["lambda_0p10"].append(a1)
        deltas.append(delta)
        participant_rows.append({
            "subject": sub,
            "n_stories": 60,
            "lambda_0_residual_rsa": a0,
            "lambda_0p10_residual_rsa": a1,
            "delta_0p10_minus_0": delta,
        })

    d = np.asarray(deltas, dtype=np.float64)
    ci = bootstrap_ci(d)
    p = exact_signflip_p(d)
    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "prospectively frozen fMRI multilingual-E5 transfer",
        "confirmatory_contrast": "ChineseEEG-trained E5 lambda=0.10 neural-guided minus lambda=0 text-only",
        "n_subjects": 12,
        "n_stories": 60,
        "n_runs": 720,
        "participant_is_inferential_unit": True,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_prefix": PREFIX,
        "model_provenance": model_provenance,
        "semantic_mapping": {
            "unit": "TR-level causal within-sentence-prefix E5 state",
            "word_event_time": "released word onset",
            "sentence_reset_punctuation": sorted(FINAL_PUNCT),
            "word_event_to_tr": "floor(word_start / 0.71)",
            "temporal_kernel": "same fixed canonical HRF as reliability analysis",
            "tr_inclusion": "reliability stimulus-period TRs with HRF word-onset density > 0",
            "model_rdm": "cosine distance",
        },
        "neural_representation": {
            "atlas": LANA_REL,
            "atlas_sha256": LANA_SHA256,
            "mask_threshold_probability": MASK_THRESHOLD,
            "n_mask_voxels": int(mask.sum()),
            "rdm": "correlation distance across LanA-mask multivoxel patterns",
        },
        "nuisance_controls": [
            "absolute temporal separation in seconds",
            "absolute difference in canonical-HRF-convolved word-onset density",
            "absolute difference in canonical-HRF-convolved acoustic RMS envelope",
        ],
        "within_story_statistic": "Spearman correlation of nuisance-residualized neural and model RDMs",
        "participant_aggregation": "unweighted Fisher-z mean across 60 stories, then tanh",
        "lambda_0_mean_participant_rsa": float(np.mean(arm_means["lambda_0"])),
        "lambda_0p10_mean_participant_rsa": float(np.mean(arm_means["lambda_0p10"])),
        "primary_mean_delta": float(np.mean(d)),
        "primary_median_delta": float(np.median(d)),
        "primary_n_positive": int(np.sum(d > 0)),
        "primary_fraction_positive": float(np.mean(d > 0)),
        "primary_bootstrap_95_ci_mean_delta": [float(ci[0]), float(ci[1])],
        "primary_exact_one_sided_signflip_p": float(p),
        "bootstrap_n": 10000,
        "bootstrap_seed": 20260827,
        "guardrails": {
            "reliability_gate_verified_before_model_loading": True,
            "no_smn4lang_training": True,
            "only_lambda_0_and_lambda_0p10_loaded": True,
            "no_layer_search": True,
            "no_lambda_search": True,
            "no_checkpoint_search": True,
            "no_roi_search": True,
            "no_lag_or_hrf_search": True,
            "no_semantic_unit_search": True,
        },
    }

    write_csv(out / "participant_results.csv", participant_rows)
    write_csv(out / "story_results.csv", story_rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
