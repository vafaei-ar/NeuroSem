#!/usr/bin/env python3
"""Cross-run negative-control summary for ChineseEEG semantic RSA.

This script reuses the prespecified within-chapter circular-shift null distributions
already generated for each held-out run. It asks a different question from the exact
run-level sign-flip test: how unusual is the observed mean semantic effect across runs
when exact row identity is broken independently within chapter in every run?

The script does not touch run-07 and does not change the neural representation,
semantic target, nuisance set, or per-run permutation procedure.
"""

from __future__ import annotations

import argparse
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

    # Legacy run-01 layout predates run-scoped output directories.
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

    raise FileNotFoundError(f"No summary found for run-{run_number:02d} under {root}")


def load_run(root: Path, run_number: int, target: str) -> dict:
    summary_path = latest_summary(root, run_number)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if target not in summary.get("observed", {}):
        raise KeyError(f"Target {target} missing in {summary_path}")
    null_path = summary_path.parent / f"{target}_within_chapter_shift_null.npy"
    if not null_path.exists():
        raise FileNotFoundError(f"Null array missing: {null_path}")
    null = np.load(null_path).astype(np.float64)
    if null.ndim != 1 or len(null) < 1000 or not np.isfinite(null).all():
        raise ValueError(f"Invalid null array: {null_path}")
    observed = float(summary["observed"][target]["mean"])
    return {
        "run": f"run-{run_number:02d}",
        "run_number": run_number,
        "summary_path": str(summary_path),
        "null_path": str(null_path),
        "observed": observed,
        "null": null,
        "null_mean": float(null.mean()),
        "null_sd": float(null.std()),
        "null_q95": float(np.quantile(null, 0.95)),
        "null_q99": float(np.quantile(null, 0.99)),
        "empirical_percentile": float(np.mean(null < observed)),
    }


def monte_carlo_crossrun_null(
    records: list[dict], draws: int, seed: int
) -> np.ndarray:
    """Independently sample one valid shifted-null statistic per run and average."""
    rng = np.random.default_rng(seed)
    out = np.empty(draws, dtype=np.float64)
    # Chunking keeps memory bounded even for large --draws values.
    chunk = 10000
    for start in range(0, draws, chunk):
        stop = min(start + chunk, draws)
        n = stop - start
        acc = np.zeros(n, dtype=np.float64)
        for rec in records:
            null = rec["null"]
            idx = rng.integers(0, len(null), size=n)
            acc += null[idx]
        out[start:stop] = acc / len(records)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize within-chapter shift negative controls across ChineseEEG runs."
    )
    parser.add_argument("--runs", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6])
    parser.add_argument(
        "--rsa-root", type=Path, default=Path("outputs/chineseeeg_semantic_rsa_pinned")
    )
    parser.add_argument("--target", choices=["final_mean", "last4_mean"], default="final_mean")
    parser.add_argument("--draws", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=20260821)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/chineseeeg_crossrun_negative_controls")
    )
    args = parser.parse_args()

    if len(args.runs) < 2:
        raise SystemExit("Need at least two runs")
    if len(set(args.runs)) != len(args.runs):
        raise SystemExit("Duplicate run numbers supplied")
    if args.draws < 10000:
        raise SystemExit("--draws must be >= 10000")

    records = [load_run(args.rsa_root, r, args.target) for r in args.runs]
    observed_effects = np.asarray([r["observed"] for r in records], dtype=np.float64)
    observed_mean = float(observed_effects.mean())

    cross_null = monte_carlo_crossrun_null(records, args.draws, args.seed)
    p = float((1 + np.sum(cross_null >= observed_mean)) / (len(cross_null) + 1))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    np.save(out / f"{args.target}_crossrun_shift_null.npy", cross_null)

    serializable_records = []
    for rec in records:
        serializable_records.append({k: v for k, v in rec.items() if k != "null"})

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "runs": [r["run"] for r in records],
        "target": args.target,
        "observed_run_effects": {r["run"]: r["observed"] for r in records},
        "observed_crossrun_mean": observed_mean,
        "n_positive_runs": int(np.sum(observed_effects > 0)),
        "n_runs": len(records),
        "per_run_controls": serializable_records,
        "crossrun_negative_control": {
            "procedure": "independently sample one within-chapter circular-shift null statistic per run, then average across runs",
            "draws": args.draws,
            "seed": args.seed,
            "null_mean": float(cross_null.mean()),
            "null_sd": float(cross_null.std()),
            "null_q95": float(np.quantile(cross_null, 0.95)),
            "null_q99": float(np.quantile(cross_null, 0.99)),
            "p_ge_observed": p,
        },
        "interpretation_notes": [
            "This is a negative-control aggregation of the already-prespecified within-chapter circular-shift nulls, not a new semantic model search.",
            "The test preserves chapter membership within each run while breaking exact row identity.",
            "It complements, rather than replaces, the exact run-level sign-flip test.",
            "Run-07 is not accessed by this script.",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Cross-run negative-control output: {out}")
    print(f"Target: {args.target} | runs: {' '.join(r['run'] for r in records)}")
    print(
        f"Observed cross-run mean={observed_mean:.4f} | positive runs={int(np.sum(observed_effects > 0))}/{len(records)}"
    )
    print(
        "Combined within-chapter-shift null: "
        f"mean={cross_null.mean():.4f} sd={cross_null.std():.4f} "
        f"q95={np.quantile(cross_null, 0.95):.4f} q99={np.quantile(cross_null, 0.99):.4f} "
        f"p={p:.6g}"
    )
    print("Per-run observed percentile under its shift null:")
    for rec in records:
        print(
            f"  {rec['run']}: observed={rec['observed']:.4f} "
            f"null95={rec['null_q95']:.4f} percentile={100 * rec['empirical_percentile']:.1f}%"
        )
    print("Run-07 was not accessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
