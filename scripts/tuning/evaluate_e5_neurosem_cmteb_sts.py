#!/usr/bin/env python3
"""Evaluate frozen multilingual-E5 NeuroSem arms on the prespecified Chinese STS benchmark."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

MODEL_ID = "intfloat/multilingual-e5-large"
MODEL_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
PREFIX = "query: "
ARMS = ("base", "text_only", "neural", "shuffled_neural")
TASKS = {
    "AFQMC": {"repo": "mteb/AFQMC", "config": None},
    "ATEC": {"repo": "mteb/ATEC", "config": None},
    "BQ": {"repo": "mteb/BQ", "config": None},
    "LCQMC": {"repo": "mteb/LCQMC", "config": None},
    "PAWSX": {"repo": "mteb/PAWSX", "config": None},
    "QBQTC": {"repo": "mteb/QBQTC", "config": None},
    "STS22 (zh)": {"repo": "mteb/sts22-crosslingual-sts", "config": "zh"},
    "STSB": {"repo": "mteb/STSB", "config": None},
}
SPLIT_ORDER = ("test", "validation", "train")


def latest_adapter(root: Path, arm: str) -> Path:
    arm_root = root / arm
    candidates = [d for d in arm_root.iterdir() if d.is_dir() and (d / "adapter").exists()] if arm_root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No saved adapter found for {arm} under {arm_root}")
    return sorted(candidates)[-1] / "adapter"


def load_arm_model(arm: str, tuning_root: Path, device: str):
    from peft import PeftModel
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    adapter_path = None
    if arm != "base":
        adapter_path = latest_adapter(tuning_root, arm)
        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval().to(device)
    return tokenizer, model, adapter_path


def masked_mean(hidden, mask):
    mask = mask.to(hidden.dtype).unsqueeze(-1)
    return (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)


def encode(model, tokenizer, texts, device, batch_size, max_length):
    import torch

    chunks = []
    with torch.inference_mode():
        for start in range(0, len(texts), batch_size):
            batch = [PREFIX + str(x) for x in texts[start:start + batch_size]]
            enc = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
            attention = enc["attention_mask"]
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc, return_dict=True)
            pooled = masked_mean(out.last_hidden_state, attention.to(device).bool())
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            chunks.append(pooled.cpu().numpy().astype(np.float32))
    return np.concatenate(chunks, axis=0)


def resolve_dataset_revisions():
    from huggingface_hub import HfApi

    api = HfApi()
    revisions = {}
    for task, spec in TASKS.items():
        sha = api.dataset_info(spec["repo"]).sha
        if not sha:
            raise RuntimeError(f"Could not resolve dataset revision for {spec['repo']}")
        revisions[task] = sha
    return revisions


def load_split(spec, revision, split):
    from datasets import load_dataset

    kwargs = {"path": spec["repo"], "split": split, "revision": revision}
    if spec["config"] is not None:
        kwargs["name"] = spec["config"]
    return load_dataset(**kwargs)


def select_labeled_split(spec, revision):
    last_error = None
    for split in SPLIT_ORDER:
        try:
            ds = load_split(spec, revision, split)
        except Exception as exc:
            last_error = exc
            continue
        required = {"sentence1", "sentence2", "score"}
        if not required.issubset(ds.column_names):
            continue
        gold = np.asarray(ds["score"], dtype=np.float64)
        if gold.size and np.isfinite(gold).all() and np.unique(gold).size >= 2:
            return split, ds, int(np.unique(gold).size)
    raise RuntimeError(f"No finite nonconstant labeled split for {spec['repo']}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuning-root", type=Path, default=Path("outputs/e5_neural_tuning_v1"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/e5_neurosem_cmteb_sts_v1"))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    import datasets
    import peft
    import torch
    import transformers

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    revisions = resolve_dataset_revisions()
    loaded = {}
    selected_splits = {}
    unique_scores = {}
    print("Resolved frozen dataset revisions and public labeled splits:")
    for task, spec in TASKS.items():
        split, ds, n_unique = select_labeled_split(spec, revisions[task])
        loaded[task] = ds
        selected_splits[task] = split
        unique_scores[task] = n_unique
        print(f"  {task}: {spec['repo']}@{revisions[task]} | split={split} | n={len(ds)} | unique_scores={n_unique}")

    results = {}
    tuning_root = args.tuning_root.resolve()
    for arm in ARMS:
        print(f"\n=== {arm} | frozen E5 C-MTEB STS ===", flush=True)
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
            print(f"  {task}: Spearman={rho:.6f} | split={selected_splits[task]} | n={len(ds)}", flush=True)

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
    wins_text = sum(results["neural"]["task_scores"][t] > results["text_only"]["task_scores"][t] for t in TASKS)
    wins_shuffle = sum(results["neural"]["task_scores"][t] > results["shuffled_neural"]["task_scores"][t] for t in TASKS)
    worst_text = min(results["neural"]["task_scores"][t] - results["text_only"]["task_scores"][t] for t in TASKS)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/e5_neural_tuning_protocol_v1.md",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "representation": "query prefix; attention-mask mean pooling; L2 normalization; cosine similarity",
        "batch_size": args.batch_size,
        "max_length": args.max_length,
        "device": device,
        "transformers_version": transformers.__version__,
        "datasets_version": datasets.__version__,
        "peft_version": peft.__version__,
        "dataset_revisions": revisions,
        "selected_splits": selected_splits,
        "unique_gold_scores": unique_scores,
        "split_selection_rule": "Before model scoring, choose first split in test -> validation -> train with all-finite and >=2 unique gold scores.",
        "results": results,
        "contrasts": contrasts,
        "neural_task_wins_vs_text_only": int(wins_text),
        "neural_task_wins_vs_shuffled_neural": int(wins_shuffle),
        "neural_worst_task_delta_vs_text_only": float(worst_text),
        "notes": [
            "This evaluation performs no parameter updates.",
            "The eight-task endpoint and public-label split rule were frozen before this E5 experiment.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Frozen E5 primary endpoint ===")
    for arm in ARMS:
        print(f"{arm}: {results[arm]['mean_spearman']:.6f}")
    print(f"neural - text_only: {contrasts['neural_minus_text_only']:+.6f}")
    print(f"neural - shuffled_neural: {contrasts['neural_minus_shuffled_neural']:+.6f}")
    print(f"neural - base: {contrasts['neural_minus_base']:+.6f}")
    print(f"Neural task wins vs text_only: {wins_text}/8")
    print(f"Neural task wins vs shuffled_neural: {wins_shuffle}/8")
    print(f"Worst neural task delta vs text_only: {worst_text:+.6f}")
    print(f"Summary: {out / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
