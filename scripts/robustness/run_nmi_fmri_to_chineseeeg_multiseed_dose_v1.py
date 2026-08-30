#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from scripts.robustness import run_nmi_bidirectional_fmri_source_calibration_v1 as cal
from scripts.robustness import evaluate_nmi_bidirectional_fmri_eeg_dose_response_v1 as dose

SEEDS = [20260829, 20260830, 20260831]
LAMBDAS = list(cal.LAMBDAS)
POSITIVE = [x for x in LAMBDAS if x > 0]
LAMBDA_DIR = {0.0: "lambda_0p0", 0.01: "lambda_0p01", 0.03: "lambda_0p03", 0.10: "lambda_0p1", 0.30: "lambda_0p3", 1.0: "lambda_1p0"}
OUT = Path("outputs/nmi_fmri_to_chineseeeg_multiseed_dose_v1/latest").resolve()


def report_progress(current: int, total: int, phase: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total,
        "phase": phase,
        "unit": "seed-lambda stages",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def train_seed(seed: int, out: Path, progress_base: int) -> dict:
    import torch
    from transformers import AutoModel, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from torch.optim import AdamW
    from scripts.analysis.run_smn4lang_fmri_reliability import TR, canonical_hrf
    from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import story_context

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        raise RuntimeError("GPU required")

    source = Path("outputs/nmi_bidirectional_fmri_source_v1/latest")
    if not (source / "summary.json").exists():
        raise FileNotFoundError(source / "summary.json")

    root = Path("data/raw/smn4lang").resolve()
    hrf = canonical_hrf(TR)
    needed = sorted(set(cal.TRAIN_STORIES + cal.VAL_STORIES))
    contexts = {s: story_context(root, s, hrf) for s in needed}
    targets = {}
    for s in needed:
        p = source / "targets" / f"story_{s:02d}.npz"
        if not p.exists():
            raise FileNotFoundError(p)
        targets[s] = np.load(p)["target"].astype(np.float32)

    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for li, lam in enumerate(LAMBDAS, 1):
        cal.set_seed(seed)
        tok = AutoTokenizer.from_pretrained(cal.MODEL_ID, revision=cal.MODEL_REVISION)
        base = AutoModel.from_pretrained(cal.MODEL_ID, revision=cal.MODEL_REVISION)
        model = get_peft_model(
            base,
            LoraConfig(r=8, lora_alpha=16, lora_dropout=.05, target_modules=["query", "value"], bias="none"),
        )
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        if hasattr(model, "enable_input_require_grads"):
            model.enable_input_require_grads()
        model.to(device)
        opt = AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4, weight_decay=.01)

        train_hist = []
        for epoch, stories in enumerate(cal.EPOCH_SCHEDULE, 1):
            vals = []
            for s in stories:
                opt.zero_grad(set_to_none=True)
                tl = cal.text_loss(model, tok, contexts[s]["prefixes"], device)
                tl.backward()
                del tl
                if lam > 0:
                    nl, corr = cal.neural_loss(model, tok, contexts[s], targets[s], device, hrf)
                    (lam * nl).backward()
                    vals.append(float(corr.detach().cpu()))
                    del nl, corr
                else:
                    with torch.no_grad():
                        _, corr = cal.neural_loss(model, tok, contexts[s], targets[s], device, hrf)
                        vals.append(float(corr.detach().cpu()))
                    del corr
                opt.step()
                torch.cuda.empty_cache()
            train_hist.append({"epoch": epoch, "stories": stories, "mean_train_fmri_corr": float(np.mean(vals))})

        model.eval()
        vc = []
        with torch.no_grad():
            for s in cal.VAL_STORIES:
                _, corr = cal.neural_loss(model, tok, contexts[s], targets[s], device, hrf)
                vc.append(float(corr.detach().cpu()))
        mean = float(np.mean(vc))
        se = float(np.std(vc, ddof=1) / np.sqrt(len(vc)))
        d = out / LAMBDA_DIR[lam]
        d.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(d / "adapter")
        tok.save_pretrained(d / "adapter")
        rec = {
            "seed": seed,
            "lambda": lam,
            "validation_story_corrs": vc,
            "validation_mean": mean,
            "validation_se": se,
            "train_history": train_hist,
            "adapter": str((d / "adapter").resolve()),
        }
        (d / "summary.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        rows.append(rec)
        del model, base
        torch.cuda.empty_cache()
        report_progress(progress_base + li, len(SEEDS) * 12, f"seed {seed} training lambda {li}/6")

    summary = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory multiseed source training for ChineseEEG dose robustness",
        "protocol": "docs/22_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_V1.md",
        "seed": seed,
        "lambda_grid": LAMBDAS,
        "training_stories": cal.TRAIN_STORIES,
        "validation_stories": cal.VAL_STORIES,
        "results": rows,
        "external_eeg_used_for_training_or_selection": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    import csv
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("GPU required")
    OUT.mkdir(parents=True, exist_ok=True)
    seed_results = []
    all_rows = []

    for si, seed in enumerate(SEEDS):
        seed_root = OUT / f"seed_{seed}"
        cal_root = seed_root / "calibration"
        train_summary = train_seed(seed, cal_root, si * 12)

        dose.CAL_ROOT = cal_root
        eval_root = seed_root / "chineseeeg"
        eval_root.mkdir(parents=True, exist_ok=True)
        eval_summary = dose.evaluate_chinese("cuda", eval_root, si * 12 + 6)
        report_progress(si * 12 + 12, len(SEEDS) * 12, f"seed {seed} ChineseEEG complete")

        contrasts = eval_summary["contrasts"]
        trend = eval_summary["trend"]
        seed_record = {
            "seed": seed,
            "source_validation": {str(r["lambda"]): r["validation_mean"] for r in train_summary["results"]},
            "chineseeeg_contrasts": contrasts,
            "chineseeeg_trend": trend,
        }
        seed_results.append(seed_record)

        csv_path = eval_root / "chineseeeg_subject_dose_results.csv"
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                row["seed"] = seed
                all_rows.append(row)

    combined_csv = OUT / "seed_subject_lambda_results.csv"
    if all_rows:
        fields = ["seed"] + [k for k in all_rows[0].keys() if k != "seed"]
        with combined_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(all_rows)

    lambda_aggregate = {}
    for lam in POSITIVE:
        recs = [next(r for r in s["chineseeeg_contrasts"] if abs(float(r["lambda"]) - lam) < 1e-12) for s in seed_results]
        means = np.asarray([float(r["mean_delta"]) for r in recs], float)
        lambda_aggregate[str(lam)] = {
            "seed_mean_deltas": means.tolist(),
            "mean_of_seed_mean_deltas": float(means.mean()),
            "n_seeds_positive": int(np.sum(means > 0)),
            "all_new_seeds_positive": bool(np.all(means > 0)),
        }

    slope_means = np.asarray([
        float(s["chineseeeg_trend"]["participant_slope_summary"]["mean_delta"])
        for s in seed_results
    ], float)

    summary = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory optimization-seed robustness of fMRI-to-ChineseEEG dose response",
        "protocol": "docs/22_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_V1.md",
        "model_id": cal.MODEL_ID,
        "model_revision": cal.MODEL_REVISION,
        "new_seeds": SEEDS,
        "lambda_grid": LAMBDAS,
        "seed_results": seed_results,
        "lambda_aggregate": lambda_aggregate,
        "trend_aggregate": {
            "seed_participant_slope_mean_values": slope_means.tolist(),
            "mean_of_seed_participant_slope_means": float(slope_means.mean()),
            "n_seeds_positive": int(np.sum(slope_means > 0)),
            "all_new_seeds_positive": bool(np.all(slope_means > 0)),
        },
        "guardrails": [
            "ChineseEEG run-07 outcomes were already observed before this robustness analysis, so this is not fresh confirmation.",
            "All three prespecified new seeds and all six frozen lambda arms are reported.",
            "No new lambda values, target-side representation choices, participant exclusions, layers or checkpoints are selected from ChineseEEG outcomes.",
            "The previously frozen lambda=.01 ZuCo test remains the primary reverse-direction external transfer result.",
            "No rescue tuning is permitted after this analysis.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"lambda_aggregate": lambda_aggregate, "trend_aggregate": summary["trend_aggregate"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
