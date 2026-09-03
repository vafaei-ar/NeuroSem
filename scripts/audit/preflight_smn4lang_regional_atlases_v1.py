#!/usr/bin/env python3
"""Model-blind atlas preflight for the frozen SMN4Lang regional/AHBA extension.

This stage materializes only public atlas resources, checks atlas grids against a
representative SMN4Lang NIfTI *header*, and checks Desikan-Killiany metadata
against the already-frozen AHBA expression bundle. It does not load BOLD values,
model embeddings, regional RSA outcomes, reliability outcomes, or AHBA
association outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

import nibabel as nib
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analysis.run_smn4lang_fmri_reliability import OPENNEURO_BASE, download

EVLAB_PAGE_URL = "https://www.evlab.mit.edu/resources-all/download-parcels"
EVLAB_LANGUAGE_NII_URL = "https://www.evlab.mit.edu/s/allParcels-language-SN220-hgwm.nii"
EVLAB_LANGUAGE_INDEX_URL = "https://evlab.squarespace.com/s/allParcels-language-SN220.txt"
EXPECTED_LANGUAGE = ("IFG", "IFGorb", "MFG", "AntTemp", "PostTemp", "AngG")
MIN_REGION_VOXELS = 100
REP_BOLD_REL = "derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-1_bold.nii.gz"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_fresh(url: str, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem/regional-atlas-preflight-v1"})
    with urllib.request.urlopen(req, timeout=600) as r, tmp.open("wb") as f:
        resolved = str(r.geturl())
        shutil.copyfileobj(r, f, length=1024 * 1024)
    tmp.replace(dest)
    if dest.stat().st_size <= 0:
        raise RuntimeError(f"empty download from {url}")
    return resolved


def fetch_page(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem/regional-atlas-preflight-v1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        resolved = str(r.geturl())
    return resolved, hashlib.sha256(body).hexdigest()


def affine_equal(a: np.ndarray, b: np.ndarray) -> bool:
    return bool(np.allclose(np.asarray(a, float), np.asarray(b, float), rtol=0.0, atol=1e-5))


def canonical_language_name(raw: str) -> str | None:
    s = re.sub(r"[^A-Za-z0-9]", "", str(raw)).upper()
    # Test more specific strings first.
    aliases = [
        ("IFGorb", ("LIFGORB", "IFGORB")),
        ("AntTemp", ("LANTTEMP", "ANTTEMP", "LANTERIORTEMP", "ANTERIORTEMP")),
        ("PostTemp", ("LPOSTTEMP", "POSTTEMP", "LPOSTERIORTEMP", "POSTERIORTEMP")),
        ("AngG", ("LANGG", "ANGG", "LANGULARGYRUS", "ANGULARGYRUS")),
        ("MFG", ("LMFG", "MFG", "LMIDDLEFRONTALGYRUS", "MIDDLEFRONTALGYRUS")),
        ("IFG", ("LIFG", "IFG", "LINFERIORFRONTALGYRUS", "INFERIORFRONTALGYRUS")),
    ]
    for canonical, candidates in aliases:
        if any(s == c or s.startswith(c) for c in candidates):
            return canonical
    return None


def parse_roi_indices(path: Path) -> tuple[dict[str, int], list[dict]]:
    mapping: dict[str, int] = {}
    parsed: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        label = None
        name = None
        m = re.match(r"^\s*(\d+)\s*[:;,\t ]+\s*(.+?)\s*$", raw)
        if m:
            label = int(m.group(1)); name = m.group(2)
        else:
            m = re.match(r"^\s*(.+?)\s*[:;,\t ]+\s*(\d+)\s*$", raw)
            if m:
                name = m.group(1); label = int(m.group(2))
        if label is None or name is None:
            continue
        canonical = canonical_language_name(name)
        parsed.append({"line": line_no, "label": label, "distributed_name": name, "canonical_name": canonical or ""})
        if canonical is not None:
            if canonical in mapping and mapping[canonical] != label:
                raise RuntimeError(f"multiple labels resolve to language region {canonical}")
            mapping[canonical] = label
    missing = [x for x in EXPECTED_LANGUAGE if x not in mapping]
    if missing:
        raise RuntimeError(f"could not resolve the six frozen left-language parcels from ROI index file; missing={missing}")
    if len(set(mapping.values())) != len(EXPECTED_LANGUAGE):
        raise RuntimeError("language ROI index mapping is not one-to-one")
    return mapping, parsed


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def norm_hemi(x: str) -> str:
    s = str(x).strip().upper()
    if s in {"L", "LH", "LEFT"}: return "L"
    if s in {"R", "RH", "RIGHT"}: return "R"
    return s


def norm_label(x: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(x)).lower()


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

    # Record the public source page separately from the downloaded resource bytes.
    page_resolved, page_sha = fetch_page(EVLAB_PAGE_URL)

    evlab_dir = root / "external/evlab_language_parcels_sn220"
    parcel_path = evlab_dir / "allParcels-language-SN220.nii"
    index_path = evlab_dir / "allParcels-language-SN220.txt"
    parcel_resolved = fetch_fresh(EVLAB_LANGUAGE_NII_URL, parcel_path)
    index_resolved = fetch_fresh(EVLAB_LANGUAGE_INDEX_URL, index_path)
    parcel_hash = sha256(parcel_path)
    index_hash = sha256(index_path)

    mapping, parsed_index = parse_roi_indices(index_path)
    parcel_img = nib.load(str(parcel_path))
    parcel_data = np.asarray(parcel_img.get_fdata(dtype=np.float32), dtype=np.float32)
    finite = np.isfinite(parcel_data)
    rounded = np.rint(parcel_data[finite]).astype(np.int64)
    if np.max(np.abs(parcel_data[finite] - rounded)) > 1e-5:
        raise RuntimeError("EvLab parcel image contains non-integer labels")
    present = {int(x) for x in np.unique(rounded) if int(x) > 0}
    if not set(mapping.values()).issubset(present):
        raise RuntimeError(f"ROI index labels missing from parcel image: {sorted(set(mapping.values()) - present)}")

    language_rows = []
    for name in EXPECTED_LANGUAGE:
        label = int(mapping[name])
        n = int(np.sum(np.rint(parcel_data).astype(np.int64) == label))
        language_rows.append({"region": name, "label": label, "mask_voxels": n, "mask_voxels_ge_100": n >= MIN_REGION_VOXELS})

    # Representative SMN4Lang header only. nib.load is lazy; get_fdata is never called.
    rep_path = root / REP_BOLD_REL
    if rep_path.is_symlink():
        rep_path.unlink()
    if not rep_path.exists() or rep_path.stat().st_size == 0:
        download(f"{OPENNEURO_BASE}/{REP_BOLD_REL}", rep_path, timeout=1200)
    rep_img = nib.load(str(rep_path))
    rep_shape = tuple(int(x) for x in rep_img.shape[:3])
    rep_affine = np.asarray(rep_img.affine, dtype=float)

    lang_grid_match = tuple(parcel_img.shape[:3]) == rep_shape and affine_equal(parcel_img.affine, rep_affine)

    # Standard volumetric DK atlas from the already-used abagen installation.
    import abagen
    atlas = abagen.fetch_desikan_killiany(surface=False)
    dk_path = Path(atlas["image"]).resolve()
    dk_info_path = Path(atlas["info"]).resolve()
    dk_img = nib.load(str(dk_path))
    dk_data = np.asarray(dk_img.get_fdata(dtype=np.float32), dtype=np.float32)
    dk_grid_match = tuple(dk_img.shape[:3]) == rep_shape and affine_equal(dk_img.affine, rep_affine)

    dk_info_all = read_csv_rows(dk_info_path)
    cortical = [r for r in dk_info_all if str(r.get("structure", "")).strip().lower() == "cortex"]
    if len(cortical) != 68:
        raise RuntimeError(f"expected 68 DK cortical rows, got {len(cortical)}")
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
    if len(expr_ids) != 68 or set(expr_ids) != set(dk_by_id):
        raise RuntimeError("volumetric DK IDs do not match frozen AHBA expression IDs")
    if set(expr_by_id) != set(dk_by_id):
        raise RuntimeError("volumetric DK metadata IDs do not match frozen AHBA expression metadata")

    metadata_mismatches = []
    for pid in expr_ids:
        a = dk_by_id[pid]; b = expr_by_id[pid]
        if norm_hemi(a.get("hemisphere", "")) != norm_hemi(b.get("hemisphere", "")) or norm_label(a.get("label", "")) != norm_label(b.get("label", "")):
            metadata_mismatches.append({"id": pid, "abagen_label": a.get("label", ""), "expression_label": b.get("label", ""), "abagen_hemi": a.get("hemisphere", ""), "expression_hemi": b.get("hemisphere", "")})
    if metadata_mismatches:
        raise RuntimeError(f"DK metadata mismatch against frozen expression bundle: {metadata_mismatches[:3]}")

    dk_rows = []
    dk_int = np.rint(dk_data).astype(np.int64)
    for pid in expr_ids:
        r = dk_by_id[pid]
        hemi = norm_hemi(r.get("hemisphere", ""))
        n = int(np.sum(dk_int == pid))
        dk_rows.append({
            "parcel_id": pid,
            "parcel_name": r.get("label", ""),
            "hemisphere": hemi,
            "mask_voxels": n,
            "mask_voxels_ge_100": n >= MIN_REGION_VOXELS,
        })

    language_possible = all(bool(r["mask_voxels_ge_100"]) for r in language_rows)
    lh34_possible = all(bool(r["mask_voxels_ge_100"]) for r in dk_rows if r["hemisphere"] == "L")
    dk68_possible = all(bool(r["mask_voxels_ge_100"]) for r in dk_rows)
    ready = bool(lang_grid_match and dk_grid_match and language_possible and lh34_possible)

    with (out / "language_parcels.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(language_rows[0])); w.writeheader(); w.writerows(language_rows)
    with (out / "dk68_parcels.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dk_rows[0])); w.writeheader(); w.writerows(dk_rows)
    with (out / "evlab_roi_index_audit.csv").open("w", encoding="utf-8", newline="") as f:
        fields = list(parsed_index[0]) if parsed_index else ["line", "label", "distributed_name", "canonical_name"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(parsed_index)

    payload = {
        "schema_version": 1,
        "analysis": "model-blind SMN4Lang regional atlas preflight v1",
        "protocol": "docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md",
        "loads_bold_values": False,
        "loads_model_embeddings": False,
        "computes_regional_reliability": False,
        "computes_regional_rsa": False,
        "computes_ahba_associations": False,
        "representative_bold_header": {"relative_path": REP_BOLD_REL, "shape_xyz": list(rep_shape), "affine": rep_affine.tolist()},
        "evlab_language_parcels": {
            "source_page_requested": EVLAB_PAGE_URL,
            "source_page_resolved": page_resolved,
            "source_page_sha256": page_sha,
            "nifti_requested": EVLAB_LANGUAGE_NII_URL,
            "nifti_resolved": parcel_resolved,
            "nifti_local_path": str(parcel_path),
            "nifti_sha256": parcel_hash,
            "index_requested": EVLAB_LANGUAGE_INDEX_URL,
            "index_resolved": index_resolved,
            "index_local_path": str(index_path),
            "index_sha256": index_hash,
            "shape_xyz": list(parcel_img.shape[:3]),
            "affine": np.asarray(parcel_img.affine, float).tolist(),
            "grid_exact_match_to_smn4lang": lang_grid_match,
            "expected_left_regions": list(EXPECTED_LANGUAGE),
            "resolved_mapping": mapping,
            "region_rows": language_rows,
        },
        "desikan_killiany": {
            "abagen_version": getattr(abagen, "__version__", None),
            "nifti_local_path": str(dk_path),
            "nifti_sha256": sha256(dk_path),
            "info_local_path": str(dk_info_path),
            "info_sha256": sha256(dk_info_path),
            "shape_xyz": list(dk_img.shape[:3]),
            "affine": np.asarray(dk_img.affine, float).tolist(),
            "grid_exact_match_to_smn4lang": dk_grid_match,
            "n_cortical": 68,
            "n_left": n_left,
            "n_right": n_right,
            "expression_metadata_match": True,
            "region_rows": dk_rows,
        },
        "minimum_region_voxels": MIN_REGION_VOXELS,
        "language_primary_structurally_possible": language_possible,
        "dk34_left_primary_molecular_structurally_possible": lh34_possible,
        "dk68_bilateral_structurally_possible": dk68_possible,
        "ready_for_frozen_regional_reliability": ready,
        "blockers": [
            x for x, bad in [
                ("EvLab language parcel grid does not exactly match SMN4Lang", not lang_grid_match),
                ("volumetric DK grid does not exactly match SMN4Lang", not dk_grid_match),
                ("one or more frozen language parcels contain fewer than 100 voxels", not language_possible),
                ("one or more left-hemisphere DK parcels contain fewer than 100 voxels", not lh34_possible),
            ] if bad
        ],
        "guardrails": [
            "This preflight reads only public atlas data, frozen AHBA metadata, and an SMN4Lang NIfTI header; it never loads BOLD values.",
            "No atlas resampling, ROI redefinition, intersection, dilation, erosion or threshold adjustment is performed.",
            "If the frozen source resources or grids fail validation, stop before neural outcomes.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if ready else "blocked",
        "language_grid_match": lang_grid_match,
        "dk_grid_match": dk_grid_match,
        "language_primary_structurally_possible": language_possible,
        "dk34_left_primary_molecular_structurally_possible": lh34_possible,
        "dk68_bilateral_structurally_possible": dk68_possible,
        "blockers": payload["blockers"],
    }, indent=2), flush=True)
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())