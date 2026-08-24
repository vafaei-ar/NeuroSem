#!/usr/bin/env python3
"""Model-blind inventory of locally available ChineseEEG time-resolved inputs.

This script does not load language-model embeddings and does not compute neural-model RSA.
It inventories only project-local ChineseEEG files/outputs needed to decide whether a
richer EEG representation (ERP windows, spectral power, phase-sensitive features,
artifact/component filtering) is feasible without materializing the full dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


SIGNAL_SUFFIXES = {".vhdr", ".vmrk", ".eeg", ".fif", ".set", ".edf", ".bdf"}
META_SUFFIXES = {".tsv", ".csv", ".json", ".xlsx", ".txt"}
KEYWORDS = {
    "eeg": ("eeg", "brainvision", "preprocess", "preprocessed", "derivative"),
    "events": ("event", "marker", "vmrk"),
    "eye_tracking": ("eye", "gaze", "fixation", "tobii"),
    "ica_components": ("ica", "component", "iclabel"),
    "filtered_30hz": ("0.5-30", "0.5_30", "30hz", "30_hz"),
    "filtered_80hz": ("0.5-80", "0.5_80", "80hz", "80_hz"),
}


def is_materialized(path: Path) -> bool:
    try:
        if path.is_symlink():
            return path.exists()
        if not path.is_file():
            return False
        return path.stat().st_size > 0
    except OSError:
        return False


def classify(path: Path) -> list[str]:
    low = str(path).lower()
    labels = []
    for label, words in KEYWORDS.items():
        if any(w in low for w in words):
            labels.append(label)
    if path.suffix.lower() in SIGNAL_SUFFIXES:
        labels.append("signal_file")
    if path.suffix.lower() in META_SUFFIXES:
        labels.append("metadata_file")
    return sorted(set(labels))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit locally available ChineseEEG time-resolved inputs.")
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    parser.add_argument("--outputs-root", type=Path, default=Path("outputs"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_time_resolved_input_audit/latest"))
    parser.add_argument("--max-listed", type=int, default=5000)
    args = parser.parse_args()

    roots = [args.data_root, args.outputs_root]
    rows: list[dict[str, object]] = []
    category_counts: Counter[str] = Counter()
    suffix_counts: Counter[str] = Counter()
    materialized_by_category: Counter[str] = Counter()
    subject_counts: Counter[str] = Counter()
    run_hints: Counter[str] = Counter()

    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Avoid crawling large irrelevant caches if present under outputs.
            dirnames[:] = [d for d in dirnames if d not in {".git", ".venv", "node_modules", "__pycache__"}]
            base = Path(dirpath)
            for name in filenames:
                path = base / name
                rel = path.as_posix()
                low = rel.lower()
                if "chineseeeg" not in low and root == args.outputs_root:
                    continue
                labels = classify(path)
                if not labels and path.suffix.lower() not in SIGNAL_SUFFIXES | META_SUFFIXES:
                    continue
                mat = is_materialized(path)
                size = None
                if mat:
                    try:
                        size = path.stat().st_size
                    except OSError:
                        size = None
                suffix_counts[path.suffix.lower() or "<none>"] += 1
                for label in labels:
                    category_counts[label] += 1
                    if mat:
                        materialized_by_category[label] += 1
                parts = path.parts
                for part in parts:
                    pl = part.lower()
                    if pl.startswith("sub-") or pl.startswith("sub_"):
                        subject_counts[part] += 1
                    if pl.startswith("run-") or pl.startswith("run_") or pl.startswith("run") and any(ch.isdigit() for ch in pl):
                        run_hints[part] += 1
                if len(rows) < args.max_listed:
                    rows.append({
                        "path": rel,
                        "suffix": path.suffix.lower(),
                        "materialized": mat,
                        "size_bytes": size,
                        "categories": ";".join(labels),
                    })

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "suffix", "materialized", "size_bytes", "categories"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Model-blind feasibility audit for richer ChineseEEG EEG representations.",
        "model_blind": True,
        "neural_model_rsa_computed": False,
        "data_root": str(args.data_root),
        "outputs_root": str(args.outputs_root),
        "listed_files": len(rows),
        "max_listed": args.max_listed,
        "category_counts": dict(category_counts),
        "materialized_by_category": dict(materialized_by_category),
        "suffix_counts": dict(suffix_counts),
        "subject_path_hints": dict(subject_counts),
        "run_path_hints": dict(run_hints),
        "feasibility_questions": {
            "time_resolved_signal_materialized": materialized_by_category.get("signal_file", 0) > 0,
            "event_metadata_materialized": materialized_by_category.get("events", 0) > 0,
            "eye_tracking_materialized": materialized_by_category.get("eye_tracking", 0) > 0,
            "ica_or_component_metadata_materialized": materialized_by_category.get("ica_components", 0) > 0,
            "filtered_30hz_materialized": materialized_by_category.get("filtered_30hz", 0) > 0,
            "filtered_80hz_materialized": materialized_by_category.get("filtered_80hz", 0) > 0,
        },
        "notes": [
            "This audit intentionally does not load EEG arrays or model embeddings.",
            "Counts are path-based and should be followed by targeted inspection before feature extraction.",
            "Do not materialize the full ChineseEEG annexed dataset based on this audit.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary["feasibility_questions"], indent=2))
    print(f"Wrote {out / 'summary.json'}")
    print(f"Wrote {out / 'file_inventory.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
