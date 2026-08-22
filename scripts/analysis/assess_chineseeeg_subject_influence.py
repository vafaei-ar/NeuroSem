#!/usr/bin/env python3
"""Assess whether ChineseEEG cross-run semantic RSA is driven by any one subject.

For each requested run, read the latest pinned semantic-RSA summary and recompute the
run-level mean after removing each subject in turn. Then aggregate those leave-one-
subject-out run means across runs using the same exact one-sided run sign-flip test
used in the primary cross-run analysis.

This is a robustness analysis, not a new primary hypothesis test. It is intended to
answer whether the positive cross-run result depends disproportionately on a single
participant (for example a consistently high-effect subject).
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def latest_summary(root: Path, run_number: int) -> Path:
    run_dir = root / f"run-{run_number:02d}"
    candidates: list[Path] = []
    if run_dir.exists():
        for child in run_dir.iterdir():
            p = child / "summary.json"
            if child.is_dir() and p.exists():
                candidates.append(p)
    if candidates:
        return sorted(candidates)[-1]

    if run_number == 1 and root.exists():
        legacy: list[Path] = []
        for child in root.iterdir():
            if not child.is_dir() or child.name.startswith("run-"):
                continue
            p = child / "summary.json"
            if p.exists():
                legacy.append(p)
        if legacy:
            return sorted(legacy)[-1]

    raise FileNotFoundError(
        f"No pinned-RSA summary found for run-{run_number:02d} under {run_dir}"
    )


def exact_signflip_p(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("values must be a finite non-empty vector")
    observed = float(values.mean())
    null = []
    for signs in itertools.product([-1.0, 1.0], repeat=len(values)):
        null.append(float(np.mean(values * np.asarray(signs, dtype=float))))
    return float(np.mean(np.asarray(null) >= observed - 1e-15))


def load_runs(root: Path, run_numbers: list[int], target: str) -> list[dict]:
    records = []
    for run_number in run_numbers:
        path = latest_summary(root, run_number)
        summary = json.loads(path.read_text(encoding="utf-8"))
        observed = summary.get("observed", {}).get(target)
        if not observed or "by_subject" not in observed:
            raise SystemExit(f"Missing observed/{target}/by_subject in {path}")
        by_subject = {k: float(v) for k, v in observed["by_subject"].items()}
        if not by_subject:
            raise SystemExit(f"No subject effects in {path}")
        records.append({
            "run": f"run-{run_number:02d}",
            "run_number": run_number,
            "path": str(path),
            "by_subject": by_subject,
            "reported_mean": float(observed["mean"]),
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Leave-one-subject-out robustness for ChineseEEG cross-run semantic RSA."
    )
    parser.add_argument("--runs", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6])
    parser.add_argument(
        "--rsa-root", type=Path, default=Path("outputs/chineseeeg_semantic_rsa_pinned")
    )
    parser.add_argument("--target", default="final_mean", choices=["final_mean", "last4_mean"])
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/chineseeeg_subject_influence")
    )
    args = parser.parse_args()

    if len(args.runs) < 2:
        raise SystemExit("Need at least two runs")
    if len(set(args.runs)) != len(args.runs):
        raise SystemExit("Duplicate run numbers supplied")

    records = load_runs(args.rsa_root, args.runs, args.target)

    # Verify that recomputing the mean from subject effects matches the stored mean.
    for r in records:
        recomputed = float(np.mean(list(r["by_subject"].values())))
        if not np.isclose(recomputed, r["reported_mean"], atol=1e-10, rtol=1e-8):
            raise SystemExit(
                f"Stored/recomputed mean mismatch for {r['run']}: "
                f"stored={r['reported_mean']}, recomputed={recomputed}"
            )

    all_subjects = sorted(set().union(*(set(r["by_subject"]) for r in records)))
    common_subjects = sorted(set.intersection(*(set(r["by_subject"]) for r in records)))

    baseline_effects = np.asarray([r["reported_mean"] for r in records], dtype=float)
    baseline_mean = float(baseline_effects.mean())
    baseline_p = exact_signflip_p(baseline_effects)

    rows = []
    for subject in all_subjects:
        run_effects = []
        runs_present = []
        for r in records:
            values = r["by_subject"]
            if subject not in values:
                # Subject absent from this run: the run mean is unchanged.
                loo_mean = float(np.mean(list(values.values())))
            else:
                kept = [v for s, v in values.items() if s != subject]
                if not kept:
                    raise SystemExit(f"Cannot remove sole subject from {r['run']}")
                loo_mean = float(np.mean(kept))
                runs_present.append(r["run"])
            run_effects.append(loo_mean)

        arr = np.asarray(run_effects, dtype=float)
        rows.append({
            "subject": subject,
            "present_in_all_runs": subject in common_subjects,
            "n_runs_present": len(runs_present),
            "crossrun_mean_after_drop": float(arr.mean()),
            "delta_from_baseline": float(arr.mean() - baseline_mean),
            "positive_runs_after_drop": int(np.sum(arr > 0)),
            "n_runs": len(arr),
            "exact_run_signflip_p_one_sided": exact_signflip_p(arr),
            "run_effects_after_drop": {
                r["run"]: float(v) for r, v in zip(records, arr)
            },
        })

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    with (out / "subject_influence.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "subject", "present_in_all_runs", "n_runs_present",
            "crossrun_mean_after_drop", "delta_from_baseline",
            "positive_runs_after_drop", "n_runs", "exact_run_signflip_p_one_sided",
        ])
        for row in rows:
            writer.writerow([
                row["subject"], row["present_in_all_runs"], row["n_runs_present"],
                row["crossrun_mean_after_drop"], row["delta_from_baseline"],
                row["positive_runs_after_drop"], row["n_runs"],
                row["exact_run_signflip_p_one_sided"],
            ])

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "runs": [r["run"] for r in records],
        "target": args.target,
        "source_summaries": {r["run"]: r["path"] for r in records},
        "baseline": {
            "run_effects": {r["run"]: r["reported_mean"] for r in records},
            "crossrun_mean": baseline_mean,
            "positive_runs": int(np.sum(baseline_effects > 0)),
            "n_runs": len(records),
            "exact_run_signflip_p_one_sided": baseline_p,
        },
        "common_subjects": common_subjects,
        "subject_influence": rows,
        "notes": [
            "This is a robustness analysis, not a replacement for the prespecified primary analysis.",
            "For a subject absent from a run, that run mean is unchanged in that subject's influence calculation.",
            "The same exact one-sided run-level sign-flip test is used after each subject deletion.",
            "A robust result should remain directionally positive and preferably retain all or nearly all positive runs after any single-subject deletion.",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Subject-influence output: {out}")
    print(
        f"Baseline {args.target}: mean={baseline_mean:.4f} | "
        f"positive runs={int(np.sum(baseline_effects > 0))}/{len(records)} | "
        f"exact run sign-flip p={baseline_p:.5g}"
    )
    for row in rows:
        print(
            f"drop {row['subject']}: mean={row['crossrun_mean_after_drop']:.4f} "
            f"delta={row['delta_from_baseline']:+.4f} | "
            f"positive runs={row['positive_runs_after_drop']}/{row['n_runs']} | "
            f"p={row['exact_run_signflip_p_one_sided']:.5g}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
