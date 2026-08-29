#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np

MODEL_ID = "google-bert/bert-base-multilingual-cased"
MODEL_REVISION = "c298d193a40f7d74951e9b8de1e278db2723f10b"
PREFIX = ""
MAX_LENGTH = 128


def load_adapter(adapter: Path, device: str):
    from peft import PeftModel
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    adapter = Path(adapter)
    if not adapter.is_dir():
        raise FileNotFoundError(adapter)
    tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    base = AutoModelForMaskedLM.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = PeftModel.from_pretrained(base, adapter)
    model.eval().to(device)
    return tok, model


def encode_texts(model, tokenizer, texts: list[str], device: str, batch_size: int = 64) -> np.ndarray:
    import torch

    all_vec = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        enc = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_special_tokens_mask=True,
            return_tensors="pt",
        )
        special = enc.pop("special_tokens_mask")
        attention = enc["attention_mask"]
        mask = attention.bool() & ~special.bool()
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.inference_mode():
            out = model(**enc, output_hidden_states=True, return_dict=True)
            hidden = out.hidden_states[-1]
            m = mask.to(device).to(hidden.dtype).unsqueeze(-1)
            pooled = (hidden * m).sum(dim=1) / m.sum(dim=1).clamp_min(1.0)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        all_vec.append(pooled.cpu().numpy().astype(np.float64))
    return np.concatenate(all_vec, axis=0)
