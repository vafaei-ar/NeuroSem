#!/usr/bin/env python3
"""Collect latest safe summary JSONs from the completed E5 replication.

This script performs no model training or evaluation. It only reads derived summary
files already written by the frozen E5 replication and emits one compact aggregate
report suitable for RunRelay artifact collection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ARMS = ("text_only", "neural", "shuffled_neural")


def latest_summary(root: Path) -> Path:
    candidates = sorted(p for p in root.glob("*/summary.json") if p.is_file())
    if not candidates:
        raise FileNotFoundError(f"No summary.json found under {root}")
    return candidates[-1]


def latest_nested_summary(root: Path) -> Path:
    candidates = sorted(p for p in root.glob("**/summary.json") if p.is_file())
    if not candidates:
        raise FileNotFoundError(f"No summary.json found under {root}")
    return candidates[-1]


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return data


def main() -> int:
    tuning = {}
    tuning_paths = {}
    for arm in ARMS:
        path = latest_summary(Path("outputs/e5_neural_tuning_v1") / arm)
        tuning[arm] = read_json(path)
        tuning_paths[arm] = str(path)

    run07 = {}
    run07_paths = {}
    for arm in ("base", *ARMS):
        path = latest_nested_summary(Path("outputs/e5_neurosem_run07_rsa_v1") / arm / "run-07")
        run07[arm] = read_json(path)
        run07_paths[arm] = str(path)

    external_path = latest_summary(Path("outputs/e5_neurosem_cmteb_sts_v1"))
    external = read_json(external_path)

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Aggregate already-completed E5 replication summaries; no parameter updates or new evaluation.",
        "tuning": tuning,
        "run07_rsa": run07,
        "external_sts": external,
        "source_paths": {
            "tuning": tuning_paths,
            "run07_rsa": run07_paths,
            "external_sts": str(external_path),
        },
    }

    out = Path("outputs/e5_replication_report/latest")
    out.mkdir(parents=True, exist_ok=True)
    target = out / "combined_summary.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"E5 replication combined summary: {target.resolve()}")
    print("Run-06 final correlations:")
    for arm in ARMS:
        print(f"  {arm}: {float(tuning[arm]['final_run06_neural_corr']):.6f}")
    print("Run-07 mean partial-Spearman:")
    for arm in ("base", *ARMS):
        print(f"  {arm}: {float(run07[arm]['observed']['mean']):.6f}")
    contrasts = external.get("contrasts", {})
    print("External STS contrasts:")
    print(f"  neural-text_only: {float(contrasts['neural_minus_text_only']):+.6f}")
    print(f"  neural-shuffled: {float(contrasts['neural_minus_shuffled_neural']):+.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
