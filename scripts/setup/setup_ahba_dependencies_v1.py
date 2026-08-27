#!/usr/bin/env python3
"""Install and verify the pinned AHBA preprocessing dependency set.

Infrastructure-only. This does not download AHBA, open EEG samples, or compute
NeuroSem/model/molecular outcomes.

Compatibility note: abagen 0.1.3 imports ``pkg_resources``. The first setup run
successfully installed abagen and nibabel but failed import because the project
Python 3.13 environment did not provide ``pkg_resources``. We therefore pin a
setuptools release that still provides that module before verifying abagen.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path

PINNED = ["setuptools==80.9.0", "abagen==0.1.3"]


def version(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_dependency_setup_v1/latest"))
    args = ap.parse_args()

    names = ["setuptools", "abagen", "nibabel", "pandas", "numpy", "scipy", "mne"]
    before = {name: version(name) for name in names}
    cp = subprocess.run([sys.executable, "-m", "pip", "install", *PINNED], text=True, capture_output=True, check=False)
    after = {name: version(name) for name in names}

    pkg_resources_ok = False
    pkg_resources_error = None
    try:
        import pkg_resources  # noqa: F401
        pkg_resources_ok = True
    except Exception as exc:
        pkg_resources_error = f"{type(exc).__name__}: {exc}"

    import_ok = False
    import_error = None
    if cp.returncode == 0 and pkg_resources_ok:
        try:
            import abagen  # noqa: F401
            import_ok = True
        except Exception as exc:
            import_error = f"{type(exc).__name__}: {exc}"

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "analysis": "AHBA dependency setup only",
        "pinned_requirements": PINNED,
        "compatibility_reason": "abagen 0.1.3 requires pkg_resources at import; setuptools 80.9.0 is pinned to provide it in the Python 3.13 project environment",
        "before": before,
        "after": after,
        "pip_returncode": cp.returncode,
        "pip_stdout_tail": cp.stdout[-3000:],
        "pip_stderr_tail": cp.stderr[-3000:],
        "pkg_resources_import_ok": pkg_resources_ok,
        "pkg_resources_import_error": pkg_resources_error,
        "abagen_import_ok": import_ok,
        "abagen_import_error": import_error,
        "loads_eeg_samples": False,
        "downloads_ahba": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_expression_outcomes": False,
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok" if cp.returncode == 0 and pkg_resources_ok and import_ok else "failed",
        "after": after,
        "pkg_resources_import_ok": pkg_resources_ok,
        "abagen_import_ok": import_ok,
    }, indent=2))
    if (
        cp.returncode != 0
        or not pkg_resources_ok
        or not import_ok
        or after.get("abagen") != "0.1.3"
        or after.get("setuptools") != "80.9.0"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
