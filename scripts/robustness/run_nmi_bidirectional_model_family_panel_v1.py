#!/usr/bin/env python3
"""Post-confirmatory bidirectional multilingual model-family panel.

One RunRelay job orchestrates 6 fixed models x 3 fixed seeds x 2 source directions.
Each unit trains matched text-only and lambda=.10 neural-guided LoRA arms under a
common sentence-geometry protocol, then evaluates one frozen cross-modal target.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import queue
import random
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy.signal import fftconvolve
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analysis.run_smn4lang_fmri_reliability import (
    SUBJECTS as FMRI_SUBJECTS,
    STORIES as FMRI_STORIES,
    TR,
    MASK_THRESHOLD,
    canonical_hrf,
    corr_rdm_vector_from_bold,
    residualize as fmri_residualize,
    fisher_mean as fmri_fisher_mean,
    bootstrap_ci as fmri_bootstrap_ci,
    exact_signflip_p as fmri_exact_signflip_p,
)
from scripts.robustness.run_nmi_bidirectional_fmri_source_calibration_v1 import (
    TRAIN_STORIES as FMRI_TRAIN_STORIES,
    VAL_STORIES as FMRI_VAL_STORIES,
    EPOCH_SCHEDULE as FMRI_EPOCH_SCHEDULE,
)
from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import story_context, fresh_lana_mask
from scripts.tuning.train_bert_neurosem_lora import load_target_run
from scripts.analysis.run_zuco2_nr_primary_representation_reliability import (
    EXPECTED,
    fisher_mean as zuco_fisher_mean,
    load_inventory,
    load_material_rows,
    load_run_features,
    nuisance_matrix,
    rdm_edges,
    residualize as zuco_residualize,
)

PROTOCOL = "docs/22_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_V1.md"
SEEDS = [20260829, 20260830, 20260831]
LAMBDA = 0.10
TEXT_TEMP = 0.05
MAX_LENGTH = 64
TEXT_BATCH = 24
GEOM_BATCH = 8
EPOCHS = 5
LR = 2e-4
WEIGHT_DECAY = 0.01
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
ROOT = Path("outputs/nmi_bidirectional_model_family_panel_v1")
LATEST = ROOT / "latest"
FMRI_CACHE = ROOT / "cache" / "fmri_neural"

MODEL_SPECS = {
    "e5_large": {
        "model_id": "intfloat/multilingual-e5-large",
        "class": "E5 retrieval/sentence embedding",
        "prefix": "query: ",
    },
    "e5_base": {
        "model_id": "intfloat/multilingual-e5-base",
        "class": "E5 retrieval/sentence embedding",
        "prefix": "query: ",
    },
    "multilingual_mpnet": {
        "model_id": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "class": "other multilingual sentence embedding",
        "prefix": "",
    },
    "multilingual_minilm": {
        "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "class": "other multilingual sentence embedding",
        "prefix": "",
    },
    "xlmr_base": {
        "model_id": "FacebookAI/xlm-roberta-base",
        "class": "generic multilingual MLM encoder",
        "prefix": "",
    },
    "mbert": {
        "model_id": "google-bert/bert-base-multilingual-cased",
        "class": "generic multilingual MLM encoder",
        "prefix": "",
    },
}


def atomic_progress(current: int, total: int, phase: str, message: str = "") -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw); p.parent.mkdir(parents=True, exist_ok=True)
    d = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else None,
        "phase": phase,
        "message": message,
        "unit": "model-seed-direction units",
        "updated_at_epoch": time.time(),
    }
    t = p.with_suffix(p.suffix + ".tmp")
    t.write_text(json.dumps(d), encoding="utf-8")
    os.replace(t, p)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def set_seed(seed: int) -> None:
    random.seed(seed); np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def model_prefix(spec: dict) -> str:
    return str(spec.get("prefix", ""))


def pooled_embeddings(model, tokenizer, texts: list[str], device: str, prefix: str, batch_size: int, grad: bool = True):
    import torch
    chunks = []
    context = torch.enable_grad() if grad else torch.inference_mode()
    with context:
        for start in range(0, len(texts), batch_size):
            batch = [prefix + str(t) for t in texts[start:start + batch_size]]
            enc = tokenizer(batch, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
            att = enc["attention_mask"].to(device)
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc, return_dict=True)
            hidden = out.last_hidden_state
            mask = att.to(hidden.dtype).unsqueeze(-1)
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1.0)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            chunks.append(pooled)
    return torch.cat(chunks, dim=0)


def pairdist_torch(x):
    import torch
    sim = x @ x.T
    iu = torch.triu_indices(x.shape[0], x.shape[0], 1, device=x.device)
    return 1.0 - sim[iu[0], iu[1]]


def z_torch(x):
    return (x - x.mean()) / x.std(unbiased=False).clamp_min(1e-8)


def text_loss(model, tokenizer, texts: list[str], device: str, prefix: str):
    import torch
    model.train()
    a = pooled_embeddings(model, tokenizer, texts, device, prefix, TEXT_BATCH, grad=True)
    b = pooled_embeddings(model, tokenizer, texts, device, prefix, TEXT_BATCH, grad=True)
    logits = (a @ b.T) / TEXT_TEMP
    labels = torch.arange(len(texts), device=device)
    return 0.5 * (torch.nn.functional.cross_entropy(logits, labels) + torch.nn.functional.cross_entropy(logits.T, labels))


def relational_loss_simple(model, tokenizer, texts: list[str], target: np.ndarray, device: str, prefix: str):
    import torch
    was = model.training; model.eval()
    emb = pooled_embeddings(model, tokenizer, texts, device, prefix, GEOM_BATCH, grad=True)
    d = z_torch(pairdist_torch(emb))
    t = torch.as_tensor(target, dtype=d.dtype, device=device)
    if d.numel() != t.numel():
        raise RuntimeError(f"edge mismatch: model={d.numel()} target={t.numel()}")
    corr = (d * t).mean()
    if was: model.train()
    return 1.0 - corr, corr


def residualize_torch(y, nuisances: list[np.ndarray]):
    import torch
    cols = [torch.ones_like(y)] + [torch.as_tensor(v, dtype=y.dtype, device=y.device) for v in nuisances]
    X = torch.stack(cols, 1)
    beta = torch.linalg.lstsq(X, y[:, None]).solution[:, 0]
    return y - X @ beta


def fmri_neural_loss(model, tokenizer, ctx: dict, target: np.ndarray, device: str, prefix: str, hrf: np.ndarray):
    import torch
    was = model.training; model.eval()
    emb = pooled_embeddings(model, tokenizer, ctx["prefixes"], device, prefix, GEOM_BATCH, grad=True)
    n_tp = ctx["n_tp"]; d_model = emb.shape[1]
    events = torch.zeros((n_tp, d_model), dtype=emb.dtype, device=device)
    idx = torch.as_tensor([int(math.floor(float(s) / TR)) for s in ctx["starts"]], device=device)
    good = (idx >= 0) & (idx < n_tp)
    events.index_add_(0, idx[good], emb[good])
    drive = torch.zeros_like(events)
    h = torch.as_tensor(hrf, dtype=events.dtype, device=device)
    for k in range(min(len(hrf), n_tp)):
        drive[k:] += events[:n_tp-k] * h[k]
    states = torch.nn.functional.normalize(drive[torch.as_tensor(ctx["valid_idx"], device=device)], p=2, dim=1)
    dist = pairdist_torch(states)
    dist = z_torch(residualize_torch(dist, ctx["nuisance"]))
    t = torch.as_tensor(target, dtype=dist.dtype, device=device)
    if dist.numel() != t.numel():
        raise RuntimeError(f"fMRI edge mismatch: model={dist.numel()} target={t.numel()}")
    corr = (dist * t).mean()
    if was: model.train()
    return 1.0 - corr, corr


def lora_targets(base_model) -> list[str]:
    names = [n.rsplit(".", 1)[-1] for n, _ in base_model.named_modules()]
    s = set(names)
    if "query" in s and "value" in s:
        return ["query", "value"]
    if "q" in s and "v" in s:
        return ["q", "v"]
    raise RuntimeError("Could not identify query/value attention projection names for LoRA")


def new_lora_model(model_id: str, revision: str, device: str):
    from transformers import AutoModel, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
    base = AutoModel.from_pretrained(model_id, revision=revision)
    targets = lora_targets(base)
    cfg = LoraConfig(r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT, target_modules=targets, bias="none")
    model = get_peft_model(base, cfg)
    if hasattr(model, "gradient_checkpointing_enable"):
        try: model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        except TypeError: model.gradient_checkpointing_enable()
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    model.to(device)
    return tok, model, targets


def save_arm(model, tokenizer, root: Path, summary: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(root / "adapter")
    tokenizer.save_pretrained(root / "adapter")
    (root / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def train_eeg_source(spec: dict, revision: str, seed: int, arm: str, out: Path, device: str) -> dict:
    import torch
    from torch.optim import AdamW
    set_seed(seed)
    prefix = model_prefix(spec)
    runs = {r: load_target_run(Path("outputs/bert_neural_tuning_targets_v1"), r) for r in range(1, 7)}
    train_rows = [(r, t) for r in range(1, 6) for t in runs[r]["texts"]]
    tok, model, targets = new_lora_model(spec["model_id"], revision, device)
    opt = AdamW([p for p in model.parameters() if p.requires_grad], lr=LR, weight_decay=WEIGHT_DECAY)
    rng = np.random.default_rng(seed)
    hist = []
    for epoch in range(1, EPOCHS + 1):
        order = rng.permutation(len(train_rows)); losses = []; corrs = []
        for start in range(0, len(order), TEXT_BATCH):
            texts = [train_rows[int(i)][1] for i in order[start:start+TEXT_BATCH]]
            if len(texts) < 2: continue
            opt.zero_grad(set_to_none=True); loss = text_loss(model, tok, texts, device, prefix); loss.backward(); opt.step(); losses.append(float(loss.detach().cpu()))
        for r in range(1, 6):
            texts = runs[r]["texts"]
            n = min(TEXT_BATCH, len(texts)); idx = rng.choice(len(texts), size=n, replace=False); aux = [texts[int(i)] for i in idx]
            opt.zero_grad(set_to_none=True); tl = text_loss(model, tok, aux, device, prefix); tl.backward(); del tl
            if arm == "neural":
                nl, c = relational_loss_simple(model, tok, texts, runs[r]["neural"], device, prefix); (LAMBDA * nl).backward(); corrs.append(float(c.detach().cpu())); del nl, c
            opt.step(); torch.cuda.empty_cache()
        model.eval()
        with torch.no_grad():
            _, vc = relational_loss_simple(model, tok, runs[6]["texts"], runs[6]["neural"], device, prefix)
        hist.append({"epoch": epoch, "mean_text_loss": float(np.mean(losses)), "mean_train_neural_corr": None if not corrs else float(np.mean(corrs)), "run06_corr": float(vc.detach().cpu())})
    final = hist[-1]["run06_corr"]
    summary = {"direction": "eeg_to_fmri", "arm": arm, "seed": seed, "model_id": spec["model_id"], "revision": revision, "prefix": prefix, "lambda": 0.0 if arm == "text" else LAMBDA, "lora_targets": targets, "history": hist, "source_validation_corr": final, "run07_accessed": False}
    save_arm(model, tok, out / arm, summary)
    del model; torch.cuda.empty_cache()
    return summary


def load_fmri_source_targets() -> tuple[dict[int, dict], dict[int, np.ndarray], np.ndarray]:
    source = Path("outputs/nmi_bidirectional_fmri_source_v1/latest")
    hrf = canonical_hrf(TR); data = Path("data/raw/smn4lang").resolve()
    stories = sorted(set(FMRI_TRAIN_STORIES + FMRI_VAL_STORIES))
    contexts = {s: story_context(data, s, hrf) for s in stories}
    targets = {}
    for s in stories:
        p = source / "targets" / f"story_{s:02d}.npz"
        if not p.exists(): raise FileNotFoundError(p)
        targets[s] = np.load(p)["target"].astype(np.float32)
    return contexts, targets, hrf


def train_fmri_source(spec: dict, revision: str, seed: int, arm: str, out: Path, device: str) -> dict:
    import torch
    from torch.optim import AdamW
    set_seed(seed); prefix = model_prefix(spec)
    contexts, targets, hrf = load_fmri_source_targets()
    tok, model, ltargets = new_lora_model(spec["model_id"], revision, device)
    opt = AdamW([p for p in model.parameters() if p.requires_grad], lr=LR, weight_decay=WEIGHT_DECAY)
    hist = []
    for epoch, stories in enumerate(FMRI_EPOCH_SCHEDULE, 1):
        corrs = []
        for s in stories:
            prefixes = contexts[s]["prefixes"]
            idx = np.linspace(0, len(prefixes)-1, min(32, len(prefixes)), dtype=int)
            aux = [prefixes[int(i)] for i in idx]
            opt.zero_grad(set_to_none=True); tl = text_loss(model, tok, aux, device, prefix); tl.backward(); del tl
            if arm == "neural":
                nl, c = fmri_neural_loss(model, tok, contexts[s], targets[s], device, prefix, hrf); (LAMBDA * nl).backward(); corrs.append(float(c.detach().cpu())); del nl, c
            opt.step(); torch.cuda.empty_cache()
        hist.append({"epoch": epoch, "stories": stories, "mean_train_fmri_corr": None if not corrs else float(np.mean(corrs))})
    model.eval(); vals = []
    with torch.no_grad():
        for s in FMRI_VAL_STORIES:
            _, c = fmri_neural_loss(model, tok, contexts[s], targets[s], device, prefix, hrf); vals.append(float(c.detach().cpu()))
    summary = {"direction": "fmri_to_eeg", "arm": arm, "seed": seed, "model_id": spec["model_id"], "revision": revision, "prefix": prefix, "lambda": 0.0 if arm == "text" else LAMBDA, "lora_targets": ltargets, "history": hist, "source_validation_story_corrs": vals, "source_validation_mean": float(np.mean(vals))}
    save_arm(model, tok, out / arm, summary)
    del model; torch.cuda.empty_cache()
    return summary


def load_adapter_generic(spec: dict, revision: str, adapter: Path, device: str):
    from transformers import AutoModel, AutoTokenizer
    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained(spec["model_id"], revision=revision)
    base = AutoModel.from_pretrained(spec["model_id"], revision=revision)
    model = PeftModel.from_pretrained(base, adapter).to(device); model.eval()
    return tok, model


def safe_spearman(a, b) -> float:
    r = float(spearmanr(np.asarray(a, float), np.asarray(b, float)).statistic)
    if not np.isfinite(r): raise RuntimeError("non-finite Spearman")
    return r


def build_fmri_cache() -> None:
    done = FMRI_CACHE / "_COMPLETE.json"
    if done.exists(): return
    reliability = json.loads(Path("outputs/smn4lang_fmri_reliability/latest/summary.json").read_text())
    if not reliability.get("reliability_gate_pass"): raise RuntimeError("fMRI reliability gate failed")
    root = Path("data/raw/smn4lang").resolve(); hrf = canonical_hrf(TR)
    runtime = ROOT / "cache" / "runtime_atlas"; mask = fresh_lana_mask(root, runtime)
    FMRI_CACHE.mkdir(parents=True, exist_ok=True)
    for story in FMRI_STORIES:
        p = FMRI_CACHE / f"story_{story:02d}.npz"
        if p.exists(): continue
        ctx = story_context(root, story, hrf); payload = {}
        for sub in FMRI_SUBJECTS:
            bold = root / f"derivatives/preprocessed_data/{sub}/MNI/{sub}_task-RDR_run-{story}_bold.nii.gz"
            neural = corr_rdm_vector_from_bold(bold, mask, ctx["valid_idx"])
            payload[sub.replace("-", "_")] = fmri_residualize(neural, ctx["nuisance"]).astype(np.float32)
        np.savez_compressed(p, **payload)
    done.write_text(json.dumps({"n_subjects": len(FMRI_SUBJECTS), "n_stories": len(FMRI_STORIES), "mask_threshold": MASK_THRESHOLD}, indent=2) + "\n")


def model_fmri_residual(model, tok, ctx: dict, device: str, prefix: str, hrf: np.ndarray) -> np.ndarray:
    emb = pooled_embeddings(model, tok, ctx["prefixes"], device, prefix, GEOM_BATCH, grad=False).detach().cpu().numpy()
    events = np.zeros((ctx["n_tp"], emb.shape[1]), dtype=np.float64)
    for start, vec in zip(ctx["starts"], emb):
        idx = int(math.floor(float(start) / TR))
        if 0 <= idx < ctx["n_tp"]: events[idx] += vec
    drive = fftconvolve(events, hrf[:, None], mode="full", axes=0)[:ctx["n_tp"]]
    x = drive[ctx["valid_idx"]]; rdm = pdist(x, metric="cosine")
    return fmri_residualize(rdm, ctx["nuisance"])


def evaluate_fmri(spec: dict, revision: str, unit: Path, device: str) -> dict:
    import torch
    root = Path("data/raw/smn4lang").resolve(); hrf = canonical_hrf(TR)
    contexts = {s: story_context(root, s, hrf) for s in FMRI_STORIES}
    arm_vals = {"text": {s: [] for s in FMRI_SUBJECTS}, "neural": {s: [] for s in FMRI_SUBJECTS}}
    for arm in ["text", "neural"]:
        tok, model = load_adapter_generic(spec, revision, unit / arm / "adapter", device)
        for story in FMRI_STORIES:
            mr = model_fmri_residual(model, tok, contexts[story], device, model_prefix(spec), hrf)
            cache = np.load(FMRI_CACHE / f"story_{story:02d}.npz")
            for sub in FMRI_SUBJECTS:
                nr = cache[sub.replace("-", "_")]
                arm_vals[arm][sub].append(safe_spearman(nr, mr))
        del model; torch.cuda.empty_cache()
    rows = []; deltas = []
    for sub in FMRI_SUBJECTS:
        a0 = fmri_fisher_mean(arm_vals["text"][sub]); a1 = fmri_fisher_mean(arm_vals["neural"][sub]); d = a1-a0; deltas.append(d); rows.append({"subject":sub,"text_rsa":a0,"neural_rsa":a1,"delta":d})
    d = np.asarray(deltas, float); ci = fmri_bootstrap_ci(d); p = fmri_exact_signflip_p(d)
    write_csv(unit / "external_participant_results.csv", rows)
    return {"target":"SMN4Lang fMRI","n_subjects":len(d),"mean_delta":float(d.mean()),"median_delta":float(np.median(d)),"n_positive":int(np.sum(d>0)),"fraction_positive":float(np.mean(d>0)),"bootstrap_95ci":[float(ci[0]),float(ci[1])],"exact_one_sided_signflip_p":float(p)}


def exact_signflip(diffs: np.ndarray) -> float:
    d = np.asarray(diffs, float); n=len(d); obs=float(d.mean()); count=0
    for mask in range(1<<n):
        signs=np.array([1.0 if (mask>>i)&1 else -1.0 for i in range(n)])
        if float(np.mean(d*signs)) >= obs-1e-15: count += 1
    return count / float(1<<n)


def bootstrap_ci(diffs: np.ndarray, seed: int) -> list[float]:
    d=np.asarray(diffs,float); rng=np.random.default_rng(seed); means=np.empty(10000,float)
    for i in range(10000): means[i]=rng.choice(d,size=len(d),replace=True).mean()
    return [float(np.percentile(means,2.5)),float(np.percentile(means,97.5))]


def evaluate_zuco(spec: dict, revision: str, unit: Path, device: str, seed: int) -> dict:
    import torch
    data_root=Path("data/raw/zuco2_nr"); input_freeze=Path("outputs/zuco2_nr_input_materialization/latest/summary.json"); mapping_freeze=Path("outputs/zuco2_nr_format_probe/latest/summary.json"); stimulus_root=Path("data/raw/zuco2_probe")
    cohort=json.loads(input_freeze.read_text()); mapping=json.loads(mapping_freeze.read_text()); ready=list(cohort.get("ready_subjects_all_7_runs") or [])
    if len(ready)!=17 or "YTL" in ready: raise RuntimeError("unexpected ZuCo cohort")
    maps={r["run"]:r for r in mapping.get("wordcount_mapping_diagnostics",[])}; inventory=load_inventory(input_freeze.parent/"session_inventory.csv"); path_by={}
    for r in inventory:
        if r.get("subject") in ready and str(r.get("ready","")).lower()=="true": path_by[(r["subject"],int(r["run"]))]=data_root.resolve()/r["osf_path"]
    texts_by_run={}; nuis={}; flat=[]
    for run in range(1,8):
        rows=load_material_rows(stimulus_root/"task_materials"/f"nr_{run}.csv"); selected=maps[f"NR{run}"]["selected_material_rows_1based"]; texts=[str(rows[i-1][2]).strip() for i in selected]; texts_by_run[run]=texts; nuis[run]=nuisance_matrix(texts); flat.extend(texts)
    model_edges={}
    for arm in ["text","neural"]:
        tok, model=load_adapter_generic(spec,revision,unit/arm/"adapter",device); emb=pooled_embeddings(model,tok,flat,device,model_prefix(spec),64,grad=False).detach().cpu().numpy(); model_edges[arm]={}; off=0
        for run in range(1,8):
            n=EXPECTED[run]; model_edges[arm][run]=pdist(emb[off:off+n],metric="cosine"); off+=n
        del model; torch.cuda.empty_cache()
    by={s:{"text":[],"neural":[]} for s in ready}
    for sub in ready:
        for run in range(1,8):
            feats,_=load_run_features(path_by[(sub,run)],EXPECTED[run]); nr=zuco_residualize(rdm_edges(feats["row_mean_all"]),nuis[run])
            for arm in ["text","neural"]:
                mr=zuco_residualize(model_edges[arm][run],nuis[run]); by[sub][arm].append(safe_spearman(nr,mr))
    rows=[]; ds=[]
    for sub in ready:
        a0=zuco_fisher_mean(by[sub]["text"]); a1=zuco_fisher_mean(by[sub]["neural"]); d=a1-a0; ds.append(d); rows.append({"subject":sub,"text_rsa":a0,"neural_rsa":a1,"delta":d})
    d=np.asarray(ds,float); write_csv(unit/"external_participant_results.csv",rows)
    return {"target":"ZuCo EEG","n_subjects":len(d),"mean_delta":float(d.mean()),"median_delta":float(np.median(d)),"n_positive":int(np.sum(d>0)),"fraction_positive":float(np.mean(d>0)),"bootstrap_95ci":bootstrap_ci(d,seed),"exact_one_sided_signflip_p":float(exact_signflip(d))}


def worker(args) -> int:
    import torch
    if not torch.cuda.is_available(): raise RuntimeError("GPU required")
    spec=dict(MODEL_SPECS[args.model_key]); revision=args.revision; seed=int(args.seed); direction=args.direction
    unit=ROOT/"units"/args.model_key/f"seed_{seed}"/direction; unit.mkdir(parents=True,exist_ok=True)
    if direction=="eeg_to_fmri":
        s0=train_eeg_source(spec,revision,seed,"text",unit,"cuda"); s1=train_eeg_source(spec,revision,seed,"neural",unit,"cuda"); ext=evaluate_fmri(spec,revision,unit,"cuda")
        source_delta=float(s1["source_validation_corr"]-s0["source_validation_corr"])
    elif direction=="fmri_to_eeg":
        s0=train_fmri_source(spec,revision,seed,"text",unit,"cuda"); s1=train_fmri_source(spec,revision,seed,"neural",unit,"cuda"); ext=evaluate_zuco(spec,revision,unit,"cuda",seed)
        source_delta=float(s1["source_validation_mean"]-s0["source_validation_mean"])
    else: raise ValueError(direction)
    payload={"model_key":args.model_key,"model_id":spec["model_id"],"model_class":spec["class"],"revision":revision,"seed":seed,"direction":direction,"lambda":LAMBDA,"source_validation_delta_neural_minus_text":source_delta,"external_result":ext,"common_protocol":{"pooling":"attention-mask mean final hidden, L2-normalized","text_objective":"symmetric dropout-view InfoNCE, temperature .05","lora":"q/v r8 alpha16 dropout .05","epochs":5,"lr":LR,"weight_decay":WEIGHT_DECAY}}
    (unit/"summary.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(payload,ensure_ascii=False),flush=True); return 0


def resolve_models() -> dict:
    from huggingface_hub import HfApi
    api=HfApi(); out={}
    for key,spec in MODEL_SPECS.items():
        info=api.model_info(spec["model_id"],revision="main")
        if not info.sha: raise RuntimeError(f"No immutable SHA resolved for {spec['model_id']}")
        out[key]={**spec,"revision":info.sha}
    return out


def visible_gpu_tokens() -> list[str]:
    raw=os.environ.get("CUDA_VISIBLE_DEVICES","").strip()
    if raw:
        xs=[x.strip() for x in raw.split(",") if x.strip()]
        if xs: return xs
    import torch
    return [str(i) for i in range(torch.cuda.device_count())]


def main_orchestrator() -> int:
    LATEST.mkdir(parents=True,exist_ok=True)
    resolved=resolve_models(); (LATEST/"resolved_models.json").write_text(json.dumps(resolved,indent=2,ensure_ascii=False)+"\n")
    build_fmri_cache()
    gpus=visible_gpu_tokens()
    if len(gpus)<2: raise RuntimeError(f"Panel requires two visible GPUs; found {gpus}")
    gpus=gpus[:2]; slots=queue.Queue()
    for g in gpus: slots.put(g)
    units=[(k,seed,d) for k in MODEL_SPECS for seed in SEEDS for d in ["eeg_to_fmri","fmri_to_eeg"]]
    total=len(units); atomic_progress(0,total,"Bidirectional model-family panel","Resolved models and built frozen fMRI cache")
    lock=threading.Lock(); completed=0; results=[]; errors=[]

    def run_one(item):
        nonlocal completed
        key,seed,direction=item; gpu=slots.get()
        try:
            env=os.environ.copy(); env["CUDA_VISIBLE_DEVICES"]=gpu
            cmd=[sys.executable,str(Path(__file__).resolve()),"--worker","--model-key",key,"--seed",str(seed),"--direction",direction,"--revision",resolved[key]["revision"]]
            print("+", " ".join(cmd), "GPU", gpu, flush=True)
            proc=subprocess.run(cmd,env=env,text=True,capture_output=True)
            unit=ROOT/"units"/key/f"seed_{seed}"/direction
            if proc.returncode!=0:
                err={"model_key":key,"seed":seed,"direction":direction,"returncode":proc.returncode,"stdout_tail":proc.stdout[-4000:],"stderr_tail":proc.stderr[-4000:]}
                return False,err
            summary=json.loads((unit/"summary.json").read_text())
            return True,summary
        finally:
            slots.put(gpu)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs={pool.submit(run_one,u):u for u in units}
        for fut in as_completed(futs):
            ok,payload=fut.result()
            with lock:
                if ok: results.append(payload)
                else: errors.append(payload)
                completed+=1; atomic_progress(completed,total,"Bidirectional model-family panel",f"Completed {completed}/{total} fixed units")

    rows=[]
    for r in sorted(results,key=lambda x:(x["model_key"],x["direction"],x["seed"])):
        e=r["external_result"]
        rows.append({"model_key":r["model_key"],"model_id":r["model_id"],"model_class":r["model_class"],"revision":r["revision"],"direction":r["direction"],"seed":r["seed"],"source_validation_delta":r["source_validation_delta_neural_minus_text"],"external_mean_delta":e["mean_delta"],"external_median_delta":e["median_delta"],"external_n_positive":e["n_positive"],"external_fraction_positive":e["fraction_positive"],"external_ci_low":e["bootstrap_95ci"][0],"external_ci_high":e["bootstrap_95ci"][1],"external_one_sided_p":e["exact_one_sided_signflip_p"]})
    write_csv(LATEST/"model_seed_direction_results.csv",rows)

    model_summary=[]
    for key,spec in MODEL_SPECS.items():
        for direction in ["eeg_to_fmri","fmri_to_eeg"]:
            rr=[r for r in results if r["model_key"]==key and r["direction"]==direction]
            vals=[r["external_result"]["mean_delta"] for r in rr]
            model_summary.append({"model_key":key,"model_id":spec["model_id"],"model_class":spec["class"],"direction":direction,"n_completed_seeds":len(rr),"seed_mean_deltas":vals,"mean_of_seed_mean_deltas":None if not vals else float(np.mean(vals)),"all_completed_seed_means_positive":None if not vals else bool(all(v>0 for v in vals)),"source_mean_delta":None if not rr else float(np.mean([r["source_validation_delta_neural_minus_text"] for r in rr]))})

    family_summary=[]
    classes=sorted(set(s["class"] for s in MODEL_SPECS.values()))
    for cls in classes:
        for direction in ["eeg_to_fmri","fmri_to_eeg"]:
            members=[m for m in model_summary if m["model_class"]==cls and m["direction"]==direction and m["mean_of_seed_mean_deltas"] is not None]
            family_summary.append({"model_class":cls,"direction":direction,"n_models":len(members),"member_model_means":{m["model_key"]:m["mean_of_seed_mean_deltas"] for m in members},"descriptive_mean_across_models":None if not members else float(np.mean([m["mean_of_seed_mean_deltas"] for m in members]))})

    payload={"schema_version":1,"analysis_stage":"post-confirmatory explanatory bidirectional model-family panel","protocol":PROTOCOL,"fixed_lambda":LAMBDA,"seeds":SEEDS,"resolved_models":resolved,"n_planned_units":total,"n_completed_units":len(results),"errors":errors,"model_direction_summary":model_summary,"descriptive_family_summary":family_summary,"guardrails":["Fixed six-model panel, three seeds and lambda=.10 before execution.","Common pooling/text/LoRA protocol across models; no model-specific rescue tuning.","ChineseEEG run-07 is not read in EEG-source training.","SMN4Lang fMRI and ZuCo external targets use previously frozen pipelines.","Family summaries are descriptive with two fixed models per class, not population inference over arbitrary architectures."]}
    (LATEST/"summary.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    if errors:
        print(json.dumps({"status":"partial_failure","n_errors":len(errors)},indent=2),flush=True); return 1
    print(json.dumps({"status":"ok","n_units":len(results),"summary":str((LATEST/'summary.json').resolve())},indent=2),flush=True); return 0


def parse_args():
    ap=argparse.ArgumentParser(); ap.add_argument("--worker",action="store_true"); ap.add_argument("--model-key",choices=list(MODEL_SPECS)); ap.add_argument("--seed",type=int); ap.add_argument("--direction",choices=["eeg_to_fmri","fmri_to_eeg"]); ap.add_argument("--revision")
    return ap.parse_args()


def main() -> int:
    args=parse_args()
    if args.worker:
        if args.model_key is None or args.seed is None or args.direction is None or not args.revision: raise SystemExit("worker arguments incomplete")
        return worker(args)
    return main_orchestrator()


if __name__ == "__main__":
    raise SystemExit(main())
