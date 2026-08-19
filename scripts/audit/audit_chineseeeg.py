#!/usr/bin/env python3
"""Structural and metadata audit for a local ChineseEEG/OpenNeuro checkout.

This script intentionally avoids loading EEG signal arrays. It inventories the BIDS tree,
parses metadata/TSV files, summarizes events/channels, records repository provenance, and
writes small shareable outputs that can be returned for scientific review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EEG_EXTENSIONS = {".bdf", ".edf", ".set", ".fdt", ".vhdr", ".eeg", ".fif", ".cnt"}
TEXT_EXTENSIONS = {".tsv", ".json", ".txt", ".md"}


def run_git(dataset: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(dataset), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            value = result.stdout.strip()
            return value or None
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            rows = list(reader)
            return list(reader.fieldnames or []), rows
    except Exception:
        return [], []


def safe_unique(values: list[str], max_values: int = 30) -> dict[str, Any]:
    cleaned = [v for v in values if v not in (None, "", "n/a", "NA", "NaN", "nan")]
    counts = Counter(cleaned)
    common = counts.most_common(max_values)
    return {
        "n_nonmissing": len(cleaned),
        "n_unique": len(counts),
        "top_values": [{"value": k, "n": v} for k, v in common],
    }


def summarize_events(path: Path) -> dict[str, Any]:
    fields, rows = read_tsv(path)
    summary: dict[str, Any] = {
        "path": str(path),
        "n_rows": len(rows),
        "columns": fields,
    }
    for candidate in [
        "trial_type",
        "value",
        "stimulus",
        "stim_file",
        "word",
        "text",
        "sentence",
        "onset",
        "duration",
    ]:
        if candidate in fields:
            summary[candidate] = safe_unique([row.get(candidate, "") for row in rows])
    return summary


def summarize_channels(path: Path) -> dict[str, Any]:
    fields, rows = read_tsv(path)
    summary: dict[str, Any] = {
        "path": str(path),
        "n_rows": len(rows),
        "columns": fields,
    }
    for candidate in ["type", "status", "status_description", "units"]:
        if candidate in fields:
            summary[candidate] = safe_unique([row.get(candidate, "") for row in rows])
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a local ChineseEEG BIDS dataset without loading EEG arrays.")
    parser.add_argument("dataset", type=Path, help="Path to downloaded ChineseEEG dataset")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/chineseeeg_audit"),
        help="Parent directory for timestamped audit output",
    )
    parser.add_argument(
        "--hash-large-files",
        action="store_true",
        help="Also SHA256 EEG/binary files. This can be slow and is not needed for the first audit.",
    )
    parser.add_argument("--make-zip", action="store_true", help="Create a ZIP archive of the audit output")
    args = parser.parse_args()

    dataset = args.dataset.expanduser().resolve()
    if not dataset.exists() or not dataset.is_dir():
        raise SystemExit(f"Dataset directory does not exist: {dataset}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    files = sorted(p for p in dataset.rglob("*") if p.is_file() and "/.git/" not in str(p))
    subjects = sorted(p.name for p in dataset.glob("sub-*") if p.is_dir())

    extension_counts = Counter((p.suffix.lower() or "<none>") for p in files)
    extension_bytes: defaultdict[str, int] = defaultdict(int)
    inventory_rows: list[dict[str, Any]] = []

    for p in files:
        rel = p.relative_to(dataset)
        suffix = p.suffix.lower()
        size = p.stat().st_size
        extension_bytes[suffix or "<none>"] += size
        is_eeg = suffix in EEG_EXTENSIONS
        should_hash = args.hash_large_files or (suffix in TEXT_EXTENSIONS and size <= 50 * 1024 * 1024)
        inventory_rows.append(
            {
                "path": str(rel),
                "size_bytes": size,
                "extension": suffix,
                "is_eeg_signal_file": is_eeg,
                "sha256": sha256(p) if should_hash else "",
            }
        )

    events_files = sorted(dataset.rglob("*_events.tsv"))
    channels_files = sorted(dataset.rglob("*_channels.tsv"))
    eeg_json_files = sorted(dataset.rglob("*_eeg.json"))

    event_summaries = [summarize_events(p) for p in events_files]
    channel_summaries = [summarize_channels(p) for p in channels_files]

    eeg_json_summary: list[dict[str, Any]] = []
    for p in eeg_json_files:
        try:
            payload = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            eeg_json_summary.append({"path": str(p.relative_to(dataset)), "error": str(exc)})
            continue
        keep = {
            k: payload.get(k)
            for k in [
                "TaskName",
                "SamplingFrequency",
                "EEGChannelCount",
                "EOGChannelCount",
                "ECGChannelCount",
                "EMGChannelCount",
                "EEGReference",
                "PowerLineFrequency",
                "SoftwareFilters",
                "HardwareFilters",
            ]
            if k in payload
        }
        keep["path"] = str(p.relative_to(dataset))
        eeg_json_summary.append(keep)

    participants_path = dataset / "participants.tsv"
    participants_fields: list[str] = []
    participants_rows: list[dict[str, str]] = []
    if participants_path.exists():
        participants_fields, participants_rows = read_tsv(participants_path)

    git_commit = run_git(dataset, "rev-parse", "HEAD")
    git_describe = run_git(dataset, "describe", "--tags", "--always", "--dirty")
    git_status = run_git(dataset, "status", "--short")

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset),
        "python": sys.version,
        "platform": platform.platform(),
        "n_files": len(files),
        "total_size_bytes": sum(r["size_bytes"] for r in inventory_rows),
        "n_subject_directories": len(subjects),
        "subjects": subjects,
        "n_events_files": len(events_files),
        "n_channels_files": len(channels_files),
        "n_eeg_json_files": len(eeg_json_files),
        "git_commit": git_commit,
        "git_describe": git_describe,
        "git_status": git_status,
        "hash_large_files": args.hash_large_files,
        "privacy_note": "Structural/metadata audit only. No EEG samples are exported.",
    }

    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "size_bytes", "extension", "is_eeg_signal_file", "sha256"])
        writer.writeheader()
        writer.writerows(inventory_rows)

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "events_summary.json").write_text(json.dumps(event_summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "channels_summary.json").write_text(json.dumps(channel_summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "eeg_json_summary.json").write_text(json.dumps(eeg_json_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    if participants_rows:
        with (out / "participants_copy.tsv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=participants_fields, delimiter="\t")
            writer.writeheader()
            writer.writerows(participants_rows)

    report_lines = [
        "# ChineseEEG Local Audit",
        "",
        f"- Dataset path: `{dataset}`",
        f"- Git/DataLad commit: `{git_commit}`",
        f"- Git describe: `{git_describe}`",
        f"- Subject directories: **{len(subjects)}**",
        f"- Files: **{len(files)}**",
        f"- Total size: **{manifest['total_size_bytes'] / (1024**3):.2f} GiB**",
        f"- `*_events.tsv`: **{len(events_files)}**",
        f"- `*_channels.tsv`: **{len(channels_files)}**",
        f"- `*_eeg.json`: **{len(eeg_json_files)}**",
        "",
        "## File types",
        "",
        "| Extension | Files | GiB |",
        "|---|---:|---:|",
    ]
    for ext, n in sorted(extension_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        report_lines.append(f"| `{ext}` | {n} | {extension_bytes[ext] / (1024**3):.3f} |")

    report_lines += [
        "",
        "## Participant metadata",
        "",
        f"`participants.tsv` present: **{participants_path.exists()}**",
        f"Rows: **{len(participants_rows)}**",
        f"Columns: `{', '.join(participants_fields)}`" if participants_fields else "Columns: none parsed",
        "",
        "## Event-file row counts",
        "",
        "| File | Rows | Columns |",
        "|---|---:|---|",
    ]
    for item in event_summaries:
        rel = Path(item["path"]).relative_to(dataset)
        report_lines.append(f"| `{rel}` | {item['n_rows']} | `{', '.join(item['columns'])}` |")

    report_lines += [
        "",
        "## Notes",
        "",
        "- This audit does not load EEG signal samples.",
        "- Metadata/text files are hashed by default when <=50 MB.",
        "- Large EEG files are hashed only with `--hash-large-files`.",
        "- Inspect `events_summary.json` for candidate stimulus/event columns before writing semantic alignment code.",
    ]
    (out / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    if args.make_zip:
        zip_path = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
        print(f"Audit ZIP: {zip_path}")

    print(f"Audit output: {out}")
    print(f"Subjects: {len(subjects)} | files: {len(files)} | size: {manifest['total_size_bytes'] / (1024**3):.2f} GiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
