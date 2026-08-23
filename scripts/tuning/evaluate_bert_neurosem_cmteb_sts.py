#!/usr/bin/env python3
"""Evaluate the frozen NeuroSem BERT tuning arms on the prespecified Chinese STS benchmark.

Primary endpoint: unweighted mean Spearman correlation across eight frozen C-MTEB STS tasks.
No task-specific tuning, pooling changes, whitening, or calibration are performed.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

MODEL_ID = "google-bert/bert-base-chinese"
MODEL_REVISION = "8d2a91f91cc38c96bb8b4556ba70c392f8d5ee55"
ARMS = ("base", "text_only", "neural", "shuffled_neural")
TASKS = {
    "AFQMC": {"repo": "mteb/AFQMC", "config": None, "split": "test"},
    "ATEC": {"repo": "mteb/ATEC", "config": None, "split": "test"},
    "BQ": {"repo": "mteb/BQ", "config": None, "split": "test"},
    "LCQMC": {"repo": "mteb/LCQMC", "config": None, "split": "test"},
    "PAWSX": {"repo": "mteb/PAWSX", "config": None, "split": "test"},
    "QBQTC": {"repo": "mteb/QBQTC", "config": None, "split": "test"},
    "STS22 (zh)": {"repo": "mteb/sts22-crosslingual-sts", "config": "zh", "split": "test"},
    "STSB": {"repo": "mteb/STSB", "config": None, "split": "test"},
}


def latest_adapter(root: Path, arm: str) -> Path:
    arm_root = root / arm
    candidates = [d for d in arm_root.iterdir() if d.is_dir() and (d / "adapter").exists()] if arm_root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No saved adapter found for {arm} under {arm_root}")
    return sorted(candidates)[-1] / "adapter"


def load_arm_model(arm: str, tuning_root: Path, device: str):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForMaskedLM.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    adapter_path = None
    if arm != "base":
        adapter_path = latest_adapter(tuning_root, arm)
        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval().to(device)
    return tokenizer, model, adapter_path


def encode(model, tokenizer, texts: list[str], device: str, batch_size: int, max_length: int) -> np.ndarray:
    import torch

    chunks: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_special_tokens_mask=True,
                return_tensors="pt",
            )
            special = enc.pop("special_tokens_mask")
            attention = enc["attention_mask"]
            mask = (attention.bool() & ~special.bool()).to(device)
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc, output_hidden_states=True, return_dict=True)
            hidden = out.hidden_states[-1]
            w = mask.to(hidden.dtype).unsqueeze(-1)
            pooled = (hidden * w).sum(dim=1) / w.sum(dim=1).clamp_min(1.0)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            chunks.append(pooled.cpu().numpy().astype(np.float32))
    return np.concatenate(chunks, axis=0)


def load_task_dataset(spec: dict, revision: str):
    from datasets import load_dataset

    kwargs = {"path": spec["repo"], "split": spec["split"], "revision": revision}
    if spec["config"] is not None:
        kwargs["name"] = spec["config"]
    ds = load_dataset(**kwargs)
    required = {"sentence1", "sentence2", "score"}
    missing = required.difference(ds.column_names)
    if missing:
        raise RuntimeError(f"Dataset {spec['repo']} missing columns: {sorted(missing)}")
    return ds


def resolve_dataset_revisions() -> dict[str, str]:
    from huggingface_hub import HfApi

    api = HfApi()
    revisions = {}
    for task, spec in TASKS.items():
        sha = api.dataset_info(spec["repo"]).sha
        if not sha:
            raise RuntimeError(f"Could not resolve dataset revision for {spec['repo']}")
        revisions[task] = sha
    return revisions


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen NeuroSem C-MTEB Chinese STS evaluation.")
    parser.add_argument("--tuning-root", type=Path, default=Path("outputs/bert_neural_tuning_v1"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/bert_neurosem_cmteb_sts_v1"))
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    import torch
    import transformers
    import datasets
    import peft

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    revisions = resolve_dataset_revisions()
    loaded = {}
    print("Resolved frozen dataset revisions:")
    for task, spec in TASKS.items():
        rev = revisions[task]
        ds = load_task_dataset(spec, rev)
        loaded[task] = ds
        print(f"  {task}: {spec['repo']}@{rev} | n={len(ds)}")

    results: dict[str, dict] = {}
    tuning_root = args.tuning_root.resolve()

    for arm in ARMS:
        print(f"\n=== {arm} | frozen C-MTEB STS ===", flush=True)
        tokenizer, model, adapter_path = load_arm_model(arm, tuning_root, device)
        task_scores = {}
        task_sizes = {}

        for task, ds in loaded.items():
            s1 = [str(x) for x in ds["sentence1"]]
            s2 = [str(x) for x in ds["sentence2"]]
            gold = np.asarray(ds["score"], dtype=np.float64)

            e1 = encode(model, tokenizer, s1, device, args.batch_size, args.max_length)
            e2 = encode(model, tokenizer, s2, device, args.batch_size, args.max_length)
            sim = np.einsum("ij,ij->i", e1, e2, dtype=np.float64)
            rho = float(spearmanr(sim, gold).statistic)
            if not np.isfinite(rho):
                raise RuntimeError(f"Non-finite Spearman for {arm}/{task}")
            task_scores[task] = rho
            task_sizes[task] = len(ds)
            print(f"  {task}: Spearman={rho:.6f} | n={len(ds)}", flush=True)

        mean_score = float(np.mean(list(task_scores.values())))
        results[arm] = {
            "mean_spearman": mean_score,
            "task_scores": task_scores,
            "task_sizes": task_sizes,
            "adapter_path": None if adapter_path is None else str(adapter_path),
        }
        print(f"{arm} mean across 8 tasks = {mean_score:.6f}", flush=True)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    neural = results["neural"]["mean_spearman"]
    text = results["text_only"]["mean_spearman"]
    shuffled = results["shuffled_neural"]["mean_spearman"]
    base = results["base"]["mean_spearman"]

    contrasts = {
        "neural_minus_text_only": neural - text,
        "neural_minus_shuffled_neural": neural - shuffled,
        "neural_minus_base": neural - base,
    }
    neural_vs_text_wins = sum(results["neural"]["task_scores"][t] > results["text_only"]["task_scores"][t] for t in TASKS)
    neural_vs_shuffle_wins = sum(results["neural"]["task_scores"][t] > results["shuffled_neural"]["task_scores"][t] for t in TASKS)
    worst_vs_text = min(results["neural"]["task_scores"][t] - results["text_only"]["task_scores"][t] for t in TASKS)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/bert_tuning_external_benchmark_v1.md",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "representation": "final hidden layer mean over non-special/non-padding tokens; cosine similarity",
        "batch_size": args.batch_size,
        "max_length": args.max_length,
        "device": device,
        "transformers_version": transformers.__version__,
        "datasets_version": datasets.__version__,
        "peft_version": peft.__version__,
        "dataset_revisions": revisions,
        "results": results,
        "contrasts": contrasts,
        "neural_task_wins_vs_text_only": int(neural_vs_text_wins),
        "neural_task_wins_vs_shuffled_neural": int(neural_vs_shuffle_wins),
        "neural_worst_task_delta_vs_text_only": float(worst_vs_text),
        "notes": [
            "This evaluation performs no parameter updates.",
            "The eight tasks and unweighted-mean primary endpoint were frozen before tuning results were interpreted.",
            "Dataset repository HEAD revisions are resolved once at evaluation start and recorded for reproducibility.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Frozen primary endpoint ===")
    for arm in ARMS:
        print(f"{arm}: {results[arm]['mean_spearman']:.6f}")
    print(f"neural - text_only: {contrasts['neural_minus_text_only']:+.6f}")
    print(f"neural - shuffled_neural: {contrasts['neural_minus_shuffled_neural']:+.6f}")
    print(f"neural - base: {contrasts['neural_minus_base']:+.6f}")
    print(f"Neural task wins vs text_only: {neural_vs_text_wins}/8")
    print(f"Neural task wins vs shuffled_neural: {neural_vs_shuffle_wins}/8")
    print(f"Worst neural task delta vs text_only: {worst_vs_text:+.6f}")
    print(f"Summary: {out / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
