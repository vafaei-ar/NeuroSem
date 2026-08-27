#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import mne
import numpy as np
from scipy.spatial.distance import pdist

ARTICLES = range(5)
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")
SEED = 20260827
MIN_LOO_CONTRIBUTORS = 11  # strict majority of the 21 leave-one-out participants
MIN_ELIGIBLE_PAIRS = 1000


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

    article_results = {s: {} for s in subjects}
    rows_out = []
    union_item_counts = {}

    for article in ARTICLES:
        item_maps = {}
        word_by_index = {}
        union_indices = set()

        # Structural pass only. Establish the article-wide participant-independent item key space.
        for subject in subjects:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            items = parse_items(ep, article)
            local = {}
            for idx, word, row_i in items:
                if idx in local:
                    raise RuntimeError(f"duplicate stimulus index article={article} subject={subject} index={idx}")
                local[idx] = (word, row_i)
                prev = word_by_index.get(idx)
                if prev is not None and prev != word:
                    raise RuntimeError(
                        f"cross-participant word conflict article={article} index={idx}: {prev!r} vs {word!r}"
                    )
                word_by_index[idx] = word
                union_indices.add(idx)
            item_maps[subject] = local

        union = sorted(union_indices)
        union_item_counts[article] = len(union)
        pos_of = {idx: i for i, idx in enumerate(union)}
        n_union = len(union)
        tri_i, tri_j = np.triu_indices(n_union, k=1)
        n_pairs = len(tri_i)
        pair_id = np.full((n_union, n_union), -1, dtype=np.int32)
        pair_id[tri_i, tri_j] = np.arange(n_pairs, dtype=np.int32)

        # Dense pair vectors avoid a huge Python dictionary while preserving missingness explicitly.
        all_subject_rdms = np.full((len(subjects), n_pairs), np.nan, dtype=np.float32)
        n_items_by_subject = {}

        for si, subject in enumerate(subjects):
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            local = item_maps[subject]
            local_indices = sorted(local)
            n_items_by_subject[subject] = len(local_indices)
            rows = [local[idx][1] for idx in local_indices]
            data = ep.get_data(picks="eeg")[rows]
            feats = np.mean(data, axis=2)  # row_mean_all: temporal mean within each retained EEG channel
            feats = zscore_features(feats)
            d = pdist(feats, metric="correlation")

            local_pos = np.asarray([pos_of[idx] for idx in local_indices], dtype=np.int32)
            li, lj = np.triu_indices(len(local_indices), k=1)
            gids = pair_id[local_pos[li], local_pos[lj]]
            if np.any(gids < 0):
                raise RuntimeError("internal pair-index mapping failure")
            all_subject_rdms[si, gids] = d.astype(np.float32)

        finite = np.isfinite(all_subject_rdms)
        total_count = finite.sum(axis=0).astype(np.int16)
        total_sum = np.nansum(all_subject_rdms, axis=0, dtype=np.float64)

        pair_pos_diff = np.abs(np.asarray(union, float)[tri_i] - np.asarray(union, float)[tri_j])
        lengths = np.asarray([len(word_by_index[idx]) for idx in union], float)
        pair_len_diff = np.abs(lengths[tri_i] - lengths[tri_j])

        for si, subject in enumerate(subjects):
            subj = all_subject_rdms[si].astype(np.float64)
            subj_finite = finite[si]
            loo_count = total_count.astype(np.int32) - subj_finite.astype(np.int32)
            eligible = subj_finite & (loo_count >= MIN_LOO_CONTRIBUTORS)
            n_eligible = int(np.sum(eligible))
            if n_eligible < MIN_ELIGIBLE_PAIRS:
                raise RuntimeError(
                    f"article {article} subject {subject} has only {n_eligible} eligible pairs "
                    f"with >= {MIN_LOO_CONTRIBUTORS} LOO contributors"
                )

            loo = (total_sum[eligible] - subj[eligible]) / loo_count[eligible]
            y = subj[eligible]
            X = np.column_stack([
                np.ones(n_eligible, float),
                pair_pos_diff[eligible],
                pair_len_diff[eligible],
            ])
            raw_r = corr(y, loo)
            primary_r = corr(residualize(y, X), residualize(loo, X))
            if not np.isfinite(primary_r) or not np.isfinite(raw_r):
                raise RuntimeError(f"non-finite reliability article={article} subject={subject}")

            article_results[subject][article] = (primary_r, raw_r)
            c = loo_count[eligible]
            rows_out.append({
                "subject": subject,
                "article": article,
                "n_subject_items": n_items_by_subject[subject],
                "n_eligible_pairs": n_eligible,
                "min_loo_pair_contributors": int(np.min(c)),
                "median_loo_pair_contributors": float(np.median(c)),
                "primary_residual_reliability": primary_r,
                "raw_reliability": raw_r,
            })

    agg_primary = []
    agg_raw = []
    for subject in subjects:
        z_primary = []
        z_raw = []
        total_pairs = 0
        for article in ARTICLES:
            pr, rr = article_results[subject][article]
            z_primary.append(np.arctanh(np.clip(pr, -0.999999, 0.999999)))
            z_raw.append(np.arctanh(np.clip(rr, -0.999999, 0.999999)))
            total_pairs += next(
                int(r["n_eligible_pairs"])
                for r in rows_out
                if r["subject"] == subject and r["article"] == article
            )
        apv = float(np.tanh(np.mean(z_primary)))
        arv = float(np.tanh(np.mean(z_raw)))
        agg_primary.append(apv)
        agg_raw.append(arv)
        rows_out.append({
            "subject": subject,
            "article": "aggregate",
            "n_subject_items": "",
            "n_eligible_pairs": total_pairs,
            "min_loo_pair_contributors": "",
            "median_loo_pair_contributors": "",
            "primary_residual_reliability": apv,
            "raw_reliability": arv,
        })

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
        w.writeheader()
        w.writerows(rows_out)

    summary = {
        "schema_version": 2,
        "dataset": "DERCo",
        "analysis": "prospectively frozen EEG-only pairwise-available leave-one-participant-out neural geometry reliability",
        "n_subjects": len(subjects),
        "articles": list(ARTICLES),
        "union_item_counts": {str(k): int(v) for k, v in union_item_counts.items()},
        "representation": "row_mean_all; featurewise z-score ddof=0; correlation-distance RDM",
        "missingness_rule": (
            "For each participant/article, evaluate every item pair retained by that participant whose LOO reference "
            f"is available in at least {MIN_LOO_CONTRIBUTORS} of the other 21 participants; average the pairwise "
            "correlation distances across those available LOO participants. No all-participant item intersection is required."
        ),
        "minimum_loo_pair_contributors": MIN_LOO_CONTRIBUTORS,
        "minimum_eligible_pairs_per_participant_article": MIN_ELIGIBLE_PAIRS,
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
            "Pairwise availability handles independent artifact rejection without outcome-driven participant or item exclusion.",
            f"The >= {MIN_LOO_CONTRIBUTORS}/21 LOO-contributor majority rule and >= {MIN_ELIGIBLE_PAIRS} pair minimum were frozen before this estimator was run.",
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
