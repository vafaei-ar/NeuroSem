#!/usr/bin/env python3
"""Model-blind structural audit for TMNRED (OpenNeuro ds005383).

This audit inspects repository metadata and materialization state only. It does not
load EEG signal arrays, language-model embeddings, adapters, or compute RSA.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def categories(path: str) -> list[str]:
    p = path.lower()
    out = []
    if "/eeg/" in p or p.endswith((".eeg", ".vhdr", ".edf", ".set", ".bdf")):
        out.append("eeg")
    if p.endswith("_events.tsv"):
        out.append("events")
    if p.endswith("_channels.tsv"):
        out.append("channels")
    if p.endswith("_electrodes.tsv"):
        out.append("electrodes")
    if "stim" in p or "material" in p or "sentence" in p:
        out.append("stimulus_metadata")
    if "preproc" in p or "derivative" in p or "processed" in p:
        out.append("preprocessed_or_derivative")
    if p.endswith(".mat"):
        out.append("matlab")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/tmnred"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/tmnred_audit/latest"))
    args = ap.parse_args()

    root = args.data_root.expanduser().absolute()
    out = args.output_dir.expanduser().absolute()
    out.mkdir(parents=True, exist_ok=True)

    if not (root / ".git").exists():
        raise SystemExit(f"Not a git/DataLad checkout: {root}")

    head = git(root, "rev-parse", "HEAD")
    tags = [x for x in git(root, "tag", "--points-at", "HEAD").splitlines() if x]
    tracked = [x for x in git(root, "ls-files").splitlines() if x]

    suffix_counts = Counter()
    category_counts = Counter()
    materialized_by_category = Counter()
    subject_files = defaultdict(int)
    inventory = []

    for rel in tracked:
        p = root / rel
        suffix = Path(rel).suffix.lower()
        cats = categories(rel)
        suffix_counts[suffix or "<none>"] += 1
        for c in cats:
            category_counts[c] += 1
        materialized = p.exists()
        if materialized:
            for c in cats:
                materialized_by_category[c] += 1
        parts = Path(rel).parts
        subject = next((x for x in parts if x.startswith("sub-")), "")
        if subject:
            subject_files[subject] += 1
        inventory.append({
            "path": rel,
            "suffix": suffix,
            "materialized": int(materialized),
            "size_bytes": p.stat().st_size if materialized and p.is_file() else "",
            "categories": ";".join(cats),
            "subject": subject,
        })

    participants_path = root / "participants.tsv"
    participants = read_tsv(participants_path) if participants_path.exists() else []
    participant_ids = [r.get("participant_id", "") for r in participants if r.get("participant_id")]

    event_files = [root / r for r in tracked if r.endswith("_events.tsv") and (root / r).exists()]
    channel_files = [root / r for r in tracked if r.endswith("_channels.tsv") and (root / r).exists()]
    electrode_files = [root / r for r in tracked if r.endswith("_electrodes.tsv") and (root / r).exists()]

    event_columns = Counter()
    event_rows_total = 0
    event_task_files = []
    for p in event_files:
        try:
            rows = read_tsv(p)
            event_rows_total += len(rows)
            if rows:
                event_columns.update(rows[0].keys())
            event_task_files.append(str(p.relative_to(root)))
        except Exception as exc:
            event_task_files.append(f"ERROR:{p.relative_to(root)}:{exc}")

    channel_names = set()
    channel_types = Counter()
    sampling_frequencies = set()
    for p in channel_files:
        try:
            for row in read_tsv(p):
                if row.get("name"):
                    channel_names.add(row["name"])
                if row.get("type"):
                    channel_types[row["type"]] += 1
                if row.get("sampling_frequency"):
                    sampling_frequencies.add(row["sampling_frequency"])
        except Exception:
            pass

    summary = {
        "schema_version": 1,
        "dataset": "TMNRED",
        "openneuro_accession": "ds005383",
        "published_snapshot": "1.0.0",
        "git_head": head,
        "tags_at_head": tags,
        "snapshot_matches_published_v1_0_0": "1.0.0" in tags,
        "model_blind": True,
        "tracked_files": len(tracked),
        "materialized_files": sum(int(r["materialized"]) for r in inventory),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "materialized_by_category": dict(sorted(materialized_by_category.items())),
        "participants_tsv_materialized": participants_path.exists(),
        "participants_count": len(participant_ids),
        "participant_ids": participant_ids,
        "subjects_seen_in_paths": sorted(subject_files),
        "n_subjects_seen_in_paths": len(subject_files),
        "event_files_materialized": len(event_files),
        "event_rows_total_materialized": event_rows_total,
        "event_columns_seen": dict(sorted(event_columns.items())),
        "event_files_sample": event_task_files[:40],
        "channel_files_materialized": len(channel_files),
        "unique_channel_names_seen": sorted(channel_names),
        "n_unique_channel_names_seen": len(channel_names),
        "channel_types_seen": dict(sorted(channel_types.items())),
        "sampling_frequencies_seen": sorted(sampling_frequencies),
        "electrode_files_materialized": len(electrode_files),
        "feasibility": {
            "has_tracked_eeg": category_counts["eeg"] > 0,
            "has_materialized_eeg": materialized_by_category["eeg"] > 0,
            "has_events": category_counts["events"] > 0,
            "has_materialized_events": len(event_files) > 0,
            "has_channels": category_counts["channels"] > 0,
            "has_electrodes": category_counts["electrodes"] > 0,
            "has_preprocessed_or_derivative": category_counts["preprocessed_or_derivative"] > 0,
            "has_matlab": category_counts["matlab"] > 0,
        },
        "notes": [
            "This audit does not recursively materialize annexed EEG payloads.",
            "Signal-level candidate definitions must be frozen only after reviewing this structural audit.",
            "No model embeddings or neural-model RSA are loaded or computed.",
        ],
    }

    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "suffix", "materialized", "size_bytes", "categories", "subject"])
        writer.writeheader()
        writer.writerows(inventory)

    print(json.dumps({
        "dataset": "TMNRED",
        "head": head,
        "tags_at_head": tags,
        "participants_count": len(participant_ids),
        "tracked_files": len(tracked),
        "materialized_files": summary["materialized_files"],
        "output_dir": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
