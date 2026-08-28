#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

LANA_ZIP_MD5 = "5e981df0866f2522e75a7899f69a00a5"
LANA_REL = "SPM/LanA_n806.nii"
LANA_SHA256 = "3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babca3"


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = Path("data/raw/smn4lang").resolve()
    atlas_zip = root / "external/lana/SPM_Atlas.zip"
    atlas_path = root / "external/lana/spm_atlas" / LANA_REL

    if not atlas_zip.exists() or digest(atlas_zip, "md5") != LANA_ZIP_MD5:
        raise RuntimeError("Verified LanA archive is missing or has wrong MD5")

    if (not atlas_path.exists()) or digest(atlas_path, "sha256") != LANA_SHA256:
        atlas_path.parent.mkdir(parents=True, exist_ok=True)
        atlas_path.unlink(missing_ok=True)
        with zipfile.ZipFile(atlas_zip) as zf:
            with zf.open(LANA_REL) as src, atlas_path.open("wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)

    if digest(atlas_path, "sha256") != LANA_SHA256:
        raise RuntimeError("LanA atlas SHA256 mismatch after verified re-extraction")

    cmd = [sys.executable, "scripts/analysis/run_smn4lang_fmri_reliability.py", "--data-root", "data/raw/smn4lang", "--output-dir", "outputs/smn4lang_fmri_reliability/latest"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
