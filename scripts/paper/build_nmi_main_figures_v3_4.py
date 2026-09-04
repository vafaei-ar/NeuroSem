#!/usr/bin/env python3
"""Canonical main-figure entry point using the NMI v4 presentation-only system."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/paper/nmi_visualizations_v4/build_nmi_visualizations_v4.py"


def main() -> int:
    if not BUILDER.exists():
        raise FileNotFoundError(BUILDER)
    completed = subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"NMI v4 main-figure build failed with exit {completed.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
