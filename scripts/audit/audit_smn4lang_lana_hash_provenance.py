#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

LANA_ZIP_MD5 = "5e981df0866f2522e75a7899f69a00a5"
LANA_REL = "SPM/LanA_n806.nii"


def digest_file(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_stream(src, algo: str) -> str:
    h = hashlib.new(algo)
    for chunk in iter(lambda: src.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_lana_hash_provenance/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    archive = root / "external/lana/SPM_Atlas.zip"
    extracted = root / "external/lana/spm_atlas" / LANA_REL
    if not archive.exists():
        raise RuntimeError("LanA archive missing")

    archive_md5 = digest_file(archive, "md5")
    if archive_md5 != LANA_ZIP_MD5:
        raise RuntimeError(f"LanA archive MD5 mismatch: {archive_md5}")

    with zipfile.ZipFile(archive) as zf:
        info = zf.getinfo(LANA_REL)
        with zf.open(info) as src:
            member_sha256 = digest_stream(src, "sha256")
        with zf.open(info) as src:
            member_md5 = digest_stream(src, "md5")

    extracted_sha256 = digest_file(extracted, "sha256") if extracted.exists() else None
    extracted_md5 = digest_file(extracted, "md5") if extracted.exists() else None

    summary = {
        "schema_version": 1,
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "archive_path": str(archive.relative_to(root)),
        "archive_md5_expected": LANA_ZIP_MD5,
        "archive_md5_observed": archive_md5,
        "archive_size_bytes": archive.stat().st_size,
        "member_path": LANA_REL,
        "member_uncompressed_size": info.file_size,
        "member_crc32": f"{info.CRC:08x}",
        "member_sha256_direct_from_verified_zip": member_sha256,
        "member_md5_direct_from_verified_zip": member_md5,
        "extracted_path": str(extracted.relative_to(root)),
        "extracted_exists": extracted.exists(),
        "extracted_size_bytes": extracted.stat().st_size if extracted.exists() else None,
        "extracted_sha256": extracted_sha256,
        "extracted_md5": extracted_md5,
        "member_equals_extracted_sha256": extracted_sha256 == member_sha256 if extracted_sha256 else None,
        "authoritative_rule": "Treat the raw member bytes read directly from the MD5-verified Figshare SPM Atlas.zip as authoritative. Do not run neural analysis in this task.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
