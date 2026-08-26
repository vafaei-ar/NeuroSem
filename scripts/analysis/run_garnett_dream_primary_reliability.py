#!/usr/bin/env python3
"""Prospectively frozen Garnett Dream EEG-only reliability analysis.

Primary: row_mean_all. Sensitivities: row_std_all and relative_8bin_all.
No language-model quantity is loaded or computed.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import tempfile
from collections import defaultdict
from pathlib import Path

import mne
import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import rankdata, spearmanr


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def zscore_columns(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError(f"Expected finite 2D features, got {x.shape}")
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - x.mean(axis=0)) / sd


def rank_z(x: np.ndarray) -> np.ndarray:
    r = rankdata(np.asarray(x, dtype=np.float64), method="average")
    r -= r.mean()
    sd = r.std()
    if sd == 0 or not np.isfinite(sd):
        raise ValueError("Degenerate ranked vector")
    return r / sd


def residualize(y: np.ndarray, nuisances: list[np.ndarray]) -> np.ndarray:
    yr = rank_z(y)
    X = np.column_stack([np.ones_like(yr)] + [rank_z(n) for n in nuisances])
    beta, *_ = np.linalg.lstsq(X, yr, rcond=None)
    resid = yr - X @ beta
    resid -= resid.mean()
    sd = resid.std()
    if sd == 0 or not np.isfinite(sd):
        raise ValueError("Degenerate residual RDM")
    return resid / sd


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise ValueError("Non-finite Spearman correlation")
    return rho


def rdm_from_features(x: np.ndarray) -> np.ndarray:
    r = pdist(zscore_columns(x), metric="correlation")
    if not np.isfinite(r).all():
        raise ValueError("Non-finite correlation-distance RDM")
    return r


def fisher_mean(values: list[float]) -> float:
    z = np.arctanh(np.clip(np.asarray(values, dtype=float), -0.999999, 0.999999))
    return float(np.tanh(z.mean()))


def bootstrap_ci(values: list[float], n_boot: int = 20000, seed: int = 20260826) -> list[float]:
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        means[i] = rng.choice(arr, size=len(arr), replace=True).mean()
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def exact_signflip(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=float)
    obs = float(arr.mean())
    stats = np.asarray([
        float(np.mean(arr * np.asarray(signs)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(arr))
    ])
    return {
        "observed_mean": obs,
        "one_sided_greater_p": float(np.mean(stats >= obs - 1e-15)),
        "two_sided_p": float(np.mean(np.abs(stats) >= abs(obs) - 1e-15)),
        "n_sign_patterns": int(len(stats)),
    }


def companion_vhdr_by_run(inventory: list[dict[str, str]]) -> dict[tuple[str, int, int], str]:
    out = {}
    for r in inventory:
        path = r.get("path", "")
        if path.endswith("_eeg.vhdr") and r.get("status") == "materialized":
            out[(str(r["subject"]), int(r["run"]), int(r["chapter"]))] = path
    return out


def read_brainvision_with_published_typo(vhdr: Path) -> mne.io.BaseRaw:
    """Read one run without modifying the dataset worktree.

    The published BrainVision headers/markers use ses-GranettDream internally
    while the tracked filenames use ses-GarnettDream. Create a temporary,
    normalized BrainVision view only for MNE I/O.
    """
    header = vhdr.read_text(encoding="utf-8-sig", errors="replace")
    if "GranettDream" not in header:
        return mne.io.read_raw_brainvision(vhdr.absolute(), preload=True, verbose="ERROR")

    actual_vmrk = vhdr.with_suffix(".vmrk")
    actual_eeg = vhdr.with_suffix(".eeg")
    marker = actual_vmrk.read_text(encoding="utf-8-sig", errors="replace")
    with tempfile.TemporaryDirectory(prefix="neurosem_garnett_bv_") as td:
        tdir = Path(td)
        tvhdr = tdir / vhdr.name
        tvmrk = tdir / actual_vmrk.name
        teeg = tdir / actual_eeg.name
        tvhdr.write_text(header.replace("GranettDream", "GarnettDream"), encoding="utf-8")
        tvmrk.write_text(marker.replace("GranettDream", "GarnettDream"), encoding="utf-8")
        teeg.symlink_to(actual_eeg.absolute())
        raw = mne.io.read_raw_brainvision(tvhdr, preload=True, verbose="ERROR")
    return raw


def features_for_run(data_root: Path, vhdr_rel: str, item_rows: list[dict[str, str]]):
    vhdr = data_root / vhdr_rel
    events = read_tsv(data_root / Path(vhdr_rel.replace("_eeg.vhdr", "_events.tsv")))
    raw = read_brainvision_with_published_typo(vhdr)
    picks = mne.pick_types(raw.info, eeg=True, meg=False, eog=False, ecg=False, stim=False, exclude=[])
    if len(picks) < 100:
        raise ValueError(f"Unexpectedly few EEG channels: {len(picks)} for {vhdr_rel}")
    channels = [raw.ch_names[int(i)] for i in picks]
    sfreq = float(raw.info["sfreq"])

    means, stds, rel8, durations = [], [], [], []
    rows_sorted = sorted(item_rows, key=lambda r: int(r["item_index"]))
    if [int(r["item_index"]) for r in rows_sorted] != list(range(1, len(rows_sorted) + 1)):
        raise ValueError("Non-contiguous frozen item_index sequence")

    for r in rows_sorted:
        si, ei = int(r["rows_event_row"]) - 1, int(r["rowe_event_row"]) - 1
        if str(events[si].get("trial_type", "")).strip() != "ROWS" or str(events[ei].get("trial_type", "")).strip() != "ROWE":
            raise ValueError("Frozen ROWS/ROWE identity no longer matches event table")
        start_sec, stop_sec = float(events[si]["onset"]), float(events[ei]["onset"])
        if stop_sec <= start_sec:
            raise ValueError("Non-positive ROWS->ROWE duration")
        start = max(0, min(raw.n_times, int(round(start_sec * sfreq))))
        stop = max(0, min(raw.n_times, int(round(stop_sec * sfreq))))
        if stop <= start:
            raise ValueError("Empty ROWS->ROWE sample interval")
        x = raw.get_data(picks=picks, start=start, stop=stop)
        if x.shape[1] < 8:
            raise ValueError("Too few samples for relative_8bin sensitivity")
        means.append(x.mean(axis=1))
        stds.append(x.std(axis=1))
        edges = np.linspace(0, x.shape[1], 9, dtype=int)
        rel8.append(np.concatenate([x[:, edges[b]:edges[b + 1]].mean(axis=1) for b in range(8)]))
        durations.append(stop_sec - start_sec)
    raw.close()
    return {
        "row_mean_all": np.asarray(means, dtype=np.float64),
        "row_std_all": np.asarray(stds, dtype=np.float64),
        "relative_8bin_all": np.asarray(rel8, dtype=np.float64),
    }, np.asarray(durations, dtype=np.float64), channels


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--input-freeze", type=Path, default=Path("outputs/garnett_dream_input_materialization/latest/summary.json"))
    ap.add_argument("--session-inventory", type=Path, default=Path("outputs/garnett_dream_input_materialization/latest/session_inventory.csv"))
    ap.add_argument("--item-identity", type=Path, default=Path("outputs/garnett_dream_input_materialization/latest/item_identity.csv"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_primary_reliability/latest"))
    args = ap.parse_args()

    data_root = args.data_root.resolve()
    freeze = json.loads(args.input_freeze.read_text(encoding="utf-8"))
    if not freeze.get("freeze_gate", {}).get("ready_for_reliability"):
        raise SystemExit("Garnett input freeze is not ready for reliability")
    if freeze.get("n_ready_subjects") != 10 or freeze.get("n_ready_runs") != 171:
        raise SystemExit("Unexpected frozen Garnett cohort/run count")

    inventory = read_csv(args.session_inventory)
    items = read_csv(args.item_identity)
    vhdrs = companion_vhdr_by_run(inventory)
    items_by_key = defaultdict(list)
    for r in items:
        items_by_key[(str(r["subject"]), int(r["run"]), int(r["chapter"]))].append(r)

    candidates = ["row_mean_all", "row_std_all", "relative_8bin_all"]
    chapter_data, chapter_durations, chapter_channels = defaultdict(dict), defaultdict(dict), {}

    for key, vhdr_rel in sorted(vhdrs.items(), key=lambda kv: (kv[0][2], kv[0][0])):
        sub, _, chapter = key
        feats, durations, channels = features_for_run(data_root, vhdr_rel, items_by_key[key])
        if chapter in chapter_channels and chapter_channels[chapter] != channels:
            raise ValueError(f"Channel identity mismatch within chapter {chapter}")
        chapter_channels.setdefault(chapter, channels)
        chapter_data[chapter][sub] = feats
        chapter_durations[chapter][sub] = durations

    chapter_rows = []
    subject_values = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for chapter in sorted(chapter_data):
        subs = sorted(chapter_data[chapter])
        if len(subs) < 8:
            raise ValueError(f"Chapter {chapter} has too few participants: {len(subs)}")
        n_items = {chapter_data[chapter][s]["row_mean_all"].shape[0] for s in subs}
        if len(n_items) != 1:
            raise ValueError(f"Item-count mismatch in chapter {chapter}: {sorted(n_items)}")
        n = next(iter(n_items))
        order_rdm = pdist(np.arange(1, n + 1, dtype=float)[:, None], metric="cityblock")
        for candidate in candidates:
            raw_rdms, resid_rdms = {}, {}
            for s in subs:
                rdm = rdm_from_features(chapter_data[chapter][s][candidate])
                duration_rdm = pdist(chapter_durations[chapter][s][:, None], metric="cityblock")
                raw_rdms[s] = rdm
                resid_rdms[s] = residualize(rdm, [order_rdm, duration_rdm])
            for s in subs:
                others = [o for o in subs if o != s]
                raw_rho = safe_spearman(raw_rdms[s], np.mean(np.stack([raw_rdms[o] for o in others]), axis=0))
                resid_rho = safe_spearman(resid_rdms[s], np.mean(np.stack([resid_rdms[o] for o in others]), axis=0))
                subject_values[s][candidate]["raw"].append(raw_rho)
                subject_values[s][candidate]["residual"].append(resid_rho)
                chapter_rows.append({"subject": s, "chapter": chapter, "candidate": candidate, "n_items": n, "n_reference_subjects": len(others), "raw_loo_spearman": raw_rho, "residual_loo_spearman": resid_rho})

    subject_rows, summaries = [], {}
    for candidate in candidates:
        raw_vals, resid_vals = [], []
        for s in sorted(subject_values):
            raw = fisher_mean(subject_values[s][candidate]["raw"])
            resid = fisher_mean(subject_values[s][candidate]["residual"])
            raw_vals.append(raw); resid_vals.append(resid)
            subject_rows.append({"subject": s, "candidate": candidate, "n_chapters": len(subject_values[s][candidate]["residual"]), "raw_fisher_mean_loo": raw, "residual_fisher_mean_loo": resid})
        summaries[candidate] = {
            "n_subjects": len(resid_vals),
            "mean_raw_loo": float(np.mean(raw_vals)),
            "median_raw_loo": float(np.median(raw_vals)),
            "mean_residual_loo": float(np.mean(resid_vals)),
            "median_residual_loo": float(np.median(resid_vals)),
            "fraction_positive_residual_loo": float(np.mean(np.asarray(resid_vals) > 0)),
            "participant_bootstrap_95ci_residual_mean": bootstrap_ci(resid_vals),
            "exact_signflip_residual_mean": exact_signflip(resid_vals),
        }

    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    with (out / "chapter_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["subject", "chapter", "candidate", "n_items", "n_reference_subjects", "raw_loo_spearman", "residual_loo_spearman"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(chapter_rows)
    with (out / "subject_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["subject", "candidate", "n_chapters", "raw_fisher_mean_loo", "residual_fisher_mean_loo"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(subject_rows)

    summary = {
        "schema_version": 1,
        "dataset": "ChineseEEG Garnett Dream",
        "analysis": "prospectively frozen EEG-only primary-representation reliability",
        "model_blind": True,
        "computes_model_quantities": False,
        "participant_inferential_unit": True,
        "primary_candidate": "row_mean_all",
        "sensitivity_candidates": ["row_std_all", "relative_8bin_all"],
        "representation": "time-average separately within every retained EEG channel; never average channels; feature-wise z-score across items; correlation-distance RDM",
        "chapter_aggregation": "within-chapter LOO Spearman reliability, then equal-weight Fisher-z mean across available chapters per participant",
        "nuisance_residualization": {
            "frozen_for_this_reliability_stage_before_outcomes": True,
            "terms": ["within-chapter row/order difference", "presentation-duration difference"],
            "historical_little_prince_terms_verified_in_current_pipeline": ["run-position difference", "duration difference", "character-count difference", "chapter-identity difference", "character-set Jaccard distance", "punctuation-count difference"],
            "omitted_here_before_outcomes": ["text-length difference", "punctuation-count difference", "lexical/Jaccard distance", "chapter-identity difference"],
            "reason": "Exact Garnett presentation-row text mapping was not available after the model-blind structural audit; chapter identity is constant within each independently analyzed chapter. No text nuisance is approximated post hoc.",
            "future_model_validation_requirement": "Freeze exact presentation-row text mapping and restore applicable text-derived nuisances before neural-model validation."
        },
        "brainvision_reference_policy": "For MNE I/O only, normalize the published internal GranettDream typo to GarnettDream in a temporary view; do not modify dataset files.",
        "cohort": freeze.get("ready_subjects"),
        "n_ready_runs": freeze.get("n_ready_runs"),
        "chapter_support_runs": freeze.get("chapter_support_runs"),
        "candidate_summaries": summaries,
        "primary_result": summaries["row_mean_all"],
        "guardrails": [
            "No participant, chapter, item, sensor, time window, or representation is selected from Garnett reliability outcomes.",
            "row_mean_all is primary; row_std_all and relative_8bin_all are sensitivity analyses only.",
            "No language-model embeddings or neural-guided adapters are loaded.",
            "A null primary result narrows same-participant/new-text generalization rather than triggering feature searches."
        ]
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "primary": summaries["row_mean_all"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
