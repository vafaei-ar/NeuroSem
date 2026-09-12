#!/usr/bin/env python3
"""Build the current NeuroSem NMI redesign review set in sequence.

This is a convenience driver. It does not alter scientific inputs; it invokes the
individual presentation builders and the Figure 1 provenance validator using the same
Python interpreter that launched this script.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

STEPS = [
    ("Figure 1 transfer-first redesign", "scripts/paper/build_nmi_figure1_transfer_redesign_v2.py"),
    ("Figure 1 provenance validation", "scripts/paper/validate_nmi_figure1_transfer_redesign_v2.py"),
    ("Figure 2 redesign", "scripts/paper/build_nmi_figure2_redesign_v1.py"),
    ("Figure 3 redesign", "scripts/paper/build_nmi_figure3_redesign_v1.py"),
    ("Figure 4 redesign", "scripts/paper/build_nmi_figure4_redesign_v1.py"),
    ("Figure 5 + Extended Data Figure 1 redesign", "scripts/paper/build_nmi_figure5_redesign_v1_1.py"),
]


def main() -> int:
    for index, (label, relpath) in enumerate(STEPS, start=1):
        path = ROOT / relpath
        if not path.is_file():
            raise FileNotFoundError(f"Missing build step: {relpath}")
        print(f"\n[{index}/{len(STEPS)}] {label}\n  {sys.executable} {relpath}", flush=True)
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)
    print("\nAll current NMI redesign review figures built successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
