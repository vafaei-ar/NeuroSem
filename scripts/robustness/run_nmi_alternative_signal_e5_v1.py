#!/usr/bin/env python3
"""Train and evaluate the frozen structured-non-neural MPNet control.

All three surrogate adapters are trained before any surrogate external outcome is opened.
The matched text-only adapters are reused from the completed E5 multi-seed analysis.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

SEEDS = [20260829, 20260830, 20260831]
TARGET_RUNS = [1, 2, 3, 4, 5, 6]
BASE_CONFIG = Path("configs/e5_neural_tuning_v1.json")
TARGET_ROOT = Path("outputs/nmi_alternative_signal_mpnet_targets_v1/latest")
CONTROL_ROOT = Path("outputs/nmi_multiseed_e5_v1")
ROOT = Path("outputs/nmi_alternative_signal_e5_v1")
STAGED_TARGET_ROOT = ROOT / "staged_targets"
LATEST = ROOT / "latest"
PROTOCOL = "docs/NMI_ALTERNATIVE_SIGNAL_SURROGATE_V1.md"
EXPECTED_E5_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
LAMBDA = 0.10
TOTAL_UNITS = 9  # 3 trainings + 6 external evaluations


def run(cmd: list[object]) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def atomic_progress(current: int, phase: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": TOTAL_UNITS,
        "fraction": current / TOTAL_UNITS,
        "phase": phase,
        "message": message,
        "unit": "train/evaluation units",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_adapter(root: Path) -> Path:
    candidates = sorted(
        [p / "adapter" for p in root.iterdir() if p.is_dir() and (p / "adapter").is_dir()]
    ) if root.exists() else []
    if not candidates:
        raise RuntimeError(f"no adapter under {root}")
    return candidates[-1]


def stage_targets() -> list[dict]:
    source_summary = json.loads((TARGET_ROOT / "summary.json").read_text(encoding="utf-8"))
    if source_summary.get("status") != "ok":
        raise RuntimeError("MPNet target materialization status is not ok")
    if source_summary.get("runs") != TARGET_RUNS:
        raise RuntimeError("MPNet target run set differs from frozen runs 01-06")
    if not source_summary.get("participant_specific_nuisance_residualization"):
        raise RuntimeError("refusing target without participant-specific nuisance residualization")

    manifest = []
    for run_number in TARGET_RUNS:
        src = TARGET_ROOT / f"run_{run_number:02d}"
        target = src / "structured_nonneural_target.npy"
        texts = src / "texts.json"
        if not target.is_file() or not texts.is_file():
            raise FileNotFoundError(f"missing materialized target for run {run_number:02d}")
        dst = STAGED_TARGET_ROOT / f"run-{run_number:02d}" / "frozen_mpnet_v1"
        dst.mkdir(parents=True, exist_ok=True)
        # The established trainer expects these historical filenames. Both point to the
        # same frozen alternative target; only the neural arm is invoked in this job.
        shutil.copy2(target, dst / "neural_target.npy")
        shutil.copy2(target, dst / "shuffled_neural_target.npy")
        shutil.copy2(texts, dst / "texts.json")
        row = {
            "run": run_number,
            "source_target": str(target),
            "source_target_sha256": sha256(target),
            "staged_neural_target_sha256": sha256(dst / "neural_target.npy"),
            "texts_sha256": sha256(texts),
        }
        if row["source_target_sha256"] != row["staged_neural_target_sha256"]:
            raise RuntimeError(f"staged target hash mismatch for run {run_number:02d}")
        manifest.append(row)
    return manifest


def get_primary(summary_path: Path) -> dict:
    obj = json.loads(summary_path.read_text(encoding="utf-8"))
    return obj.get("primary_result", obj)


def first_present(d: dict, keys: list[str], default=None):
    for key in keys:
        if key in d and d[key] is not None:
            return d[key]
    return default


def summarize_external(seed: int, target: str, summary_path: Path) -> dict:
    p = get_primary(summary_path)
    mean_delta = float(first_present(p, ["mean_delta", "mean_participant_delta"]))
    frac = first_present(p, ["fraction_subjects_positive", "fraction_participants_positive"])
    n_pos = first_present(p, ["n_subjects_positive", "n_participants_positive", "positive_subjects", "positive_participants"])
    ci = first_present(p, ["bootstrap_ci_95", "bootstrap_95_ci", "ci_95", "participant_bootstrap_ci"])
    ci_low = ci_high = None
    if isinstance(ci, (list, tuple)) and len(ci) == 2:
        ci_low, ci_high = float(ci[0]), float(ci[1])
    return {
        "seed": seed,
        "target": target,
        "surrogate_minus_text_mean_delta": mean_delta,
        "fraction_positive": None if frac is None else float(frac),
        "n_positive": n_pos,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "summary_path": str(summary_path),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    LATEST.mkdir(parents=True, exist_ok=True)
    atomic_progress(0, "preflight", "verifying frozen targets and matched baselines")

    target_manifest = stage_targets()
    cfg0 = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    if cfg0.get("model_revision") != EXPECTED_E5_REVISION:
        raise RuntimeError("E5 revision differs from frozen alternative-signal protocol")

    resolved = []
    for seed in SEEDS:
        text_adapter = latest_adapter(CONTROL_ROOT / f"seed_{seed}" / "text_only")
        train_summary = text_adapter.parent / "summary.json"
        if not train_summary.is_file():
            raise FileNotFoundError(f"missing text-only training summary for seed {seed}")
        text_meta = json.loads(train_summary.read_text(encoding="utf-8"))
        if int(text_meta["config"]["seed"]) != seed:
            raise RuntimeError(f"text-only seed mismatch for {seed}")
        if text_meta["config"].get("model_revision") != EXPECTED_E5_REVISION:
            raise RuntimeError(f"text-only E5 revision mismatch for {seed}")
        resolved.append({"seed": seed, "text_adapter": str(text_adapter), "text_summary": str(train_summary)})

    # Train every surrogate adapter first. No surrogate ZuCo/fMRI result is opened before
    # all three optimization trajectories have completed.
    surrogate_adapters: dict[int, Path] = {}
    done = 0
    for seed in SEEDS:
        seed_root = ROOT / f"seed_{seed}"
        seed_root.mkdir(parents=True, exist_ok=True)
        cfg = dict(cfg0)
        cfg["seed"] = seed
        cfg["postconfirmatory_alternative_signal_control"] = True
        cfg["alternative_signal_protocol"] = PROTOCOL
        cfg_path = seed_root / "config.json"
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        run([
            ".venv/bin/python", "scripts/tuning/train_e5_neurosem_lora.py",
            "--arm", "neural", "--config", cfg_path,
            "--target-root", STAGED_TARGET_ROOT,
            "--output-dir", seed_root, "--device", "auto",
            "--neural-loss-weight", str(LAMBDA),
        ])
        surrogate_adapters[seed] = latest_adapter(seed_root / "neural")
        done += 1
        atomic_progress(done, "train-surrogate", f"trained surrogate adapter seed {seed}")

    rows = []
    for seed in SEEDS:
        seed_root = ROOT / f"seed_{seed}"
        text_adapter = Path(next(r["text_adapter"] for r in resolved if r["seed"] == seed))
        surrogate_root = seed_root / "neural"
        for target in ["zuco", "smn4lang_fmri"]:
            out = seed_root / target
            run([
                ".venv/bin/python", "scripts/robustness/evaluate_external_with_adapters_v1.py",
                "--dataset", target,
                "--text-adapter", text_adapter,
                "--neural-root", surrogate_root,
                "--output-dir", out,
            ])
            rows.append(summarize_external(seed, target, out / "summary.json"))
            done += 1
            atomic_progress(done, "external-evaluation", f"completed {target} evaluation for seed {seed}")

    write_csv(LATEST / "seed_target_results.csv", rows)
    (LATEST / "training_manifest.json").write_text(json.dumps({
        "protocol": PROTOCOL,
        "lambda": LAMBDA,
        "seeds": SEEDS,
        "target_materialization_summary": str(TARGET_ROOT / "summary.json"),
        "target_manifest": target_manifest,
        "matched_text_baselines": resolved,
        "surrogate_adapters": {str(k): str(v) for k, v in surrogate_adapters.items()},
        "all_surrogate_adapters_trained_before_external_evaluation": True,
    }, indent=2) + "\n", encoding="utf-8")

    by_target = {}
    for target in ["zuco", "smn4lang_fmri"]:
        vals = [r["surrogate_minus_text_mean_delta"] for r in rows if r["target"] == target]
        by_target[target] = {
            "seed_mean_deltas": vals,
            "all_three_positive": bool(all(v > 0 for v in vals)),
            "mean_of_seed_mean_deltas": float(sum(vals) / len(vals)),
            "min_seed_mean_delta": float(min(vals)),
            "max_seed_mean_delta": float(max(vals)),
        }

    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory structured non-neural alternative-signal control",
        "protocol": PROTOCOL,
        "alternative_signal": "multilingual-MPNet item-linked nuisance-residualized relational geometry",
        "lambda": LAMBDA,
        "seeds": SEEDS,
        "all_surrogate_adapters_trained_before_external_evaluation": True,
        "results": rows,
        "target_summaries": by_target,
        "interpretation_guardrail": (
            "Report all seeds and both targets descriptively. This analysis tests whether one frozen structured "
            "non-neural item-linked target can reproduce external transfer; it does not establish uniqueness "
            "relative to all possible non-neural relational targets."
        ),
    }
    (LATEST / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (LATEST / "report.txt").write_text(
        "NeuroSem structured non-neural MPNet surrogate control\n\n"
        f"Seeds: {SEEDS}\nLambda: {LAMBDA}\n"
        "All three surrogate adapters were trained before any surrogate external outcome was evaluated.\n"
        f"ZuCo seed mean deltas: {by_target['zuco']['seed_mean_deltas']}\n"
        f"SMN4Lang fMRI seed mean deltas: {by_target['smn4lang_fmri']['seed_mean_deltas']}\n",
        encoding="utf-8",
    )
    atomic_progress(TOTAL_UNITS, "complete", "all frozen surrogate train/evaluation units completed")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
