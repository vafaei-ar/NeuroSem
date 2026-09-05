#!/usr/bin/env python3
"""Compatibility wrapper for the NMI v1.13 table export."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.paper.build_nmi_submission_tables_v1 as base


def supplementary_2():
    rows = base.read_csv(base.MODEL)
    out = []
    for r in rows:
        out.append({
            "Model": r["model_key"],
            "Direction": r["direction"],
            "Seed": r["seed"],
            "Source Δ": r["source_validation_delta"],
            "External mean Δ": r["external_mean_delta"],
            "n positive": r["external_n_positive"],
            "95% CI low": r["external_ci_low"],
            "95% CI high": r["external_ci_high"],
            "one-sided P": r["external_one_sided_p"],
        })
    return out


base.supplementary_2 = supplementary_2

if __name__ == "__main__":
    raise SystemExit(base.main())
