#!/usr/bin/env python3
"""Train a displacement-only MPNet-surrogate dose grid and select one matched dose.

The selection stage is outcome-blind with respect to ZuCo and SMN4Lang. It reads only:
(1) the frozen structured MPNet source targets and source texts, (2) existing seed-matched
text-only adapters, (3) the committed matched-surrogate config, and (4) the source-side
genuine-displacement calibration. It must not open external neural data or transfer
outcomes. One deterministic displacement-only refinement is allowed by the config.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np

from scripts.robustness.run_nmi_mpnet_model_space_comparison_v1 import (
    compare,
    encode_adapter,
    latest_adapter,
)

CONFIG = Path("configs/nmi_matched_mpnet_surrogate_v1.json")
BASE_CONFIG = Path("configs/e5_neural_tuning_v1.json")
TARGET_ROOT = Path("outputs/nmi_alternative_signal_mpnet_targets_v1/latest")
CONTROL_ROOT = Path("outputs/nmi_multiseed_e5_v1")
CALIBRATION = Path("outputs/nmi_matched_mpnet_calibration_v1/latest/summary.json")
ROOT = Path("outputs/nmi_matched_mpnet_surrogate_v1")
STAGED_TARGET_ROOT = ROOT / "staged_targets"
LATEST = ROOT / "latest"
EXPECTED_E5_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
RUNS = [1, 2, 3, 4, 5, 6]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_sha256(path: Path) -> str:
    h = hashlib.sha256()
    files = sorted(p for p in path.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError(f"no files in adapter directory {path}")
    for p in files:
        rel = p.relative_to(path).as_posix().encode("utf-8")
        h.update(len(rel).to_bytes(4, "big"))
        h.update(rel)
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()


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
        "unit": "train/encoding units",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    tmp.replace(p)


def slug_lambda(v: float) -> str:
    s = f"{v:.8g}".replace(".", "p")
    return s


def load_source_texts() -> list[str]:
    out: list[str] = []
    for run_number in RUNS:
        p = TARGET_ROOT / f"run_{run_number:02d}" / "texts.json"
        obj = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(obj, list) or not obj or not all(isinstance(x, str) for x in obj):
            raise RuntimeError(f"unexpected source text payload: {p}")
        out.extend([x.strip() for x in obj])
    if not out or any(not x for x in out):
        raise RuntimeError("invalid source calibration texts")
    return out


def stage_targets() -> list[dict]:
    source_summary = json.loads((TARGET_ROOT / "summary.json").read_text(encoding="utf-8"))
    if source_summary.get("status") != "ok":
        raise RuntimeError("MPNet target materialization status is not ok")
    if source_summary.get("runs") != RUNS:
        raise RuntimeError("MPNet target run set differs from frozen runs 01-06")
    if not source_summary.get("participant_specific_nuisance_residualization"):
        raise RuntimeError("refusing target without participant-specific nuisance residualization")
    manifest = []
    for run_number in RUNS:
        src = TARGET_ROOT / f"run_{run_number:02d}"
        target = src / "structured_nonneural_target.npy"
        texts = src / "texts.json"
        if not target.is_file() or not texts.is_file():
            raise FileNotFoundError(f"missing materialized target for run {run_number:02d}")
        dst = STAGED_TARGET_ROOT / f"run-{run_number:02d}" / "frozen_mpnet_v1"
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dst / "neural_target.npy")
        shutil.copy2(target, dst / "shuffled_neural_target.npy")
        shutil.copy2(texts, dst / "texts.json")
        if sha256(target) != sha256(dst / "neural_target.npy"):
            raise RuntimeError(f"staged target hash mismatch for run {run_number:02d}")
        manifest.append({
            "run": run_number,
            "target_sha256": sha256(target),
            "texts_sha256": sha256(texts),
        })
    return manifest


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def validate_config(cfg: dict, calibration: dict) -> None:
    if cfg.get("schema_version") != 1:
        raise RuntimeError("unexpected matched-surrogate config schema")
    if cfg.get("model_revision") != EXPECTED_E5_REVISION:
        raise RuntimeError("E5 revision mismatch")
    if cfg.get("seeds") != [20260829, 20260830, 20260831]:
        raise RuntimeError("seed set mismatch")
    if cfg.get("calibration_stimulus_set") != "ChineseEEG source runs 01-06 canonical texts":
        raise RuntimeError("unexpected calibration stimulus set")
    if cfg.get("primary_displacement_metric") != "1-linear-centered-CKA":
        raise RuntimeError("unexpected primary displacement metric")
    if cfg.get("external_outcomes_permitted_during_selection") is not False:
        raise RuntimeError("config must prohibit external outcomes during selection")
    expected_sha = cfg.get("calibration_summary_sha256")
    if expected_sha != sha256(CALIBRATION):
        raise RuntimeError("calibration summary hash differs from committed config")
    for key in ["genuine_mean_delta", "tolerance_half_width", "tolerance_low", "tolerance_high"]:
        if key not in cfg:
            raise RuntimeError(f"missing config key {key}")
    if not math.isclose(float(cfg["genuine_mean_delta"]), float(calibration["mean_delta"]), rel_tol=0, abs_tol=1e-15):
        raise RuntimeError("genuine mean delta does not match calibration")
    if cfg.get("dose_grid") is None or len(cfg["dose_grid"]) < 2:
        raise RuntimeError("dose grid missing")


def train_one(lam: float, seed: int, cfg0: dict, protocol: str) -> Path:
    seed_root = ROOT / f"lambda_{slug_lambda(lam)}" / f"seed_{seed}"
    seed_root.mkdir(parents=True, exist_ok=True)
    cfg = dict(cfg0)
    cfg["seed"] = seed
    cfg["postconfirmatory_matched_surrogate"] = True
    cfg["matched_surrogate_protocol"] = protocol
    cfg["matched_surrogate_lambda"] = lam
    cfg_path = seed_root / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    run([
        ".venv/bin/python", "scripts/tuning/train_e5_neurosem_lora.py",
        "--arm", "neural", "--config", cfg_path,
        "--target-root", STAGED_TARGET_ROOT,
        "--output-dir", seed_root,
        "--device", "auto",
        "--neural-loss-weight", str(lam),
    ])
    return latest_adapter(seed_root / "neural")


def encode_grid(lams: list[float], seeds: list[int], texts: list[str], adapters: dict[tuple[float, int], Path], progress: list[int], total_ref: list[int]) -> list[dict]:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    text_embeddings: dict[int, np.ndarray] = {}
    rows: list[dict] = []
    for seed in seeds:
        ta = latest_adapter(CONTROL_ROOT / f"seed_{seed}" / "text_only")
        text_embeddings[seed] = encode_adapter(ta, texts, device)
        progress[0] += 1
        write_progress(progress[0], total_ref[0], "encode", f"text-only source encoding seed {seed}")
    for lam in lams:
        for seed in seeds:
            sa = adapters[(lam, seed)]
            es = encode_adapter(sa, texts, device)
            metrics = compare(text_embeddings[seed], es)
            cka = float(metrics["linear_centered_cka"])
            rows.append({
                "lambda": lam,
                "seed": seed,
                "surrogate_adapter": str(sa),
                "surrogate_adapter_sha256": dir_sha256(sa),
                **metrics,
                "delta_1_minus_cka": 1.0 - cka,
            })
            progress[0] += 1
            write_progress(progress[0], total_ref[0], "encode", f"surrogate source encoding lambda={lam:g} seed {seed}")
    return rows


def summarize_lambdas(rows: list[dict], lams: list[float]) -> list[dict]:
    out = []
    for lam in sorted(lams):
        vals = [float(r["delta_1_minus_cka"]) for r in rows if math.isclose(float(r["lambda"]), lam)]
        out.append({
            "lambda": lam,
            "seed_delta_values": vals,
            "mean_delta": float(np.mean(vals)),
            "min_delta": float(np.min(vals)),
            "max_delta": float(np.max(vals)),
        })
    return out


def select_match(summary_rows: list[dict], cfg: dict) -> tuple[float | None, str]:
    lo = float(cfg["tolerance_low"])
    hi = float(cfg["tolerance_high"])
    g = float(cfg["genuine_mean_delta"])
    matched = [r for r in summary_rows if lo <= float(r["mean_delta"]) <= hi]
    if not matched:
        return None, "none"
    matched.sort(key=lambda r: (abs(math.log(float(r["mean_delta"]) / g)), float(r["lambda"])))
    return float(matched[0]["lambda"]), "within_band"


def choose_extension(summary_rows: list[dict], cfg: dict) -> tuple[float | None, str]:
    lo = float(cfg["tolerance_low"])
    hi = float(cfg["tolerance_high"])
    ordered = sorted(summary_rows, key=lambda r: float(r["lambda"]))
    means = [float(r["mean_delta"]) for r in ordered]
    lams = [float(r["lambda"]) for r in ordered]
    if all(v < lo for v in means):
        return lams[-1] * 2.0, "outward_high"
    if all(v > hi for v in means):
        return lams[0] / 2.0, "outward_low"
    for i in range(len(ordered) - 1):
        a, b = means[i], means[i + 1]
        if a < lo and b > hi:
            return math.sqrt(lams[i] * lams[i + 1]), "log_midpoint_bracket"
        if a > hi and b < lo:
            return math.sqrt(lams[i] * lams[i + 1]), "log_midpoint_bracket"
    return None, "no_deterministic_extension_case"


def main() -> int:
    LATEST.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    validate_config(cfg, calibration)
    cfg0 = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    if cfg0.get("model_revision") != EXPECTED_E5_REVISION:
        raise RuntimeError("base E5 config revision mismatch")
    target_manifest = stage_targets()
    texts = load_source_texts()
    seeds = [int(x) for x in cfg["seeds"]]
    grid = [float(x) for x in cfg["dose_grid"]]
    protocol = str(cfg["protocol_document"])
    adapters: dict[tuple[float, int], Path] = {}

    max_units = len(grid) * len(seeds) * 2 + len(seeds)
    progress = [0]
    total_ref = [max_units]
    write_progress(0, total_ref[0], "train", "starting prespecified surrogate grid")

    for lam in grid:
        for seed in seeds:
            adapters[(lam, seed)] = train_one(lam, seed, cfg0, protocol)
            progress[0] += 1
            write_progress(progress[0], total_ref[0], "train", f"trained lambda={lam:g} seed {seed}")

    metric_rows = encode_grid(grid, seeds, texts, adapters, progress, total_ref)
    lambda_rows = summarize_lambdas(metric_rows, grid)
    selected, selection_status = select_match(lambda_rows, cfg)
    extension = None

    if selected is None and bool(cfg["one_extension"]["allowed"]):
        ext_lambda, ext_reason = choose_extension(lambda_rows, cfg)
        if ext_lambda is not None:
            if any(math.isclose(ext_lambda, x, rel_tol=0, abs_tol=1e-15) for x in grid):
                raise RuntimeError("extension duplicated an existing grid point")
            extension = {"lambda": ext_lambda, "reason": ext_reason}
            total_ref[0] += len(seeds) * 3
            for seed in seeds:
                adapters[(ext_lambda, seed)] = train_one(ext_lambda, seed, cfg0, protocol)
                progress[0] += 1
                write_progress(progress[0], total_ref[0], "train-extension", f"trained extension lambda={ext_lambda:g} seed {seed}")
            ext_rows = encode_grid([ext_lambda], seeds, texts, adapters, progress, total_ref)
            metric_rows.extend(ext_rows)
            grid.append(ext_lambda)
            lambda_rows = summarize_lambdas(metric_rows, grid)
            selected, selection_status = select_match(lambda_rows, cfg)
            if selected is None:
                selection_status = "no_match_after_one_extension"
        else:
            selection_status = "no_match_no_permitted_extension_case"

    write_csv(LATEST / "seed_displacement_metrics.csv", metric_rows)
    with (LATEST / "lambda_displacement_summary.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["lambda", "mean_delta", "min_delta", "max_delta", "seed_delta_values"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in lambda_rows:
            w.writerow({**r, "seed_delta_values": json.dumps(r["seed_delta_values"])})

    selected_adapters = {}
    if selected is not None:
        for seed in seeds:
            p = adapters[(selected, seed)]
            selected_adapters[str(seed)] = {"path": str(p), "sha256": dir_sha256(p)}

    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory displacement-only matched-surrogate selection",
        "protocol_document": protocol,
        "config_path": str(CONFIG),
        "config_sha256": sha256(CONFIG),
        "calibration_summary_path": str(CALIBRATION),
        "calibration_summary_sha256": sha256(CALIBRATION),
        "calibration_stimulus_set": cfg["calibration_stimulus_set"],
        "n_calibration_items": len(texts),
        "primary_displacement_metric": cfg["primary_displacement_metric"],
        "genuine_mean_delta": float(cfg["genuine_mean_delta"]),
        "tolerance_band": [float(cfg["tolerance_low"]), float(cfg["tolerance_high"])],
        "initial_grid": [float(x) for x in cfg["dose_grid"]],
        "extension": extension,
        "lambda_summaries": lambda_rows,
        "selection_status": selection_status,
        "selected_lambda": selected,
        "selected_adapters": selected_adapters,
        "target_manifest": target_manifest,
        "guardrails": {
            "external_target_stimuli_read": False,
            "external_neural_data_read": False,
            "external_transfer_outcomes_read": False,
            "selection_uses_displacement_only": True,
            "one_common_lambda_across_seeds": True,
            "max_one_extension": True,
        },
    }
    (LATEST / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (LATEST / "training_manifest.json").write_text(json.dumps({
        "config_sha256": sha256(CONFIG),
        "protocol_document": protocol,
        "target_manifest": target_manifest,
        "adapter_count": len(adapters),
        "adapter_hashes": {
            f"lambda={lam:g}/seed={seed}": {"path": str(p), "sha256": dir_sha256(p)}
            for (lam, seed), p in sorted(adapters.items())
        },
    }, indent=2) + "\n", encoding="utf-8")
    (LATEST / "report.txt").write_text(
        "NeuroSem displacement-matched MPNet surrogate selection\n\n"
        f"Genuine mean 1-CKA: {float(cfg['genuine_mean_delta']):.10g}\n"
        f"Tolerance band: [{float(cfg['tolerance_low']):.10g}, {float(cfg['tolerance_high']):.10g}]\n"
        f"Initial grid: {cfg['dose_grid']}\n"
        f"Extension: {extension}\n"
        f"Selection status: {selection_status}\n"
        f"Selected lambda: {selected}\n"
        "No ZuCo/SMN4Lang stimuli, neural data, or transfer outcomes were read during selection.\n",
        encoding="utf-8",
    )
    write_progress(total_ref[0], total_ref[0], "complete", f"matched-surrogate selection complete: {selection_status}")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
