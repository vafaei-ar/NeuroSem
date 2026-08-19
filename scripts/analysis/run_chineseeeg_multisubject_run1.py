#!/usr/bin/env python3
"""Run ChineseEEG run-01 alignment validation, manifest building, and feature extraction across subjects.

This orchestrator intentionally reuses the existing per-subject scripts so that each subject has
its own timing manifest. It does not assume one participant's event timings apply to another.
Subjects with no tracked/available run for the requested session/run are reported as unavailable,
not treated as processing failures.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_SUBJECTS = [
    "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-09", "sub-10", "sub-13", "sub-14", "sub-15",
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def latest_manifest(root: Path) -> Path:
    matches = sorted(root.glob("*/pilot_manifest.csv"))
    if not matches:
        raise RuntimeError(f"No pilot_manifest.csv created under {root}")
    return matches[-1]


def required_run_files(dataset: Path, derivative: str, subject: str, session: str, run_name: str) -> list[Path]:
    base = (
        dataset / "derivatives" / derivative / subject / session / "eeg"
        / f"{subject}_{session}_task-reading_{run_name}"
    )
    return [
        Path(str(base) + "_eeg.vhdr"),
        Path(str(base) + "_events.tsv"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and extract ChineseEEG LittlePrince run-01 features across subjects.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS)
    parser.add_argument("--session", default="ses-LittlePrince")
    parser.add_argument("--run", default="run-01")
    parser.add_argument("--run-number", type=int, default=1)
    parser.add_argument("--derivative", default="filtered_0.5_30")
    parser.add_argument("--relative-bins", type=int, default=8)
    parser.add_argument("--onset-ms", type=float, default=500.0)
    args = parser.parse_args()

    dataset = args.dataset.expanduser().resolve()
    py = sys.executable

    failures: list[tuple[str, str]] = []
    completed: list[str] = []
    unavailable: list[str] = []

    for subject in args.subjects:
        print(f"\n=== {subject} ===", flush=True)
        required = required_run_files(dataset, args.derivative, subject, args.session, args.run)
        if not any(path.exists() for path in required):
            unavailable.append(subject)
            print(f"UNAVAILABLE {subject}: no {args.session}/{args.run} files in this dataset checkout", flush=True)
            continue
        if not all(path.exists() for path in required):
            missing = [str(path) for path in required if not path.exists()]
            failures.append((subject, "partial/missing required files: " + ", ".join(missing)))
            print(f"FAILED {subject}: partial/missing required files", file=sys.stderr, flush=True)
            continue

        manifest_root = Path("outputs/chineseeeg_pilot_manifest") / subject
        feature_root = Path("outputs/chineseeeg_row_features") / subject
        alignment_root = Path("outputs/chineseeeg_text_alignment") / subject

        try:
            run([
                py, "scripts/audit/validate_chineseeeg_text_alignment.py", str(dataset),
                "--subject", subject,
                "--session", args.session,
                "--run", args.run,
                "--run-number", str(args.run_number),
                "--derivative", args.derivative,
                "--output-dir", str(alignment_root),
            ])

            run([
                py, "scripts/audit/build_chineseeeg_pilot_manifest.py", str(dataset),
                "--subject", subject,
                "--session", args.session,
                "--run", args.run,
                "--run-number", str(args.run_number),
                "--derivative", args.derivative,
                "--output-dir", str(manifest_root),
            ])

            manifest = latest_manifest(manifest_root)

            run([
                py, "scripts/analysis/extract_chineseeeg_row_features.py", str(dataset),
                "--subject", subject,
                "--session", args.session,
                "--run", args.run,
                "--derivative", args.derivative,
                "--manifest", str(manifest),
                "--relative-bins", str(args.relative_bins),
                "--onset-ms", str(args.onset_ms),
                "--output-dir", str(feature_root),
            ])
            completed.append(subject)
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            failures.append((subject, str(exc)))
            print(f"FAILED {subject}: {exc}", file=sys.stderr, flush=True)

    print("\n=== Batch summary ===")
    print(f"Completed: {len(completed)}/{len(args.subjects)} -> {' '.join(completed) if completed else 'none'}")
    if unavailable:
        print(f"Unavailable for requested run: {len(unavailable)} -> {' '.join(unavailable)}")
    if failures:
        print("Failures:")
        for subject, error in failures:
            print(f"  {subject}: {error}")
        return 2

    if len(completed) < 3:
        print("Too few completed subjects for cross-subject reliability.", file=sys.stderr)
        return 3

    print("All available subjects passed alignment/manifest/feature extraction.")
    print("Next: compare row identity/order, channel order, and neural RDM reliability across subjects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
