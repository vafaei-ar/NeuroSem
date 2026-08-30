#!/usr/bin/env python3
"""Frozen post-confirmatory SMN4Lang-fMRI -> ZuCo EEG transfer test."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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

CAL_ROOT = Path("outputs/nmi_bidirectional_fmri_calibration_v1/latest")
TEXT_ADAPTER = CAL_ROOT / "lambda_0p0" / "adapter"
SELECTED_ADAPTER = CAL_ROOT / "lambda_0p01" / "adapter"
ARMS = ["lambda_0", "fmri_guided_lambda_0p01"]


def write_csv(path: Path, rows: list[dict]) -> None:
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


def assert_source_freeze() -> dict:
    p = CAL_ROOT / "summary.json"
    if not p.exists():
        raise FileNotFoundError(p)
    s = json.loads(p.read_text(encoding="utf-8"))
    if s.get("external_eeg_read") is not False:
        raise RuntimeError("source calibration is not EEG-blind")
    if s.get("source_gate_pass") is not True:
        raise RuntimeError("source-learning gate did not pass")
    if abs(float(s.get("selected_lambda")) - 0.01) > 1e-12:
        raise RuntimeError(f"unexpected selected lambda: {s.get('selected_lambda')}")
    if not TEXT_ADAPTER.exists() or not SELECTED_ADAPTER.exists():
        raise FileNotFoundError("missing frozen calibration adapter")
    return s


def build_model_edges(texts_by_run: dict[int, list[str]], device: str):
    import torch

    specs = {
        "lambda_0": TEXT_ADAPTER,
        "fmri_guided_lambda_0p01": SELECTED_ADAPTER,
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


def main() -> int:
    import argparse
    import torch

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_nr"))
    ap.add_argument("--input-freeze", type=Path, default=Path("outputs/zuco2_nr_input_materialization/latest/summary.json"))
    ap.add_argument("--mapping-freeze", type=Path, default=Path("outputs/zuco2_nr_format_probe/latest/summary.json"))
    ap.add_argument("--stimulus-root", type=Path, default=Path("data/raw/zuco2_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/nmi_bidirectional_fmri_to_zuco_v1/latest"))
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    source = assert_source_freeze()
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
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
        if not rec or not rec.get("freeze_ready") or rec.get("skipped_material_rows_1based") != [1, 2, 3]:
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
            d = vals["fmri_guided_lambda_0p01"] - vals["lambda_0"]
            session_rows.append({
                "subject": sub,
                "run": f"NR{run}",
                "lambda_0_resid_rsa": vals["lambda_0"],
                "fmri_guided_lambda_0p01_resid_rsa": vals["fmri_guided_lambda_0p01"],
                "delta_fmri_guided_minus_0": d,
                "n_edges": len(neural),
            })

    subject_rows = []
    diffs = []
    for sub in ready:
        a0 = fisher_mean(by_subject[sub]["lambda_0"])
        a1 = fisher_mean(by_subject[sub]["fmri_guided_lambda_0p01"])
        d = a1 - a0
        diffs.append(d)
        subject_rows.append({
            "subject": sub,
            "lambda_0_resid_rsa": a0,
            "fmri_guided_lambda_0p01_resid_rsa": a1,
            "delta_fmri_guided_minus_0": d,
        })

    diffs = np.asarray(diffs, float)
    primary = {
        "contrast": "fmri_guided_lambda_0p01_minus_lambda_0",
        "mean_delta": float(diffs.mean()),
        "median_delta": float(np.median(diffs)),
        "fraction_subjects_positive": float(np.mean(diffs > 0)),
        "bootstrap_95ci": boot_ci(diffs),
        "exact_signflip": exact_signflip_p(diffs),
    }
    payload = {
        "schema_version": 1,
        "analysis_stage": "post-confirmatory bidirectional cross-modal transfer primary target",
        "protocol": "docs/19_NMI_BIDIRECTIONAL_FMRI_TO_ZUCO_V1.md",
        "source_dataset": "SMN4Lang fMRI",
        "target_dataset": "ZuCo 2.0 Task 1 normal reading EEG",
        "selected_lambda": 0.01,
        "source_selection_rule": source.get("selection_rule"),
        "source_selected_validation_mean": source.get("selected_validation_mean"),
        "source_lambda0_validation_mean": source.get("lambda0_validation_mean"),
        "source_gate_pass": source.get("source_gate_pass"),
        "n_frozen_subjects": len(ready),
        "frozen_subjects": ready,
        "primary_eeg_representation": "row_mean_all",
        "no_zuco_tuning": True,
        "model_provenance": provenance,
        "primary_result": primary,
        "guardrails": [
            "The fMRI-guided candidate was selected before ZuCo was read.",
            "No ZuCo representation, item, subject, model, lambda, layer, or checkpoint selection is performed from this outcome.",
            "This is a post-confirmatory secondary generalization experiment and does not alter the status of the original prospective chain.",
            "ChineseEEG run-07 is not read by this job.",
        ],
    }
    write_csv(out / "subject_results.csv", subject_rows)
    write_csv(out / "session_results.csv", session_rows)
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "primary_result": primary, "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
