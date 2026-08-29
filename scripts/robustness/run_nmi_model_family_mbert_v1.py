#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

SEEDS = [20260829, 20260830, 20260831]
BASE_CONFIG = Path("configs/mbert_model_family_robustness_v1.json")
ROOT = Path("outputs/nmi_model_family_mbert_v1")


def run(cmd: list[object]) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def latest_adapter(root: Path) -> Path:
    candidates = sorted([p / "adapter" for p in root.iterdir() if p.is_dir() and (p / "adapter").is_dir()]) if root.exists() else []
    if not candidates:
        raise RuntimeError(f"no adapter under {root}")
    return candidates[-1]


def report_progress(current: int, total: int, phase: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": max(0.0, min(1.0, current / total)) if total > 0 else None,
        "phase": phase,
        "message": message,
        "unit": "seeds",
        "updated_at_epoch": time.time(),
    }
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    if base.get("prespecified_seeds") != SEEDS:
        raise RuntimeError("seed freeze mismatch")
    if float(base.get("neural_loss_weight")) != 0.10:
        raise RuntimeError("strict lambda freeze mismatch")

    rows = []
    report_progress(0, len(SEEDS), "Second-model-family robustness", "Starting prespecified multilingual-BERT seeds")

    for idx, seed in enumerate(SEEDS, start=1):
        print(f"=== post-confirmatory mBERT seed {idx}/{len(SEEDS)}: {seed} ===", flush=True)
        seed_root = ROOT / f"seed_{seed}"
        seed_root.mkdir(parents=True, exist_ok=True)
        cfg = dict(base)
        cfg["seed"] = seed
        cfg_path = seed_root / "config.json"
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

        run([".venv/bin/python", "scripts/tuning/train_bert_neurosem_lora.py", "--arm", "text_only", "--config", cfg_path, "--output-dir", seed_root, "--device", "auto"])
        run([".venv/bin/python", "scripts/tuning/train_bert_neurosem_lora.py", "--arm", "neural", "--config", cfg_path, "--output-dir", seed_root, "--device", "auto"])

        text_adapter = latest_adapter(seed_root / "text_only")
        neural_root = seed_root / "neural"
        zuco_out = seed_root / "zuco"
        fmri_out = seed_root / "smn4lang_fmri"

        run([".venv/bin/python", "scripts/robustness/evaluate_external_with_mbert_adapters_v1.py", "--dataset", "zuco", "--text-adapter", text_adapter, "--neural-root", neural_root, "--output-dir", zuco_out])
        run([".venv/bin/python", "scripts/robustness/evaluate_external_with_mbert_adapters_v1.py", "--dataset", "smn4lang_fmri", "--text-adapter", text_adapter, "--neural-root", neural_root, "--output-dir", fmri_out])

        z = json.loads((zuco_out / "summary.json").read_text(encoding="utf-8"))["primary_result"]
        f = json.loads((fmri_out / "summary.json").read_text(encoding="utf-8"))
        text_summary = json.loads((text_adapter.parent / "summary.json").read_text(encoding="utf-8"))
        neural_adapter = latest_adapter(neural_root)
        neural_summary = json.loads((neural_adapter.parent / "summary.json").read_text(encoding="utf-8"))

        rows.append({
            "seed": seed,
            "source_run06_text_only_corr": float(text_summary["final_run06_neural_corr"]),
            "source_run06_neural_corr": float(neural_summary["final_run06_neural_corr"]),
            "zuco_mean_delta": float(z["mean_delta"]),
            "zuco_fraction_positive": float(z["fraction_subjects_positive"]),
            "zuco_bootstrap_95ci": z["bootstrap_95ci"],
            "zuco_exact_one_sided_p": float(z["exact_signflip"]["one_sided_greater_p"]),
            "smn4lang_fmri_mean_delta": float(f["primary_mean_delta"]),
            "smn4lang_fmri_fraction_positive": float(f["primary_fraction_positive"]),
            "smn4lang_fmri_bootstrap_95ci": f["primary_bootstrap_95_ci_mean_delta"],
            "smn4lang_fmri_exact_one_sided_p": float(f["primary_exact_one_sided_signflip_p"]),
        })
        report_progress(idx, len(SEEDS), "Second-model-family robustness", f"Completed prespecified seed {idx} of {len(SEEDS)}")

    payload = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory second-model-family robustness",
        "protocol": "docs/16_NMI_SECOND_MODEL_FAMILY_MBBERT_PROTOCOL_V1.md",
        "model_id": base["model_id"],
        "model_revision": base["model_revision"],
        "lambda": 0.10,
        "seeds": SEEDS,
        "results": rows,
        "summary": {
            "zuco_all_seed_mean_deltas_positive": bool(all(r["zuco_mean_delta"] > 0 for r in rows)),
            "smn4lang_fmri_all_seed_mean_deltas_positive": bool(all(r["smn4lang_fmri_mean_delta"] > 0 for r in rows)),
            "zuco_mean_of_seed_mean_deltas": float(sum(r["zuco_mean_delta"] for r in rows) / len(rows)),
            "smn4lang_fmri_mean_of_seed_mean_deltas": float(sum(r["smn4lang_fmri_mean_delta"] for r in rows) / len(rows)),
        },
        "guardrail": "All prespecified seeds and both frozen external targets are reported. No rescue tuning is permitted. Results are post-confirmatory model-family robustness, not prospective confirmation."
    }
    latest = ROOT / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
