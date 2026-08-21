#!/usr/bin/env python3
"""Aggregate held-out ChineseEEG semantic RSA results across runs.

This script treats runs as replication units rather than combining per-run p-values.
It reads the latest pinned-RSA summary for each requested run and reports:

1. unweighted mean/median primary effect across runs;
2. exact one-sided sign-flip inference across run-level effects;
3. leave-one-run-out aggregate means;
4. common-subject mean effects across runs and exact one-sided sign-flip inference
   across subjects as a complementary subject-level analysis;
5. the same descriptive summaries for the prespecified last-four-layer sensitivity target.

The run-level sign-flip test is deliberately conservative with few runs. With four
positive runs, the smallest possible one-sided exact p-value is 1/16 = 0.0625.
No Fisher/Stouffer combination of per-run p-values is used because the same subjects
contribute to multiple runs and those p-values are not independent.
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
    candidates = []
    if run_dir.exists():
        for child in run_dir.iterdir():
            p = child / "summary.json"
            if child.is_dir() and p.exists():
                candidates.append(p)
    if not candidates:
        raise FileNotFoundError(f"No pinned-RSA summary found for run-{run_number:02d} under {run_dir}")
    return sorted(candidates)[-1]


def exact_signflip_p(values: np.ndarray) -> tuple[float, np.ndarray]:
    """One-sided exact sign-flip test for mean(values) > 0."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("values must be a finite non-empty vector")
    observed = float(values.mean())
    stats = []
    for signs in itertools.product([-1.0, 1.0], repeat=len(values)):
        stats.append(float(np.mean(values * np.asarray(signs, dtype=float))))
    null = np.asarray(stats, dtype=float)
    p = float(np.mean(null >= observed - 1e-15))
    return p, null


def summarize_target(run_records: list[dict], target: str) -> dict:
    effects = np.asarray([r["summary"]["observed"][target]["mean"] for r in run_records], dtype=float)
    p_run, null_run = exact_signflip_p(effects)

    loo = {}
    for i, r in enumerate(run_records):
        keep = np.delete(effects, i)
        loo[r["run"]] = float(keep.mean()) if len(keep) else float("nan")

    subject_sets = [set(r["summary"]["observed"][target]["by_subject"]) for r in run_records]
    common_subjects = sorted(set.intersection(*subject_sets)) if subject_sets else []
    subject_means = {}
    for subject in common_subjects:
        vals = [float(r["summary"]["observed"][target]["by_subject"][subject]) for r in run_records]
        subject_means[subject] = float(np.mean(vals))

    if common_subjects:
        p_subject, null_subject = exact_signflip_p(np.asarray(list(subject_means.values()), dtype=float))
    else:
        p_subject = float("nan")
        null_subject = np.asarray([], dtype=float)

    return {
        "run_effects": {r["run"]: float(e) for r, e in zip(run_records, effects)},
        "run_mean": float(effects.mean()),
        "run_median": float(np.median(effects)),
        "n_positive_runs": int(np.sum(effects > 0)),
        "n_runs": int(len(effects)),
        "run_exact_signflip_p_one_sided": p_run,
        "run_signflip_null": null_run,
        "leave_one_run_out_means": loo,
        "common_subjects": common_subjects,
        "subject_mean_effects": subject_means,
        "subject_mean": float(np.mean(list(subject_means.values()))) if subject_means else float("nan"),
        "n_positive_subject_means": int(np.sum(np.asarray(list(subject_means.values()), dtype=float) > 0)) if subject_means else 0,
        "n_common_subjects": len(common_subjects),
        "subject_exact_signflip_p_one_sided": p_subject,
        "subject_signflip_null": null_subject,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate pinned ChineseEEG semantic RSA results across held-out runs.")
    parser.add_argument("--runs", nargs="+", type=int, default=[1, 2, 3, 4])
    parser.add_argument("--rsa-root", type=Path, default=Path("outputs/chineseeeg_semantic_rsa_pinned"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_semantic_rsa_crossrun"))
    args = parser.parse_args()

    if len(args.runs) < 2:
        raise SystemExit("Need at least two runs")
    if len(set(args.runs)) != len(args.runs):
        raise SystemExit("Duplicate run numbers supplied")

    run_records = []
    for run_number in args.runs:
        path = latest_summary(args.rsa_root, run_number)
        summary = json.loads(path.read_text(encoding="utf-8"))
        for target in ["final_mean", "last4_mean"]:
            if target not in summary.get("observed", {}):
                raise SystemExit(f"Target {target} missing in {path}")
        run_records.append({
            "run": f"run-{run_number:02d}",
            "run_number": run_number,
            "path": str(path),
            "summary": summary,
        })

    primary = summarize_target(run_records, "final_mean")
    sensitivity = summarize_target(run_records, "last4_mean")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    with (out / "run_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run", "n_subjects", "n_rows", "primary_mean", "primary_p", "sensitivity_mean", "sensitivity_p", "summary_path"])
        for r in run_records:
            s = r["summary"]
            writer.writerow([
                r["run"], s.get("n_subjects"), s.get("n_rows"),
                s["observed"]["final_mean"]["mean"], s["inference"]["final_mean"]["p_ge_observed"],
                s["observed"]["last4_mean"]["mean"], s["inference"]["last4_mean"]["p_ge_observed"],
                r["path"],
            ])

    common = primary["common_subjects"]
    with (out / "common_subject_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["subject", "primary_mean_across_runs", "sensitivity_mean_across_runs"])
        for subject in common:
            writer.writerow([
                subject,
                primary["subject_mean_effects"][subject],
                sensitivity["subject_mean_effects"].get(subject, float("nan")),
            ])

    np.save(out / "primary_run_signflip_null.npy", primary.pop("run_signflip_null"))
    np.save(out / "primary_subject_signflip_null.npy", primary.pop("subject_signflip_null"))
    np.save(out / "sensitivity_run_signflip_null.npy", sensitivity.pop("run_signflip_null"))
    np.save(out / "sensitivity_subject_signflip_null.npy", sensitivity.pop("subject_signflip_null"))

    summary_out = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "runs": [r["run"] for r in run_records],
        "source_summaries": {r["run"]: r["path"] for r in run_records},
        "primary_target": "final_mean",
        "primary": primary,
        "sensitivity_target": "last4_mean",
        "sensitivity": sensitivity,
        "inference_notes": [
            "Runs are treated as replication units; per-run p-values are not combined with Fisher or Stouffer methods.",
            "Run-level inference uses an exact one-sided sign-flip test on run mean effects.",
            "With four runs, the minimum attainable one-sided exact run-level p-value is 0.0625.",
            "Common-subject aggregation is complementary because the same subjects contribute across runs; it does not replace run-level replication inference.",
            "No neural representation, embedding layer, nuisance set, or permutation scheme is selected using these aggregate results.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary_out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Cross-run semantic RSA aggregate output: {out}")
    print(f"Runs: {' '.join(summary_out['runs'])}")
    print(
        "PRIMARY final_mean: "
        f"run mean={primary['run_mean']:.4f} median={primary['run_median']:.4f} | "
        f"positive runs={primary['n_positive_runs']}/{primary['n_runs']} | "
        f"exact run sign-flip p={primary['run_exact_signflip_p_one_sided']:.5g}"
    )
    print("  per run: " + " ".join(f"{k}={v:.4f}" for k, v in primary["run_effects"].items()))
    print(
        "  common-subject aggregate: "
        f"mean={primary['subject_mean']:.4f} | "
        f"positive subjects={primary['n_positive_subject_means']}/{primary['n_common_subjects']} | "
        f"exact subject sign-flip p={primary['subject_exact_signflip_p_one_sided']:.5g}"
    )
    print("  leave-one-run-out means: " + " ".join(f"drop-{k}={v:.4f}" for k, v in primary["leave_one_run_out_means"].items()))
    print(
        "SENSITIVITY last4_mean: "
        f"run mean={sensitivity['run_mean']:.4f} | positive runs={sensitivity['n_positive_runs']}/{sensitivity['n_runs']} | "
        f"exact run sign-flip p={sensitivity['run_exact_signflip_p_one_sided']:.5g}"
    )
    print("Interpret run-level inference as primary; subject-level aggregation is complementary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
