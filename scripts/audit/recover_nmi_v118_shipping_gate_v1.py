#!/usr/bin/env python3
"""Recover the NeuroSem NMI v1.18 shipping gate after F8K2V7M4.

The failed F8 wrapper completed the publication rebuild and fresh bundle, then failed
only because the final audit still expected the pre-rebuild spatial presentation hash.
This recovery does not rebuild scientific or publication outputs. It regenerates the
bundle with the corrected final overlay and reruns the document-linked shipping audit.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STEPS = [
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
    print("NMI v1.18 shipping-gate recovery completed: fresh bundle and final audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
