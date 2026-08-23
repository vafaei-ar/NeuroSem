#!/usr/bin/env python3
"""Run one frozen NeuroSem BERT tuning arm.

Arms:
- base: no parameter updates
- text_only: LoRA + MLM
- neural: LoRA + MLM + genuine residual neural geometry
- shuffled_neural: LoRA + MLM + fixed shuffled neural geometry

Runs 01-05 are training, run 06 is validation, and run 07 is never accessed here.
"""

from __future__ import annotations

import argparse
import json
import math
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
        "summary": json.loads((d / "summary.json").read_text(encoding="utf-8")),
    }


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def pairwise_cosine_distance(x):
    import torch
    x = torch.nn.functional.normalize(x, p=2, dim=1)
    sim = x @ x.T
    iu = torch.triu_indices(x.shape[0], x.shape[0], offset=1, device=x.device)
    return 1.0 - sim[iu[0], iu[1]]


def standardized(x):
    return (x - x.mean()) / x.std(unbiased=False).clamp_min(1e-8)


def clean_row_embeddings(model, tokenizer, texts: list[str], device: str, max_length: int, batch_size: int):
    import torch
    chunks = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_special_tokens_mask=True,
            return_tensors="pt",
        )
        special = encoded.pop("special_tokens_mask")
        attention = encoded["attention_mask"]
        mask = attention.bool() & ~special.bool()
        encoded = {k: v.to(device) for k, v in encoded.items()}
        outputs = model(**encoded, output_hidden_states=True, return_dict=True)
        hidden = outputs.hidden_states[-1]
        mask = mask.to(device).to(hidden.dtype).unsqueeze(-1)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        chunks.append(pooled)
    return torch.cat(chunks, dim=0)


def relational_loss(model, tokenizer, texts, target, device, max_length, geometry_batch_size):
    import torch
    emb = clean_row_embeddings(model, tokenizer, texts, device, max_length, geometry_batch_size)
    d = standardized(pairwise_cosine_distance(emb))
    target_t = torch.as_tensor(target, dtype=d.dtype, device=device)
    if target_t.numel() != d.numel():
        raise RuntimeError(f"Target/model edge mismatch: {target_t.numel()} vs {d.numel()}")
    corr = torch.mean(d * target_t)
    return 1.0 - corr, corr


def make_mlm_batch(tokenizer, texts: list[str], max_length: int, collator, device: str):
    encoded = tokenizer(texts, truncation=True, max_length=max_length, add_special_tokens=True)
    features = [{k: encoded[k][i] for k in encoded} for i in range(len(texts))]
    batch = collator(features)
    return {k: v.to(device) for k, v in batch.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen four-arm NeuroSem BERT LoRA experiment.")
    parser.add_argument("--arm", required=True, choices=["base", "text_only", "neural", "shuffled_neural"])
    parser.add_argument("--config", type=Path, default=Path("configs/bert_neural_tuning_v1.json"))
    parser.add_argument("--target-root", type=Path, default=Path("outputs/bert_neural_tuning_targets_v1"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/bert_neural_tuning_v1"))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--geometry-batch-size", type=int, default=128)
    args = parser.parse_args()

    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from torch.optim import AdamW
    from transformers import AutoModelForMaskedLM, AutoTokenizer, DataCollatorForLanguageModeling

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if cfg["final_holdout_run"] != 7:
        raise SystemExit("Frozen protocol requires run 07 as final holdout")
    train_runs = list(cfg["train_runs"])
    if train_runs != [1, 2, 3, 4, 5] or int(cfg["validation_run"]) != 6:
        raise SystemExit("Frozen v1 split must be train 01-05 and validation 06")

    set_seed(int(cfg["seed"]))
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    runs = {r: load_target_run(args.target_root, r) for r in train_runs + [int(cfg["validation_run"])]}
    train_texts = [(r, t) for r in train_runs for t in runs[r]["texts"]]

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_id"], revision=cfg["model_revision"])
    model = AutoModelForMaskedLM.from_pretrained(cfg["model_id"], revision=cfg["model_revision"])

    if args.arm != "base":
        lora = cfg["lora"]
        peft_cfg = LoraConfig(
            task_type=TaskType.FEATURE_EXTRACTION,
            r=int(lora["rank"]),
            lora_alpha=int(lora["alpha"]),
            lora_dropout=float(lora["dropout"]),
            target_modules=list(lora["target_modules"]),
            bias="none",
        )
        model = get_peft_model(model, peft_cfg)
    model.to(device)

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=True, mlm_probability=float(cfg["mlm_probability"]))
    history: list[dict] = []

    def validation_corr() -> float:
        model.eval()
        with torch.no_grad():
            _, corr = relational_loss(
                model, tokenizer, runs[6]["texts"], runs[6]["neural"], device,
                int(cfg["max_length"]), args.geometry_batch_size,
            )
        model.train()
        return float(corr.detach().cpu())

    initial_val = validation_corr()
    print(f"Arm={args.arm} | initial run-06 neural correlation={initial_val:.6f}")

    if args.arm != "base":
        optimizer = AdamW(model.parameters(), lr=float(cfg["learning_rate"]), weight_decay=float(cfg["weight_decay"]))
        batch_size = int(cfg["batch_size"])
        epochs = int(cfg["epochs"])
        rng = np.random.default_rng(int(cfg["seed"]))

        for epoch in range(1, epochs + 1):
            model.train()
            order = rng.permutation(len(train_texts))
            mlm_losses: list[float] = []

            for start in range(0, len(order), batch_size):
                chosen = [train_texts[i][1] for i in order[start:start + batch_size]]
                batch = make_mlm_batch(tokenizer, chosen, int(cfg["max_length"]), collator, device)
                optimizer.zero_grad(set_to_none=True)
                out = model(**batch, return_dict=True)
                loss = out.loss
                loss.backward()
                optimizer.step()
                mlm_losses.append(float(loss.detach().cpu()))

            aux_mlm: list[float] = []
            rel_losses: list[float] = []
            rel_corrs: list[float] = []
            for run_number in train_runs:
                texts = runs[run_number]["texts"]
                n = min(batch_size, len(texts))
                idx = rng.choice(len(texts), size=n, replace=False)
                aux_texts = [texts[int(i)] for i in idx]
                batch = make_mlm_batch(tokenizer, aux_texts, int(cfg["max_length"]), collator, device)

                optimizer.zero_grad(set_to_none=True)
                mlm_out = model(**batch, return_dict=True)
                total = mlm_out.loss
                aux_mlm.append(float(mlm_out.loss.detach().cpu()))

                if args.arm in {"neural", "shuffled_neural"}:
                    target_key = "neural" if args.arm == "neural" else "shuffled"
                    rel, corr = relational_loss(
                        model, tokenizer, texts, runs[run_number][target_key], device,
                        int(cfg["max_length"]), args.geometry_batch_size,
                    )
                    total = total + float(cfg["neural_loss_weight"]) * rel
                    rel_losses.append(float(rel.detach().cpu()))
                    rel_corrs.append(float(corr.detach().cpu()))

                total.backward()
                optimizer.step()

            val_corr = validation_corr()
            rec = {
                "epoch": epoch,
                "mean_mlm_loss": float(np.mean(mlm_losses)),
                "mean_aux_mlm_loss": float(np.mean(aux_mlm)),
                "mean_relational_loss": None if not rel_losses else float(np.mean(rel_losses)),
                "mean_train_relational_corr": None if not rel_corrs else float(np.mean(rel_corrs)),
                "run06_neural_corr": val_corr,
            }
            history.append(rec)
            print(
                f"epoch {epoch}/{epochs} | mlm={rec['mean_mlm_loss']:.4f} | "
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
        "geometry_batch_size": args.geometry_batch_size,
        "initial_run06_neural_corr": initial_val,
        "final_run06_neural_corr": final_val,
        "history": history,
        "run07_accessed": False,
        "notes": [
            "Run 07 is not read by this training script.",
            "Every tuned arm receives the same standard MLM pass and five auxiliary optimizer steps per epoch.",
            "The text_only auxiliary steps contain MLM only; neural arms add the prespecified relational term to those same-budget steps.",
            "Validation correlation is reported descriptively only; v1 uses fixed epochs and no early stopping."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tuning output: {out}")
    print(f"Arm={args.arm} | initial run06 corr={initial_val:.6f} | final={final_val:.6f}")
    print("Run-07 was not accessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
