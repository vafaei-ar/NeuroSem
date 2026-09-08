#!/usr/bin/env python3
"""Presentation/provenance-only finalization wrapper for NeuroSem NMI v1.18."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STEPS = [
    ROOT / "scripts/paper/build_publication_figures_tables_v2.py",
    ROOT / "scripts/audit/build_nmi_v118_shipping_bundle_v1.py",
    ROOT / "scripts/audit/audit_nmi_v118_final_shipping_v1.py",
]


def main() -> int:
    for step in STEPS:
        if not step.is_file():
            raise FileNotFoundError(step)
        print(f"=== {step.relative_to(ROOT)} ===", flush=True)
        proc = subprocess.run([sys.executable, str(step)], cwd=ROOT, check=False)
        if proc.returncode != 0:
            print(f"FAILED: {step.relative_to(ROOT)} exit={proc.returncode}", file=sys.stderr)
            return proc.returncode
    print("NMI v1.18 finalization completed: publication rebuild, fresh bundle and final shipping audit all passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
