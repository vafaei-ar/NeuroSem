#!/usr/bin/env python3
"""Model-blind regional SMN4Lang fMRI reliability for the frozen NeuroSem extension.

This stage implements Stage 1 of docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md.
It reads SMN4Lang BOLD data and the already-frozen regional atlases, but it does
not import or load language-model representations, adapters, or model outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.processing import resample_from_to

from scripts.analysis.run_smn4lang_fmri_reliability import (
    OPENNEURO_BASE,
    STORIES,
    SUBJECTS,
    TR,
    canonical_hrf,
    download,
    fisher_mean,
    pair_abs,
    pearson,
    preflight_story,
    residualize,
)
from scripts.audit.preflight_smn4lang_regional_atlases_v1 import (
    EVLAB_LANGUAGE_NII_URL,
    EXPECTED_LANGUAGE,
    NAME_TO_LEFT_LABEL,
    affine_equal,
    integer_label_image,
    norm_hemi,
)

PROTOCOL = "docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md"
AMENDMENTS = [
    "docs/27_NMI_REGIONAL_FMRI_ATLAS_PREFLIGHT_AMENDMENT_V1.md",
    "docs/28_NMI_REGIONAL_FMRI_DK_RESAMPLING_AMENDMENT_V1.md",
]
PREFLIGHT_DIR = Path("outputs/smn4lang_regional_atlas_preflight_v1/latest")
BOOTSTRAP_SEED = 20260902
N_BOOT = 10_000
MIN_NONCONSTANT_VOXELS = 100


def sha256(path: Path) -> str:
    h = hashlib.sha256()
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


def write_progress(current: int, total: int, message: str) -> None:
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
        "phase": "regional_fmri_reliability",
        "message": message,
        "unit": "stories",
        "updated_at_epoch": time.time(),
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def exact_two_sided_signflip_p(vals: np.ndarray) -> float:
    vals = np.asarray(vals, dtype=np.float64)
    if vals.ndim != 1 or len(vals) != len(SUBJECTS) or not np.all(np.isfinite(vals)):
        raise RuntimeError("invalid participant values for exact sign-flip test")
    obs = abs(float(np.mean(vals)))
    ge = 0
    total = 1 << len(vals)
    for bits in range(total):
        signs = np.ones(len(vals), dtype=np.float64)
        for j in range(len(vals)):
            if (bits >> j) & 1:
                signs[j] = -1.0
        stat = abs(float(np.mean(vals * signs)))
        if stat >= obs - 1e-15:
            ge += 1
    return ge / total


def bootstrap_ci(vals: np.ndarray, resample_idx: np.ndarray) -> tuple[float, float]:
    vals = np.asarray(vals, dtype=np.float64)
    means = vals[resample_idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def load_and_validate_preflight(root: Path, preflight_dir: Path) -> tuple[list[dict], tuple[int, int, int], np.ndarray, str]:
    summary_path = preflight_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(
            "regional atlas preflight summary is missing; run run_smn4lang_regional_atlas_preflight_v1 first"
        )
    preflight_hash = sha256(summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("ready_for_frozen_regional_reliability") is not True:
        raise RuntimeError(f"regional atlas preflight is not ready: blockers={summary.get('blockers')}")
    if summary.get("blockers") not in ([], None):
        raise RuntimeError(f"regional atlas preflight reports blockers: {summary.get('blockers')}")
    if summary.get("loads_bold_values") is not False or summary.get("computes_regional_reliability") is not False:
        raise RuntimeError("unexpected preflight provenance flags")

    rep = summary["representative_bold_header"]
    target_shape = tuple(int(x) for x in rep["shape_xyz"])
    target_affine = np.asarray(rep["affine"], dtype=np.float64)

    ev = summary["evlab_language_parcels"]
    if ev.get("grid_exact_match_to_smn4lang") is not True:
        raise RuntimeError("preflight did not establish exact EvLab-SMN4Lang grid agreement")
    ev_path = root / "external/evlab_language_parcels_sn220/allParcels-language-SN220.nii"
    if not ev_path.exists() or ev_path.stat().st_size == 0:
        download(EVLAB_LANGUAGE_NII_URL, ev_path, timeout=600)
    if sha256(ev_path) != str(ev["nifti_sha256"]):
        raise RuntimeError("EvLab parcel bytes do not match the successful frozen preflight")
    ev_img = nib.load(str(ev_path))
    if tuple(ev_img.shape[:3]) != target_shape or not affine_equal(ev_img.affine, target_affine):
        raise RuntimeError("EvLab parcel grid changed after the successful preflight")
    ev_int = integer_label_image(ev_img, "EvLab language parcels")

    dk = summary["desikan_killiany"]
    if dk.get("resampled_grid_exact_match_to_smn4lang") is not True:
        raise RuntimeError("preflight did not establish resampled DK-SMN4Lang grid agreement")
    if dk.get("missing_cortical_ids_after_resampling") not in ([], None):
        raise RuntimeError("preflight reports missing cortical DK IDs after resampling")
    if int(dk.get("n_cortical", -1)) != 68 or int(dk.get("n_left", -1)) != 34 or int(dk.get("n_right", -1)) != 34:
        raise RuntimeError("unexpected DK cortical metadata counts in preflight")
    if dk.get("expression_id_match") is not True or int(dk.get("expression_metadata_mismatch_count", -1)) != 0:
        raise RuntimeError("DK metadata does not match the frozen AHBA expression bundle")

    dk_resampled_path = preflight_dir / "dk68_resampled_to_smn4lang.nii.gz"
    expected_dk_hash = str(dk["resampled_nifti_sha256"])
    if not dk_resampled_path.exists() or dk_resampled_path.stat().st_size == 0:
        import abagen

        atlas = abagen.fetch_desikan_killiany(surface=False)
        if not isinstance(atlas, dict) or "image" not in atlas:
            raise RuntimeError("unexpected abagen Desikan-Killiany return object")
        source_path = Path(atlas["image"]).resolve()
        if sha256(source_path) != str(dk["source_nifti_sha256"]):
            raise RuntimeError("DK source atlas bytes differ from the successful frozen preflight")
        source_img = nib.load(str(source_path))
        resampled = resample_from_to(
            source_img,
            (target_shape, target_affine),
            order=0,
            mode="constant",
            cval=0.0,
        )
        dk_resampled_path.parent.mkdir(parents=True, exist_ok=True)
        nib.save(resampled, str(dk_resampled_path))
    if sha256(dk_resampled_path) != expected_dk_hash:
        raise RuntimeError("resampled DK bytes do not match the successful frozen preflight")
    dk_img = nib.load(str(dk_resampled_path))
    if tuple(dk_img.shape[:3]) != target_shape or not affine_equal(dk_img.affine, target_affine):
        raise RuntimeError("resampled DK grid changed after the successful preflight")
    dk_int = integer_label_image(dk_img, "resampled Desikan-Killiany atlas")

    regions: list[dict] = []
    language_rows = ev.get("region_rows", [])
    by_name = {str(r["region"]): r for r in language_rows}
    if set(by_name) != set(EXPECTED_LANGUAGE):
        raise RuntimeError("successful preflight does not contain the exact six frozen language regions")
    for name in EXPECTED_LANGUAGE:
        label = int(NAME_TO_LEFT_LABEL[name])
        row = by_name[name]
        if int(row["label"]) != label:
            raise RuntimeError(f"language label mismatch for {name}")
        mask = ev_int == label
        atlas_voxels = int(np.sum(mask))
        if atlas_voxels != int(row["mask_voxels"]):
            raise RuntimeError(f"language atlas voxel-count mismatch for {name}")
        regions.append(
            {
                "key": f"language:{name}",
                "family": "language",
                "region_name": name,
                "hemisphere": "L",
                "parcel_id": "",
                "atlas_label": label,
                "atlas_voxels": atlas_voxels,
                "mask": mask,
            }
        )

    dk_rows = dk.get("region_rows", [])
    if len(dk_rows) != 68:
        raise RuntimeError(f"successful preflight contains {len(dk_rows)} DK rows, expected 68")
    seen_ids: set[int] = set()
    for row in dk_rows:
        pid = int(row["parcel_id"])
        if pid in seen_ids:
            raise RuntimeError(f"duplicate DK parcel ID {pid}")
        seen_ids.add(pid)
        mask = dk_int == pid
        atlas_voxels = int(np.sum(mask))
        if atlas_voxels != int(row["resampled_voxels"]):
            raise RuntimeError(f"DK resampled voxel-count mismatch for parcel {pid}")
        regions.append(
            {
                "key": f"dk:{pid}",
                "family": "dk68",
                "region_name": str(row["parcel_name"]),
                "hemisphere": norm_hemi(str(row["hemisphere"])),
                "parcel_id": pid,
                "atlas_label": pid,
                "atlas_voxels": atlas_voxels,
                "mask": mask,
            }
        )
    if len(regions) != 74:
        raise RuntimeError(f"expected 74 frozen regions, got {len(regions)}")
    return regions, target_shape, target_affine, preflight_hash


def region_rdm_from_loaded_bold(
    data: np.ndarray,
    mask: np.ndarray,
    valid_idx: np.ndarray,
    iu: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray | None, int, str]:
    x = np.asarray(data[mask, :][:, valid_idx].T, dtype=np.float32)
    if x.ndim != 2 or x.shape[0] != len(valid_idx):
        return None, 0, "unexpected_extracted_shape"
    mu = np.mean(x, axis=0, dtype=np.float64).astype(np.float32)
    sd = np.std(x, axis=0, ddof=0, dtype=np.float64).astype(np.float32)
    keep = np.isfinite(mu) & np.isfinite(sd) & (sd > 1e-6)
    n_nonconstant = int(np.sum(keep))
    if n_nonconstant < MIN_NONCONSTANT_VOXELS:
        return None, n_nonconstant, "fewer_than_100_nonconstant_voxels"

    z = (x[:, keep] - mu[keep]) / sd[keep]
    if not np.all(np.isfinite(z)):
        return None, n_nonconstant, "nonfinite_standardized_voxel_values"
    z -= np.mean(z, axis=1, keepdims=True, dtype=np.float64).astype(np.float32)
    norms = np.linalg.norm(z, axis=1)
    if np.any(~np.isfinite(norms)) or np.any(norms <= 1e-8):
        return None, n_nonconstant, "zero_or_nonfinite_tr_pattern_norm"
    z = z / norms[:, None]
    sim = np.clip(z @ z.T, -1.0, 1.0)
    rdm = (1.0 - sim[iu]).astype(np.float32)
    if not np.all(np.isfinite(rdm)):
        return None, n_nonconstant, "nonfinite_rdm"
    return rdm, n_nonconstant, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--preflight-dir", type=Path, default=PREFLIGHT_DIR)
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_regional_fmri_reliability_v1/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    preflight_dir = args.preflight_dir.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    regions, target_shape, target_affine, preflight_hash = load_and_validate_preflight(root, preflight_dir)
    region_by_key = {r["key"]: r for r in regions}
    region_keys = [r["key"] for r in regions]

    hrf = canonical_hrf(TR)
    n_tp_by_story: dict[int, int] = {}
    nuisance_by_story: dict[int, dict] = {}

    # Freeze and validate all stimulus-side materials before reading regional BOLD values.
    for story in STORIES:
        rep_rel = f"derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-{story}_bold.nii.gz"
        rep_path = root / rep_rel
        if rep_path.is_symlink():
            rep_path.unlink()
        if not rep_path.exists() or rep_path.stat().st_size == 0:
            download(f"{OPENNEURO_BASE}/{rep_rel}", rep_path, timeout=1200)
        rep_img = nib.load(str(rep_path))
        if tuple(rep_img.shape[:3]) != target_shape or not affine_equal(rep_img.affine, target_affine):
            raise RuntimeError(f"story {story}: representative MNI grid mismatch")
        n_tp = int(rep_img.shape[3])
        n_tp_by_story[story] = n_tp
        nuisance_by_story[story] = preflight_story(root, story, n_tp, hrf)

    per_region_primary: dict[str, dict[str, list[float]]] = {
        key: {sub: [] for sub in SUBJECTS} for key in region_keys
    }
    per_region_raw: dict[str, dict[str, list[float]]] = {
        key: {sub: [] for sub in SUBJECTS} for key in region_keys
    }
    structurally_usable_runs = {key: 0 for key in region_keys}
    complete_loo_stories = {key: 0 for key in region_keys}
    story_rows: list[dict] = []

    write_progress(0, len(STORIES), "starting frozen regional fMRI reliability")

    for story_index, story in enumerate(STORIES, start=1):
        info = nuisance_by_story[story]
        valid_idx = np.asarray(info["valid_idx"], dtype=int)
        iu = np.triu_indices(len(valid_idx), k=1)
        rdms_by_region: dict[str, list[np.ndarray | None]] = {key: [] for key in region_keys}
        counts_by_region: dict[str, list[int]] = {key: [] for key in region_keys}
        reasons_by_region: dict[str, list[str]] = {key: [] for key in region_keys}

        for sub in SUBJECTS:
            rel = f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"
            path = root / rel
            if path.is_symlink():
                path.unlink()
            if not path.exists() or path.stat().st_size == 0:
                download(f"{OPENNEURO_BASE}/{rel}", path, timeout=1200)
            img = nib.load(str(path))
            if tuple(img.shape[:3]) != target_shape or not affine_equal(img.affine, target_affine):
                raise RuntimeError(f"{sub} story {story}: MNI grid mismatch")
            if int(img.shape[3]) != n_tp_by_story[story]:
                raise RuntimeError(
                    f"{sub} story {story}: timepoint mismatch {img.shape[3]} vs {n_tp_by_story[story]}"
                )
            data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
            if data.ndim != 4:
                raise RuntimeError(f"{sub} story {story}: expected 4D BOLD data")

            for spec in regions:
                key = spec["key"]
                rdm, n_nonconstant, reason = region_rdm_from_loaded_bold(
                    data,
                    spec["mask"],
                    valid_idx,
                    iu,
                )
                rdms_by_region[key].append(rdm)
                counts_by_region[key].append(n_nonconstant)
                reasons_by_region[key].append(reason)
                if rdm is not None:
                    structurally_usable_runs[key] += 1
            del data

        nuis = [
            pair_abs(info["times"]),
            pair_abs(info["word_drive"]),
            pair_abs(info["acoustic_drive"]),
        ]

        for spec in regions:
            key = spec["key"]
            rdms = rdms_by_region[key]
            story_complete = all(x is not None for x in rdms)
            primary_for_subject: dict[str, float] = {}
            raw_for_subject: dict[str, float] = {}
            if story_complete:
                stack = np.stack([np.asarray(x, dtype=np.float32) for x in rdms], axis=0).astype(np.float64)
                total = np.sum(stack, axis=0)
                complete_loo_stories[key] += 1
                for i, sub in enumerate(SUBJECTS):
                    target = stack[i]
                    loo = (total - target) / (len(SUBJECTS) - 1)
                    raw_r = pearson(target, loo)
                    target_res = residualize(target, nuis)
                    loo_res = residualize(loo, nuis)
                    primary_r = pearson(target_res, loo_res)
                    if not np.isfinite(primary_r) or not np.isfinite(raw_r):
                        raise RuntimeError(f"nonfinite reliability for {key}, {sub}, story {story}")
                    per_region_primary[key][sub].append(primary_r)
                    per_region_raw[key][sub].append(raw_r)
                    primary_for_subject[sub] = primary_r
                    raw_for_subject[sub] = raw_r

            for i, sub in enumerate(SUBJECTS):
                run_usable = rdms[i] is not None
                reason = reasons_by_region[key][i]
                if run_usable and not story_complete:
                    reason = "story_loo_incomplete_due_to_other_run"
                story_rows.append(
                    {
                        "region_key": key,
                        "family": spec["family"],
                        "region_name": spec["region_name"],
                        "hemisphere": spec["hemisphere"],
                        "parcel_id": spec["parcel_id"],
                        "atlas_label": spec["atlas_label"],
                        "subject": sub,
                        "story": story,
                        "n_timepoints": int(len(valid_idx)),
                        "n_pairs": int(len(iu[0])),
                        "atlas_voxels": spec["atlas_voxels"],
                        "n_nonconstant_voxels": counts_by_region[key][i],
                        "run_structurally_usable": run_usable,
                        "story_complete_for_loo": story_complete,
                        "structural_or_rdm_failure": reason,
                        "primary_residual_reliability": primary_for_subject.get(sub),
                        "raw_reliability": raw_for_subject.get(sub),
                    }
                )

        write_progress(
            story_index,
            len(STORIES),
            f"completed story {story_index} of {len(STORIES)}",
        )

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    resample_idx = rng.integers(0, len(SUBJECTS), size=(N_BOOT, len(SUBJECTS)))

    participant_rows: list[dict] = []
    region_rows: list[dict] = []
    n_required_runs = len(SUBJECTS) * len(STORIES)

    for spec in regions:
        key = spec["key"]
        structural_complete = structurally_usable_runs[key] == n_required_runs
        full_story_set = complete_loo_stories[key] == len(STORIES)
        participant_primary: list[float] = []
        participant_raw: list[float] = []

        for sub in SUBJECTS:
            vals = per_region_primary[key][sub]
            raws = per_region_raw[key][sub]
            complete_subject = structural_complete and full_story_set and len(vals) == len(STORIES) and len(raws) == len(STORIES)
            primary = fisher_mean(vals) if complete_subject else None
            raw = fisher_mean(raws) if complete_subject else None
            if complete_subject:
                participant_primary.append(float(primary))
                participant_raw.append(float(raw))
            participant_rows.append(
                {
                    "region_key": key,
                    "family": spec["family"],
                    "region_name": spec["region_name"],
                    "hemisphere": spec["hemisphere"],
                    "parcel_id": spec["parcel_id"],
                    "subject": sub,
                    "n_required_stories": len(STORIES),
                    "n_story_reliabilities_available": len(vals),
                    "complete_required_story_set": complete_subject,
                    "primary_residual_reliability": primary,
                    "raw_reliability": raw,
                }
            )

        row = {
            "region_key": key,
            "family": spec["family"],
            "region_name": spec["region_name"],
            "hemisphere": spec["hemisphere"],
            "parcel_id": spec["parcel_id"],
            "atlas_label": spec["atlas_label"],
            "atlas_voxels": spec["atlas_voxels"],
            "required_runs": n_required_runs,
            "structurally_usable_runs": structurally_usable_runs[key],
            "structurally_available_all_runs": structural_complete,
            "complete_loo_stories": complete_loo_stories[key],
            "complete_required_story_set": full_story_set,
            "primary_mean": None,
            "primary_median": None,
            "primary_n_positive": None,
            "primary_fraction_positive": None,
            "primary_bootstrap_ci_low": None,
            "primary_bootstrap_ci_high": None,
            "primary_exact_two_sided_signflip_p": None,
            "raw_mean_sensitivity": None,
            "raw_median_sensitivity": None,
            "reliability_gate_pass": False,
            "interpretation_status": "structurally_unavailable" if not structural_complete or not full_story_set else "reliability_limited",
        }

        if structural_complete and full_story_set:
            if len(participant_primary) != len(SUBJECTS):
                raise RuntimeError(f"participant aggregation incomplete for {key}")
            primary_arr = np.asarray(participant_primary, dtype=np.float64)
            raw_arr = np.asarray(participant_raw, dtype=np.float64)
            if not np.all(np.isfinite(primary_arr)) or not np.all(np.isfinite(raw_arr)):
                raise RuntimeError(f"nonfinite participant aggregate for {key}")
            ci_lo, ci_hi = bootstrap_ci(primary_arr, resample_idx)
            p_two = exact_two_sided_signflip_p(primary_arr)
            gate = bool(float(np.mean(primary_arr)) > 0.0 and ci_lo > 0.0)
            row.update(
                {
                    "primary_mean": float(np.mean(primary_arr)),
                    "primary_median": float(np.median(primary_arr)),
                    "primary_n_positive": int(np.sum(primary_arr > 0)),
                    "primary_fraction_positive": float(np.mean(primary_arr > 0)),
                    "primary_bootstrap_ci_low": ci_lo,
                    "primary_bootstrap_ci_high": ci_hi,
                    "primary_exact_two_sided_signflip_p": p_two,
                    "raw_mean_sensitivity": float(np.mean(raw_arr)),
                    "raw_median_sensitivity": float(np.median(raw_arr)),
                    "reliability_gate_pass": gate,
                    "interpretation_status": "reliable" if gate else "reliability_limited",
                }
            )
        region_rows.append(row)

    write_csv(out / "story_results.csv", story_rows)
    write_csv(out / "participant_results.csv", participant_rows)
    write_csv(out / "region_summary.csv", region_rows)

    language_rows = [r for r in region_rows if r["family"] == "language"]
    dk_rows = [r for r in region_rows if r["family"] == "dk68"]
    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "post-confirmatory model-blind regional fMRI neural reliability",
        "protocol": PROTOCOL,
        "pre_outcome_amendments": AMENDMENTS,
        "preflight_summary_sha256": preflight_hash,
        "model_blind": True,
        "loads_model_embeddings": False,
        "computes_model_outcomes": False,
        "n_subjects": len(SUBJECTS),
        "n_stories": len(STORIES),
        "n_regions": len(regions),
        "n_language_regions": len(language_rows),
        "n_dk68_regions": len(dk_rows),
        "tr_seconds": TR,
        "minimum_nonconstant_voxels_per_required_run": MIN_NONCONSTANT_VOXELS,
        "neural_rdm": "correlation distance across region-restricted z-scored multivoxel TR patterns",
        "reference": "within-story leave-one-participant-out mean neural RDM across the other 11 participants",
        "nuisance_controls": [
            "absolute temporal separation in seconds",
            "absolute difference in canonical-HRF-convolved word-onset density",
            "absolute difference in canonical-HRF-convolved acoustic RMS envelope",
        ],
        "participant_aggregation": "unweighted Fisher-z mean across the fixed 60 stories, then tanh",
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "signflip": "exact two-sided across all 2^12 participant sign configurations",
        "reliability_gate": "mean residual reliability > 0 and participant-bootstrap 95% CI lower bound > 0",
        "language_regions_structurally_available": int(sum(bool(r["structurally_available_all_runs"]) for r in language_rows)),
        "language_regions_passing_reliability_gate": int(sum(bool(r["reliability_gate_pass"]) for r in language_rows)),
        "dk68_regions_structurally_available": int(sum(bool(r["structurally_available_all_runs"]) for r in dk_rows)),
        "dk68_regions_passing_reliability_gate": int(sum(bool(r["reliability_gate_pass"]) for r in dk_rows)),
        "regions": region_rows,
        "guardrails": {
            "all_six_language_regions_retained": len(language_rows) == 6,
            "all_68_dk_regions_retained": len(dk_rows) == 68,
            "no_region_selection": True,
            "no_model_embeddings_loaded": True,
            "no_roi_threshold_search": True,
            "no_lag_or_hrf_search": True,
            "no_participant_or_story_selection": True,
            "no_result_driven_rescue": True,
            "reliability_is_interpretation_gate_not_selection_rule": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "completed",
                "model_blind": True,
                "language_regions_structurally_available": summary["language_regions_structurally_available"],
                "language_regions_passing_reliability_gate": summary["language_regions_passing_reliability_gate"],
                "dk68_regions_structurally_available": summary["dk68_regions_structurally_available"],
                "dk68_regions_passing_reliability_gate": summary["dk68_regions_passing_reliability_gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
