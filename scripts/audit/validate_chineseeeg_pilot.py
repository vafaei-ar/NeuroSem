#!/usr/bin/env python3
"""Validate the first materialized ChineseEEG pilot run with MNE.

This script is intentionally read-only. It checks that the BrainVision triplet and BIDS
metadata are internally consistent, loads only a small data slice, summarizes annotations
and events, and writes a compact JSON/Markdown report that can be shared for review.
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a materialized ChineseEEG pilot BrainVision run.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--subject", default="sub-04")
    parser.add_argument("--session", default="ses-LittlePrince")
    parser.add_argument("--run", default="run-01")
    parser.add_argument("--derivative", default="filtered_0.5_30")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_pilot_validation"))
    parser.add_argument("--sample-seconds", type=float, default=20.0,
                        help="Small signal window to load for numerical sanity checks.")
    args = parser.parse_args()

    dataset = args.dataset.expanduser().resolve()
    base = (
        dataset / "derivatives" / args.derivative / args.subject / args.session / "eeg"
        / f"{args.subject}_{args.session}_task-reading_{args.run}"
    )

    vhdr = Path(str(base) + "_eeg.vhdr")
    eeg = Path(str(base) + "_eeg.eeg")
    vmrk = Path(str(base) + "_eeg.vmrk")
    eeg_json = Path(str(base) + "_eeg.json")
    channels_tsv = Path(str(base) + "_channels.tsv")
    events_tsv = Path(str(base) + "_events.tsv")

    required = [vhdr, eeg, vmrk, eeg_json, channels_tsv, events_tsv]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing pilot files:\n" + "\n".join(missing))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    meta = json.loads(eeg_json.read_text(encoding="utf-8-sig"))
    channel_fields, channel_rows = read_tsv(channels_tsv)
    event_fields, event_rows = read_tsv(events_tsv)

    raw = mne.io.read_raw_brainvision(vhdr, preload=False, verbose="ERROR")

    sfreq = float(raw.info["sfreq"])
    duration_sec = raw.n_times / sfreq
    sample_stop = min(raw.n_times, max(1, int(round(args.sample_seconds * sfreq))))
    data = raw.get_data(start=0, stop=sample_stop)

    finite_fraction = float(np.isfinite(data).mean()) if data.size else 0.0
    channel_std = np.nanstd(data, axis=1) if data.size else np.array([])
    zero_var_channels = int(np.sum(channel_std == 0)) if channel_std.size else 0
    median_std = float(np.nanmedian(channel_std)) if channel_std.size else None

    bids_sfreq = meta.get("SamplingFrequency")
    bids_eeg_count = meta.get("EEGChannelCount")
    channel_type_counts = Counter(row.get("type", "") for row in channel_rows)
    channel_status_counts = Counter(row.get("status", "") for row in channel_rows)
    event_trial_counts = Counter(row.get("trial_type", "") for row in event_rows)
    event_value_counts = Counter(row.get("value", "") for row in event_rows)

    try:
        onset = np.array([float(row["onset"]) for row in event_rows if row.get("onset") not in (None, "", "n/a")])
    except Exception:
        onset = np.array([])
    try:
        durations = np.array([float(row["duration"]) for row in event_rows if row.get("duration") not in (None, "", "n/a")])
    except Exception:
        durations = np.array([])

    checks = {
        "sfreq_matches_json": None if bids_sfreq is None else bool(np.isclose(sfreq, float(bids_sfreq))),
        "channel_count_matches_json": None if bids_eeg_count is None else bool(len(raw.ch_names) == int(bids_eeg_count)),
        "all_sample_values_finite": finite_fraction == 1.0,
        "zero_variance_channels_in_sample": zero_var_channels,
        "events_within_recording": None if onset.size == 0 else bool(np.nanmax(onset) <= duration_sec + 1.0),
    }

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset),
        "pilot": {
            "subject": args.subject,
            "session": args.session,
            "run": args.run,
            "derivative": args.derivative,
        },
        "files": {p.suffix: str(p) for p in required},
        "mne_version": mne.__version__,
        "raw": {
            "n_channels": len(raw.ch_names),
            "n_times": int(raw.n_times),
            "sfreq_hz": sfreq,
            "duration_sec": duration_sec,
            "first_channels": raw.ch_names[:10],
            "bads": list(raw.info.get("bads", [])),
            "annotation_count": len(raw.annotations),
            "annotation_descriptions": dict(Counter(raw.annotations.description.tolist())),
        },
        "metadata": {
            "eeg_json": meta,
            "channel_columns": channel_fields,
            "channel_rows": len(channel_rows),
            "channel_type_counts": dict(channel_type_counts),
            "channel_status_counts": dict(channel_status_counts),
            "event_columns": event_fields,
            "event_rows": len(event_rows),
            "trial_type_counts": dict(event_trial_counts),
            "value_counts": dict(event_value_counts),
            "event_onset_min": float(np.nanmin(onset)) if onset.size else None,
            "event_onset_max": float(np.nanmax(onset)) if onset.size else None,
            "event_duration_min": float(np.nanmin(durations)) if durations.size else None,
            "event_duration_max": float(np.nanmax(durations)) if durations.size else None,
        },
        "signal_sample": {
            "requested_seconds": args.sample_seconds,
            "loaded_seconds": sample_stop / sfreq,
            "shape": list(data.shape),
            "finite_fraction": finite_fraction,
            "zero_variance_channels": zero_var_channels,
            "median_channel_std": median_std,
        },
        "checks": checks,
    }

    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# ChineseEEG pilot validation",
        "",
        f"- Pilot: `{args.subject} / {args.session} / {args.run} / {args.derivative}`",
        f"- MNE: `{mne.__version__}`",
        f"- Channels: **{len(raw.ch_names)}**",
        f"- Sampling rate: **{sfreq:g} Hz**",
        f"- Samples: **{raw.n_times:,}**",
        f"- Duration: **{duration_sec / 60:.2f} min**",
        f"- Events TSV rows: **{len(event_rows)}**",
        f"- MNE annotations: **{len(raw.annotations)}**",
        f"- Sample loaded: **{sample_stop / sfreq:.1f} s**",
        f"- Finite sample values: **{finite_fraction:.6f}**",
        f"- Zero-variance channels in sample: **{zero_var_channels}**",
        "",
        "## Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- `{key}`: **{value}**")
    lines += [
        "",
        "## Trial types",
        "",
    ]
    for key, value in event_trial_counts.most_common():
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Annotation descriptions",
        "",
    ]
    for key, value in Counter(raw.annotations.description.tolist()).most_common():
        lines.append(f"- `{key}`: {value}")

    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Validation output: {out}")
    print(f"MNE read OK: {len(raw.ch_names)} channels, {sfreq:g} Hz, {duration_sec/60:.2f} min")
    print(f"Events: {len(event_rows)} | annotations: {len(raw.annotations)}")
    print(f"Sample finite fraction: {finite_fraction:.6f} | zero-var channels: {zero_var_channels}")
    print("Checks:")
    for key, value in checks.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
