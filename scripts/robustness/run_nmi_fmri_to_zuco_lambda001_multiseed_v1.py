#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

from scripts.robustness import run_nmi_bidirectional_fmri_source_calibration_v1 as cal
from scripts.analysis.run_zuco2_nr_primary_representation_reliability import (
    EXPECTED,
    boot_ci,
    exact_signflip_p,
    fisher_mean,
    load_inventory,
    load_material_rows,
    load_run_features,
    nuisance_matrix,
    rdm_edges,
    residualize,
)
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import encode_texts, load_adapter

SEEDS = [20260829, 20260830, 20260831]
LAMBDAS = [0.0, 0.01]
OUT = Path("outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest").resolve()
PROTOCOL = "docs/30_NMI_FMRI_TO_ZUCO_LAMBDA001_MULTISEED_ROBUSTNESS_V1.md"
TOTAL_STAGES = len(SEEDS) * 3


def write_progress(current: int, phase: str, message: str) -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": TOTAL_STAGES,
        "fraction": current / TOTAL_STAGES,
        "phase": phase,
        "message": message,
        "unit": "seed-arm/evaluation stages",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def safe_rho(a: np.ndarray, b: np.ndarray) -> float:
    r = float(spearmanr(a, b).statistic)
    if not np.isfinite(r):
        raise RuntimeError("non-finite Spearman RSA")
    return r


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def train_arm(seed: int, lam: float, out: Path) -> dict:
    import torch
    from transformers import AutoModel, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from torch.optim import AdamW
    from scripts.analysis.run_smn4lang_fmri_reliability import TR, canonical_hrf
    from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import story_context

    if not torch.cuda.is_available():
        raise RuntimeError("GPU required")
    device = "cuda"
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

    arm_name = "lambda_0p0" if lam == 0 else "lambda_0p01"
    arm_dir = out / arm_name
    arm_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(arm_dir / "adapter")
    tok.save_pretrained(arm_dir / "adapter")
    rec = {
        "seed": seed,
        "lambda": lam,
        "validation_story_corrs": vc,
        "validation_mean": mean,
        "validation_se": se,
        "train_history": train_hist,
        "adapter": str((arm_dir / "adapter").resolve()),
        "equal_optimizer_step_count": True,
        "source_training_or_selection_used_zuco": False,
    }
    (arm_dir / "summary.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    del model, base
    torch.cuda.empty_cache()
    return rec


def build_model_edges(texts_by_run: dict[int, list[str]], text_adapter: Path, guided_adapter: Path, device: str):
    import torch

    specs = {"lambda_0": text_adapter, "fmri_guided_lambda_0p01": guided_adapter}
    flat = [t for run in range(1, 8) for t in texts_by_run[run]]
    out = {}
    provenance = {}
    for label, adapter in specs.items():
        tok, model = load_adapter(adapter, device)
        emb = encode_texts(model, tok, flat, device)
        if emb.shape[0] != sum(EXPECTED.values()):
            raise RuntimeError(f"expected 349 embeddings, got {emb.shape}")
        out[label] = {}
        off = 0
        for run in range(1, 8):
            n = EXPECTED[run]
            e = emb[off:off+n]
            d = pdist(e, metric="cosine")
            if not np.isfinite(d).all():
                raise RuntimeError(f"non-finite model RDM for {label} NR{run}")
            out[label][run] = d
            off += n
        provenance[label] = str(adapter.resolve())
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return out, provenance


def prepare_zuco_inputs():
    data_root = Path("data/raw/zuco2_nr").resolve()
    input_freeze = Path("outputs/zuco2_nr_input_materialization/latest/summary.json")
    mapping_freeze = Path("outputs/zuco2_nr_format_probe/latest/summary.json")
    stimulus_root = Path("data/raw/zuco2_probe")

    cohort = json.loads(input_freeze.read_text(encoding="utf-8"))
    mapping = json.loads(mapping_freeze.read_text(encoding="utf-8"))
    ready = list(cohort.get("ready_subjects_all_7_runs") or [])
    if cohort.get("n_ready_subjects_all_7_runs") != 17 or len(ready) != 17 or "YTL" in ready:
        raise RuntimeError("unexpected frozen ZuCo cohort")
    if not mapping.get("all_runs_freeze_ready"):
        raise RuntimeError("ZuCo stimulus mapping is not freeze-ready")
    maps = {r["run"]: r for r in mapping.get("wordcount_mapping_diagnostics", [])}
    for run in range(1, 8):
        rec = maps.get(f"NR{run}")
        if not rec or not rec.get("freeze_ready") or rec.get("skipped_material_rows_1based") != [1, 2, 3]:
            raise RuntimeError(f"unexpected mapping freeze for NR{run}")

    inventory = load_inventory(input_freeze.parent / "session_inventory.csv")
    path_by = {}
    for r in inventory:
        if r.get("subject") in ready and str(r.get("ready", "")).lower() == "true":
            path_by[(r["subject"], int(r["run"]))] = data_root / r["osf_path"]
    if len(path_by) != 17 * 7:
        raise RuntimeError(f"expected 119 frozen EEG files, found {len(path_by)}")

    texts_by_run = {}
    nuisance_by_run = {}
    for run in range(1, 8):
        rows = load_material_rows(stimulus_root / "task_materials" / f"nr_{run}.csv")
        selected = maps[f"NR{run}"]["selected_material_rows_1based"]
        texts = [str(rows[i-1][2]).strip() for i in selected]
        if len(texts) != EXPECTED[run]:
            raise RuntimeError(f"NR{run} text count mismatch")
        texts_by_run[run] = texts
        nuisance_by_run[run] = nuisance_matrix(texts)
    return ready, path_by, texts_by_run, nuisance_by_run


def evaluate_seed(seed: int, seed_root: Path, ready, path_by, texts_by_run, nuisance_by_run) -> dict:
    text_adapter = seed_root / "calibration" / "lambda_0p0" / "adapter"
    guided_adapter = seed_root / "calibration" / "lambda_0p01" / "adapter"
    if not text_adapter.exists() or not guided_adapter.exists():
        raise FileNotFoundError("missing matched seed adapters")

    model_edges, provenance = build_model_edges(texts_by_run, text_adapter, guided_adapter, "cuda")
    session_rows = []
    by_subject = {s: {"lambda_0": [], "fmri_guided_lambda_0p01": []} for s in ready}
    for sub in ready:
        for run in range(1, 8):
            feats, _ = load_run_features(path_by[(sub, run)], EXPECTED[run])
            neural = rdm_edges(feats["row_mean_all"])
            X = nuisance_by_run[run]
            nr = residualize(neural, X)
            vals = {}
            for arm in ["lambda_0", "fmri_guided_lambda_0p01"]:
                mr = residualize(model_edges[arm][run], X)
                rho = safe_rho(nr, mr)
                vals[arm] = rho
                by_subject[sub][arm].append(rho)
            session_rows.append({
                "seed": seed,
                "subject": sub,
                "run": f"NR{run}",
                "lambda_0_resid_rsa": vals["lambda_0"],
                "fmri_guided_lambda_0p01_resid_rsa": vals["fmri_guided_lambda_0p01"],
                "delta_fmri_guided_minus_0": vals["fmri_guided_lambda_0p01"] - vals["lambda_0"],
                "n_edges": len(neural),
            })

    subject_rows = []
    diffs = []
    a0s = []
    a1s = []
    for sub in ready:
        a0 = fisher_mean(by_subject[sub]["lambda_0"])
        a1 = fisher_mean(by_subject[sub]["fmri_guided_lambda_0p01"])
        d = a1 - a0
        a0s.append(a0)
        a1s.append(a1)
        diffs.append(d)
        subject_rows.append({
            "seed": seed,
            "subject": sub,
            "lambda_0_resid_rsa": a0,
            "fmri_guided_lambda_0p01_resid_rsa": a1,
            "delta_fmri_guided_minus_0": d,
        })
    diffs = np.asarray(diffs, float)
    result = {
        "seed": seed,
        "lambda_0_mean_rsa": float(np.mean(a0s)),
        "lambda_0p01_mean_rsa": float(np.mean(a1s)),
        "mean_delta": float(diffs.mean()),
        "median_delta": float(np.median(diffs)),
        "n_positive": int(np.sum(diffs > 0)),
        "fraction_positive": float(np.mean(diffs > 0)),
        "bootstrap_95ci": boot_ci(diffs),
        "exact_signflip": exact_signflip_p(diffs),
        "model_provenance": provenance,
    }
    return {"summary": result, "subject_rows": subject_rows, "session_rows": session_rows}


def main() -> int:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("GPU required")
    OUT.mkdir(parents=True, exist_ok=True)
    ready, path_by, texts_by_run, nuisance_by_run = prepare_zuco_inputs()

    all_subject_rows = []
    all_session_rows = []
    seed_results = []
    stage = 0
    for seed in SEEDS:
        cal_dir = OUT / f"seed_{seed}" / "calibration"
        cal_dir.mkdir(parents=True, exist_ok=True)
        training = []
        for lam in LAMBDAS:
            training.append(train_arm(seed, lam, cal_dir))
            stage += 1
            write_progress(stage, "source_training", f"seed {seed} lambda {lam:g} trained")
        ev = evaluate_seed(seed, OUT / f"seed_{seed}", ready, path_by, texts_by_run, nuisance_by_run)
        all_subject_rows.extend(ev["subject_rows"])
        all_session_rows.extend(ev["session_rows"])
        seed_results.append({"seed": seed, "training": training, "zuco": ev["summary"]})
        stage += 1
        write_progress(stage, "zuco_evaluation", f"seed {seed} ZuCo evaluation complete")

    write_csv(OUT / "seed_subject_results.csv", all_subject_rows)
    write_csv(OUT / "seed_session_results.csv", all_session_rows)
    means = np.asarray([r["zuco"]["mean_delta"] for r in seed_results], dtype=float)
    summary = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory optimization-seed robustness of frozen fMRI-to-ZuCo lambda=0.01 transfer",
        "protocol": PROTOCOL,
        "model_id": cal.MODEL_ID,
        "model_revision": cal.MODEL_REVISION,
        "seeds": SEEDS,
        "lambdas": LAMBDAS,
        "n_zuco_subjects": len(ready),
        "seed_results": seed_results,
        "aggregate": {
            "seed_mean_deltas": means.tolist(),
            "mean_of_seed_mean_deltas": float(means.mean()),
            "n_seed_means_positive": int(np.sum(means > 0)),
        },
        "guardrails": [
            "The original source-selected lambda=0.01 ZuCo result remains the frozen primary reverse-direction result.",
            "All three prespecified added seeds are reported irrespective of outcome; no 3/3-positive success gate is imposed.",
            "Only the matched lambda=0 and lambda=0.01 arms are trained; no new lambda search is performed.",
            "No ZuCo outcome is used for training, model selection, representation selection, participant selection, run selection, layer selection or checkpoint selection.",
            "Human participants are biological inferential units within each seed; optimization seeds are robustness trajectories.",
            "No rescue tuning is permitted after this analysis.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_progress(TOTAL_STAGES, "complete", "all frozen seed trajectories complete")
    print(json.dumps({"status": "ok", "aggregate": summary["aggregate"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
