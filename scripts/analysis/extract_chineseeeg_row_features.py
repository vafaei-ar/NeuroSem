#!/usr/bin/env python3
"""Extract simple, prespecified sensor-level features for aligned ChineseEEG rows.

This is an engineering/representation checkpoint, not the primary NeuroSem test.
It uses the published filtered derivative without additional filtering and preserves
row-level metadata. Semantic chapter-number rows are excluded by default.

Outputs:
- metadata.csv: row identity/timing information for extracted semantic rows
- row_mean.npy: whole-row mean voltage, shape [rows, channels]
- row_std.npy: whole-row voltage SD, shape [rows, channels]
- relative_8bin_mean.npy: duration-normalized 8-bin means, shape [rows, 8, channels]
- onset_500ms_mean.npy: first-500-ms means, NaN for rows shorter than 500 ms
- channels.txt
- summary.json

Important: whole-row and duration-normalized representations are intentionally
simple baselines and can carry duration/position structure. They must not be
interpreted as semantic effects without nuisance-controlled analyses.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import mne
import numpy as np


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_manifest(root: Path) -> Path:
    matches = sorted(root.glob("*/pilot_manifest.csv"))
    if not matches:
        raise SystemExit(
            f"No pilot_manifest.csv found under {root}. "
            "Run build_chineseeeg_pilot_manifest.py first or pass --manifest."
        )
    return matches[-1]


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract simple aligned ChineseEEG row-level neural features.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--subject", default="sub-04")
    parser.add_argument("--session", default="ses-LittlePrince")
    parser.add_argument("--run", default="run-01")
    parser.add_argument("--derivative", default="filtered_0.5_30")
    parser.add_argument("--relative-bins", type=int, default=8)
    parser.add_argument("--onset-ms", type=float, default=500.0)
    parser.add_argument("--include-structural", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_row_features"))
    args = parser.parse_args()

    if args.relative_bins < 2:
        raise SystemExit("--relative-bins must be >= 2")
    if args.onset_ms <= 0:
        raise SystemExit("--onset-ms must be > 0")

    dataset = args.dataset.expanduser().resolve()
    manifest = (
        args.manifest.expanduser().resolve()
        if args.manifest is not None
        else latest_manifest(Path("outputs/chineseeeg_pilot_manifest"))
    )

    base = (
        dataset
        / "derivatives"
        / args.derivative
        / args.subject
        / args.session
        / "eeg"
        / f"{args.subject}_{args.session}_task-reading_{args.run}"
    )
    vhdr = Path(str(base) + "_eeg.vhdr")
    if not vhdr.exists():
        raise SystemExit(f"BrainVision header not materialized: {vhdr}")
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}")

    rows = read_manifest(manifest)
    if not rows:
        raise SystemExit("Manifest is empty")

    selected = []
    for row in rows:
        eligible = parse_bool(row.get("semantic_eligible", ""))
        if eligible or args.include_structural:
            selected.append(row)
    if not selected:
        raise SystemExit("No rows selected from manifest")

    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="ERROR")
    sfreq = float(raw.info["sfreq"])
    n_channels = len(raw.ch_names)
    onset_samples = max(1, int(round(args.onset_ms * sfreq / 1000.0)))

    n_rows = len(selected)
    row_mean = np.full((n_rows, n_channels), np.nan, dtype=np.float32)
    row_std = np.full((n_rows, n_channels), np.nan, dtype=np.float32)
    relative = np.full((n_rows, args.relative_bins, n_channels), np.nan, dtype=np.float32)
    onset_mean = np.full((n_rows, n_channels), np.nan, dtype=np.float32)

    out_meta: list[dict[str, object]] = []
    short_for_onset = 0
    clipped_segments = 0

    for i, row in enumerate(selected):
        start_sec = float(row["start_sec"])
        end_sec = float(row["end_sec"])
        start = int(round(start_sec * sfreq))
        stop = int(round(end_sec * sfreq))
        start = max(0, min(start, raw.n_times))
        stop = max(0, min(stop, raw.n_times))
        if stop <= start:
            raise SystemExit(
                f"Non-positive segment after sample conversion at alignment_index={row.get('alignment_index')}: "
                f"start={start}, stop={stop}"
            )
        expected_stop = int(round(end_sec * sfreq))
        if expected_stop > raw.n_times:
            clipped_segments += 1

        data = raw.get_data(start=start, stop=stop)  # [channels, time]
        if not np.isfinite(data).all():
            raise SystemExit(f"Non-finite EEG values at alignment_index={row.get('alignment_index')}")

        row_mean[i] = data.mean(axis=1, dtype=np.float64).astype(np.float32)
        row_std[i] = data.std(axis=1, dtype=np.float64).astype(np.float32)

        edges = np.linspace(0, data.shape[1], args.relative_bins + 1)
        edges = np.round(edges).astype(int)
        for b in range(args.relative_bins):
            lo, hi = int(edges[b]), int(edges[b + 1])
            if hi <= lo:
                hi = min(data.shape[1], lo + 1)
            if hi > lo:
                relative[i, b] = data[:, lo:hi].mean(axis=1, dtype=np.float64).astype(np.float32)

        if data.shape[1] >= onset_samples:
            onset_mean[i] = data[:, :onset_samples].mean(axis=1, dtype=np.float64).astype(np.float32)
        else:
            short_for_onset += 1

        out_meta.append({
            "feature_row": i,
            "alignment_index": row.get("alignment_index", ""),
            "embedding_index": row.get("embedding_index", ""),
            "text": row.get("text", ""),
            "chapter_marker_context": row.get("chapter_marker_context", ""),
            "semantic_eligible": row.get("semantic_eligible", ""),
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration_sec": end_sec - start_sec,
            "start_sample": start,
            "stop_sample": stop,
            "n_samples": stop - start,
            "char_count": row.get("char_count", ""),
            "run_position_fraction": row.get("run_position_fraction", ""),
            "onset_window_available": data.shape[1] >= onset_samples,
        })

    if np.isnan(row_mean).any() or np.isnan(row_std).any() or np.isnan(relative).any():
        raise SystemExit("Unexpected NaN in mandatory whole-row or relative-bin features")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    np.save(out / "row_mean.npy", row_mean)
    np.save(out / "row_std.npy", row_std)
    np.save(out / f"relative_{args.relative_bins}bin_mean.npy", relative)
    np.save(out / f"onset_{int(round(args.onset_ms))}ms_mean.npy", onset_mean)
    (out / "channels.txt").write_text("\n".join(raw.ch_names) + "\n", encoding="utf-8")

    meta_fields = list(out_meta[0].keys())
    with (out / "metadata.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=meta_fields)
        writer.writeheader()
        writer.writerows(out_meta)

    durations = np.array([float(x["duration_sec"]) for x in out_meta], dtype=float)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset),
        "manifest": str(manifest),
        "subject": args.subject,
        "session": args.session,
        "run": args.run,
        "derivative": args.derivative,
        "mne_version": mne.__version__,
        "sfreq_hz": sfreq,
        "n_channels": n_channels,
        "n_rows": n_rows,
        "include_structural": bool(args.include_structural),
        "relative_bins": args.relative_bins,
        "onset_window_ms": args.onset_ms,
        "rows_shorter_than_onset_window": short_for_onset,
        "clipped_segments": clipped_segments,
        "duration_sec": {
            "min": float(durations.min()),
            "median": float(np.median(durations)),
            "max": float(durations.max()),
        },
        "shapes": {
            "row_mean": list(row_mean.shape),
            "row_std": list(row_std.shape),
            "relative": list(relative.shape),
            "onset_mean": list(onset_mean.shape),
        },
        "notes": [
            "No extra filtering, rereferencing, baseline correction, or normalization was applied.",
            "Whole-row and relative-time features are baseline representations and can reflect duration/position structure.",
            "Rows shorter than the onset window have NaN in onset-window features and must be excluded from analyses using that feature.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Feature output: {out}")
    print(f"Rows: {n_rows} | channels: {n_channels} | sfreq: {sfreq:g} Hz")
    print(
        "Duration (s): "
        f"min={durations.min():.3f} median={np.median(durations):.3f} max={durations.max():.3f}"
    )
    print(f"Rows shorter than {args.onset_ms:g} ms: {short_for_onset}")
    print(f"Clipped segments: {clipped_segments}")
    print(f"row_mean shape: {row_mean.shape}")
    print(f"row_std shape: {row_std.shape}")
    print(f"relative_{args.relative_bins}bin_mean shape: {relative.shape}")
    print(f"onset_{int(round(args.onset_ms))}ms_mean shape: {onset_mean.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
