#!/usr/bin/env python3
"""Model-blind probe of Nature directional-word event metadata.

This script intentionally does not load any language model or compute neural-model RSA.
It records only structural event/metadata information needed to freeze the external
validation protocol before model comparison.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import mne
import pandas as pd


def norm(v):
    if pd.isna(v):
        return None
    if isinstance(v, (int, float, bool)):
        return v
    return str(v)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("dataset_root", type=Path)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    root = args.dataset_root
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    records = []
    event_rows = []

    for language in ("russian", "spanish"):
        lang_root = root / "preprocessed" / language
        if not lang_root.exists():
            continue
        for subject_dir in sorted(p for p in lang_root.iterdir() if p.is_dir()):
            subject = subject_dir.name
            fif_files = sorted(subject_dir.glob("*_epochs.fif"))
            xlsx_files = sorted(subject_dir.glob("*.xlsx"))
            if not fif_files or not xlsx_files:
                continue

            epochs = mne.read_epochs(fif_files[0], preload=False, verbose="ERROR")
            inv = {int(v): k for k, v in epochs.event_id.items()}
            counts = Counter(inv.get(int(code), f"UNKNOWN_{int(code)}") for code in epochs.events[:, 2])
            for label, count in sorted(counts.items()):
                event_rows.append({
                    "language": language,
                    "subject": subject,
                    "event_label": label,
                    "count": int(count),
                })

            df = pd.read_excel(xlsx_files[0])
            col_summary = {}
            for col in df.columns:
                s = df[col].dropna()
                unique = [norm(v) for v in s.unique().tolist()]
                col_summary[str(col)] = {
                    "dtype": str(df[col].dtype),
                    "n_nonmissing": int(s.shape[0]),
                    "n_unique": int(s.nunique(dropna=True)),
                    "unique_values_if_le_40": unique if len(unique) <= 40 else None,
                    "first_10_values": [norm(v) for v in s.head(10).tolist()],
                }

            records.append({
                "language": language,
                "subject": subject,
                "xlsx_columns": [str(c) for c in df.columns],
                "xlsx_n_rows": int(len(df)),
                "xlsx_column_summary": col_summary,
                "event_id": {str(k): int(v) for k, v in epochs.event_id.items()},
                "event_counts": dict(sorted(counts.items())),
            })

    text_like = []
    for pattern in ("README*", "readme*", "*.txt", "*.json", "*.csv"):
        for path in root.rglob(pattern):
            if path.is_file():
                try:
                    rel = str(path.relative_to(root))
                except ValueError:
                    rel = str(path)
                text_like.append(rel)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Model-blind event/metadata probe before freezing Nature external neural validation.",
        "dataset_root": str(root),
        "model_blind": True,
        "neural_model_rsa_computed": False,
        "subjects_probed": len(records),
        "text_like_files": sorted(set(text_like)),
        "subjects": records,
    }

    with (out / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with (out / "event_counts.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["language", "subject", "event_label", "count"])
        writer.writeheader()
        writer.writerows(event_rows)

    print(json.dumps({
        "subjects_probed": len(records),
        "summary": str(out / "summary.json"),
        "event_counts": str(out / "event_counts.csv"),
        "neural_model_rsa_computed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
