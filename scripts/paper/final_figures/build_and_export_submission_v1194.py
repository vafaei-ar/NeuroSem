#!/usr/bin/env python3
"""Build the frozen NeuroSem submission figures and immediately export exact PNG transports.

Presentation/transport only. This wrapper runs the canonical eight-figure build and then
base64-encodes the resulting PNG bytes without resizing or recompression. It performs no
model training, model evaluation, neural analysis, selection, or new inference.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def run(name: str) -> None:
    subprocess.run([sys.executable, str(HERE / name)], cwd=ROOT, check=True)

def main() -> int:
    run("build_all_figures.py")
    run("export_png_transports_v1193.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
