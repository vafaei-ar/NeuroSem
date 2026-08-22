#!/usr/bin/env python3
"""Aggregate ChineseEEG model-panel semantic RSA results across runs.

Treat runs as replication units. Report unweighted mean/median effect, exact one-sided
sign-flip inference across run-level effects, leave-one-run-out means, and common-subject
mean effects with complementary subject-level sign-flip inference.

This script is intended for prespecified model-family screening on runs 01-06 and does
not access run 07 unless it is explicitly requested.
"""

from __future__ import annotations

import argparse
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def latest_summary(root: Path, model_key: str, run_number: int) -> Path:
    run_dir = root / model_key / f"run-{run_number:02d}"
    candidates = []
    if run_dir.exists():
        for child in run_dir.iterdir():
            p = child / "summary.json"
            if child.is_dir() and p.exists():
                candidates.append(p)
    if not candidates:
        raise FileNotFoundError(f"No model-panel summary found under {run_dir}")
    return sorted(candidates)[-1]


def exact_signflip_p(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("values must be a finite non-empty vector")
    observed = float(values.mean())
    stats = []
    for signs in itertools.product([-1.0, 1.0], repeat=len(values)):
        stats.append(float(np.mean(values * np.asarray(signs, dtype=float))))
    null = np.asarray(stats, dtype=float)
    return float(np.mean(null >= observed - 1e-15))


def get_effect(summary: dict) -> float:
    # Model-panel summary stores one semantic target. Support a few possible schemas.
    if "observed" in summary:
        obs = summary["observed"]
        if isinstance(obs, dict):
            if "mean" in obs:
                return float(obs["mean"])
            for key in ("model", "primary", "semantic"):
                if key in obs and isinstance(obs[key], dict) and "mean" in obs[key]:
                    return float(obs[key]["mean"])
    for key in ("mean_partial_spearman", "mean_effect", "effect_mean"):
        if key in summary:
            return float(summary[key])
    raise KeyError("Could not locate run-level mean effect in summary.json")


def get_by_subject(summary: dict) -> dict[str, float]:
    if "observed" in summary and isinstance(summary["observed"], dict):
        obs = summary["observed"]
        if "by_subject" in obs:
            return {k: float(v) for k, v in obs["by_subject"].items()}
        for key in ("model", "primary", "semantic"):
            if key in obs and isinstance(obs[key], dict) and "by_subject" in obs[key]:
                return {k: float(v) for k, v in obs[key]["by_subject"].items()}
    if "by_subject" in summary:
        return {k: float(v) for k, v in summary["by_subject"].items()}
    raise KeyError("Could not locate by-subject effects in summary.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--runs", nargs="+", type=int, required=True)
    parser.add_argument("--rsa-root", type=Path, default=Path("outputs/chineseeeg_model_panel_rsa"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/chineseeeg_model_panel_crossrun"))
    args = parser.parse_args()

    records = []
    for run in args.runs:
        p = latest_summary(args.rsa_root, args.model_key, run)
        summary = json.loads(p.read_text(encoding="utf-8"))
        records.append({"run": f"run-{run:02d}", "path": str(p), "summary": summary})

    effects = np.asarray([get_effect(r["summary"]) for r in records], dtype=float)
    p_run = exact_signflip_p(effects)
    loo = {}
    for i, r in enumerate(records):
        keep = np.delete(effects, i)
        loo[r["run"]] = float(keep.mean()) if len(keep) else float("nan")

    subject_sets = [set(get_by_subject(r["summary"])) for r in records]
    common_subjects = sorted(set.intersection(*subject_sets)) if subject_sets else []
    subject_means = {}
    for subject in common_subjects:
        vals = [get_by_subject(r["summary"])[subject] for r in records]
        subject_means[subject] = float(np.mean(vals))
    subj_vals = np.asarray(list(subject_means.values()), dtype=float)
    p_subject = exact_signflip_p(subj_vals) if len(subj_vals) else float("nan")

    model_ids = []
    revisions = []
    for r in records:
        s = r["summary"]
        for key in ("model_id", "embedding_model", "model"):
            if key in s and isinstance(s[key], str):
                model_ids.append(s[key])
                break
        for key in ("model_revision", "revision"):
            if key in s and isinstance(s[key], str):
                revisions.append(s[key])
                break

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_root / args.model_key / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)

    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_key": args.model_key,
        "model_ids_seen": sorted(set(model_ids)),
        "revisions_seen": sorted(set(revisions)),
        "runs": [r["run"] for r in records],
        "run_effects": {r["run"]: float(e) for r, e in zip(records, effects)},
        "run_mean": float(effects.mean()),
        "run_median": float(np.median(effects)),
        "positive_runs": int(np.sum(effects > 0)),
        "exact_run_signflip_p": p_run,
        "leave_one_run_out_means": loo,
        "common_subjects": common_subjects,
        "subject_means": subject_means,
        "common_subject_mean": float(subj_vals.mean()) if len(subj_vals) else float("nan"),
        "positive_subjects": int(np.sum(subj_vals > 0)) if len(subj_vals) else 0,
        "exact_subject_signflip_p": p_subject,
        "source_summaries": [r["path"] for r in records],
        "note": "Run-level inference is primary; subject-level aggregation is complementary because subjects recur across runs.",
    }
    (out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Model-panel cross-run output: {out}")
    print(f"Model key: {args.model_key} | runs: {' '.join(result['runs'])}")
    print(
        f"Run mean={result['run_mean']:.4f} median={result['run_median']:.4f} | "
        f"positive runs={result['positive_runs']}/{len(effects)} | exact run sign-flip p={p_run:.6g}"
    )
    print("  per run: " + " ".join(f"{k}={v:.4f}" for k, v in result["run_effects"].items()))
    print(
        f"  common-subject aggregate: mean={result['common_subject_mean']:.4f} | "
        f"positive subjects={result['positive_subjects']}/{len(common_subjects)} | p={p_subject:.6g}"
    )
    print("  leave-one-run-out means: " + " ".join(f"drop-{k}={v:.4f}" for k, v in loo.items()))
    if 7 not in args.runs:
        print("Run-07 was not accessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
