#!/usr/bin/env python3
"""Compare representation-space displacement from matched text-only adapters.

This post-confirmatory diagnostic uses only already-trained adapters. For the three
prespecified optimization seeds it compares genuine-neural and frozen MPNet-surrogate
lambda=0.10 adapters with their seed-matched text-only controls on the same frozen ZuCo
normal-reading text set used by the existing model-space characterization. No neural
outcome, external target value, retraining, checkpoint selection or rescue tuning is
performed.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr, spearmanr

from scripts.analysis.run_zuco2_nr_primary_representation_reliability import EXPECTED, load_material_rows
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import load_adapter, encode_texts

SEEDS = [20260829, 20260830, 20260831]
K = 10
TEXT_ROOT = Path("outputs/nmi_multiseed_e5_v1")
SURROGATE_ROOT = Path("outputs/nmi_alternative_signal_e5_v1")
OUT = Path("outputs/nmi_mpnet_model_space_comparison_v1/latest")


def write_progress(current: int, total: int, phase: str, message: str) -> None:
    path = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not path:
        return
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": max(0.0, min(1.0, current / total if total else 0.0)),
        "phase": phase,
        "message": message,
        "unit": "adapter encodings",
        "updated_at_epoch": time.time(),
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    tmp.replace(p)


def latest_adapter(root: Path) -> Path:
    c = sorted([p / "adapter" for p in root.iterdir() if p.is_dir() and (p / "adapter").is_dir()]) if root.exists() else []
    if not c:
        raise RuntimeError(f"No adapter under {root}")
    return c[-1]


def centered_linear_cka(x: np.ndarray, y: np.ndarray) -> float:
    x = x - x.mean(axis=0, keepdims=True)
    y = y - y.mean(axis=0, keepdims=True)
    num = float(np.sum((x.T @ y) ** 2))
    den = float(np.linalg.norm(x.T @ x, ord="fro") * np.linalg.norm(y.T @ y, ord="fro"))
    return num / den if den > 0 else float("nan")


def knn_overlap(a: np.ndarray, b: np.ndarray, k: int) -> float:
    da = squareform(pdist(a, metric="cosine"))
    db = squareform(pdist(b, metric="cosine"))
    vals = []
    for i in range(a.shape[0]):
        na = set(np.argsort(da[i])[1:k + 1].tolist())
        nb = set(np.argsort(db[i])[1:k + 1].tolist())
        vals.append(len(na & nb) / len(na | nb))
    return float(np.mean(vals))


def effective_rank(x: np.ndarray) -> float:
    xc = x - x.mean(axis=0, keepdims=True)
    s = np.linalg.svd(xc, compute_uv=False)
    v = s * s
    p = v / np.clip(v.sum(), 1e-15, None)
    p = p[p > 0]
    return float(np.exp(-np.sum(p * np.log(p))))


def intrinsic(x: np.ndarray) -> dict:
    norms = np.linalg.norm(x, axis=1)
    d = pdist(x, metric="cosine")
    sim = 1.0 - d
    return {
        "effective_rank": effective_rank(x),
        "mean_pairwise_cosine_similarity": float(np.mean(sim)),
        "pairwise_cosine_distance_variance": float(np.var(d)),
        "embedding_norm_mean": float(np.mean(norms)),
        "embedding_norm_sd": float(np.std(norms)),
    }


def compare(a: np.ndarray, b: np.ndarray) -> dict:
    item_cos = np.sum(a * b, axis=1) / np.clip(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-12, None)
    da = pdist(a, metric="cosine")
    db = pdist(b, metric="cosine")
    return {
        "corresponding_item_cosine_similarity_mean": float(np.mean(item_cos)),
        "corresponding_item_cosine_similarity_median": float(np.median(item_cos)),
        "pairwise_cosine_distance_pearson": float(pearsonr(da, db).statistic),
        "pairwise_cosine_distance_spearman": float(spearmanr(da, db).statistic),
        "linear_centered_cka": centered_linear_cka(a, b),
        "knn_k": K,
        "mean_knn_jaccard_overlap": knn_overlap(a, b, K),
    }


def frozen_texts() -> list[str]:
    mapping = json.loads(Path("outputs/zuco2_nr_format_probe/latest/summary.json").read_text(encoding="utf-8"))
    maps = {r["run"]: r for r in mapping["wordcount_mapping_diagnostics"]}
    texts = []
    for run in range(1, 8):
        rows = load_material_rows(Path("data/raw/zuco2_probe/task_materials") / f"nr_{run}.csv")
        selected = maps[f"NR{run}"]["selected_material_rows_1based"]
        rt = [str(rows[i - 1][2]).strip() for i in selected]
        if len(rt) != EXPECTED[run]:
            raise RuntimeError(f"NR{run}: frozen text count mismatch")
        texts.extend(rt)
    return texts


def encode_adapter(adapter: Path, texts: list[str], device: str) -> np.ndarray:
    import torch
    tok, model = load_adapter(adapter, device)
    e = encode_texts(model, tok, texts, device)
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return e


def main() -> int:
    import torch
    OUT.mkdir(parents=True, exist_ok=True)
    texts = frozen_texts()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    comparison_rows = []
    intrinsic_rows = []
    completed = 0
    total_encodings = len(SEEDS) * 3
    write_progress(0, total_encodings, "encode", "starting frozen adapter encodings")

    for seed in SEEDS:
        seed_base = TEXT_ROOT / f"seed_{seed}"
        text_adapter = latest_adapter(seed_base / "text_only")
        genuine_adapter = latest_adapter(seed_base / "neural")
        surrogate_adapter = latest_adapter(SURROGATE_ROOT / f"seed_{seed}" / "neural")

        print(f"=== seed {seed}: text ===", flush=True)
        et = encode_adapter(text_adapter, texts, device)
        completed += 1
        write_progress(completed, total_encodings, "encode", f"completed text-only encoding for seed {seed}")
        print(f"=== seed {seed}: genuine neural ===", flush=True)
        eg = encode_adapter(genuine_adapter, texts, device)
        completed += 1
        write_progress(completed, total_encodings, "encode", f"completed genuine-neural encoding for seed {seed}")
        print(f"=== seed {seed}: MPNet surrogate ===", flush=True)
        es = encode_adapter(surrogate_adapter, texts, device)
        completed += 1
        write_progress(completed, total_encodings, "encode", f"completed MPNet-surrogate encoding for seed {seed}")
        if et.shape != eg.shape or et.shape != es.shape or et.shape[0] != len(texts):
            raise RuntimeError(f"seed {seed}: embedding shape mismatch")

        for arm, emb, adapter in [("text_only", et, text_adapter), ("genuine_neural", eg, genuine_adapter), ("mpnet_surrogate", es, surrogate_adapter)]:
            rec = {"seed": seed, "arm": arm, "adapter": str(adapter), **intrinsic(emb)}
            intrinsic_rows.append(rec)

        for arm, emb, adapter in [("genuine_neural", eg, genuine_adapter), ("mpnet_surrogate", es, surrogate_adapter)]:
            rec = {"seed": seed, "comparison": f"{arm}_vs_text_only", "adapter": str(adapter), "text_adapter": str(text_adapter), **compare(et, emb)}
            comparison_rows.append(rec)

    with (OUT / "seed_comparison_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comparison_rows[0])); w.writeheader(); w.writerows(comparison_rows)
    with (OUT / "representation_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(intrinsic_rows[0])); w.writeheader(); w.writerows(intrinsic_rows)

    summaries = {}
    for comp in ["genuine_neural_vs_text_only", "mpnet_surrogate_vs_text_only"]:
        rs = [r for r in comparison_rows if r["comparison"] == comp]
        summaries[comp] = {}
        for k in ["corresponding_item_cosine_similarity_mean", "pairwise_cosine_distance_pearson", "pairwise_cosine_distance_spearman", "linear_centered_cka", "mean_knn_jaccard_overlap"]:
            vals = [float(r[k]) for r in rs]
            summaries[comp][k] = {"seed_values": vals, "mean": float(np.mean(vals)), "min": float(np.min(vals)), "max": float(np.max(vals))}

    payload = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory no-retraining model-space diagnostic",
        "stimulus_set": "frozen ZuCo 2.0 Task 1 normal-reading texts",
        "n_items": len(texts),
        "seeds": SEEDS,
        "comparisons": summaries,
        "guardrails": {
            "retraining_performed": False,
            "external_neural_outcomes_read": False,
            "target_selection_performed": False,
            "checkpoint_selection_performed": False,
        },
        "interpretation": "This diagnostic quantifies whether the frozen MPNet surrogate caused a larger or qualitatively different representation-space displacement than genuine neural guidance. It does not change the surrogate transfer endpoint.",
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.txt").write_text(
        "NeuroSem MPNet surrogate model-space diagnostic\n\n"
        f"Items: {len(texts)}\nSeeds: {SEEDS}\n"
        f"Genuine-neural vs text mean CKA: {summaries['genuine_neural_vs_text_only']['linear_centered_cka']['mean']:.6f}\n"
        f"MPNet-surrogate vs text mean CKA: {summaries['mpnet_surrogate_vs_text_only']['linear_centered_cka']['mean']:.6f}\n"
        f"Genuine-neural vs text mean kNN Jaccard: {summaries['genuine_neural_vs_text_only']['mean_knn_jaccard_overlap']['mean']:.6f}\n"
        f"MPNet-surrogate vs text mean kNN Jaccard: {summaries['mpnet_surrogate_vs_text_only']['mean_knn_jaccard_overlap']['mean']:.6f}\n"
        "No retraining or external neural outcome was used.\n",
        encoding="utf-8",
    )
    write_progress(total_encodings, total_encodings, "complete", "model-space comparison complete")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
