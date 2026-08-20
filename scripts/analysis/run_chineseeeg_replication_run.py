#!/usr/bin/env python3
"""Run a prespecified held-out ChineseEEG LittlePrince replication run end to end.

For one run number this script:
1. discovers subjects with materialized filtered BrainVision data and events;
2. validates text/EEG alignment per subject;
3. builds subject-specific manifests;
4. extracts the prespecified row-level neural features;
5. generates pinned BERT embeddings for that run; and
6. runs the pinned nuisance-controlled semantic RSA with the available subjects.

Outputs are run-scoped so later runs cannot silently overwrite or become the "latest"
input for another run. The primary neural representation and semantic target are fixed
from run-01 and are not reselected on replication runs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ALL_SUBJECTS = [
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


def subject_ready(dataset: Path, derivative: str, subject: str, session: str, run_label: str) -> bool:
    prefix = dataset / "derivatives" / derivative / subject / session / "eeg" / f"{subject}_{session}_task-reading_{run_label}"
    required = [
        Path(f"{prefix}_eeg.eeg"),
        Path(f"{prefix}_eeg.vhdr"),
        Path(f"{prefix}_eeg.vmrk"),
        Path(f"{prefix}_events.tsv"),
    ]
    return all(p.exists() for p in required)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run held-out ChineseEEG LittlePrince replication for one run.")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/raw/chineseeeg"))
    parser.add_argument("--run-number", type=int, required=True)
    parser.add_argument("--subjects", nargs="+", default=ALL_SUBJECTS)
    parser.add_argument("--session", default="ses-LittlePrince")
    parser.add_argument("--derivative", default="filtered_0.5_30")
    parser.add_argument("--relative-bins", type=int, default=8)
    parser.add_argument("--onset-ms", type=float, default=500.0)
    parser.add_argument("--permutations", type=int, default=10000)
    args = parser.parse_args()

    if args.run_number < 1:
        raise SystemExit("--run-number must be >= 1")
    if args.permutations < 1000:
        raise SystemExit("--permutations must be >= 1000")

    dataset = args.dataset.expanduser().resolve()
    run_label = f"run-{args.run_number:02d}"
    run_key = run_label
    py = sys.executable

    available = [
        s for s in args.subjects
        if subject_ready(dataset, args.derivative, s, args.session, run_label)
    ]
    unavailable = [s for s in args.subjects if s not in available]

    print(f"Replication run: {run_label}")
    print(f"Available subjects ({len(available)}): {' '.join(available) if available else 'none'}")
    if unavailable:
        print(f"Unavailable/not materialized: {' '.join(unavailable)}")
    if len(available) < 3:
        raise SystemExit("Need at least 3 materialized subjects. Run the targeted retrieval script first.")

    manifest_base = Path("outputs/chineseeeg_pilot_manifest") / run_key
    feature_base = Path("outputs/chineseeeg_row_features") / run_key
    alignment_base = Path("outputs/chineseeeg_text_alignment") / run_key
    embedding_base = Path("outputs/chineseeeg_pinned_embeddings") / run_key
    rsa_base = Path("outputs/chineseeeg_semantic_rsa_pinned") / run_key

    completed: list[str] = []
    failures: list[tuple[str, str]] = []

    for subject in available:
        print(f"\n=== {subject} {run_label} ===", flush=True)
        manifest_root = manifest_base / subject
        feature_root = feature_base / subject
        alignment_root = alignment_base / subject
        try:
            run([
                py, "scripts/audit/validate_chineseeeg_text_alignment.py", str(dataset),
                "--subject", subject,
                "--session", args.session,
                "--run", run_label,
                "--run-number", str(args.run_number),
                "--derivative", args.derivative,
                "--output-dir", str(alignment_root),
            ])
            run([
                py, "scripts/audit/build_chineseeeg_pilot_manifest.py", str(dataset),
                "--subject", subject,
                "--session", args.session,
                "--run", run_label,
                "--run-number", str(args.run_number),
                "--derivative", args.derivative,
                "--output-dir", str(manifest_root),
            ])
            manifest = latest_manifest(manifest_root)
            run([
                py, "scripts/analysis/extract_chineseeeg_row_features.py", str(dataset),
                "--subject", subject,
                "--session", args.session,
                "--run", run_label,
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

    print("\n=== Subject preprocessing summary ===")
    print(f"Completed: {len(completed)}/{len(available)} -> {' '.join(completed) if completed else 'none'}")
    if failures:
        for subject, error in failures:
            print(f"  FAILED {subject}: {error}")
        raise SystemExit("Replication preprocessing had subject failures; semantic RSA not run.")

    run([
        py, "scripts/embeddings/generate_chineseeeg_pinned_embeddings.py", str(dataset),
        "--run-number", str(args.run_number),
        "--output-dir", str(embedding_base),
    ])

    rsa_cmd = [
        py, "scripts/analysis/assess_chineseeeg_semantic_rsa_pinned.py",
        "--embedding-root", str(embedding_base),
        "--feature-root", str(feature_base),
        "--subjects", *completed,
        "--permutations", str(args.permutations),
        "--output-dir", str(rsa_base),
    ]
    run(rsa_cmd)

    print("\nReplication run complete.")
    print(f"Run: {run_label} | subjects: {len(completed)} | permutations: {args.permutations}")
    print("Interpret this as a held-out run using analysis choices fixed before seeing this run's semantic result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
