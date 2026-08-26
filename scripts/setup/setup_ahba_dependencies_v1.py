#!/usr/bin/env python3
"""Install and verify the pinned AHBA preprocessing dependency set.

This is infrastructure-only. It does not download AHBA, open EEG samples, or compute
NeuroSem/model/molecular outcomes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path

PINNED = ["abagen==0.1.3"]


def version(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_dependency_setup_v1/latest"))
    args = ap.parse_args()

    before = {name: version(name) for name in ["abagen", "nibabel", "pandas", "numpy", "scipy", "mne"]}
    cp = subprocess.run([sys.executable, "-m", "pip", "install", *PINNED], text=True, capture_output=True, check=False)
    after = {name: version(name) for name in ["abagen", "nibabel", "pandas", "numpy", "scipy", "mne"]}

    import_ok = False
    import_error = None
    if cp.returncode == 0:
        try:
            import abagen  # noqa: F401
            import_ok = True
        except Exception as exc:
            import_error = f"{type(exc).__name__}: {exc}"

    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "analysis": "AHBA dependency setup only",
        "pinned_requirements": PINNED,
        "before": before,
        "after": after,
        "pip_returncode": cp.returncode,
        "pip_stdout_tail": cp.stdout[-3000:],
        "pip_stderr_tail": cp.stderr[-3000:],
        "abagen_import_ok": import_ok,
        "abagen_import_error": import_error,
        "loads_eeg_samples": False,
        "downloads_ahba": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_expression_outcomes": False,
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok" if cp.returncode == 0 and import_ok else "failed", "after": after, "abagen_import_ok": import_ok}, indent=2))
    if cp.returncode != 0 or not import_ok or after.get("abagen") != "0.1.3":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
