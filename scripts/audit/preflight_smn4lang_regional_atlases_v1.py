#!/usr/bin/env python3
"""Outcome-blind atlas preflight for the frozen SMN4Lang regional/AHBA extension.

This stage reads public atlas resources, frozen AHBA metadata, and only the header
of one representative SMN4Lang NIfTI. It does not read BOLD values, model
embeddings, regional reliability/RSA outcomes, or AHBA association outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import urllib.request
from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.processing import resample_from_to

OPENNEURO_BASE = "https://s3.amazonaws.com/openneuro.org/ds004078"
EVLAB_PAGE_URL = "https://www.evlab.mit.edu/resources-all/download-parcels"
EVLAB_LANGUAGE_NII_URL = "https://evlab.squarespace.com/s/allParcels-language-SN220.nii"
REP_BOLD_REL = "derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-1_bold.nii.gz"
MIN_REGION_VOXELS = 100

LEFT_LABEL_TO_NAME = {
    1: "IFGorb",
    2: "IFG",
    3: "MFG",
    4: "AntTemp",
    5: "PostTemp",
    6: "AngG",
}
EXPECTED_LANGUAGE = ("IFG", "IFGorb", "MFG", "AntTemp", "PostTemp", "AngG")
NAME_TO_LEFT_LABEL = {v: k for k, v in LEFT_LABEL_TO_NAME.items()}
MAPPING_SOURCE_REPO = "ryskina/concepts-brain-llms"
MAPPING_SOURCE_COMMIT = "c3c331432887fbbae28c250f4852407cd678ccdf"
MAPPING_SOURCE_FILE = "figures.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_fresh(url: str, dest: Path, timeout: int = 600) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        dest.unlink()
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem/regional-atlas-preflight-v1"})
    with urllib.request.urlopen(req, timeout=timeout) as r, tmp.open("wb") as f:
        resolved = str(r.geturl())
        shutil.copyfileobj(r, f, length=1024 * 1024)
    tmp.replace(dest)
    if not dest.exists() or dest.stat().st_size <= 0:
        raise RuntimeError(f"empty download from {url}")
    return resolved


def fetch_if_missing(url: str, dest: Path, timeout: int = 1200) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        dest.unlink()
    if dest.exists() and dest.stat().st_size > 0:
        return url
    return fetch_fresh(url, dest, timeout=timeout)


def fetch_page(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem/regional-atlas-preflight-v1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        resolved = str(r.geturl())
    return resolved, hashlib.sha256(body).hexdigest()


def affine_equal(a: np.ndarray, b: np.ndarray) -> bool:
    return bool(np.allclose(np.asarray(a, float), np.asarray(b, float), rtol=0.0, atol=1e-5))


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def norm_hemi(x: str) -> str:
    s = str(x).strip().upper()
    if s in {"L", "LH", "LEFT"}:
        return "L"
    if s in {"R", "RH", "RIGHT"}:
        return "R"
    return s


def norm_label(x: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(x)).lower()


def integer_label_image(img: nib.spatialimages.SpatialImage, name: str) -> np.ndarray:
    data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
    finite = np.isfinite(data)
    if not finite.any():
        raise RuntimeError(f"{name}: no finite voxels")
    rounded = np.rint(data[finite]).astype(np.int64)
    if float(np.max(np.abs(data[finite] - rounded))) > 1e-5:
        raise RuntimeError(f"{name}: contains non-integer labels")
    out = np.zeros(data.shape, dtype=np.int64)
    out[finite] = rounded
    return out


def label_geometry(label_img: np.ndarray, affine: np.ndarray, label: int) -> dict:
    ijk = np.argwhere(label_img == int(label))
    if ijk.size == 0:
        return {
            "voxel_count": 0,
            "centroid_x_mm": None,
            "centroid_y_mm": None,
            "centroid_z_mm": None,
        }
    xyz = nib.affines.apply_affine(np.asarray(affine, float), ijk)
    c = np.mean(xyz, axis=0)
    return {
        "voxel_count": int(len(ijk)),
        "centroid_x_mm": float(c[0]),
        "centroid_y_mm": float(c[1]),
        "centroid_z_mm": float(c[2]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--expression-root", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_regional_atlas_preflight_v1/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    expression_root = args.expression_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []

    page_resolved, page_sha = fetch_page(EVLAB_PAGE_URL)
    evlab_dir = root / "external/evlab_language_parcels_sn220"
    parcel_path = evlab_dir / "allParcels-language-SN220.nii"
    parcel_resolved = fetch_fresh(EVLAB_LANGUAGE_NII_URL, parcel_path)
    parcel_img = nib.load(str(parcel_path))
    parcel_int = integer_label_image(parcel_img, "EvLab language parcel image")
    positive_labels = sorted(int(x) for x in np.unique(parcel_int) if int(x) > 0)

    mapping_rows: list[dict] = []
    geometry_by_label: dict[int, dict] = {}
    for label in positive_labels:
        g = label_geometry(parcel_int, parcel_img.affine, label)
        geometry_by_label[label] = g
        if 1 <= label <= 6:
            name = LEFT_LABEL_TO_NAME[label]
            expected_hemi = "L"
        elif 7 <= label <= 12:
            name = LEFT_LABEL_TO_NAME[label - 6]
            expected_hemi = "R"
        else:
            name = ""
            expected_hemi = ""
        x = g["centroid_x_mm"]
        centroid_hemi = "L" if x is not None and x < 0 else ("R" if x is not None and x > 0 else "MIDLINE")
        mapping_rows.append({
            "label": label,
            "frozen_region_name": name,
            "expected_hemisphere": expected_hemi,
            "centroid_hemisphere": centroid_hemi,
            **g,
        })

    missing_left = [label for label in range(1, 7) if label not in geometry_by_label]
    if missing_left:
        blockers.append(f"EvLab parcel image is missing frozen left-language labels: {missing_left}")
    left_centroids_ok = all(
        label in geometry_by_label
        and geometry_by_label[label]["centroid_x_mm"] is not None
        and geometry_by_label[label]["centroid_x_mm"] < 0
        for label in range(1, 7)
    )
    if not left_centroids_ok:
        blockers.append("one or more frozen labels 1-6 do not have a left-hemisphere centroid")

    right_labels_present = all(label in geometry_by_label for label in range(7, 13))
    right_centroids_ok = None
    if right_labels_present:
        right_centroids_ok = all(geometry_by_label[label]["centroid_x_mm"] > 0 for label in range(7, 13))
        if not right_centroids_ok:
            blockers.append("labels 7-12 are present but one or more do not have a right-hemisphere centroid")

    language_rows: list[dict] = []
    for name in EXPECTED_LANGUAGE:
        label = NAME_TO_LEFT_LABEL[name]
        g = geometry_by_label.get(label, {"voxel_count": 0, "centroid_x_mm": None, "centroid_y_mm": None, "centroid_z_mm": None})
        n = int(g["voxel_count"])
        language_rows.append({
            "region": name,
            "label": label,
            "mask_voxels": n,
            "centroid_x_mm": g["centroid_x_mm"],
            "centroid_y_mm": g["centroid_y_mm"],
            "centroid_z_mm": g["centroid_z_mm"],
            "left_centroid_pass": bool(g["centroid_x_mm"] is not None and g["centroid_x_mm"] < 0),
            "mask_voxels_ge_100": n >= MIN_REGION_VOXELS,
        })
    language_possible = all(bool(r["mask_voxels_ge_100"]) for r in language_rows)
    if not language_possible:
        blockers.append("one or more frozen language parcels contain fewer than 100 atlas voxels")

    rep_path = root / REP_BOLD_REL
    fetch_if_missing(f"{OPENNEURO_BASE}/{REP_BOLD_REL}", rep_path, timeout=1200)
    rep_img = nib.load(str(rep_path))
    rep_shape = tuple(int(x) for x in rep_img.shape[:3])
    rep_affine = np.asarray(rep_img.affine, dtype=float)

    lang_grid_match = tuple(parcel_img.shape[:3]) == rep_shape and affine_equal(parcel_img.affine, rep_affine)
    if not lang_grid_match:
        blockers.append("EvLab language parcel grid does not exactly match SMN4Lang")

    import abagen

    atlas = abagen.fetch_desikan_killiany(surface=False)
    if not isinstance(atlas, dict) or "image" not in atlas or "info" not in atlas:
        raise RuntimeError("unexpected abagen Desikan-Killiany return object")
    dk_path = Path(atlas["image"]).resolve()
    dk_info_path = Path(atlas["info"]).resolve()
    dk_img = nib.load(str(dk_path))
    dk_source_int = integer_label_image(dk_img, "Desikan-Killiany source atlas")
    dk_source_grid_match = tuple(dk_img.shape[:3]) == rep_shape and affine_equal(dk_img.affine, rep_affine)

    dk_resampled_img = resample_from_to(
        dk_img,
        (rep_shape, rep_affine),
        order=0,
        mode="constant",
        cval=0.0,
    )
    dk_resampled_path = out / "dk68_resampled_to_smn4lang.nii.gz"
    nib.save(dk_resampled_img, str(dk_resampled_path))
    dk_int = integer_label_image(dk_resampled_img, "Desikan-Killiany resampled atlas")
    dk_target_grid_match = tuple(dk_resampled_img.shape[:3]) == rep_shape and affine_equal(dk_resampled_img.affine, rep_affine)
    if not dk_target_grid_match:
        blockers.append("resampled DK grid does not exactly match SMN4Lang")

    dk_info_all = read_csv_rows(dk_info_path)
    cortical = [r for r in dk_info_all if str(r.get("structure", "")).strip().lower() == "cortex"]
    if len(cortical) != 68:
        raise RuntimeError(f"expected 68 DK cortical metadata rows, got {len(cortical)}")
    dk_by_id = {int(r["id"]): r for r in cortical}
    if len(dk_by_id) != 68:
        raise RuntimeError("duplicate DK cortical IDs")
    n_left = sum(norm_hemi(r.get("hemisphere", "")) == "L" for r in cortical)
    n_right = sum(norm_hemi(r.get("hemisphere", "")) == "R" for r in cortical)
    if (n_left, n_right) != (34, 34):
        raise RuntimeError(f"expected 34 DK parcels per hemisphere, got L={n_left}, R={n_right}")

    expr_ids_path = expression_root / "primary_leftright/region_ids.json"
    expr_info_path = expression_root / "primary_leftright/atlas_info.csv"
    if not expr_ids_path.exists() or not expr_info_path.exists():
        raise FileNotFoundError("frozen AHBA expression metadata is missing")
    expr_ids = [int(x) for x in json.loads(expr_ids_path.read_text(encoding="utf-8"))]
    expr_rows = read_csv_rows(expr_info_path)
    expr_by_id = {int(r["id"]): r for r in expr_rows}

    dk_id_match = len(expr_ids) == 68 and set(expr_ids) == set(dk_by_id) and set(expr_by_id) == set(dk_by_id)
    if not dk_id_match:
        blockers.append("DK IDs do not exactly match frozen AHBA expression IDs")

    metadata_mismatches: list[dict] = []
    for pid in sorted(set(expr_by_id).intersection(dk_by_id)):
        a = dk_by_id[pid]
        b = expr_by_id[pid]
        if norm_hemi(a.get("hemisphere", "")) != norm_hemi(b.get("hemisphere", "")) or norm_label(a.get("label", "")) != norm_label(b.get("label", "")):
            metadata_mismatches.append({
                "id": pid,
                "abagen_label": a.get("label", ""),
                "expression_label": b.get("label", ""),
                "abagen_hemi": a.get("hemisphere", ""),
                "expression_hemi": b.get("hemisphere", ""),
            })
    if metadata_mismatches:
        blockers.append(f"DK metadata mismatch against frozen AHBA expression bundle ({len(metadata_mismatches)} parcels)")

    resampled_present = {int(x) for x in np.unique(dk_int) if int(x) > 0}
    missing_cortical_after_resampling = sorted(set(expr_ids) - resampled_present)
    if missing_cortical_after_resampling:
        blockers.append(f"resampled DK image is missing cortical IDs: {missing_cortical_after_resampling}")

    dk_rows: list[dict] = []
    for pid in expr_ids:
        r = dk_by_id.get(pid, expr_by_id.get(pid, {}))
        hemi = norm_hemi(r.get("hemisphere", ""))
        src = label_geometry(dk_source_int, dk_img.affine, pid)
        dst = label_geometry(dk_int, dk_resampled_img.affine, pid)
        n = int(dst["voxel_count"])
        dk_rows.append({
            "parcel_id": pid,
            "parcel_name": r.get("label", ""),
            "hemisphere": hemi,
            "source_voxels": src["voxel_count"],
            "resampled_voxels": n,
            "source_centroid_x_mm": src["centroid_x_mm"],
            "source_centroid_y_mm": src["centroid_y_mm"],
            "source_centroid_z_mm": src["centroid_z_mm"],
            "resampled_centroid_x_mm": dst["centroid_x_mm"],
            "resampled_centroid_y_mm": dst["centroid_y_mm"],
            "resampled_centroid_z_mm": dst["centroid_z_mm"],
            "mask_voxels_ge_100": n >= MIN_REGION_VOXELS,
        })

    lh34_possible = all(bool(r["mask_voxels_ge_100"]) for r in dk_rows if r["hemisphere"] == "L")
    dk68_possible = all(bool(r["mask_voxels_ge_100"]) for r in dk_rows)
    if not lh34_possible:
        blockers.append("one or more left-hemisphere DK parcels contain fewer than 100 voxels after frozen resampling")

    ready = len(blockers) == 0
    write_csv(out / "language_parcels.csv", language_rows)
    write_csv(out / "dk68_parcels.csv", dk_rows)
    write_csv(out / "evlab_roi_index_audit.csv", mapping_rows)

    payload = {
        "schema_version": 3,
        "analysis": "model-blind SMN4Lang regional atlas preflight v1",
        "protocol": "docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md",
        "pre_outcome_amendments": [
            "docs/27_NMI_REGIONAL_FMRI_ATLAS_PREFLIGHT_AMENDMENT_V1.md",
            "docs/28_NMI_REGIONAL_FMRI_DK_RESAMPLING_AMENDMENT_V1.md",
        ],
        "loads_bold_values": False,
        "loads_model_embeddings": False,
        "computes_regional_reliability": False,
        "computes_regional_rsa": False,
        "computes_ahba_associations": False,
        "representative_bold_header": {
            "relative_path": REP_BOLD_REL,
            "shape_xyz": list(rep_shape),
            "affine": rep_affine.tolist(),
        },
        "evlab_language_parcels": {
            "source_page_requested": EVLAB_PAGE_URL,
            "source_page_resolved": page_resolved,
            "source_page_sha256": page_sha,
            "nifti_requested": EVLAB_LANGUAGE_NII_URL,
            "nifti_resolved": parcel_resolved,
            "nifti_local_path": str(parcel_path),
            "nifti_sha256": sha256(parcel_path),
            "shape_xyz": list(parcel_img.shape[:3]),
            "affine": np.asarray(parcel_img.affine, float).tolist(),
            "positive_integer_labels": positive_labels,
            "frozen_left_label_mapping": {str(k): v for k, v in LEFT_LABEL_TO_NAME.items()},
            "mapping_source": {
                "repository": MAPPING_SOURCE_REPO,
                "commit": MAPPING_SOURCE_COMMIT,
                "file": MAPPING_SOURCE_FILE,
            },
            "left_labels_1_to_6_centroid_check": left_centroids_ok,
            "right_labels_7_to_12_all_present": right_labels_present,
            "right_labels_7_to_12_centroid_check": right_centroids_ok,
            "grid_exact_match_to_smn4lang": lang_grid_match,
            "region_rows": language_rows,
            "all_label_geometry": mapping_rows,
        },
        "desikan_killiany": {
            "abagen_version": getattr(abagen, "__version__", None),
            "source_nifti_local_path": str(dk_path),
            "source_nifti_sha256": sha256(dk_path),
            "source_shape_xyz": list(dk_img.shape[:3]),
            "source_affine": np.asarray(dk_img.affine, float).tolist(),
            "source_grid_exact_match_to_smn4lang": dk_source_grid_match,
            "resampling_rule": {
                "implementation": "nibabel.processing.resample_from_to",
                "order": 0,
                "mode": "constant",
                "cval": 0.0,
                "target": "representative SMN4Lang MNI shape+affine",
            },
            "resampled_nifti_local_path": str(dk_resampled_path),
            "resampled_nifti_sha256": sha256(dk_resampled_path),
            "resampled_shape_xyz": list(dk_resampled_img.shape[:3]),
            "resampled_affine": np.asarray(dk_resampled_img.affine, float).tolist(),
            "resampled_grid_exact_match_to_smn4lang": dk_target_grid_match,
            "info_local_path": str(dk_info_path),
            "info_sha256": sha256(dk_info_path),
            "n_cortical": 68,
            "n_left": n_left,
            "n_right": n_right,
            "expression_id_match": dk_id_match,
            "expression_metadata_mismatch_count": len(metadata_mismatches),
            "missing_cortical_ids_after_resampling": missing_cortical_after_resampling,
            "region_rows": dk_rows,
        },
        "minimum_region_voxels": MIN_REGION_VOXELS,
        "language_primary_structurally_possible": language_possible,
        "dk34_left_primary_molecular_structurally_possible": lh34_possible,
        "dk68_bilateral_structurally_possible": dk68_possible,
        "ready_for_frozen_regional_reliability": ready,
        "blockers": blockers,
        "guardrails": [
            "No regional BOLD values, model representations or regional outcomes are read in this preflight.",
            "EvLab language parcels are not resampled because they already match the SMN4Lang grid.",
            "The DK label image is resampled only by the pre-outcome frozen nearest-neighbor rule in amendment 28.",
            "No atlas, interpolation order, threshold or mask is optimized using regional neural outcomes.",
            "A blocked atlas gate is a valid completed preflight and stops subsequent regional neural analysis.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if ready else "blocked",
        "language_grid_match": lang_grid_match,
        "dk_source_grid_match": dk_source_grid_match,
        "dk_resampled_grid_match": dk_target_grid_match,
        "language_left_centroids_ok": left_centroids_ok,
        "language_primary_structurally_possible": language_possible,
        "dk68_cortical_ids_retained": len(missing_cortical_after_resampling) == 0,
        "dk34_left_primary_molecular_structurally_possible": lh34_possible,
        "dk68_bilateral_structurally_possible": dk68_possible,
        "blockers": blockers,
    }, indent=2), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
