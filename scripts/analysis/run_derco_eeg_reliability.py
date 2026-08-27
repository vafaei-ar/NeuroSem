#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import mne
import numpy as np
from scipy.spatial.distance import pdist

ARTICLES = range(5)
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")
SEED = 20260827


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
    return out


def zscore_features(x: np.ndarray) -> np.ndarray:
    mu = np.nanmean(x, axis=0, keepdims=True)
    sd = np.nanstd(x, axis=0, ddof=0, keepdims=True)
    sd = np.where((~np.isfinite(sd)) | (sd == 0), 1.0, sd)
    return (x - mu) / sd


def residualize(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


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
    return extreme / total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_eeg_reliability/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    subjects = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name != "prediction")
    if len(subjects) != 22:
        raise RuntimeError(f"expected frozen 22 subjects, found {len(subjects)}")

    rdms = {a: {} for a in ARTICLES}
    nuisance = {}
    common_counts = {}
    article_words = {}

    for article in ARTICLES:
        item_maps = {}
        ep_cache = {}
        for subject in subjects:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            items = parse_items(ep, article)
            item_maps[subject] = {idx: (word, row_i) for idx, word, row_i in items}
            ep_cache[subject] = ep
        common = sorted(set.intersection(*(set(item_maps[s]) for s in subjects)))
        common_counts[article] = len(common)
        if len(common) < 100:
            raise RuntimeError(f"article {article} has only {len(common)} all-participant common items")
        words = []
        for idx in common:
            ws = {item_maps[s][idx][0] for s in subjects}
            if len(ws) != 1:
                raise RuntimeError(f"word conflict article={article} index={idx}: {ws}")
            words.append(next(iter(ws)))
        article_words[article] = words
        pos = np.asarray(common, float)
        lengths = np.asarray([len(w) for w in words], float)
        nuisance[article] = np.column_stack([
            np.ones(len(pdist(pos[:, None], metric="cityblock"))),
            pdist(pos[:, None], metric="cityblock"),
            pdist(lengths[:, None], metric="cityblock"),
        ])
        for subject in subjects:
            ep = ep_cache[subject]
            rows = [item_maps[subject][idx][1] for idx in common]
            data = ep.get_data(picks="eeg")[rows]
            feats = np.mean(data, axis=2)
            feats = zscore_features(feats)
            rdms[article][subject] = pdist(feats, metric="correlation")

    rows_out = []
    agg_primary = []
    agg_raw = []
    for subject in subjects:
        z_primary = []
        z_raw = []
        for article in ARTICLES:
            subj_rdm = rdms[article][subject]
            others = [rdms[article][s] for s in subjects if s != subject]
            loo = np.mean(np.vstack(others), axis=0)
            X = nuisance[article]
            raw_r = corr(subj_rdm, loo)
            pr = corr(residualize(subj_rdm, X), residualize(loo, X))
            z_primary.append(np.arctanh(np.clip(pr, -0.999999, 0.999999)))
            z_raw.append(np.arctanh(np.clip(raw_r, -0.999999, 0.999999)))
            rows_out.append({"subject": subject, "article": article, "n_common_items": common_counts[article], "primary_residual_reliability": pr, "raw_reliability": raw_r})
        apv = float(np.tanh(np.mean(z_primary)))
        arv = float(np.tanh(np.mean(z_raw)))
        agg_primary.append(apv)
        agg_raw.append(arv)
        rows_out.append({"subject": subject, "article": "aggregate", "n_common_items": sum(common_counts.values()), "primary_residual_reliability": apv, "raw_reliability": arv})

    vals = np.asarray(agg_primary, float)
    raw_vals = np.asarray(agg_raw, float)
    rng = np.random.default_rng(SEED)
    boot = np.empty(10000, float)
    for i in range(len(boot)):
        boot[i] = np.mean(rng.choice(vals, size=len(vals), replace=True))
    ci = np.quantile(boot, [0.025, 0.975])
    p_sf = exact_signflip_p(vals)
    gate = bool(np.mean(vals) > 0 and ci[0] > 0)

    with (out / "participant_article_reliability.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader(); w.writerows(rows_out)

    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "prospectively frozen EEG-only leave-one-participant-out neural geometry reliability",
        "n_subjects": len(subjects),
        "articles": list(ARTICLES),
        "common_item_counts": {str(k): int(v) for k, v in common_counts.items()},
        "representation": "row_mean_all; featurewise z-score ddof=0; correlation-distance RDM",
        "primary_nuisances": ["absolute stimulus-index difference", "absolute event-label word-length difference"],
        "participant_aggregation": "unweighted Fisher-z mean across five articles, then tanh",
        "primary_mean": float(np.mean(vals)),
        "primary_median": float(np.median(vals)),
        "primary_n_positive": int(np.sum(vals > 0)),
        "primary_bootstrap_95_ci": [float(ci[0]), float(ci[1])],
        "primary_exact_one_sided_signflip_p": float(p_sf),
        "raw_mean_sensitivity": float(np.mean(raw_vals)),
        "raw_median_sensitivity": float(np.median(raw_vals)),
        "reliability_gate_rule": "pass iff participant mean > 0 and participant-bootstrap 95% CI lower bound > 0",
        "reliability_gate_pass": gate,
        "guardrails": [
            "All 22 frozen participants and all five articles are retained.",
            "No embedding model or NeuroSem model checkpoint is loaded.",
            "No semantic RSA or transfer outcome is computed.",
            "No participant, article, representation, nuisance, or item subset is selected using the reliability result."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
