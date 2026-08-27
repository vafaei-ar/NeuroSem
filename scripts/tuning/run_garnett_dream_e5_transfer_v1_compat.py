#!/usr/bin/env python3
"""Compatibility launcher for the frozen Garnett E5 transfer test.

The completed Garnett reliability artifact stores the primary row_mean_all summary
under `primary_result` / `candidate_summaries`, while the original transfer script
looked for a legacy `summaries` key. This launcher performs only that schema
normalization in a temporary file and then executes the unchanged frozen transfer
implementation. No scientific choice, cohort, representation, nuisance, model,
lambda, or inferential target is changed.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    argv = sys.argv[1:]
    try:
        i = argv.index("--reliability-summary")
        src = Path(argv[i + 1])
    except (ValueError, IndexError):
        src = Path("outputs/garnett_dream_primary_reliability/latest/summary.json")
        argv += ["--reliability-summary", str(src)]
        i = len(argv) - 2

    payload = json.loads(src.read_text(encoding="utf-8"))
    if payload.get("primary_candidate") != "row_mean_all":
        raise SystemExit("unexpected Garnett reliability primary candidate")
    primary = payload.get("primary_result") or payload.get("candidate_summaries", {}).get("row_mean_all")
    if not isinstance(primary, dict):
        raise SystemExit("Garnett reliability primary result missing")
    ci = primary.get("participant_bootstrap_95ci_residual_mean", [])
    if len(ci) != 2 or float(ci[0]) <= 0 or float(primary.get("mean_residual_loo", 0.0)) <= 0:
        raise SystemExit("prospectively required Garnett EEG reliability gate is not positive")

    normalized = dict(payload)
    normalized["summaries"] = {"row_mean_all": primary}

    with tempfile.TemporaryDirectory(prefix="neurosem_garnett_rel_schema_") as td:
        tmp = Path(td) / "summary.json"
        tmp.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
        argv[i + 1] = str(tmp)
        target = Path(__file__).with_name("evaluate_garnett_dream_e5_transfer_v1.py")
        cp = subprocess.run([sys.executable, str(target), *argv], check=False)
        return int(cp.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
