#!/usr/bin/env python3
"""Common differentiable geometry/gradient helpers for target compatibility v1."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.tuning.train_e5_neurosem_lora import load_target_run
from scripts.tuning import build_bert_neural_targets as source_builder

MODEL_ID = "intfloat/multilingual-e5-large"
MODEL_REVISION = "3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3"
TEXT_ADAPTER = ROOT / "outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter"
SOURCE_TARGET_ROOT = ROOT / "outputs/bert_neural_tuning_targets_v1"
PREFIX = "query: "
SOURCE_RUNS = [1, 2, 3, 4, 5]
BOOTSTRAP_SEED = 20260926
BOOTSTRAP_N = 10000


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def z_np(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    sd = float(np.std(x, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("degenerate vector for z standardization")
    return (x - float(np.mean(x))) / sd


def standard_design_from_columns(cols: list[np.ndarray]) -> np.ndarray:
    if not cols:
        raise RuntimeError("nuisance design requires >=1 column")
    zcols = []
    n = len(np.asarray(cols[0]).reshape(-1))
    for c in cols:
        v = np.asarray(c, dtype=np.float64).reshape(-1)
        if len(v) != n:
            raise RuntimeError("nuisance column length mismatch")
        sd = float(np.std(v, ddof=0))
        zcols.append((v - float(np.mean(v))) / sd if sd > 0 else np.zeros_like(v))
    return np.column_stack([np.ones(n, dtype=np.float64)] + zcols)


def ranked_design_from_columns(cols: list[np.ndarray]) -> np.ndarray:
    if not cols:
        raise RuntimeError("ranked nuisance design requires >=1 column")
    rz = [source_builder.rank_z(np.asarray(c, dtype=np.float64)) for c in cols]
    n = len(rz[0])
    if any(len(x) != n for x in rz):
        raise RuntimeError("ranked nuisance column length mismatch")
    return np.column_stack([np.ones(n, dtype=np.float64)] + rz)


def residualize_np(y: np.ndarray, design: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    A = np.asarray(design, dtype=np.float64)
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ beta


def residualize_torch(y, design: np.ndarray):
    import torch
    A_np = np.asarray(design, dtype=np.float64)
    pinv_np = np.linalg.pinv(A_np)
    A = torch.as_tensor(A_np, dtype=y.dtype, device=y.device)
    pinv = torch.as_tensor(pinv_np, dtype=y.dtype, device=y.device)
    return y - A @ (pinv @ y)


def z_torch(x):
    return (x - x.mean()) / x.std(unbiased=False).clamp_min(1e-8)


def pairwise_cosine_distance_torch(x):
    import torch
    import torch.nn.functional as F
    x = F.normalize(x, p=2, dim=1)
    iu = torch.triu_indices(x.shape[0], x.shape[0], offset=1, device=x.device)
    return 1.0 - torch.sum(x[iu[0]] * x[iu[1]], dim=1)


def loss_from_model_edges(model_edges, neural_residual: np.ndarray, model_design: np.ndarray):
    import torch
    mr = residualize_torch(model_edges, model_design)
    mz = z_torch(mr)
    nz = torch.as_tensor(z_np(neural_residual), dtype=mz.dtype, device=mz.device)
    if nz.numel() != mz.numel():
        raise RuntimeError(f"model/neural edge mismatch: {mz.numel()} vs {nz.numel()}")
    corr = torch.mean(mz * nz)
    return 1.0 - corr, corr


def encode_grad(model, tokenizer, texts: list[str], device: str, max_length: int, batch_size: int):
    import torch
    chunks = []
    for start in range(0, len(texts), batch_size):
        batch = [PREFIX + t for t in texts[start:start + batch_size]]
        enc = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        attention = enc["attention_mask"].to(device)
        enc = {k: v.to(device) for k, v in enc.items()}
        out = model(**enc, return_dict=True)
        mask = attention.to(out.last_hidden_state.dtype).unsqueeze(-1)
        pooled = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        chunks.append(pooled)
    return torch.cat(chunks, dim=0)


def load_reference_model(device: str):
    from transformers import AutoModel, AutoTokenizer
    from peft import PeftModel

    if not TEXT_ADAPTER.is_dir():
        raise FileNotFoundError(TEXT_ADAPTER)
    tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    base = AutoModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = PeftModel.from_pretrained(base, TEXT_ADAPTER, is_trainable=True)
    model.eval().to(device)

    named = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    if not named:
        raise RuntimeError("no trainable parameters in text-only reference adapter")
    bad = [n for n, _ in named if "lora_" not in n or (".query." not in n and ".value." not in n)]
    if bad:
        raise RuntimeError(f"unexpected trainable parameter names: {bad[:10]}")
    return tok, model, named


def parameter_manifest(named_params) -> dict:
    rows = [{"name": n, "shape": list(p.shape), "numel": int(p.numel())} for n, p in named_params]
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "n_tensors": len(rows),
        "n_parameters": int(sum(r["numel"] for r in rows)),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "tensors": rows,
    }


def flat_grads_from_parameter_grad(named_params, scale: float = 1.0):
    import torch
    parts = []
    for _, p in named_params:
        if p.grad is None:
            raise RuntimeError("missing source parameter gradient")
        parts.append((p.grad.detach() * scale).reshape(-1).float().cpu())
    return torch.cat(parts)


def accumulate_autograd_loss(loss, named_params, dest, retain_graph: bool):
    import torch
    params = [p for _, p in named_params]
    grads = torch.autograd.grad(loss, params, retain_graph=retain_graph, create_graph=False, allow_unused=False)
    off = 0
    for g in grads:
        n = g.numel()
        dest[off:off+n].add_(g.detach().reshape(-1).float().cpu())
        off += n
    if off != dest.numel():
        raise RuntimeError("target gradient accumulation size mismatch")


def source_designs_for_run(run_number: int, texts: list[str]) -> list[np.ndarray]:
    rec = load_target_run(SOURCE_TARGET_ROOT, run_number)
    summary = json.loads((rec["dir"] / "summary.json").read_text(encoding="utf-8"))
    feature_dirs = summary.get("feature_dirs") or {}
    if not feature_dirs:
        raise RuntimeError(f"source run {run_number}: missing feature_dirs")

    orth = source_builder.char_set_jaccard_rdm(texts)
    punct = np.asarray([source_builder.punctuation_count(t) for t in texts], dtype=float)
    punct_rdm = pdist(punct[:, None], metric="cityblock")
    designs = []
    for subject in sorted(feature_dirs):
        raw = Path(str(feature_dirs[subject]))
        d = raw if raw.is_absolute() else ROOT / raw
        meta = source_builder.read_csv(d / "metadata.csv")
        row_texts = [r["text"] for r in meta]
        if row_texts != texts:
            raise RuntimeError(f"source run {run_number}/{subject}: text mismatch")
        position = np.asarray([float(r["run_position_fraction"]) for r in meta], dtype=float)
        duration = np.asarray([float(r["duration_sec"]) for r in meta], dtype=float)
        char_count = np.asarray([float(r["char_count"]) for r in meta], dtype=float)
        chapters = np.asarray([int((r["chapter_marker_context"] or "CH00")[2:]) for r in meta], dtype=int)
        nuisances = [
            pdist(position[:, None], metric="cityblock"),
            pdist(duration[:, None], metric="cityblock"),
            pdist(char_count[:, None], metric="cityblock"),
            pdist(chapters[:, None], metric="hamming"),
            orth,
            punct_rdm,
        ]
        designs.append(ranked_design_from_columns(nuisances))
    return designs


def compute_source_gradient(model, tokenizer, named_params, device: str):
    import torch
    model.zero_grad(set_to_none=True)
    run_rows = []
    for run_number in SOURCE_RUNS:
        rec = load_target_run(SOURCE_TARGET_ROOT, run_number)
        texts = list(rec["texts"])
        target = np.asarray(rec["neural"], dtype=np.float64)
        emb = encode_grad(model, tokenizer, texts, device, max_length=64, batch_size=16)
        edges = pairwise_cosine_distance_torch(emb)
        designs = source_designs_for_run(run_number, texts)
        model_resid = None
        for A in designs:
            rr = residualize_torch(edges, A)
            model_resid = rr if model_resid is None else model_resid + rr
        model_resid = model_resid / float(len(designs))
        mz = z_torch(model_resid)
        nz = torch.as_tensor(z_np(target), dtype=mz.dtype, device=mz.device)
        if mz.numel() != nz.numel():
            raise RuntimeError(f"source run {run_number}: edge mismatch")
        corr = torch.mean(mz * nz)
        loss = 1.0 - corr
        (loss / len(SOURCE_RUNS)).backward()
        run_rows.append({
            "run": run_number,
            "n_items": len(texts),
            "n_edges": int(edges.numel()),
            "n_source_participant_designs": len(designs),
            "reference_corr": float(corr.detach().cpu()),
            "reference_loss": float(loss.detach().cpu()),
        })
        del emb, edges, model_resid, mz, nz, corr, loss
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    source = flat_grads_from_parameter_grad(named_params)
    model.zero_grad(set_to_none=True)
    norm = float(torch.linalg.vector_norm(source.double()))
    if not np.isfinite(norm) or norm <= 0:
        raise RuntimeError("degenerate source gradient")
    digest = hashlib.sha256(source.numpy().tobytes()).hexdigest()
    return source, {"norm": norm, "sha256_float32": digest, "runs": run_rows}


def bootstrap_mean_ci(values: list[float]) -> list[float]:
    a = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(a), size=(BOOTSTRAP_N, len(a)))
    means = a[idx].mean(axis=1)
    q = np.quantile(means, [0.025, 0.975])
    return [float(q[0]), float(q[1])]
