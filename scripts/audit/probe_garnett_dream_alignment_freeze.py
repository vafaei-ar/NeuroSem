#!/usr/bin/env python3
"""Orchestrate the model-blind Garnett Dream structural + text mapping freeze."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_alignment_freeze_probe/latest"))
    args = ap.parse_args()

    root = args.data_root
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve().parent
    core = here / "probe_garnett_dream_alignment_freeze_core.py"
    text_probe = here / "probe_garnett_dream_text_mapping.py"

    cp1 = subprocess.run([
        sys.executable, str(core), "--data-root", str(root), "--output-dir", str(out)
    ], check=False)
    if cp1.returncode != 0:
        return cp1.returncode

    mapping_out = out / "text_mapping_internal"
    cp2 = subprocess.run([
        sys.executable, str(text_probe),
        "--data-root", str(root),
        "--alignment-freeze", str(out / "summary.json"),
        "--output-dir", str(mapping_out),
    ], check=False)
    if cp2.returncode != 0:
        return cp2.returncode

    main_summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    mapping_summary = json.loads((mapping_out / "summary.json").read_text(encoding="utf-8"))
    main_summary["public_text_mapping_probe"] = mapping_summary
    main_summary["freeze_gate"] = {
        "ready_for_materialization": bool(mapping_summary.get("freeze_gate", {}).get("ready_for_eeg_materialization")),
        "ready_for_reliability": False,
        "reason": "Public text structure is now probed model-blind; selected EEG BrainVision companions and final row identity mapping must still be materialized/frozen before reliability.",
    }
    (out / "summary.json").write_text(json.dumps(main_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Replace the prior broad text-candidate artifact with a concise safe summary.
    # No copyrighted novel text is exported.
    (out / "text_candidates.json").write_text(json.dumps(mapping_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "structural_freeze": "complete",
        "text_mapping_probe": "complete",
        "ready_for_materialization": main_summary["freeze_gate"]["ready_for_materialization"],
        "ready_for_reliability": False,
        "output_dir": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
