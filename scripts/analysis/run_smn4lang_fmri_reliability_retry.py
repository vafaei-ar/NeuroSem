#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

LANA_ZIP_MD5 = "5e981df0866f2522e75a7899f69a00a5"
LANA_REL = "SPM/LanA_n806.nii"
# Authoritative 64-hex SHA256 observed from the verified ZIP member bytes.
LANA_SHA256 = "3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babcaa3"
LEGACY_MALFORMED_SHA256 = "3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babca3"


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def link_dir(src: Path, dst: Path) -> None:
    if dst.is_symlink() or dst.exists():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(src, dst, target_is_directory=True)


def main() -> int:
    source_root = Path("data/raw/smn4lang").resolve()
    source_zip = source_root / "external/lana/SPM_Atlas.zip"
    if not source_zip.exists() or digest(source_zip, "md5") != LANA_ZIP_MD5:
        raise RuntimeError("Verified LanA archive is missing or has wrong MD5")

    runtime_root = Path("outputs/smn4lang_fmri_reliability/runtime_data").resolve()
    runtime_root.mkdir(parents=True, exist_ok=True)
    for name in ["derivatives", "stimuli"] + [f"sub-{i:02d}" for i in range(1, 13)]:
        link_dir(source_root / name, runtime_root / name)

    runtime_zip = runtime_root / "external/lana/SPM_Atlas.zip"
    runtime_zip.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_zip, runtime_zip)
    if digest(runtime_zip, "md5") != LANA_ZIP_MD5:
        raise RuntimeError("Runtime LanA archive MD5 mismatch")

    atlas_path = runtime_root / "external/lana/spm_atlas" / LANA_REL
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    atlas_path.unlink(missing_ok=True)
    with zipfile.ZipFile(runtime_zip) as zf:
        with zf.open(LANA_REL) as src, atlas_path.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    observed = digest(atlas_path, "sha256")
    if observed != LANA_SHA256:
        raise RuntimeError(f"LanA runtime atlas SHA256 mismatch: {observed}")

    # The prospectively frozen analysis driver contains the same historical checksum
    # typo. Make a runtime-only copy and correct exactly that malformed 63-hex literal.
    # No analytical code, thresholds, nuisance controls, participants, or stories change.
    frozen_driver = Path("scripts/analysis/run_smn4lang_fmri_reliability.py").resolve()
    driver_text = frozen_driver.read_text(encoding="utf-8")
    count = driver_text.count(LEGACY_MALFORMED_SHA256)
    if count != 1:
        raise RuntimeError(f"Expected exactly one malformed LanA checksum literal in frozen driver, found {count}")
    runtime_driver = Path("outputs/smn4lang_fmri_reliability/runtime_driver.py").resolve()
    runtime_driver.parent.mkdir(parents=True, exist_ok=True)
    runtime_driver.write_text(driver_text.replace(LEGACY_MALFORMED_SHA256, LANA_SHA256), encoding="utf-8")

    cmd = [
        sys.executable,
        str(runtime_driver),
        "--data-root",
        str(runtime_root),
        "--output-dir",
        "outputs/smn4lang_fmri_reliability/latest",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
