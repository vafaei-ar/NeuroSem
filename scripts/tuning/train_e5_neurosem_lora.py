#!/usr/bin/env python3
"""Run one frozen multilingual-E5 NeuroSem tuning arm.

Runs 01-05 train, run 06 validates, and run 07 is never accessed here.
The matched text-only objective is symmetric dropout-view InfoNCE.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def latest_dir(root: Path, required: str) -> Path:
    candidates = [d for d in root.iterdir() if d.is_dir() and (d / required).exists()] if root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No directory containing {required} under {root}")
    return sorted(candidates)[-1]


def load_target_run(root: Path, run_number: int) -> dict:
    d = latest_dir(root / f"run-{run_number:02d}", "neural_target.npy")
    return {
        "dir": d,
        "texts": json.loads((d / "texts.json").read_text(encoding="utf-8")),
        "neural": np.load(d / "neural_target.npy").astype(np.float32),
        "shuffled": np.load(d / "shuffled_neural_target.npy").astype(np.float32),
    }


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def masked_mean(hidden, mask):
    mask = mask.to(hidden.dtype).unsqueeze(-1)
    return (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)


def encode_rows(model, tokenizer, texts, prefix, device, max_length, batch_size):
    import torch

    chunks = []
    for start in range(0, len(texts), batch_size):
        batch = [prefix + t for t in texts[start:start + batch_size]]
        enc = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        attention = enc["attention_mask"]
        enc = {k: v.to(device) for k, v in enc.items()}
        out = model(**enc, return_dict=True)
        pooled = masked_mean(out.last_hidden_state, attention.to(device).bool())
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        chunks.append(pooled)
    return torch.cat(chunks, dim=0)


def pairwise_cosine_distance(x):
    import torch
    sim = x @ x.T
    iu = torch.triu_indices(x.shape[0], x.shape[0], offset=1, device=x.device)
    return 1.0 - sim[iu[0], iu[1]]


def standardized(x):
    return (x - x.mean()) / x.std(unbiased=False).clamp_min(1e-8)


def relational_loss(model, tokenizer, texts, target, prefix, device, max_length, batch_size):
    import torch

    was_training = model.training
    model.eval()
    emb = encode_rows(model, tokenizer, texts, prefix, device, max_length, batch_size)
    d = standardized(pairwise_cosine_distance(emb))
    target_t = torch.as_tensor(target, dtype=d.dtype, device=device)
    if target_t.numel() != d.numel():
        raise RuntimeError(f"Target/model edge mismatch: {target_t.numel()} vs {d.numel()}")
    corr = torch.mean(d * target_t)
    if was_training:
        model.train()
    return 1.0 - corr, corr


def contrastive_loss(model, tokenizer, texts, prefix, device, max_length, temperature):
    import torch

    model.train()
    z1 = encode_rows(model, tokenizer, texts, prefix, device, max_length, len(texts))
    z2 = encode_rows(model, tokenizer, texts, prefix, device, max_length, len(texts))
    logits = (z1 @ z2.T) / temperature
    labels = torch.arange(logits.shape[0], device=device)
    loss12 = torch.nn.functional.cross_entropy(logits, labels)
    loss21 = torch.nn.functional.cross_entropy(logits.T, labels)
    return 0.5 * (loss12 + loss21)


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen four-arm multilingual-E5 NeuroSem LoRA experiment.")
    parser.add_argument("--arm", required=True, choices=["base", "text_only", "neural", "shuffled_neural"])
    parser.add_argument("--config", type=Path, default=Path("configs/e5_neural_tuning_v1.json"))
    parser.add_argument("--target-root", type=Path, default=Path("outputs/bert_neural_tuning_targets_v1"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/e5_neural_tuning_v1"))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    import torch
    from peft import LoraConfig, get_peft_model
    from torch.optim import AdamW
    from transformers import AutoModel, AutoTokenizer

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if list(cfg["train_runs"]) != [1, 2, 3, 4, 5] or int(cfg["validation_run"]) != 6 or int(cfg["final_holdout_run"]) != 7:
        raise SystemExit("Frozen E5 split must be train 01-05, validation 06, holdout 07")

    set_seed(int(cfg["seed"]))
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    train_runs = list(cfg["train_runs"])
    runs = {r: load_target_run(args.target_root, r) for r in train_runs + [6]}
    train_texts = [(r, t) for r in train_runs for t in runs[r]["texts"]]

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_id"], revision=cfg["model_revision"])
    model = AutoModel.from_pretrained(cfg["model_id"], revision=cfg["model_revision"])

    if args.arm != "base":
        lora = cfg["lora"]
        peft_cfg = LoraConfig(
            r=int(lora["rank"]),
            lora_alpha=int(lora["alpha"]),
            lora_dropout=float(lora["dropout"]),
            target_modules=list(lora["target_modules"]),
            bias="none",
        )
        model = get_peft_model(model, peft_cfg)
        model.print_trainable_parameters()
    model.to(device)

    prefix = str(cfg["input_prefix"])
    max_length = int(cfg["max_length"])
    geometry_batch_size = int(cfg["geometry_batch_size"])
    temperature = float(cfg["contrastive_temperature"])

    def validation_corr() -> float:
        model.eval()
        with torch.no_grad():
            _, corr = relational_loss(
                model, tokenizer, runs[6]["texts"], runs[6]["neural"], prefix,
                device, max_length, geometry_batch_size,
            )
        return float(corr.detach().cpu())

    initial_val = validation_corr()
    print(f"Arm={args.arm} | initial run-06 neural correlation={initial_val:.6f}")
    history = []

    if args.arm != "base":
        optimizer = AdamW(
            [p for p in model.parameters() if p.requires_grad],
            lr=float(cfg["learning_rate"]),
            weight_decay=float(cfg["weight_decay"]),
        )
        batch_size = int(cfg["batch_size"])
        epochs = int(cfg["epochs"])
        rng = np.random.default_rng(int(cfg["seed"]))

        for epoch in range(1, epochs + 1):
            order = rng.permutation(len(train_texts))
            text_losses = []
            for start in range(0, len(order), batch_size):
                chosen = [train_texts[i][1] for i in order[start:start + batch_size]]
                if len(chosen) < 2:
                    continue
                optimizer.zero_grad(set_to_none=True)
                loss = contrastive_loss(model, tokenizer, chosen, prefix, device, max_length, temperature)
                loss.backward()
                optimizer.step()
                text_losses.append(float(loss.detach().cpu()))

            aux_text_losses = []
            rel_losses = []
            rel_corrs = []
            for run_number in train_runs:
                texts = runs[run_number]["texts"]
                n = min(batch_size, len(texts))
                idx = rng.choice(len(texts), size=n, replace=False)
                aux_texts = [texts[int(i)] for i in idx]

                optimizer.zero_grad(set_to_none=True)
                total = contrastive_loss(model, tokenizer, aux_texts, prefix, device, max_length, temperature)
                aux_text_losses.append(float(total.detach().cpu()))

                if args.arm in {"neural", "shuffled_neural"}:
                    target_key = "neural" if args.arm == "neural" else "shuffled"
                    rel, corr = relational_loss(
                        model, tokenizer, texts, runs[run_number][target_key], prefix,
                        device, max_length, geometry_batch_size,
                    )
                    total = total + float(cfg["neural_loss_weight"]) * rel
                    rel_losses.append(float(rel.detach().cpu()))
                    rel_corrs.append(float(corr.detach().cpu()))

                total.backward()
                optimizer.step()

            val_corr = validation_corr()
            rec = {
                "epoch": epoch,
                "mean_text_loss": float(np.mean(text_losses)),
                "mean_aux_text_loss": float(np.mean(aux_text_losses)),
                "mean_relational_loss": None if not rel_losses else float(np.mean(rel_losses)),
                "mean_train_relational_corr": None if not rel_corrs else float(np.mean(rel_corrs)),
                "run06_neural_corr": val_corr,
            }
            history.append(rec)
            print(
                f"epoch {epoch}/{epochs} | text={rec['mean_text_loss']:.4f} | "
                f"rel={rec['mean_relational_loss']} | run06_corr={val_corr:.6f}",
                flush=True,
            )

    final_val = validation_corr()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (args.output_dir / args.arm / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    if args.arm != "base":
        model.save_pretrained(out / "adapter")
        tokenizer.save_pretrained(out / "adapter")

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "arm": args.arm,
        "config": cfg,
        "target_root": str(args.target_root.resolve()),
        "device": device,
        "initial_run06_neural_corr": initial_val,
        "final_run06_neural_corr": final_val,
        "history": history,
        "run07_accessed": False,
        "notes": [
            "Run 07 is not read by this training script.",
            "Text-only adaptation is symmetric dropout-view InfoNCE with the frozen E5 representation.",
            "Every tuned arm receives the same text-only pass plus five matched auxiliary optimizer steps per epoch.",
            "Validation correlation is descriptive only; epochs are fixed and there is no early stopping."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tuning output: {out}")
    print(f"Arm={args.arm} | initial run06 corr={initial_val:.6f} | final={final_val:.6f}")
    print("Run-07 was not accessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
