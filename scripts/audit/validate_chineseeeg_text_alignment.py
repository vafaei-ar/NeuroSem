#!/usr/bin/env python3
"""Validate ChineseEEG run-level mapping between text rows, event markers, and author embeddings."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import mne
import numpy as np
import openpyxl


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--subject", default="sub-04")
    parser.add_argument("--session", default="ses-LittlePrince")
    parser.add_argument("--run", default="run-01")
    parser.add_argument("--run-number", type=int, default=1)
    parser.add_argument("--derivative", default="filtered_0.5_30")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_text_alignment"))
    args = parser.parse_args()

    dataset = args.dataset.expanduser().resolve()
    base = dataset / "derivatives" / args.derivative / args.subject / args.session / "eeg" / f"{args.subject}_{args.session}_task-reading_{args.run}"
    vhdr = Path(str(base) + "_eeg.vhdr")
    events_tsv = Path(str(base) + "_events.tsv")
    text_xlsx = dataset / "derivatives" / "novels" / "segmented_novel" / "LittlePrince" / f"segmented_Chinense_novel_run_{args.run_number}.xlsx"
    embed_npy = dataset / "derivatives" / "text_embeddings" / "LittlePrince_text_embedding" / f"text_embedding_run_{args.run_number}.npy"

    required = [vhdr, events_tsv, text_xlsx, embed_npy]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing required files:\n" + "\n".join(missing))

    wb = openpyxl.load_workbook(text_xlsx, read_only=True, data_only=True)
    ws = wb.active
    text_rows = [ws.cell(row=i, column=1).value for i in range(2, ws.max_row + 1)]
    text_rows = [x for x in text_rows if x is not None]
    if not text_rows:
        raise SystemExit("No text rows parsed from xlsx")

    start_chapter = int(text_rows[0])
    start_marker = f"CH{start_chapter:02d}"
    stimuli = text_rows[1:]

    raw = mne.io.read_raw_brainvision(vhdr, preload=False, verbose="ERROR")
    annotations = [(float(o), float(d), str(desc)) for o, d, desc in zip(raw.annotations.onset, raw.annotations.duration, raw.annotations.description)]
    descriptions = [x[2] for x in annotations]

    start_indices = [i for i, desc in enumerate(descriptions) if desc == start_marker or desc.endswith("/" + start_marker)]
    if not start_indices:
        raise SystemExit(f"Start chapter marker not found in annotations: {start_marker}")
    start_idx = start_indices[0]
    relevant = annotations[start_idx:]

    rows = []
    open_start = None
    for onset, duration, desc in relevant:
        normalized = desc.split("/")[-1]
        if normalized == "ROWS":
            open_start = onset
        elif normalized == "ROWE" and open_start is not None:
            rows.append((open_start, onset))
            open_start = None

    embeddings = np.load(embed_npy, mmap_mode="r")
    event_rows = read_tsv(events_tsv)

    n_segments = len(rows)
    n_stimuli = len(stimuli)
    n_embeddings = int(embeddings.shape[0]) if embeddings.ndim >= 1 else 0
    durations = np.array([b - a for a, b in rows], dtype=float) if rows else np.array([])

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "pilot": {"subject": args.subject, "session": args.session, "run": args.run, "derivative": args.derivative},
        "text_file": str(text_xlsx),
        "embedding_file": str(embed_npy),
        "start_chapter": start_chapter,
        "start_marker": start_marker,
        "xlsx_rows_after_header": len(text_rows),
        "stimulus_rows_excluding_chapter_id": n_stimuli,
        "paired_ROWS_ROWE_segments": n_segments,
        "embedding_shape": list(embeddings.shape),
        "event_tsv_rows": len(event_rows),
        "annotation_counts": dict(Counter(descriptions)),
        "segment_duration_sec": {
            "min": float(durations.min()) if durations.size else None,
            "median": float(np.median(durations)) if durations.size else None,
            "max": float(durations.max()) if durations.size else None,
        },
        "checks": {
            "stimuli_equal_segments": n_stimuli == n_segments,
            "stimuli_equal_embeddings": n_stimuli == n_embeddings,
            "segments_equal_embeddings": n_segments == n_embeddings,
            "all_segments_positive_duration": bool(np.all(durations > 0)) if durations.size else False,
        },
        "first_pairs": [
            {"index": i, "text": str(stimuli[i]), "start_sec": rows[i][0], "end_sec": rows[i][1], "duration_sec": rows[i][1]-rows[i][0]}
            for i in range(min(10, n_stimuli, n_segments))
        ],
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Validation output: {out}")
    print(f"Start chapter/marker: {start_chapter} / {start_marker}")
    print(f"Stimulus rows: {n_stimuli}")
    print(f"ROWS-ROWE segments: {n_segments}")
    print(f"Embedding shape: {tuple(embeddings.shape)}")
    print("Checks:")
    for key, value in summary["checks"].items():
        print(f"  {key}: {value}")
    print("First aligned text rows:")
    for item in summary["first_pairs"][:5]:
        print(f"  {item['index']:03d} {item['start_sec']:.3f}-{item['end_sec']:.3f}s  {item['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
