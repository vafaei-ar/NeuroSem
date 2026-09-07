#!/usr/bin/env python3
"""Compatibility entry point for NeuroSem Figure 1.

The submission figure is artifact-driven. This wrapper delegates to the canonical
v1.18 Figure 1 builder and supplies the frozen development summary, the S0YJMCMF
ChineseEEG reliability replay, and the two frozen C-MTEB STS summaries. No
outcome-valued scientific constants are defined in this compatibility path.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/paper/nmi_visualizations_v4/build_figure1_chineseeeg.py"
DEV = ROOT / "paper/figure_data/chineseeeg_development_v1.json"
RELIABILITY = ROOT / "outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/summary.json"
STS1 = ROOT / "outputs/bert_neurosem_cmteb_sts_v1/20260823_122332/summary.json"
STS2 = ROOT / "outputs/bert_neurosem_cmteb_sts_v1_seed2/20260823_123910/summary.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-prefix", type=Path, required=True)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    cmd = [str(ROOT / ".venv/bin/python"), str(BUILDER), "--out-prefix", str(args.out_prefix)]
    if args.demo:
        cmd.append("--demo")
    else:
        required = [BUILDER, DEV, RELIABILITY, STS1, STS2]
        missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
        if missing:
            raise FileNotFoundError("Missing Figure 1 provenance inputs: " + ", ".join(missing))
        cmd.extend([
            "--development-json", str(DEV),
            "--reliability-summary", str(RELIABILITY),
            "--sts-seed1-summary", str(STS1),
            "--sts-seed2-summary", str(STS2),
        ])

    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
