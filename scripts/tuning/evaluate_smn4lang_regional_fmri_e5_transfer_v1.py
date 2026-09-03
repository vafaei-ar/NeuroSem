#!/usr/bin/env python3
"""Frozen Stage-2 regional SMN4Lang multilingual-E5 transfer analysis.

Implements Stage 2 of docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md only after
successful completion of the model-blind Stage-1 regional reliability analysis.
The model contrast, semantic time course, nuisance model, participants, stories,
regional masks, and inferential procedures are fixed by that protocol.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import nibabel as nib
import numpy as np

from scripts.analysis.run_smn4lang_fmri_reliability import (
    STORIES,
    SUBJECTS,
    TR,
    canonical_hrf,
    fisher_mean,
    residualize,
)
from scripts.analysis.run_smn4lang_regional_fmri_reliability_v1 import (
    BOOTSTRAP_SEED,
    MIN_NONCONSTANT_VOXELS,
    load_and_validate_preflight,
    region_rdm_from_loaded_bold,
)
from scripts.audit.preflight_smn4lang_regional_atlases_v1 import affine_equal
from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import (
    ARMS,
    LAMBDA_010_ROOT,
    MODEL_ID,
    MODEL_REVISION,
    PREFIX,
    TEXT_ONLY_ADAPTER,
    latest_completed_adapter,
    load_adapter,
    model_residual_rdm,
    safe_spearman,
    story_context,
)

PROTOCOL = "docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md"
PREFLIGHT_DIR = Path("outputs/smn4lang_regional_atlas_preflight_v1/latest")
RELIABILITY_DIR = Path("outputs/smn4lang_regional_fmri_reliability_v1/latest")
N_BOOT = 10_000
LANGUAGE_KEYS = (
    "language:IFG",
    "language:IFGorb",
    "language:MFG",
    "language:AntTemp",
    "language:PostTemp",
    "language:AngG",
)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_progress(current: int, total: int, phase: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE", "").strip()
    if not raw:
        return
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": int(current),
        "total": int(total),
        "fraction": float(max(0.0, min(1.0, current / total if total else 0.0))),
        "phase": phase,
        "message": message,
        "unit": "story-stages",
        "updated_at_epoch": time.time(),
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def exact_two_sided_signflip_p(vals: np.ndarray) -> float:
    vals = np.asarray(vals, dtype=np.float64)
    if vals.shape != (len(SUBJECTS),) or not np.all(np.isfinite(vals)):
        raise RuntimeError("invalid participant vector for exact sign-flip test")
    obs = abs(float(np.mean(vals)))
    ge = 0
    total = 1 << len(vals)
    for bits in range(total):
        signs = np.ones(len(vals), dtype=np.float64)
        for j in range(len(vals)):
            if (bits >> j) & 1:
                signs[j] = -1.0
        if abs(float(np.mean(vals * signs))) >= obs - 1e-15:
            ge += 1
    return ge / total


def participant_bootstrap_ci(vals: np.ndarray) -> tuple[float, float]:
    vals = np.asarray(vals, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(vals), size=(N_BOOT, len(vals)))
    means = vals[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def language_fwer_p(delta_matrix: np.ndarray) -> np.ndarray:
    """Exact max-|mean| FWER p-values for a 12 x 6 participant-by-region matrix."""
    x = np.asarray(delta_matrix, dtype=np.float64)
    if x.shape != (len(SUBJECTS), len(LANGUAGE_KEYS)) or not np.all(np.isfinite(x)):
        raise RuntimeError("invalid language delta matrix for FWER")
    obs = np.abs(np.mean(x, axis=0))
    null_max = np.empty(1 << len(SUBJECTS), dtype=np.float64)
    for bits in range(1 << len(SUBJECTS)):
        signs = np.ones(len(SUBJECTS), dtype=np.float64)
        for j in range(len(SUBJECTS)):
            if (bits >> j) & 1:
                signs[j] = -1.0
        null_max[bits] = float(np.max(np.abs(np.mean(x * signs[:, None], axis=0))))
    return np.asarray([np.mean(null_max >= v - 1e-15) for v in obs], dtype=np.float64)


def twofactor_bootstrap(
    arm0: np.ndarray,
    arm1: np.ndarray,
) -> tuple[float, float, float]:
    """Resample participants and stories, retaining Fisher-z story aggregation."""
    a0 = np.asarray(arm0, dtype=np.float64)
    a1 = np.asarray(arm1, dtype=np.float64)
    if a0.shape != (len(SUBJECTS), len(STORIES)) or a1.shape != a0.shape:
        raise RuntimeError("invalid matrices for participant-by-story bootstrap")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    boot = np.empty(N_BOOT, dtype=np.float64)
    for b in range(N_BOOT):
        pidx = rng.integers(0, len(SUBJECTS), size=len(SUBJECTS))
        sidx = rng.integers(0, len(STORIES), size=len(STORIES))
        deltas = np.empty(len(SUBJECTS), dtype=np.float64)
        for i, pi in enumerate(pidx):
            z0 = np.arctanh(np.clip(a0[pi, sidx], -0.999999, 0.999999))
            z1 = np.arctanh(np.clip(a1[pi, sidx], -0.999999, 0.999999))
            deltas[i] = np.tanh(np.mean(z1)) - np.tanh(np.mean(z0))
        boot[b] = float(np.mean(deltas))
    return (
        float(np.percentile(boot, 2.5)),
        float(np.percentile(boot, 97.5)),
        float(np.mean(boot > 0.0)),
    )


def load_reliability_gate(reliability_dir: Path, region_keys: list[str]) -> tuple[dict, dict[str, dict]]:
    summary_path = reliability_dir / "summary.json"
    region_path = reliability_dir / "region_summary.csv"
    if not summary_path.exists() or not region_path.exists():
        raise FileNotFoundError(
            "completed Stage-1 regional reliability outputs are missing; run the frozen reliability task first"
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("model_blind") is not True or summary.get("computes_model_outcomes") is not False:
        raise RuntimeError("unexpected Stage-1 provenance flags")
    if int(summary.get("language_regions_structurally_available", -1)) != 6:
        raise RuntimeError("not all six frozen language regions were structurally available in Stage 1")
    if int(summary.get("dk68_regions_structurally_available", -1)) != 68:
        raise RuntimeError("not all 68 frozen DK regions were structurally available in Stage 1")
    rows = read_csv(region_path)
    by_key = {str(r["region_key"]): r for r in rows}
    if set(by_key) != set(region_keys):
        raise RuntimeError("Stage-1 regional key set does not match the frozen Stage-2 region set")
    for key in region_keys:
        r = by_key[key]
        if str(r.get("structurally_available_all_runs", "")).lower() != "true":
            raise RuntimeError(f"Stage-1 region unexpectedly structurally unavailable: {key}")
        if int(r.get("complete_loo_stories", -1)) != len(STORIES):
            raise RuntimeError(f"Stage-1 region lacks complete story set: {key}")
    return summary, by_key


def build_model_rdms_with_progress(
    contexts: dict[int, dict],
    device: str,
    hrf: np.ndarray,
    progress_offset: int,
    progress_total: int,
) -> tuple[dict[str, dict[int, np.ndarray]], dict[str, str]]:
    import torch

    adapter_010 = latest_completed_adapter(LAMBDA_010_ROOT)
    specs = {"lambda_0": TEXT_ONLY_ADAPTER, "lambda_0p10": adapter_010}
    output: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in ARMS}
    provenance: dict[str, str] = {}
    current = progress_offset
    for arm in ARMS:
        adapter = specs[arm]
        print(f"Loading frozen model arm {arm}: {adapter}", flush=True)
        tokenizer, model = load_adapter(adapter, device)
        for story in STORIES:
            output[arm][story] = model_residual_rdm(model, tokenizer, contexts[story], device, hrf)
            current += 1
            write_progress(
                current,
                progress_total,
                "regional_model_geometry",
                f"encoded {arm} story {story} of {len(STORIES)}",
            )
        provenance[arm] = str(adapter.resolve())
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return output, provenance


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--preflight-dir", type=Path, default=PREFLIGHT_DIR)
    ap.add_argument("--reliability-dir", type=Path, default=RELIABILITY_DIR)
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest"))
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
    preflight_dir = args.preflight_dir.resolve()
    reliability_dir = args.reliability_dir.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    regions, target_shape, target_affine, preflight_hash = load_and_validate_preflight(root, preflight_dir)
    region_keys = [str(r["key"]) for r in regions]
    region_by_key = {str(r["key"]): r for r in regions}
    if tuple(k for k in region_keys if k.startswith("language:")) != LANGUAGE_KEYS:
        raise RuntimeError("language region order differs from frozen six-region family")

    reliability_summary, reliability_by_key = load_reliability_gate(reliability_dir, region_keys)

    hrf = canonical_hrf(TR)
    contexts = {story: story_context(root, story, hrf) for story in STORIES}
    progress_total = len(ARMS) * len(STORIES) + len(STORIES)
    write_progress(0, progress_total, "regional_model_geometry", "starting frozen Stage-2 regional transfer")
    model_rdms, model_provenance = build_model_rdms_with_progress(contexts, device, hrf, 0, progress_total)

    # story-level values: region -> subject -> arm -> 60 story values
    values: dict[str, dict[str, dict[str, list[float]]]] = {
        key: {sub: {arm: [] for arm in ARMS} for sub in SUBJECTS} for key in region_keys
    }
    story_rows: list[dict] = []
    structural_failures: list[dict] = []
    progress_current = len(ARMS) * len(STORIES)

    print("Evaluating frozen regional neural-model alignment", flush=True)
    for story in STORIES:
        ctx = contexts[story]
        valid_idx = np.asarray(ctx["valid_idx"], dtype=int)
        iu = np.triu_indices(len(valid_idx), k=1)
        for sub in SUBJECTS:
            path = root / f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"
            if not path.exists() or path.stat().st_size == 0:
                raise FileNotFoundError(path)
            img = nib.load(str(path))
            if tuple(img.shape[:3]) != target_shape or not affine_equal(img.affine, target_affine):
                raise RuntimeError(f"{sub} story {story}: MNI grid mismatch")
            if img.shape[3] <= int(valid_idx[-1]):
                raise RuntimeError(f"{sub} story {story}: time index out of bounds")
            data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
            for region in regions:
                key = str(region["key"])
                neural, n_nonconstant, reason = region_rdm_from_loaded_bold(
                    data, np.asarray(region["mask"], dtype=bool), valid_idx, iu
                )
                if neural is None:
                    structural_failures.append({
                        "region_key": key,
                        "subject": sub,
                        "story": story,
                        "n_nonconstant_voxels": n_nonconstant,
                        "reason": reason,
                    })
                    raise RuntimeError(
                        f"Stage-2 structural failure despite Stage-1 all-run availability: {key} {sub} story {story}: {reason}"
                    )
                neural_resid = residualize(neural, ctx["nuisance"])
                r0 = safe_spearman(neural_resid, model_rdms["lambda_0"][story])
                r1 = safe_spearman(neural_resid, model_rdms["lambda_0p10"][story])
                values[key][sub]["lambda_0"].append(r0)
                values[key][sub]["lambda_0p10"].append(r1)
                story_rows.append({
                    "region_key": key,
                    "family": region["family"],
                    "region_name": region["region_name"],
                    "hemisphere": region["hemisphere"],
                    "parcel_id": region["parcel_id"],
                    "subject": sub,
                    "story": story,
                    "n_timepoints": len(valid_idx),
                    "n_pairs": len(iu[0]),
                    "n_nonconstant_voxels": n_nonconstant,
                    "lambda_0_residual_rsa": r0,
                    "lambda_0p10_residual_rsa": r1,
                    "delta_0p10_minus_0": r1 - r0,
                })
            del data
        progress_current += 1
        write_progress(
            progress_current,
            progress_total,
            "regional_neural_model_rsa",
            f"completed regional RSA story {story} of {len(STORIES)}",
        )
        print(f"Completed regional RSA story {story:02d}/60", flush=True)

    participant_rows: list[dict] = []
    participant_by_region: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for key in region_keys:
        region = region_by_key[key]
        for sub in SUBJECTS:
            if any(len(values[key][sub][arm]) != len(STORIES) for arm in ARMS):
                raise RuntimeError(f"incomplete story set for {key} {sub}")
            a0 = fisher_mean(values[key][sub]["lambda_0"])
            a1 = fisher_mean(values[key][sub]["lambda_0p10"])
            delta = a1 - a0
            participant_by_region[key][sub] = {"lambda_0": a0, "lambda_0p10": a1, "delta": delta}
            participant_rows.append({
                "region_key": key,
                "family": region["family"],
                "region_name": region["region_name"],
                "hemisphere": region["hemisphere"],
                "parcel_id": region["parcel_id"],
                "subject": sub,
                "n_stories": len(STORIES),
                "lambda_0_residual_rsa": a0,
                "lambda_0p10_residual_rsa": a1,
                "delta_0p10_minus_0": delta,
            })

    language_delta = np.asarray(
        [[participant_by_region[key][sub]["delta"] for key in LANGUAGE_KEYS] for sub in SUBJECTS],
        dtype=np.float64,
    )
    fwer = language_fwer_p(language_delta)

    region_rows: list[dict] = []
    twofactor_rows: list[dict] = []
    for key in region_keys:
        region = region_by_key[key]
        a0 = np.asarray([participant_by_region[key][sub]["lambda_0"] for sub in SUBJECTS], dtype=np.float64)
        a1 = np.asarray([participant_by_region[key][sub]["lambda_0p10"] for sub in SUBJECTS], dtype=np.float64)
        d = a1 - a0
        ci_lo, ci_hi = participant_bootstrap_ci(d)
        reliability = reliability_by_key[key]
        row = {
            "region_key": key,
            "family": region["family"],
            "region_name": region["region_name"],
            "hemisphere": region["hemisphere"],
            "parcel_id": region["parcel_id"],
            "atlas_voxels": region["atlas_voxels"],
            "model_blind_reliability_mean": float(reliability["primary_mean"]),
            "reliability_gate_pass": str(reliability["reliability_gate_pass"]).lower() == "true",
            "lambda_0_mean": float(np.mean(a0)),
            "lambda_0_median": float(np.median(a0)),
            "lambda_0p10_mean": float(np.mean(a1)),
            "lambda_0p10_median": float(np.median(a1)),
            "delta_mean": float(np.mean(d)),
            "delta_median": float(np.median(d)),
            "delta_n_positive": int(np.sum(d > 0)),
            "delta_fraction_positive": float(np.mean(d > 0)),
            "delta_bootstrap_ci_low": ci_lo,
            "delta_bootstrap_ci_high": ci_hi,
            "delta_exact_two_sided_signflip_p": exact_two_sided_signflip_p(d),
            "language_family_fwer_p": "",
            "interpretation_status": "reliable" if str(reliability["reliability_gate_pass"]).lower() == "true" else "reliability-limited",
        }
        if key in LANGUAGE_KEYS:
            row["language_family_fwer_p"] = float(fwer[LANGUAGE_KEYS.index(key)])
            m0 = np.asarray([values[key][sub]["lambda_0"] for sub in SUBJECTS], dtype=np.float64)
            m1 = np.asarray([values[key][sub]["lambda_0p10"] for sub in SUBJECTS], dtype=np.float64)
            tf_lo, tf_hi, tf_gt0 = twofactor_bootstrap(m0, m1)
            twofactor_rows.append({
                "region_key": key,
                "region_name": region["region_name"],
                "bootstrap_n": N_BOOT,
                "seed": BOOTSTRAP_SEED,
                "ci_low": tf_lo,
                "ci_high": tf_hi,
                "fraction_mean_delta_gt_0": tf_gt0,
                "scope": "sensitivity over the 12 analyzed participants and 60 analyzed stories",
            })
        region_rows.append(row)

    dk_keys = [key for key in region_keys if key.startswith("dk:")]
    dk_matrix_rows: list[dict] = []
    for key in dk_keys:
        region = region_by_key[key]
        row = {
            "parcel_id": region["parcel_id"],
            "parcel_name": region["region_name"],
            "hemisphere": region["hemisphere"],
            "atlas_voxels": region["atlas_voxels"],
        }
        for sub in SUBJECTS:
            row[f"{sub}_delta"] = participant_by_region[key][sub]["delta"]
        row["participant_mean_delta"] = float(np.mean([participant_by_region[key][s]["delta"] for s in SUBJECTS]))
        row["participant_median_delta"] = float(np.median([participant_by_region[key][s]["delta"] for s in SUBJECTS]))
        dk_matrix_rows.append(row)

    summary = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory regional SMN4Lang multilingual-E5 transfer",
        "protocol": PROTOCOL,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "n_subjects": len(SUBJECTS),
        "n_stories": len(STORIES),
        "n_regions": len(regions),
        "n_language_regions": len(LANGUAGE_KEYS),
        "n_dk68_regions": len(dk_keys),
        "participant_is_primary_inferential_unit": True,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_prefix": PREFIX,
        "contrast": "ChineseEEG-trained multilingual-E5 lambda=0.10 genuine-neural minus lambda=0 text-only",
        "model_adapters": model_provenance,
        "preflight_summary_sha256": preflight_hash,
        "stage1_reliability_model_blind": reliability_summary.get("model_blind"),
        "stage1_language_regions_passing_gate": reliability_summary.get("language_regions_passing_reliability_gate"),
        "stage1_dk68_regions_passing_gate": reliability_summary.get("dk68_regions_passing_reliability_gate"),
        "rsa": {
            "story_metric": "Spearman correlation after residualizing neural and model RDMs against frozen nuisance family",
            "participant_aggregation": "unweighted Fisher-z mean across all 60 stories then tanh",
            "delta": "participant neural-guided RSA minus participant text-only RSA",
        },
        "language_inference": {
            "bootstrap_n": N_BOOT,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "signflip": "exact two-sided across 2^12 participant sign configurations",
            "fwer": "exact max-absolute-mean sign-flip across the fixed six-language-region family",
            "twofactor_bootstrap": "participants x analyzed stories, preserving Fisher-z story aggregation",
        },
        "dk68_inference": "spatial characterization phenotype; no parcel-level p-value is used for AHBA selection",
        "structural_failures": structural_failures,
        "guardrails": {
            "no_new_training": True,
            "no_target_side_model_selection": True,
            "no_roi_selection_from_transfer_outcomes": True,
            "no_model_layer_checkpoint_pooling_or_lambda_search": True,
            "stage1_completed_before_model_import_and_load": True,
            "all_predefined_regions_reported": True,
        },
        "language_regions": [r for r in region_rows if r["family"] == "language"],
        "dk68_regions": [r for r in region_rows if r["family"] == "dk68"],
    }

    write_csv(out / "story_results.csv", story_rows)
    write_csv(out / "participant_results.csv", participant_rows)
    write_csv(out / "region_summary.csv", region_rows)
    write_csv(out / "language_twofactor_bootstrap.csv", twofactor_rows)
    write_csv(out / "dk68_participant_delta_matrix.csv", dk_matrix_rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write_progress(progress_total, progress_total, "regional_transfer_complete", "completed frozen Stage-2 regional transfer")
    print(json.dumps({
        "status": "completed",
        "language_regions": len(LANGUAGE_KEYS),
        "dk68_regions": len(dk_keys),
        "structural_failures": len(structural_failures),
        "device": device,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
