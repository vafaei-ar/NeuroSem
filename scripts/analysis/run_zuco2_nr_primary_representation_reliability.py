#!/usr/bin/env python3
"""Prospectively frozen model-blind ZuCo 2.0 Task 1 NR EEG reliability analysis.

Primary endpoint: all-retained-channel temporal mean within each sentence window.
Secondary sensitivity endpoints: channel-wise temporal SD and relative 8-bin means.
Sentence identity and English nuisance controls are frozen by the prior model-blind
word-count alignment probe. No language-model embeddings are loaded here.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import re
import unicodedata
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

CANDIDATES = ["row_mean_all", "row_std_all", "relative_8bin_all"]
EXPECTED = {1: 50, 2: 50, 3: 51, 4: 50, 5: 50, 6: 49, 7: 49}


def decode_text_dataset(f, ds):
    arr = np.asarray(ds[()])
    if h5py.check_dtype(ref=ds.dtype) is not None:
        vals = []
        for ref in arr.ravel():
            obj = f[ref]
            x = np.asarray(obj[()])
            if x.dtype.kind in "uifb" and x.size > 1:
                vals.append("".join(chr(int(v)) for v in x.ravel() if int(v) != 0))
            elif x.size:
                vals.append(str(x.ravel()[0]))
            else:
                vals.append("")
        return vals
    return [str(x) for x in arr.ravel()]


def decode_numeric_refs(f, ds):
    arr = np.asarray(ds[()])
    if h5py.check_dtype(ref=ds.dtype) is not None:
        vals = []
        for ref in arr.ravel():
            x = np.asarray(f[ref][()]).ravel()
            vals.append(float(x[0]) if x.size else np.nan)
        return vals
    return [float(x) for x in arr.ravel()]


def scalar(group, name):
    obj = group.get(name)
    if not isinstance(obj, h5py.Dataset):
        raise RuntimeError(f"missing EEG/{name}")
    arr = np.asarray(obj[()]).ravel()
    if not arr.size:
        raise RuntimeError(f"empty EEG/{name}")
    return float(arr[0])


def sentence_pairs(f, eeg, expected):
    ev = eeg.get("event")
    if not isinstance(ev, h5py.Group) or not all(k in ev for k in ("type", "latency")):
        raise RuntimeError("missing event type/latency")
    types = [str(x).strip() for x in decode_text_dataset(f, ev["type"])]
    lats = decode_numeric_refs(f, ev["latency"])
    core = [(t, lat) for t, lat in zip(types, lats) if t in {"10", "11", "12", "13"}]
    if len(core) % 2:
        raise RuntimeError("odd core event count")
    pairs = []
    for i in range(0, len(core), 2):
        a, b = core[i], core[i + 1]
        if (a[0], b[0]) not in {("10", "11"), ("12", "13")}:
            raise RuntimeError("invalid sentence event pair sequence")
        pairs.append((a, b))
    if len(pairs) != expected:
        raise RuntimeError(f"sentence count {len(pairs)} != expected {expected}")
    return pairs


def segment_matrix(data, start_latency, end_latency, pnts, nbchan):
    # EEGLAB latencies are 1-based sample coordinates. Freeze sentence windows as
    # [start-trigger, end-trigger), rounded to the nearest stored sample.
    start = int(round(float(start_latency))) - 1
    end = int(round(float(end_latency))) - 1
    start = max(0, start)
    end = min(int(pnts), end)
    if end <= start + 1:
        raise RuntimeError(f"invalid sentence sample interval {start}:{end}")
    shape = tuple(data.shape)
    if shape == (int(pnts), int(nbchan)):
        x = np.asarray(data[start:end, :], dtype=np.float64)
    elif shape == (int(nbchan), int(pnts)):
        x = np.asarray(data[:, start:end], dtype=np.float64).T
    else:
        raise RuntimeError(f"unexpected EEG data shape {shape} for pnts={pnts}, nbchan={nbchan}")
    if x.ndim != 2 or x.shape[1] != int(nbchan):
        raise RuntimeError(f"bad sentence matrix shape {x.shape}")
    return x


def segment_features(x):
    # x: samples x retained channels
    mean = x.mean(axis=0)
    std = x.std(axis=0, ddof=0)
    bins = np.array_split(np.arange(x.shape[0]), 8)
    if any(len(b) == 0 for b in bins):
        raise RuntimeError("sentence too short for 8 relative bins")
    binned = np.concatenate([x[b, :].mean(axis=0) for b in bins])
    return {
        "row_mean_all": mean,
        "row_std_all": std,
        "relative_8bin_all": binned,
    }


def load_run_features(path: Path, expected: int):
    out = {c: [] for c in CANDIDATES}
    durations = []
    with h5py.File(path, "r") as f:
        if "EEG" not in f:
            raise RuntimeError("missing EEG group")
        eeg = f["EEG"]
        data = eeg.get("data")
        if not isinstance(data, h5py.Dataset):
            raise RuntimeError("missing EEG/data")
        pnts = int(round(scalar(eeg, "pnts")))
        nbchan = int(round(scalar(eeg, "nbchan")))
        srate = float(scalar(eeg, "srate"))
        pairs = sentence_pairs(f, eeg, expected)
        for a, b in pairs:
            x = segment_matrix(data, a[1], b[1], pnts, nbchan)
            feat = segment_features(x)
            for c in CANDIDATES:
                out[c].append(feat[c])
            durations.append(x.shape[0] / srate)
    for c in CANDIDATES:
        out[c] = np.asarray(out[c], dtype=float)
    return out, {
        "n_sentences": expected,
        "nbchan": nbchan,
        "srate": srate,
        "mean_sentence_duration_s": float(np.mean(durations)),
        "min_sentence_duration_s": float(np.min(durations)),
        "max_sentence_duration_s": float(np.max(durations)),
    }


def zscore_cols(x):
    x = np.asarray(x, float)
    mu = x.mean(axis=0)
    sd = x.std(axis=0)
    good = np.isfinite(sd) & (sd > 1e-12)
    if good.sum() < 2:
        raise RuntimeError("insufficient nonconstant features")
    z = (x[:, good] - mu[good]) / sd[good]
    if not np.isfinite(z).all():
        raise RuntimeError("non-finite standardized features")
    return z


def rdm_edges(x):
    z = zscore_cols(x)
    d = pdist(z, metric="correlation")
    if not np.isfinite(d).all():
        raise RuntimeError("non-finite correlation-distance RDM")
    return d


def load_material_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f, delimiter=";", quotechar='"') if any(str(x).strip() for x in r)]


def lexical_set(text):
    return set(re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", str(text).lower()))


def nuisance_matrix(texts):
    n = len(texts)
    words = [len(re.findall(r"\S+", t.strip())) for t in texts]
    punct = [sum(unicodedata.category(ch).startswith("P") for ch in t) for t in texts]
    lex = [lexical_set(t) for t in texts]
    vals = []
    for i in range(n):
        for j in range(i + 1, n):
            union = lex[i] | lex[j]
            jac = 1.0 - (len(lex[i] & lex[j]) / len(union) if union else 1.0)
            vals.append([abs(i - j), abs(words[i] - words[j]), abs(punct[i] - punct[j]), jac])
    X = np.asarray(vals, float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    good = sd > 1e-12
    if good.sum() < 1:
        raise RuntimeError("all nuisance columns constant")
    return (X[:, good] - mu[good]) / sd[good]


def residualize(y, X):
    A = np.column_stack([np.ones(len(y)), X])
    beta = np.linalg.lstsq(A, y, rcond=None)[0]
    return y - A @ beta


def fisher_mean(rs):
    rs = np.asarray([r for r in rs if np.isfinite(r)], float)
    if not len(rs):
        return float("nan")
    z = np.arctanh(np.clip(rs, -0.999999, 0.999999))
    return float(np.tanh(z.mean()))


def boot_ci(values, seed=20260825, nboot=10000):
    v = np.asarray([x for x in values if np.isfinite(x)], float)
    rng = np.random.default_rng(seed)
    means = np.empty(nboot)
    for b in range(nboot):
        means[b] = rng.choice(v, len(v), replace=True).mean()
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def exact_signflip_p(values):
    v = np.asarray([x for x in values if np.isfinite(x)], float)
    if len(v) > 20:
        raise RuntimeError("exact sign flip intentionally capped at 20 subjects")
    obs = float(v.mean())
    ge = 0
    abs_ge = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(v)):
        m = float(np.dot(v, np.asarray(signs)) / len(v))
        ge += m >= obs - 1e-15
        abs_ge += abs(m) >= abs(obs) - 1e-15
        total += 1
    return {
        "observed_mean": obs,
        "one_sided_greater_p": ge / total,
        "two_sided_p": abs_ge / total,
        "n_sign_patterns": total,
    }


def load_inventory(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_nr"))
    ap.add_argument("--input-freeze", type=Path, default=Path("outputs/zuco2_nr_input_materialization/latest/summary.json"))
    ap.add_argument("--mapping-freeze", type=Path, default=Path("outputs/zuco2_nr_format_probe/latest/summary.json"))
    ap.add_argument("--stimulus-root", type=Path, default=Path("data/raw/zuco2_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_primary_representation_reliability/latest"))
    ap.add_argument("--min-reference-edge-subjects", type=int, default=12)
    args = ap.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cohort = json.loads(args.input_freeze.read_text(encoding="utf-8"))
    mapping = json.loads(args.mapping_freeze.read_text(encoding="utf-8"))

    ready = list(cohort.get("ready_subjects_all_7_runs") or [])
    if cohort.get("n_ready_subjects_all_7_runs") != 17 or len(ready) != 17:
        raise SystemExit("frozen ZuCo cohort must contain exactly 17 structurally ready participants")
    if "YTL" in ready:
        raise SystemExit("YTL must not be in the frozen all-seven-runs cohort")
    if not mapping.get("all_runs_freeze_ready"):
        raise SystemExit("stimulus mapping freeze is not ready")
    maps = {r["run"]: r for r in mapping.get("wordcount_mapping_diagnostics", [])}
    if set(maps) != {f"NR{i}" for i in range(1, 8)}:
        raise SystemExit("mapping freeze missing one or more NR runs")
    for run in range(1, 8):
        rec = maps[f"NR{run}"]
        if not rec.get("freeze_ready") or rec.get("total_absolute_wordcount_cost") != 0 or not rec.get("unique_optimum"):
            raise SystemExit(f"NR{run} mapping is not a unique zero-cost freeze")
        if rec.get("skipped_material_rows_1based") != [1, 2, 3]:
            raise SystemExit(f"NR{run} unexpected frozen skipped rows")

    inventory_path = args.input_freeze.parent / "session_inventory.csv"
    inventory = load_inventory(inventory_path)
    path_by = {}
    for r in inventory:
        if r.get("subject") in ready and str(r.get("ready", "")).lower() == "true":
            path_by[(r["subject"], int(r["run"]))] = args.data_root.resolve() / r["osf_path"]
    if len(path_by) != 17 * 7:
        raise SystemExit(f"expected 119 frozen subject-run paths, found {len(path_by)}")

    texts_by_run = {}
    nuisance_by_run = {}
    for run in range(1, 8):
        rows = load_material_rows(args.stimulus_root / "task_materials" / f"nr_{run}.csv")
        selected = maps[f"NR{run}"]["selected_material_rows_1based"]
        texts = [str(rows[i - 1][2]).strip() for i in selected]
        if len(texts) != EXPECTED[run]:
            raise SystemExit(f"NR{run} frozen text count mismatch")
        texts_by_run[run] = texts
        nuisance_by_run[run] = nuisance_matrix(texts)

    # Build one neural RDM per participant x run x candidate while reading each EEG file once.
    rdms = {c: {run: np.full((len(ready), EXPECTED[run] * (EXPECTED[run] - 1) // 2), np.nan) for run in range(1, 8)} for c in CANDIDATES}
    loader_rows = []
    for qi, sub in enumerate(ready):
        for run in range(1, 8):
            feats, meta = load_run_features(path_by[(sub, run)], EXPECTED[run])
            for c in CANDIDATES:
                rdms[c][run][qi, :] = rdm_edges(feats[c])
            loader_rows.append({"subject": sub, "run": f"NR{run}", **meta})

    candidate_metrics = []
    subject_rows = []
    session_rows = []
    for c in CANDIDATES:
        per_subject = {sub: {"raw": [], "resid": [], "edges": []} for sub in ready}
        pairwise_raw = []
        pairwise_resid = []
        for run in range(1, 8):
            mat = rdms[c][run]
            X = nuisance_by_run[run]
            if X.shape[0] != mat.shape[1]:
                raise RuntimeError(f"NR{run} nuisance/RDM edge mismatch")
            for i, sub in enumerate(ready):
                others = np.delete(mat, i, axis=0)
                support = np.sum(np.isfinite(others), axis=0)
                ref = np.nanmean(others, axis=0)
                mask = np.isfinite(mat[i]) & np.isfinite(ref) & (support >= args.min_reference_edge_subjects)
                if mask.sum() < 500:
                    raise RuntimeError(f"too few LOO edges {c} {sub} NR{run}: {mask.sum()}")
                y = mat[i, mask]
                r = ref[mask]
                Xm = X[mask]
                raw = float(spearmanr(y, r).statistic)
                resid = float(spearmanr(residualize(y, Xm), residualize(r, Xm)).statistic)
                per_subject[sub]["raw"].append(raw)
                per_subject[sub]["resid"].append(resid)
                per_subject[sub]["edges"].append(int(mask.sum()))
                session_rows.append({"candidate": c, "subject": sub, "run": f"NR{run}", "raw_loo": raw, "resid_loo": resid, "n_edges": int(mask.sum())})
            for i in range(len(ready)):
                for j in range(i + 1, len(ready)):
                    mask = np.isfinite(mat[i]) & np.isfinite(mat[j])
                    if mask.sum() < 500:
                        continue
                    pairwise_raw.append(float(spearmanr(mat[i, mask], mat[j, mask]).statistic))
                    pairwise_resid.append(float(spearmanr(residualize(mat[i, mask], X[mask]), residualize(mat[j, mask], X[mask])).statistic))

        agg_raw = []
        agg_resid = []
        for sub in ready:
            raw = fisher_mean(per_subject[sub]["raw"])
            resid = fisher_mean(per_subject[sub]["resid"])
            agg_raw.append(raw)
            agg_resid.append(resid)
            subject_rows.append({
                "candidate": c,
                "subject": sub,
                "raw_loo": raw,
                "resid_loo": resid,
                "fraction_runs_positive_resid": float(np.mean(np.asarray(per_subject[sub]["resid"]) > 0)),
                "mean_edges": float(np.mean(per_subject[sub]["edges"])),
            })
        signflip = exact_signflip_p(agg_resid)
        candidate_metrics.append({
            "candidate": c,
            "primary": c == "row_mean_all",
            "mean_raw_loo": float(np.mean(agg_raw)),
            "mean_resid_loo": float(np.mean(agg_resid)),
            "median_resid_loo": float(np.median(agg_resid)),
            "resid_loo_bootstrap_95ci": boot_ci(agg_resid),
            "fraction_subjects_positive_resid": float(np.mean(np.asarray(agg_resid) > 0)),
            "exact_signflip": signflip,
            "mean_raw_pairwise": float(np.nanmean(pairwise_raw)),
            "mean_resid_pairwise": float(np.nanmean(pairwise_resid)),
        })

    with (out / "candidate_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["candidate", "primary", "mean_raw_loo", "mean_resid_loo", "median_resid_loo", "ci_low", "ci_high", "fraction_subjects_positive_resid", "one_sided_signflip_p", "two_sided_signflip_p", "mean_raw_pairwise", "mean_resid_pairwise"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for m in candidate_metrics:
            w.writerow({
                "candidate": m["candidate"], "primary": m["primary"], "mean_raw_loo": m["mean_raw_loo"],
                "mean_resid_loo": m["mean_resid_loo"], "median_resid_loo": m["median_resid_loo"],
                "ci_low": m["resid_loo_bootstrap_95ci"][0], "ci_high": m["resid_loo_bootstrap_95ci"][1],
                "fraction_subjects_positive_resid": m["fraction_subjects_positive_resid"],
                "one_sided_signflip_p": m["exact_signflip"]["one_sided_greater_p"],
                "two_sided_signflip_p": m["exact_signflip"]["two_sided_p"],
                "mean_raw_pairwise": m["mean_raw_pairwise"], "mean_resid_pairwise": m["mean_resid_pairwise"],
            })
    with (out / "subject_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(subject_rows[0]))
        w.writeheader(); w.writerows(subject_rows)
    with (out / "session_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(session_rows[0]))
        w.writeheader(); w.writerows(session_rows)

    payload = {
        "schema_version": 1,
        "dataset": "ZuCo 2.0 Task 1 normal reading",
        "model_blind": True,
        "frozen_subjects": ready,
        "n_frozen_subjects": len(ready),
        "structural_exclusion": "YTL (failed all-seven-runs structural QC before outcome analysis)",
        "sentence_mapping": "unique zero-cost monotonic alignment of EEG wordbounds counts to public task-material rows; rows 1-3 skipped for every run",
        "sentence_window": "continuous preprocessed EEG samples from each 10/12 start trigger to its paired 11/13 end trigger, [start,end)",
        "primary_candidate": "row_mean_all",
        "sensitivity_candidates": ["row_std_all", "relative_8bin_all"],
        "rdm": "feature-wise z-score across sentences within run, correlation distance",
        "nuisance_rdms": ["absolute within-run sentence-order difference", "word-count difference", "punctuation-count difference", "lowercased lexical-set Jaccard distance"],
        "min_reference_edge_subjects": args.min_reference_edge_subjects,
        "participant_aggregation": "Fisher-z mean across seven within-run LOO Spearman reliabilities",
        "inference": "participant bootstrap 95% CI plus exact participant-level sign-flip test around zero",
        "metrics": candidate_metrics,
        "loader_summary": loader_rows,
        "guardrails": [
            "No language-model embeddings are loaded.",
            "The all-retained-channel temporal mean is the prospectively designated primary ZuCo endpoint inherited from ChineseEEG.",
            "SD and relative 8-bin representations are sensitivity analyses only.",
            "No subject, sentence, candidate, nuisance control, or time window is selected from ZuCo reliability outcomes.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "primary": candidate_metrics[0], "output_dir": str(out)}, indent=2))


if __name__ == "__main__":
    main()
