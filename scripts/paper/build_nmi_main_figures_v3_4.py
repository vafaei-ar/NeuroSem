#!/usr/bin/env python3
"""Canonical main-figure entry point using the NMI v4 presentation-only system."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/paper/nmi_visualizations_v4/build_nmi_visualizations_v4.py"
CANONICAL_OUT = ROOT / "outputs/nmi_main_figures_v3/latest"


def main() -> int:
    if not BUILDER.exists():
        raise FileNotFoundError(BUILDER)

    completed = subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)

    if completed.returncode != 0:
        CANONICAL_OUT.mkdir(parents=True, exist_ok=True)
        diagnostic = {
            "schema_version": 1,
            "analysis": "NMI v4 figure-build diagnostic",
            "status": "failed",
            "returncode": completed.returncode,
            "builder": str(BUILDER.relative_to(ROOT)),
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
            "guardrails": [
                "Diagnostic capture only; no scientific analysis or input changes.",
                "Failure output is written to the already-declared source_manifest.json artifact for direct retrieval.",
            ],
        }
        (CANONICAL_OUT / "source_manifest.json").write_text(
            json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8"
        )
        return completed.returncode

    # The v4 orchestrator writes the four main figures and source manifest
    # directly to the canonical nmi_main_figures_v3 output directory. Do not
    # copy from the auxiliary directory, which contains only the regional
    # Extended Data figure.
    required = [
        CANONICAL_OUT / f"{stem}.{ext}"
        for stem in ("figure1", "figure2", "figure3", "figure4")
        for ext in ("pdf", "svg", "png")
    ] + [CANONICAL_OUT / "source_manifest.json"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing canonical NMI v4 outputs: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
