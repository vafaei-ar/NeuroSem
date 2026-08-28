#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import nibabel as nib

FIGSHARE_ARTICLE_API = "https://api.figshare.com/v2/articles/20425209"
OPENNEURO_BASE = "https://s3.amazonaws.com/openneuro.org/ds004078"
MNI_REL = "derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-1_bold.nii.gz"


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=300) as r, tmp.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_lana_inventory/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    article = get_json(FIGSHARE_ARTICLE_API)
    files = []
    for f in article.get("files", []):
        files.append({
            "id": f.get("id"),
            "name": f.get("name"),
            "size": f.get("size"),
            "download_url": f.get("download_url"),
            "supplied_md5": f.get("supplied_md5"),
            "computed_md5": f.get("computed_md5"),
        })

    mni_path = root / MNI_REL
    if mni_path.is_symlink() or (mni_path.exists() and mni_path.stat().st_size == 0):
        mni_path.unlink(missing_ok=True)
    download(f"{OPENNEURO_BASE}/{MNI_REL}", mni_path)
    img = nib.load(str(mni_path))

    nii_like = [f for f in files if str(f.get("name", "")).lower().endswith((".nii", ".nii.gz"))]
    spm_like = [f for f in files if "spm" in str(f.get("name", "")).lower() or "atlas" in str(f.get("name", "")).lower()]

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "lana_source": {
            "article_id": article.get("id"),
            "title": article.get("title"),
            "doi": article.get("doi"),
            "url_private_api": FIGSHARE_ARTICLE_API,
            "n_files": len(files),
            "files": files,
            "nii_like_files": nii_like,
            "spm_or_atlas_named_files": spm_like,
        },
        "representative_mni_run": {
            "relative_path": MNI_REL,
            "size_bytes": mni_path.stat().st_size,
            "sha256": sha256(mni_path),
            "shape": list(img.shape),
            "dtype": str(img.get_data_dtype()),
            "zooms": [float(x) for x in img.header.get_zooms()],
            "affine": [[float(v) for v in row] for row in img.affine],
            "qform_code": int(img.header["qform_code"]),
            "sform_code": int(img.header["sform_code"]),
        },
        "decision_rule": "Use only an independently released LanA group probabilistic atlas in MNI space; select the canonical group atlas by explicit filename/provenance after this inventory, then freeze checksum and resampling before any neural outcome.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "n_figshare_files": len(files), "mni_shape": summary["representative_mni_run"]["shape"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
