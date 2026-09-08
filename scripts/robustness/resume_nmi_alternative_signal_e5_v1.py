#!/usr/bin/env python3
"""Resume the frozen MPNet alternative-signal control after an output-parser failure.

The failed parent run completed all three surrogate trainings and the first seed's
ZuCo and SMN4Lang evaluations. This recovery does not retrain adapters and does not
repeat complete evaluations. It verifies completed outputs against exact adapter
provenance, reuses them, runs only missing seed-target evaluations, and consolidates
all six frozen results.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from pathlib import Path

SEEDS = [20260829, 20260830, 20260831]
TARGETS = ["zuco", "smn4lang_fmri"]
ROOT = Path("outputs/nmi_alternative_signal_e5_v1")
LATEST = ROOT / "latest"
CONTROL_ROOT = Path("outputs/nmi_multiseed_e5_v1")
PROTOCOL = "docs/NMI_ALTERNATIVE_SIGNAL_SURROGATE_V1.md"
EXPECTED_E5_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
FAILED_PARENT_JOB = "H7M4K9R2"
TOTAL_UNITS = len(SEEDS) * len(TARGETS)


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
        "unit": "seed-target evaluations",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def latest_adapter(root: Path) -> Path:
    candidates = sorted(
        [p / "adapter" for p in root.iterdir() if p.is_dir() and (p / "adapter").is_dir()]
    ) if root.exists() else []
    if not candidates:
        raise RuntimeError(f"no adapter under {root}")
    return candidates[-1]


def validate_training_adapter(seed: int, adapter: Path) -> dict:
    summary_path = adapter.parent / "summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(summary_path)
    obj = json.loads(summary_path.read_text(encoding="utf-8"))
    cfg = obj.get("config") or {}
    if obj.get("arm") != "neural":
        raise RuntimeError(f"seed {seed}: surrogate adapter is not neural-arm training output")
    if int(cfg.get("seed", -1)) != seed:
        raise RuntimeError(f"seed {seed}: surrogate adapter seed mismatch")
    if cfg.get("model_revision") != EXPECTED_E5_REVISION:
        raise RuntimeError(f"seed {seed}: surrogate E5 revision mismatch")
    if abs(float(cfg.get("neural_loss_weight", -1)) - 0.10) > 1e-12:
        raise RuntimeError(f"seed {seed}: surrogate lambda mismatch")
    if not cfg.get("postconfirmatory_alternative_signal_control"):
        raise RuntimeError(f"seed {seed}: missing alternative-signal control marker")
    if obj.get("run07_accessed") is not False:
        raise RuntimeError(f"seed {seed}: run-07 access guardrail not satisfied")
    return {
        "seed": seed,
        "adapter": str(adapter.resolve()),
        "training_summary": str(summary_path.resolve()),
        "final_run06_surrogate_corr": obj.get("final_run06_neural_corr"),
    }


def validate_text_adapter(seed: int, adapter: Path) -> dict:
    summary_path = adapter.parent / "summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(summary_path)
    obj = json.loads(summary_path.read_text(encoding="utf-8"))
    cfg = obj.get("config") or {}
    if obj.get("arm") != "text_only" or int(cfg.get("seed", -1)) != seed:
        raise RuntimeError(f"seed {seed}: matched text-only adapter mismatch")
    if cfg.get("model_revision") != EXPECTED_E5_REVISION:
        raise RuntimeError(f"seed {seed}: matched text-only E5 revision mismatch")
    return {
        "seed": seed,
        "adapter": str(adapter.resolve()),
        "training_summary": str(summary_path.resolve()),
    }


def expected_provenance(target: str, text_adapter: Path, surrogate_adapter: Path) -> dict[str, str]:
    if target not in TARGETS:
        raise RuntimeError(target)
    return {
        "lambda_0": str(text_adapter.resolve()),
        "lambda_0p10": str(surrogate_adapter.resolve()),
    }


def load_and_validate_output(
    seed: int,
    target: str,
    summary_path: Path,
    text_adapter: Path,
    surrogate_adapter: Path,
) -> dict:
    obj = json.loads(summary_path.read_text(encoding="utf-8"))
    observed = obj.get("model_provenance") or {}
    expected = expected_provenance(target, text_adapter, surrogate_adapter)
    if observed != expected:
        raise RuntimeError(
            f"seed {seed} {target}: completed output provenance mismatch; "
            f"observed={observed!r}, expected={expected!r}"
        )

    if target == "zuco":
        p = obj.get("primary_result") or {}
        mean_delta = float(p["mean_delta"])
        frac = float(p["fraction_subjects_positive"])
        n_total = int(obj.get("n_frozen_subjects", 17))
        n_positive = int(round(frac * n_total))
        ci = p["bootstrap_95ci"]
        one_sided_p = float((p.get("exact_signflip") or {})["one_sided_greater_p"])
    else:
        mean_delta = float(obj["primary_mean_delta"])
        frac = float(obj["primary_fraction_positive"])
        n_total = int(obj.get("n_subjects", 12))
        n_positive = int(obj["primary_n_positive"])
        ci = obj["primary_bootstrap_95_ci_mean_delta"]
        one_sided_p = float(obj["primary_exact_one_sided_signflip_p"])

    return {
        "seed": seed,
        "target": target,
        "surrogate_minus_text_mean_delta": mean_delta,
        "n_positive": n_positive,
        "n_total": n_total,
        "fraction_positive": frac,
        "ci_low": float(ci[0]),
        "ci_high": float(ci[1]),
        "one_sided_p": one_sided_p,
        "summary_path": str(summary_path.resolve()),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    LATEST.mkdir(parents=True, exist_ok=True)
    atomic_progress(0, "recovery-preflight", "verifying completed surrogate trainings and partial evaluations")

    surrogate_by_seed: dict[int, Path] = {}
    text_by_seed: dict[int, Path] = {}
    surrogate_manifest = []
    text_manifest = []

    for seed in SEEDS:
        surrogate = latest_adapter(ROOT / f"seed_{seed}" / "neural")
        text = latest_adapter(CONTROL_ROOT / f"seed_{seed}" / "text_only")
        surrogate_manifest.append(validate_training_adapter(seed, surrogate))
        text_manifest.append(validate_text_adapter(seed, text))
        surrogate_by_seed[seed] = surrogate
        text_by_seed[seed] = text

    rows: list[dict] = []
    execution_rows: list[dict] = []
    completed = 0

    for seed in SEEDS:
        for target in TARGETS:
            out = ROOT / f"seed_{seed}" / target
            summary_path = out / "summary.json"
            reused = summary_path.is_file()
            if not reused:
                run([
                    ".venv/bin/python",
                    "scripts/robustness/evaluate_external_with_adapters_v1.py",
                    "--dataset", target,
                    "--text-adapter", text_by_seed[seed],
                    "--neural-root", ROOT / f"seed_{seed}" / "neural",
                    "--output-dir", out,
                ])
            row = load_and_validate_output(
                seed, target, summary_path, text_by_seed[seed], surrogate_by_seed[seed]
            )
            rows.append(row)
            execution_rows.append({
                "seed": seed,
                "target": target,
                "reused_completed_output": reused,
                "summary_path": str(summary_path.resolve()),
            })
            completed += 1
            atomic_progress(
                completed,
                "external-evaluation",
                f"{'reused' if reused else 'completed'} {target} for seed {seed}",
            )

    write_csv(LATEST / "seed_target_results.csv", rows)
    write_csv(LATEST / "recovery_execution.csv", execution_rows)

    target_summaries = {}
    for target in TARGETS:
        vals = [r["surrogate_minus_text_mean_delta"] for r in rows if r["target"] == target]
        target_summaries[target] = {
            "seed_mean_deltas": vals,
            "all_three_positive": bool(all(v > 0 for v in vals)),
            "all_three_negative": bool(all(v < 0 for v in vals)),
            "mean_of_seed_mean_deltas": float(sum(vals) / len(vals)),
            "min_seed_mean_delta": float(min(vals)),
            "max_seed_mean_delta": float(max(vals)),
        }

    recovery_manifest = {
        "schema_version": 1,
        "failed_parent_job": FAILED_PARENT_JOB,
        "failure_type": "post-evaluation summary-parser mismatch",
        "scientific_protocol_changed": False,
        "retraining_performed": False,
        "completed_outputs_recomputed": False,
        "surrogate_trainings": surrogate_manifest,
        "matched_text_baselines": text_manifest,
        "evaluation_execution": execution_rows,
    }
    (LATEST / "recovery_manifest.json").write_text(
        json.dumps(recovery_manifest, indent=2) + "\n", encoding="utf-8"
    )

    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory structured non-neural alternative-signal control",
        "protocol": PROTOCOL,
        "recovered_from_failed_job": FAILED_PARENT_JOB,
        "recovery_was_implementation_only": True,
        "retraining_performed": False,
        "alternative_signal": "multilingual-MPNet item-linked nuisance-residualized relational geometry",
        "lambda": 0.10,
        "seeds": SEEDS,
        "all_surrogate_adapters_trained_before_first_external_evaluation": True,
        "results": rows,
        "target_summaries": target_summaries,
        "interpretation_guardrail": (
            "Report all three seeds and both targets. The control tests one frozen structured non-neural "
            "item-linked target and does not establish uniqueness relative to every possible non-neural target."
        ),
    }
    (LATEST / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (LATEST / "report.txt").write_text(
        "NeuroSem MPNet alternative-signal control, recovered after implementation-only parser failure\n\n"
        f"Parent failed job: {FAILED_PARENT_JOB}\n"
        "No surrogate adapter was retrained. Complete prior evaluations were verified and reused.\n"
        f"ZuCo seed mean deltas: {target_summaries['zuco']['seed_mean_deltas']}\n"
        f"SMN4Lang fMRI seed mean deltas: {target_summaries['smn4lang_fmri']['seed_mean_deltas']}\n",
        encoding="utf-8",
    )
    atomic_progress(TOTAL_UNITS, "complete", "all six frozen seed-target outputs consolidated")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
