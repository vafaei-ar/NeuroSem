#!/usr/bin/env python3
"""Evaluate the one displacement-matched MPNet surrogate on frozen external targets.

This job may run only after the displacement-only grid job has selected exactly one
lambda under the committed protocol. It evaluates the selected three surrogate adapters
once on the unchanged ZuCo and SMN4Lang pipelines and performs the prespecified
participant-level genuine-neural versus matched-surrogate comparison.
"""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import time
from pathlib import Path

import numpy as np

CONFIG = Path("configs/nmi_matched_mpnet_surrogate_v1.json")
GRID_SUMMARY = Path("outputs/nmi_matched_mpnet_surrogate_v1/latest/summary.json")
CONTROL_ROOT = Path("outputs/nmi_multiseed_e5_v1")
ROOT = Path("outputs/nmi_matched_mpnet_external_v1")
LATEST = ROOT / "latest"


def run(cmd: list[object]) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def write_progress(current: int, total: int, phase: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else 0.0,
        "phase": phase,
        "message": message,
        "unit": "external evaluations",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    tmp.replace(p)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def latest_adapter(root: Path) -> Path:
    c = sorted([p / "adapter" for p in root.iterdir() if p.is_dir() and (p / "adapter").is_dir()]) if root.exists() else []
    if not c:
        raise RuntimeError(f"no adapter under {root}")
    return c[-1]


def bootstrap_ci(values: np.ndarray, n_boot: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    n = len(values)
    idx = rng.integers(0, n, size=(n_boot, n))
    means = values[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return [float(lo), float(hi)]


def exact_two_sided_signflip(values: np.ndarray) -> float:
    v = np.asarray(values, dtype=float)
    n = len(v)
    obs = abs(float(np.mean(v)))
    count = 0
    total = 1 << n
    for mask in range(total):
        s = np.ones(n, dtype=float)
        for i in range(n):
            if (mask >> i) & 1:
                s[i] = -1.0
        stat = abs(float(np.mean(s * v)))
        if stat >= obs - 1e-15:
            count += 1
    return float(count / total)


def holm_two(p_a: float, p_b: float) -> tuple[float, float]:
    pairs = sorted([(p_a, 0), (p_b, 1)])
    adj_sorted = [0.0, 0.0]
    running = 0.0
    for rank, (p, _) in enumerate(pairs):
        val = min(1.0, (2 - rank) * p)
        running = max(running, val)
        adj_sorted[rank] = running
    out = [0.0, 0.0]
    for rank, (_, original_index) in enumerate(pairs):
        out[original_index] = adj_sorted[rank]
    return float(out[0]), float(out[1])


def participant_file(dataset: str, root: Path) -> Path:
    return root / ("subject_results.csv" if dataset == "zuco" else "participant_results.csv")


def delta_col() -> str:
    return "delta_0p10_minus_0"


def baseline_col(dataset: str) -> str:
    return "lambda_0_resid_rsa" if dataset == "zuco" else "lambda_0_residual_rsa"


def guided_col(dataset: str) -> str:
    return "lambda_0p10_resid_rsa" if dataset == "zuco" else "lambda_0p10_residual_rsa"


def load_by_subject(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    out = {str(r["subject"]): r for r in rows}
    if len(out) != len(rows):
        raise RuntimeError(f"duplicate subject in {path}")
    return out


def summarize_target(dataset: str, seed_rows: list[dict], cfg: dict) -> tuple[dict, list[dict]]:
    seeds = [int(x) for x in cfg["seeds"]]
    subjects = sorted({r["subject"] for r in seed_rows})
    expected_n = 17 if dataset == "zuco" else 12
    if len(subjects) != expected_n:
        raise RuntimeError(f"{dataset}: expected {expected_n} participants, got {len(subjects)}")
    per_participant = []
    for sub in subjects:
        rows = [r for r in seed_rows if r["subject"] == sub]
        if sorted(int(r["seed"]) for r in rows) != sorted(seeds):
            raise RuntimeError(f"{dataset} {sub}: incomplete seed set")
        genuine = np.asarray([float(r["genuine_delta"]) for r in rows], dtype=float)
        surrogate = np.asarray([float(r["surrogate_delta"]) for r in rows], dtype=float)
        diff = genuine - surrogate
        per_participant.append({
            "target": dataset,
            "subject": sub,
            "genuine_delta_mean_across_seeds": float(np.mean(genuine)),
            "surrogate_delta_mean_across_seeds": float(np.mean(surrogate)),
            "genuine_minus_surrogate_mean_across_seeds": float(np.mean(diff)),
        })
    d = np.asarray([r["genuine_minus_surrogate_mean_across_seeds"] for r in per_participant], dtype=float)
    surr = np.asarray([r["surrogate_delta_mean_across_seeds"] for r in per_participant], dtype=float)
    gen = np.asarray([r["genuine_delta_mean_across_seeds"] for r in per_participant], dtype=float)
    seed = int(cfg["external_inference"]["bootstrap_seed_zuco" if dataset == "zuco" else "bootstrap_seed_smn4lang"])
    n_boot = int(cfg["external_inference"]["bootstrap_n"])
    summary = {
        "target": dataset,
        "n_participants": len(d),
        "primary_estimand": "participant mean across 3 seeds of genuine-neural delta minus matched-surrogate delta",
        "genuine_minus_surrogate_mean": float(np.mean(d)),
        "genuine_minus_surrogate_median": float(np.median(d)),
        "genuine_minus_surrogate_n_positive": int(np.sum(d > 0)),
        "genuine_minus_surrogate_bootstrap_95_ci": bootstrap_ci(d, n_boot, seed),
        "genuine_minus_surrogate_exact_two_sided_signflip_p": exact_two_sided_signflip(d),
        "matched_surrogate_minus_text_mean": float(np.mean(surr)),
        "matched_surrogate_minus_text_n_positive_participant_averaged": int(np.sum(surr > 0)),
        "genuine_minus_text_mean": float(np.mean(gen)),
        "genuine_minus_text_n_positive_participant_averaged": int(np.sum(gen > 0)),
    }
    return summary, per_participant


def main() -> int:
    LATEST.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    grid = json.loads(GRID_SUMMARY.read_text(encoding="utf-8"))
    if grid.get("status") != "ok":
        raise RuntimeError("grid selection status is not ok")
    selected = grid.get("selected_lambda")
    if selected is None or not str(grid.get("selection_status", "")).startswith("within_band"):
        raise RuntimeError("no prespecified displacement-matched surrogate was selected; external evaluation is prohibited")
    if cfg.get("external_outcomes_permitted_during_selection") is not False:
        raise RuntimeError("invalid config guardrail")
    seeds = [int(x) for x in cfg["seeds"]]
    total = len(seeds) * 2
    done = 0
    seed_rows: list[dict] = []

    for seed in seeds:
        text_adapter = latest_adapter(CONTROL_ROOT / f"seed_{seed}" / "text_only")
        selected_info = grid["selected_adapters"].get(str(seed))
        if not selected_info:
            raise RuntimeError(f"missing selected adapter metadata for seed {seed}")
        surrogate_adapter = Path(selected_info["path"])
        surrogate_root = surrogate_adapter.parent.parent
        for dataset in ["zuco", "smn4lang_fmri"]:
            out = ROOT / f"seed_{seed}" / dataset
            run([
                ".venv/bin/python", "scripts/robustness/evaluate_external_with_adapters_v1.py",
                "--dataset", dataset,
                "--text-adapter", text_adapter,
                "--neural-root", surrogate_root,
                "--output-dir", out,
            ])
            genuine_file = participant_file(dataset, CONTROL_ROOT / f"seed_{seed}" / dataset)
            surrogate_file = participant_file(dataset, out)
            genuine = load_by_subject(genuine_file)
            surrogate = load_by_subject(surrogate_file)
            if set(genuine) != set(surrogate):
                raise RuntimeError(f"{dataset} seed {seed}: participant set mismatch")
            for sub in sorted(genuine):
                gr = genuine[sub]
                sr = surrogate[sub]
                base_g = float(gr[baseline_col(dataset)])
                base_s = float(sr[baseline_col(dataset)])
                if not math.isclose(base_g, base_s, rel_tol=0, abs_tol=1e-12):
                    raise RuntimeError(f"{dataset} seed {seed} {sub}: text-only baseline mismatch")
                gd = float(gr[delta_col()])
                sd = float(sr[delta_col()])
                seed_rows.append({
                    "target": dataset,
                    "seed": seed,
                    "subject": sub,
                    "text_only_rsa": base_g,
                    "genuine_guided_rsa": float(gr[guided_col(dataset)]),
                    "matched_surrogate_rsa": float(sr[guided_col(dataset)]),
                    "genuine_delta": gd,
                    "surrogate_delta": sd,
                    "genuine_minus_surrogate": gd - sd,
                })
            done += 1
            write_progress(done, total, "external-evaluation", f"{dataset} seed {seed}")

    target_summaries = []
    participant_rows = []
    for dataset in ["zuco", "smn4lang_fmri"]:
        summary, p_rows = summarize_target(dataset, [r for r in seed_rows if r["target"] == dataset], cfg)
        target_summaries.append(summary)
        participant_rows.extend(p_rows)

    pz = float(target_summaries[0]["genuine_minus_surrogate_exact_two_sided_signflip_p"])
    pf = float(target_summaries[1]["genuine_minus_surrogate_exact_two_sided_signflip_p"])
    hz, hf = holm_two(pz, pf)
    target_summaries[0]["holm_adjusted_p_across_two_targets"] = hz
    target_summaries[1]["holm_adjusted_p_across_two_targets"] = hf

    write_csv(LATEST / "seed_participant_results.csv", seed_rows)
    write_csv(LATEST / "participant_averaged_results.csv", participant_rows)
    write_csv(LATEST / "target_summary.csv", target_summaries)

    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory displacement-matched structured surrogate external evaluation",
        "protocol_document": cfg["protocol_document"],
        "selected_lambda": float(selected),
        "selection_status": grid["selection_status"],
        "seeds": seeds,
        "primary_inference": {
            "unit": "participant",
            "seed_aggregation": "average within participant across the three fixed seeds before inference",
            "contrast": "genuine-neural minus displacement-matched MPNet surrogate",
            "test": "exact two-sided sign-flip separately by target",
            "multiplicity": "Holm correction across ZuCo and SMN4Lang target tests",
            "bootstrap": f"{int(cfg['external_inference']['bootstrap_n'])} participant resamples; percentile 95% CI",
        },
        "targets": target_summaries,
        "interpretation_table": cfg["interpretation_table"],
        "guardrails": {
            "selected_lambda_fixed_before_external_evaluation": True,
            "all_three_selected_adapters_fixed_before_external_evaluation": True,
            "no_checkpoint_search": True,
            "no_seed_exclusion": True,
            "no_target_side_tuning": True,
            "no_rescue_analysis": True,
            "no_surrogate_substitution": True,
        },
    }
    (LATEST / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (LATEST / "report.txt").write_text(
        "NeuroSem displacement-matched MPNet external evaluation\n\n"
        f"Selected lambda: {float(selected):g}\n"
        + "\n".join(
            f"{r['target']}: genuine-surrogate mean={r['genuine_minus_surrogate_mean']:.8g}, "
            f"95% CI={r['genuine_minus_surrogate_bootstrap_95_ci']}, "
            f"n+={r['genuine_minus_surrogate_n_positive']}/{r['n_participants']}, "
            f"exact two-sided p={r['genuine_minus_surrogate_exact_two_sided_signflip_p']:.8g}, "
            f"Holm p={r['holm_adjusted_p_across_two_targets']:.8g}, "
            f"surrogate-text mean={r['matched_surrogate_minus_text_mean']:.8g}"
            for r in target_summaries
        )
        + "\n",
        encoding="utf-8",
    )
    write_progress(total, total, "complete", "matched-surrogate external evaluation complete")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
