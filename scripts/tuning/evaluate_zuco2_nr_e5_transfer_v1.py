#!/usr/bin/env python3
"""Frozen ChineseEEG-to-ZuCo 2.0 Task 1 NR multilingual-E5 transfer test.

Primary confirmatory contrast: ChineseEEG-trained lambda=0.10 neural-guided adapter
versus lambda=0 text-only adapter, evaluated against the prospectively frozen ZuCo
all-retained-channel temporal-mean EEG geometry. No ZuCo tuning or representation
selection is performed here.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

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
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import (
    LAMBDA_010_ROOT,
    TEXT_ONLY_ADAPTER,
    encode_texts,
    latest_completed_adapter,
    load_adapter,
)

ARMS = ["lambda_0", "lambda_0p10"]


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def safe_rho(a, b):
    r = float(spearmanr(a, b).statistic)
    if not np.isfinite(r):
        raise RuntimeError("non-finite Spearman RSA")
    return r


def build_model_edges(texts_by_run: dict[int, list[str]], device: str):
    import torch

    specs = {
        "lambda_0": TEXT_ONLY_ADAPTER,
        "lambda_0p10": latest_completed_adapter(LAMBDA_010_ROOT),
    }
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_nr"))
    ap.add_argument("--input-freeze", type=Path, default=Path("outputs/zuco2_nr_input_materialization/latest/summary.json"))
    ap.add_argument("--mapping-freeze", type=Path, default=Path("outputs/zuco2_nr_format_probe/latest/summary.json"))
    ap.add_argument("--stimulus-root", type=Path, default=Path("data/raw/zuco2_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_e5_transfer_v1/latest"))
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    import torch
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    cohort = json.loads(args.input_freeze.read_text(encoding="utf-8"))
    mapping = json.loads(args.mapping_freeze.read_text(encoding="utf-8"))
    ready = list(cohort.get("ready_subjects_all_7_runs") or [])
    if cohort.get("n_ready_subjects_all_7_runs") != 17 or len(ready) != 17 or "YTL" in ready:
        raise SystemExit("unexpected frozen ZuCo cohort")
    if not mapping.get("all_runs_freeze_ready"):
        raise SystemExit("ZuCo stimulus mapping is not freeze-ready")
    maps = {r["run"]: r for r in mapping.get("wordcount_mapping_diagnostics", [])}
    for run in range(1, 8):
        rec = maps.get(f"NR{run}")
        if not rec or not rec.get("freeze_ready") or rec.get("skipped_material_rows_1based") != [1,2,3]:
            raise SystemExit(f"unexpected mapping freeze for NR{run}")

    inventory = load_inventory(args.input_freeze.parent / "session_inventory.csv")
    path_by = {}
    for r in inventory:
        if r.get("subject") in ready and str(r.get("ready", "")).lower() == "true":
            path_by[(r["subject"], int(r["run"]))] = args.data_root.resolve() / r["osf_path"]
    if len(path_by) != 17 * 7:
        raise SystemExit(f"expected 119 frozen EEG files, found {len(path_by)}")

    texts_by_run = {}
    nuisance_by_run = {}
    for run in range(1, 8):
        rows = load_material_rows(args.stimulus_root / "task_materials" / f"nr_{run}.csv")
        selected = maps[f"NR{run}"]["selected_material_rows_1based"]
        texts = [str(rows[i-1][2]).strip() for i in selected]
        if len(texts) != EXPECTED[run]:
            raise SystemExit(f"NR{run} text count mismatch")
        texts_by_run[run] = texts
        nuisance_by_run[run] = nuisance_matrix(texts)

    model_edges, provenance = build_model_edges(texts_by_run, device)

    session_rows = []
    by_subject = {s: {a: [] for a in ARMS} for s in ready}
    for sub in ready:
        for run in range(1, 8):
            feats, _ = load_run_features(path_by[(sub, run)], EXPECTED[run])
            neural = rdm_edges(feats["row_mean_all"])
            X = nuisance_by_run[run]
            nr = residualize(neural, X)
            vals = {}
            for arm in ARMS:
                mr = residualize(model_edges[arm][run], X)
                rho = safe_rho(nr, mr)
                vals[arm] = rho
                by_subject[sub][arm].append(rho)
            session_rows.append({
                "subject": sub,
                "run": f"NR{run}",
                "lambda_0_resid_rsa": vals["lambda_0"],
                "lambda_0p10_resid_rsa": vals["lambda_0p10"],
                "delta_0p10_minus_0": vals["lambda_0p10"] - vals["lambda_0"],
                "n_edges": len(neural),
            })

    subject_rows = []
    diffs = []
    for sub in ready:
        a0 = fisher_mean(by_subject[sub]["lambda_0"])
        a1 = fisher_mean(by_subject[sub]["lambda_0p10"])
        d = a1 - a0
        diffs.append(d)
        subject_rows.append({"subject": sub, "lambda_0_resid_rsa": a0, "lambda_0p10_resid_rsa": a1, "delta_0p10_minus_0": d})

    diffs = np.asarray(diffs, float)
    primary = {
        "contrast": "lambda_0p10_minus_lambda_0",
        "mean_delta": float(diffs.mean()),
        "median_delta": float(np.median(diffs)),
        "fraction_subjects_positive": float(np.mean(diffs > 0)),
        "bootstrap_95ci": boot_ci(diffs),
        "exact_signflip": exact_signflip_p(diffs),
    }
    payload = {
        "schema_version": 1,
        "dataset": "ZuCo 2.0 Task 1 normal reading",
        "frozen_subjects": ready,
        "n_frozen_subjects": len(ready),
        "structural_exclusion": "YTL",
        "primary_eeg_representation": "row_mean_all",
        "primary_contrast": "ChineseEEG-trained E5 lambda=0.10 neural-guided minus lambda=0 text-only",
        "no_zuco_tuning": True,
        "nuisance_rdms": ["sentence-order difference", "word-count difference", "punctuation-count difference", "lowercased lexical-set Jaccard distance"],
        "participant_aggregation": "Fisher-z mean across seven within-run nuisance-residualized Spearman RSAs",
        "model_provenance": provenance,
        "primary_result": primary,
        "guardrails": [
            "ZuCo EEG reliability was established before this model-transfer test.",
            "No ZuCo representation, item, subject, model, or lambda selection is performed from transfer outcomes.",
            "The sole confirmatory neural-guidance contrast is lambda=0.10 versus lambda=0 on the frozen temporal-mean EEG target.",
        ],
    }
    write_csv(out / "subject_results.csv", subject_rows)
    write_csv(out / "session_results.csv", session_rows)
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "primary_result": primary, "output_dir": str(out)}, indent=2))


if __name__ == "__main__":
    main()
