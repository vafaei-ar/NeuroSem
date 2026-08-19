#!/usr/bin/env python3
"""Validate ChineseEEG run-level mapping between text rows, BIDS events, and author embeddings.

The BIDS events TSV is the canonical source for semantic event labels (CHxx, ROWS, ROWE).
BrainVision/MNE annotations are retained as a secondary consistency check because MNE may
encode BrainVision marker descriptions differently from the BIDS ``trial_type`` labels.
"""

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


def read_tsv(path: Path) -> list[dict[str, str]]:
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
    base = (
        dataset / "derivatives" / args.derivative / args.subject / args.session / "eeg"
        / f"{args.subject}_{args.session}_task-reading_{args.run}"
    )
    vhdr = Path(str(base) + "_eeg.vhdr")
    events_tsv = Path(str(base) + "_events.tsv")
    text_xlsx = (
        dataset / "derivatives" / "novels" / "segmented_novel" / "LittlePrince"
        / f"segmented_Chinense_novel_run_{args.run_number}.xlsx"
    )
    embed_npy = (
        dataset / "derivatives" / "text_embeddings" / "LittlePrince_text_embedding"
        / f"text_embedding_run_{args.run_number}.npy"
    )

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

    event_rows = read_tsv(events_tsv)
    if not event_rows:
        raise SystemExit("No rows parsed from events TSV")

    trial_types = [str(row.get("trial_type", "")).strip() for row in event_rows]
    start_indices = [i for i, label in enumerate(trial_types) if label == start_marker]
    if not start_indices:
        available_ch = sorted({x for x in trial_types if x.startswith("CH")})
        raise SystemExit(
            f"Start chapter marker not found in BIDS events TSV: {start_marker}. "
            f"Available chapter markers: {available_ch}"
        )
    start_idx = start_indices[0]
    relevant_events = event_rows[start_idx:]

    # Pair ROWS and ROWE in temporal sequence from the BIDS event table.
    segments: list[tuple[float, float]] = []
    open_start: float | None = None
    malformed = []
    for row in relevant_events:
        label = str(row.get("trial_type", "")).strip()
        try:
            onset = float(row["onset"])
        except (TypeError, ValueError, KeyError):
            continue
        if label == "ROWS":
            if open_start is not None:
                malformed.append({"type": "nested_ROWS", "previous_start": open_start, "new_start": onset})
            open_start = onset
        elif label == "ROWE":
            if open_start is None:
                malformed.append({"type": "ROWE_without_ROWS", "end": onset})
            else:
                segments.append((open_start, onset))
                open_start = None
    if open_start is not None:
        malformed.append({"type": "unclosed_ROWS", "start": open_start})

    embeddings = np.load(embed_npy, mmap_mode="r")

    # MNE/BrainVision annotations are a secondary structural check only.
    raw = mne.io.read_raw_brainvision(vhdr, preload=False, verbose="ERROR")
    annotation_descriptions = [str(x) for x in raw.annotations.description]
    annotation_count = len(annotation_descriptions)

    n_segments = len(segments)
    n_stimuli = len(stimuli)
    n_embeddings = int(embeddings.shape[0]) if embeddings.ndim >= 1 else 0
    durations = np.array([b - a for a, b in segments], dtype=float) if segments else np.array([])

    checks = {
        "start_marker_present_in_bids_events": True,
        "stimuli_equal_segments": n_stimuli == n_segments,
        "stimuli_equal_embeddings": n_stimuli == n_embeddings,
        "segments_equal_embeddings": n_segments == n_embeddings,
        "all_segments_positive_duration": bool(np.all(durations > 0)) if durations.size else False,
        "no_malformed_ROWS_ROWE_sequence": len(malformed) == 0,
        "mne_annotation_count_equals_bids_event_count": annotation_count == len(event_rows),
    }

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "pilot": {
            "subject": args.subject,
            "session": args.session,
            "run": args.run,
            "derivative": args.derivative,
        },
        "text_file": str(text_xlsx),
        "embedding_file": str(embed_npy),
        "events_file": str(events_tsv),
        "start_chapter": start_chapter,
        "start_marker": start_marker,
        "xlsx_rows_after_header": len(text_rows),
        "stimulus_rows_excluding_chapter_id": n_stimuli,
        "paired_ROWS_ROWE_segments": n_segments,
        "embedding_shape": list(embeddings.shape),
        "event_tsv_rows": len(event_rows),
        "bids_trial_type_counts": dict(Counter(trial_types)),
        "mne_annotation_count": annotation_count,
        "mne_annotation_description_counts": dict(Counter(annotation_descriptions)),
        "malformed_marker_sequences": malformed,
        "segment_duration_sec": {
            "min": float(durations.min()) if durations.size else None,
            "median": float(np.median(durations)) if durations.size else None,
            "max": float(durations.max()) if durations.size else None,
        },
        "checks": checks,
        "first_pairs": [
            {
                "index": i,
                "text": str(stimuli[i]),
                "start_sec": segments[i][0],
                "end_sec": segments[i][1],
                "duration_sec": segments[i][1] - segments[i][0],
            }
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
    print(f"BIDS events: {len(event_rows)} | MNE annotations: {annotation_count}")
    print(f"Malformed ROWS/ROWE sequences: {len(malformed)}")
    print("Checks:")
    for key, value in checks.items():
        print(f"  {key}: {value}")
    print("First aligned text rows:")
    for item in summary["first_pairs"][:5]:
        print(f"  {item['index']:03d} {item['start_sec']:.3f}-{item['end_sec']:.3f}s  {item['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
