#!/usr/bin/env python3
"""Frozen ChineseEEG-to-DERCo multilingual-E5 transfer test.

Primary confirmatory contrast: ChineseEEG-trained lambda=0.10 neural-guided adapter
versus lambda=0 text-only adapter, evaluated against prospectively frozen DERCo
word-epoch row_mean_all EEG geometry. No DERCo tuning or model selection is performed.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import mne
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import (
    LAMBDA_010_ROOT,
    TEXT_ONLY_ADAPTER,
    MODEL_ID,
    MODEL_REVISION,
    encode_texts,
    latest_completed_adapter,
    load_adapter,
)

ARTICLES = range(5)
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")
ARMS = ["lambda_0", "lambda_0p10"]
SEED = 20260827
MIN_PAIRS = 1000


def parse_items(ep, article: int):
    inv = {int(code): label for label, code in ep.event_id.items()}
    out = []
    for row_i, code in enumerate(ep.events[:, 2].tolist()):
        label = inv[int(code)]
        m = EVENT_RE.match(label)
        if not m:
            raise RuntimeError(f"unexpected event label {label!r}")
        a = int(m.group("article"))
        if a != article:
            raise RuntimeError(f"article mismatch: folder={article} label={label!r}")
        out.append((int(m.group("stim_index")), m.group("word"), row_i))
    idx = [x[0] for x in out]
    if len(set(idx)) != len(idx) or any(b <= a for a, b in zip(idx, idx[1:])):
        raise RuntimeError(f"non-unique or non-monotonic item indices in article {article}")
    return out


def zscore_features(x: np.ndarray) -> np.ndarray:
    mu = np.nanmean(x, axis=0, keepdims=True)
    sd = np.nanstd(x, axis=0, ddof=0, keepdims=True)
    sd = np.where((~np.isfinite(sd)) | (sd == 0), 1.0, sd)
    return (x - mu) / sd


def residualize(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def safe_rho(a, b) -> float:
    r = float(spearmanr(a, b).statistic)
    if not np.isfinite(r):
        raise RuntimeError("non-finite Spearman RSA")
    return r


def fisher_mean(rs) -> float:
    v = np.asarray(rs, float)
    return float(np.tanh(np.mean(np.arctanh(np.clip(v, -0.999999, 0.999999)))))


def bootstrap_ci(values: np.ndarray, nboot: int = 10000):
    rng = np.random.default_rng(SEED)
    values = np.asarray(values, float)
    boot = np.empty(nboot, float)
    for i in range(nboot):
        boot[i] = np.mean(rng.choice(values, size=len(values), replace=True))
    q = np.quantile(boot, [0.025, 0.975])
    return [float(q[0]), float(q[1])]


def exact_signflip_p(values: np.ndarray) -> float:
    values = np.asarray(values, float)
    n = len(values)
    obs = float(values.mean())
    total = 1 << n
    extreme = 0
    chunk = 1 << 15
    bitpos = np.arange(n, dtype=np.uint64)
    for start in range(0, total, chunk):
        stop = min(start + chunk, total)
        ids = np.arange(start, stop, dtype=np.uint64)[:, None]
        signs = np.where(((ids >> bitpos) & 1) == 1, 1.0, -1.0)
        means = (signs @ values) / n
        extreme += int(np.count_nonzero(means >= obs - 1e-15))
    return float(extreme / total)


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def build_canonical_items(root: Path, subjects: list[str]):
    words = {a: {} for a in ARTICLES}
    for article in ARTICLES:
        for subject in subjects:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            for idx, word, _ in parse_items(ep, article):
                prev = words[article].get(idx)
                if prev is not None and prev.casefold() != word.casefold():
                    raise RuntimeError(f"cross-participant word conflict article={article} index={idx}: {prev!r} vs {word!r}")
                words[article][idx] = word
    return {a: [(idx, words[a][idx]) for idx in sorted(words[a])] for a in ARTICLES}


def build_model_rdms(canonical, device: str):
    import torch
    adapters = {
        "lambda_0": TEXT_ONLY_ADAPTER,
        "lambda_0p10": latest_completed_adapter(LAMBDA_010_ROOT),
    }
    flat = [word for a in ARTICLES for _, word in canonical[a]]
    sizes = {a: len(canonical[a]) for a in ARTICLES}
    out = {}
    provenance = {}
    for arm, adapter in adapters.items():
        tok, model = load_adapter(adapter, device)
        emb = encode_texts(model, tok, flat, device)
        out[arm] = {}
        off = 0
        for a in ARTICLES:
            n = sizes[a]
            mat = emb[off:off+n]
            out[arm][a] = squareform(pdist(mat, metric="cosine"))
            off += n
        provenance[arm] = str(adapter.resolve())
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return out, provenance


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--reliability-summary", type=Path, default=Path("outputs/derco_eeg_reliability/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_e5_transfer_v1/latest"))
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    import torch
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    rel = json.loads(args.reliability_summary.read_text(encoding="utf-8"))
    if rel.get("n_subjects") != 22 or rel.get("reliability_gate_pass") is not True:
        raise SystemExit("DERCo frozen reliability gate has not passed")
    if rel.get("representation") != "row_mean_all; featurewise z-score ddof=0; correlation-distance RDM":
        raise SystemExit("DERCo reliability representation mismatch")

    root = args.data_root.resolve()
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    subjects = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name != "prediction")
    if len(subjects) != 22:
        raise RuntimeError(f"expected 22 frozen subjects, found {len(subjects)}")

    canonical = build_canonical_items(root, subjects)
    model_rdms, provenance = build_model_rdms(canonical, device)
    canonical_pos = {a: {idx: i for i, (idx, _) in enumerate(canonical[a])} for a in ARTICLES}

    session_rows = []
    by_subject = {s: {arm: [] for arm in ARMS} for s in subjects}
    for subject in subjects:
        for article in ARTICLES:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            items = parse_items(ep, article)
            indices = [x[0] for x in items]
            words = [x[1] for x in items]
            rows = [x[2] for x in items]
            data = ep.get_data(picks="eeg")[rows]
            feat = zscore_features(np.mean(data, axis=2))
            neural = pdist(feat, metric="correlation")
            if len(neural) < MIN_PAIRS:
                raise RuntimeError(f"{subject}/article_{article}: only {len(neural)} pairs")
            pos = np.asarray(indices, float)
            lengths = np.asarray([len(w) for w in words], float)
            X = np.column_stack([
                np.ones(len(neural)),
                pdist(pos[:, None], metric="cityblock"),
                pdist(lengths[:, None], metric="cityblock"),
            ])
            nr = residualize(neural, X)
            canon_ix = np.asarray([canonical_pos[article][idx] for idx in indices], int)
            vals = {}
            for arm in ARMS:
                square = model_rdms[arm][article]
                model_vec = squareform(square[np.ix_(canon_ix, canon_ix)], checks=False)
                mr = residualize(model_vec, X)
                rho = safe_rho(nr, mr)
                vals[arm] = rho
                by_subject[subject][arm].append(rho)
            session_rows.append({
                "subject": subject,
                "article": article,
                "n_items": len(items),
                "n_edges": len(neural),
                "lambda_0_resid_rsa": vals["lambda_0"],
                "lambda_0p10_resid_rsa": vals["lambda_0p10"],
                "delta_0p10_minus_0": vals["lambda_0p10"] - vals["lambda_0"],
            })

    subject_rows = []
    diffs = []
    for subject in subjects:
        a0 = fisher_mean(by_subject[subject]["lambda_0"])
        a1 = fisher_mean(by_subject[subject]["lambda_0p10"])
        d = a1 - a0
        diffs.append(d)
        subject_rows.append({
            "subject": subject,
            "lambda_0_resid_rsa": a0,
            "lambda_0p10_resid_rsa": a1,
            "delta_0p10_minus_0": d,
        })

    diffs = np.asarray(diffs, float)
    primary = {
        "contrast": "lambda_0p10_minus_lambda_0",
        "mean_delta": float(np.mean(diffs)),
        "median_delta": float(np.median(diffs)),
        "n_positive": int(np.sum(diffs > 0)),
        "fraction_subjects_positive": float(np.mean(diffs > 0)),
        "bootstrap_95ci": bootstrap_ci(diffs),
        "exact_one_sided_signflip_p": exact_signflip_p(diffs),
    }
    payload = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "prospectively gated frozen ChineseEEG-trained multilingual-E5 transfer",
        "n_subjects": 22,
        "articles": list(ARTICLES),
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_provenance": provenance,
        "device": device,
        "semantic_unit": "retained DERCo word epoch identified by event-label (article, stimulus_index), with event-label word as model text",
        "primary_eeg_representation": "row_mean_all; featurewise z-score ddof=0; correlation-distance RDM",
        "primary_nuisances": ["absolute stimulus-index difference", "absolute event-label word-length difference"],
        "participant_aggregation": "unweighted Fisher-z mean across five within-article nuisance-residualized Spearman RSAs",
        "primary_contrast": "ChineseEEG-trained E5 lambda=0.10 neural-guided minus lambda=0 text-only",
        "no_derco_tuning": True,
        "reliability_gate_source": str(args.reliability_summary),
        "primary_result": primary,
        "guardrails": [
            "DERCo EEG reliability gate passed before this model-transfer outcome was exposed.",
            "All 22 frozen participants and all five articles are retained.",
            "No DERCo model, lambda, representation, time window, participant, article, or item subset is selected from transfer outcomes.",
            "The sole confirmatory model contrast is lambda=0.10 versus lambda=0.",
        ],
    }
    write_csv(out / "participant_results.csv", subject_rows)
    write_csv(out / "participant_article_results.csv", session_rows)
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "primary_result": primary, "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
