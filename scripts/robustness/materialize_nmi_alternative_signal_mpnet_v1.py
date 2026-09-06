#!/usr/bin/env python3
"""Materialize the frozen structured non-neural MPNet source targets.

This stage is intentionally source-text-only. It reconstructs the same source-row
nuisance structure used by the neural target, but it never reads EEG feature arrays,
neural target values, external target data, transfer outcomes, or manuscript results.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import string
import time
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import rankdata

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "docs/NMI_ALTERNATIVE_SIGNAL_SURROGATE_V1.md"
SOURCE_TARGET_ROOT = REPO_ROOT / "outputs/bert_neural_tuning_targets_v1"
OUT = REPO_ROOT / "outputs/nmi_alternative_signal_mpnet_targets_v1/latest"
MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
RUNS = [1, 2, 3, 4, 5, 6]
MAX_LENGTH = 64
BATCH_SIZE = 64
NUISANCE_LABELS = [
    "run_position_lag",
    "duration_difference",
    "character_count_difference",
    "chapter_mismatch",
    "character_set_jaccard_distance",
    "punctuation_count_difference",
]


def atomic_progress(current: int, total: int, phase: str, message: str = "") -> None:
    raw = os.environ.get("RUNRELAY_PROGRESS_FILE")
    if not raw:
        return
    p = Path(raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "current": current,
        "total": total,
        "fraction": current / total if total else None,
        "phase": phase,
        "message": message,
        "unit": "source runs",
        "updated_at_epoch": time.time(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def latest_dir(root: Path, required: str) -> Path:
    candidates = sorted(
        [d for d in root.iterdir() if d.is_dir() and (d / required).is_file()]
    ) if root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No directory containing {required} under {root}")
    return candidates[-1]


def rank_z(x: np.ndarray) -> np.ndarray:
    r = rankdata(np.asarray(x, dtype=np.float64), method="average")
    r -= r.mean()
    sd = r.std()
    if sd == 0:
        raise RuntimeError("Zero-variance ranked vector")
    return r / sd


def residualize_ranked(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    X = np.column_stack([np.ones_like(yr), *[rank_z(n) for n in nuisances]])
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    resid -= resid.mean()
    sd = resid.std()
    if sd == 0:
        raise RuntimeError("Zero-variance residual target")
    return resid / sd


def char_set_jaccard_rdm(texts: list[str]) -> np.ndarray:
    sets = [set(t) for t in texts]
    out: list[float] = []
    for i in range(len(sets) - 1):
        for j in range(i + 1, len(sets)):
            union = len(sets[i] | sets[j])
            sim = len(sets[i] & sets[j]) / union if union else 1.0
            out.append(1.0 - sim)
    return np.asarray(out, dtype=np.float64)


def punctuation_count(text: str) -> int:
    punct = set(string.punctuation) | set("，。！？；：、“”‘’（）《》〈〉【】…—·")
    return sum(ch in punct for ch in text)


def resolve_feature_dir(raw: str) -> Path:
    p = Path(raw)
    if p.is_dir():
        return p
    s = str(raw).replace("\\", "/")
    marker = "/outputs/"
    if marker in s:
        candidate = REPO_ROOT / ("outputs/" + s.split(marker, 1)[1])
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Frozen source metadata directory unavailable: {raw}")


def metadata_signature(rows: list[dict[str, str]]) -> list[tuple[str, str, str, str, str]]:
    return [
        (
            str(r["text"]),
            str(r["run_position_fraction"]),
            str(r["duration_sec"]),
            str(r["char_count"]),
            str(r.get("chapter_marker_context") or "CH00"),
        )
        for r in rows
    ]


def canonical_source(run_number: int) -> tuple[list[str], list[dict[str, str]], dict]:
    d = latest_dir(SOURCE_TARGET_ROOT / f"run-{run_number:02d}", "texts.json")
    texts = json.loads((d / "texts.json").read_text(encoding="utf-8"))
    summary = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    feature_dirs = summary.get("feature_dirs") or {}
    if not feature_dirs:
        raise RuntimeError(f"run {run_number}: source target summary lacks feature_dirs")

    reference_rows = None
    reference_sig = None
    checked = []
    for subject, raw_dir in sorted(feature_dirs.items()):
        fd = resolve_feature_dir(str(raw_dir))
        rows = read_csv(fd / "metadata.csv")
        if [r["text"] for r in rows] != texts:
            raise RuntimeError(f"run {run_number}: text identity mismatch for {subject}")
        sig = metadata_signature(rows)
        if reference_sig is None:
            reference_sig = sig
            reference_rows = rows
        elif sig != reference_sig:
            raise RuntimeError(f"run {run_number}: source nuisance metadata mismatch for {subject}")
        checked.append({"subject": subject, "metadata_path": str(fd / "metadata.csv")})

    if reference_rows is None:
        raise RuntimeError(f"run {run_number}: no source metadata rows")
    provenance = {
        "source_target_dir": str(d),
        "source_target_summary_sha256": sha256(d / "summary.json"),
        "source_texts_sha256": sha256(d / "texts.json"),
        "metadata_subjects_checked": checked,
    }
    return texts, reference_rows, provenance


def nuisances_from_metadata(texts: list[str], rows: list[dict[str, str]]) -> list[np.ndarray]:
    position = np.asarray([float(r["run_position_fraction"]) for r in rows], dtype=float)
    duration = np.asarray([float(r["duration_sec"]) for r in rows], dtype=float)
    char_count = np.asarray([float(r["char_count"]) for r in rows], dtype=float)
    chapters = np.asarray([int((r.get("chapter_marker_context") or "CH00")[2:]) for r in rows], dtype=int)
    orth = char_set_jaccard_rdm(texts)
    punct = np.asarray([punctuation_count(t) for t in texts], dtype=float)
    return [
        pdist(position[:, None], metric="cityblock"),
        pdist(duration[:, None], metric="cityblock"),
        pdist(char_count[:, None], metric="cityblock"),
        pdist(chapters[:, None], metric="hamming"),
        orth,
        pdist(punct[:, None], metric="cityblock"),
    ]


def encode(model, tokenizer, texts: list[str], device: str) -> np.ndarray:
    import torch

    chunks = []
    model.eval()
    with torch.inference_mode():
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start:start + BATCH_SIZE]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            attention = enc["attention_mask"].to(device)
            enc = {k: v.to(device) for k, v in enc.items()}
            hidden = model(**enc, return_dict=True).last_hidden_state
            mask = attention.to(hidden.dtype).unsqueeze(-1)
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1.0)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            chunks.append(pooled.cpu().numpy())
    return np.concatenate(chunks, axis=0)


def main() -> int:
    import torch
    from huggingface_hub import HfApi
    from transformers import AutoModel, AutoTokenizer

    OUT.mkdir(parents=True, exist_ok=True)
    atomic_progress(0, len(RUNS), "resolve-model", "resolving immutable MPNet revision")

    info = HfApi().model_info(MODEL_ID, revision="main")
    if not info.sha:
        raise RuntimeError("Could not resolve immutable MPNet revision")
    revision = str(info.sha)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=revision)
    model = AutoModel.from_pretrained(MODEL_ID, revision=revision)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    manifest_rows = []
    run_summaries = []
    for idx, run_number in enumerate(RUNS, start=1):
        texts, rows, source_provenance = canonical_source(run_number)
        nuisances = nuisances_from_metadata(texts, rows)
        emb = encode(model, tokenizer, texts, device)
        if emb.shape[0] != len(texts) or not np.isfinite(emb).all():
            raise RuntimeError(f"run {run_number}: invalid MPNet embedding matrix")
        model_rdm = pdist(emb, metric="cosine")
        target = residualize_ranked(model_rdm, nuisances)
        if not np.isfinite(target).all() or abs(float(target.mean())) > 1e-10 or not np.isclose(float(target.std()), 1.0, atol=1e-8):
            raise RuntimeError(f"run {run_number}: target standardization invariant failed")

        run_dir = OUT / f"run_{run_number:02d}"
        run_dir.mkdir(parents=True, exist_ok=True)
        target_path = run_dir / "structured_nonneural_target.npy"
        texts_path = run_dir / "texts.json"
        np.save(target_path, target.astype(np.float32))
        texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2), encoding="utf-8")

        run_summary = {
            "run_number": run_number,
            "n_rows": len(texts),
            "n_edges": int(len(target)),
            "alternative_target_model_id": MODEL_ID,
            "alternative_target_model_revision": revision,
            "pooling": "attention-mask mean final hidden state; L2-normalized",
            "max_length": MAX_LENGTH,
            "model_rdm": "cosine distance",
            "target_transform": "rank-z model RDM residualized against the six frozen source nuisances; residual z-standardized",
            "nuisances": NUISANCE_LABELS,
            "target_mean_float64_before_float32_save": float(target.mean()),
            "target_std_float64_before_float32_save": float(target.std()),
            "source_provenance": source_provenance,
        }
        summary_path = run_dir / "summary.json"
        summary_path.write_text(json.dumps(run_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        run_summary["target_sha256"] = sha256(target_path)
        run_summary["texts_sha256"] = sha256(texts_path)
        run_summaries.append(run_summary)
        manifest_rows.append({
            "run": run_number,
            "n_rows": len(texts),
            "n_edges": len(target),
            "model_revision": revision,
            "target_sha256": sha256(target_path),
            "texts_sha256": sha256(texts_path),
        })
        atomic_progress(idx, len(RUNS), "materialize-targets", f"completed source run {run_number:02d}")

    summary = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "post-confirmatory alternative-signal target materialization",
        "protocol": PROTOCOL,
        "alternative_signal_type": "structured item-linked non-neural multilingual-MPNet geometry",
        "model_id": MODEL_ID,
        "model_revision": revision,
        "runs": RUNS,
        "guardrails": {
            "eeg_feature_arrays_read": False,
            "neural_target_values_read": False,
            "external_target_data_read": False,
            "transfer_outcomes_read": False,
            "e5_training_performed": False,
            "external_evaluation_performed": False,
        },
        "run_summaries": run_summaries,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(OUT / "target_manifest.csv", manifest_rows)
    (OUT / "report.txt").write_text(
        "NeuroSem alternative-signal MPNet target materialization v1\n\n"
        f"Model: {MODEL_ID}\nRevision: {revision}\n"
        "Runs: 01-06\n"
        "Target: nuisance-residualized item-linked MPNet relational geometry\n"
        "No EEG feature arrays, neural target values, external outcomes, E5 training or external evaluation were read/performed.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "model_revision": revision, "runs": RUNS}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
