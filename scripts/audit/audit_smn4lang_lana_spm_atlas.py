#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, urllib.request, zipfile
from pathlib import Path

import nibabel as nib
import numpy as np

SPM_ATLAS_URL = "https://ndownloader.figshare.com/files/36524940"
EXPECTED_MD5 = "5e981df0866f2522e75a7899f69a00a5"
MNI_REL = "derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-1_bold.nii.gz"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    with urllib.request.urlopen(url, timeout=120) as r, dest.open("wb") as f:
        f.write(r.read())


def geom(img):
    return {
        "shape": list(img.shape),
        "zooms": [float(x) for x in img.header.get_zooms()[:3]],
        "affine": [[float(v) for v in row] for row in img.affine],
        "dtype": str(img.get_data_dtype()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_lana_spm_atlas/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve(); out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)

    zip_path = root / "external/lana/SPM_Atlas.zip"
    download(SPM_ATLAS_URL, zip_path)
    checksum_ok = md5(zip_path) == EXPECTED_MD5
    if not checksum_ok:
        raise RuntimeError("LanA SPM Atlas.zip MD5 mismatch")

    extract_dir = root / "external/lana/spm_atlas"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        members = zf.namelist()
        zf.extractall(extract_dir)

    mni_img = nib.load(str(root / MNI_REL))
    atlas_rows = []
    for p in sorted(extract_dir.rglob("*")):
        if not p.is_file() or not (p.name.endswith(".nii") or p.name.endswith(".nii.gz")):
            continue
        img = nib.load(str(p))
        data = np.asanyarray(img.dataobj)
        finite = data[np.isfinite(data)]
        atlas_rows.append({
            "relative_path": str(p.relative_to(extract_dir)),
            "sha256": sha256(p),
            **geom(img),
            "min": float(finite.min()) if finite.size else None,
            "max": float(finite.max()) if finite.size else None,
            "n_nonzero": int(np.count_nonzero(finite)) if finite.size else 0,
            "n_unique_sampled": int(len(np.unique(finite))) if finite.size <= 5_000_000 else None,
            "exact_grid_match_to_smn4lang": bool(img.shape[:3] == mni_img.shape[:3] and np.allclose(img.affine, mni_img.affine, atol=1e-5)),
        })

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "lana_spm_zip": {"url": SPM_ATLAS_URL, "expected_md5": EXPECTED_MD5, "computed_md5": md5(zip_path), "checksum_ok": checksum_ok, "members": members},
        "smn4lang_mni_geometry": geom(mni_img),
        "atlas_nifti_files": atlas_rows,
        "decision_rule": "Freeze the independently published group probabilistic LanA atlas file identified by the release contents. If its grid differs from SMN4Lang, resample the atlas once into the SMN4Lang 2-mm MNI grid using continuous interpolation before thresholding. Do not use participant-specific LanA maps or neural outcomes to choose the mask.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status":"ok","n_members":len(members),"n_nifti":len(atlas_rows),"exact_matches":sum(x["exact_grid_match_to_smn4lang"] for x in atlas_rows)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
