#!/usr/bin/env python3
"""Run the prospectively frozen Garnett Dream EEG-only reliability analysis.

This is the first outcome-bearing Garnett Dream analysis. It uses the frozen
filtered_0.5_30 BrainVision inputs and the frozen chapter + ROWS->ROWE item
identity. No language-model quantity is loaded or computed.

Primary representation: row_mean_all (time mean within each retained EEG
channel; never average channels), feature-wise z-score across items, then
correlation-distance RDM.

Because the model-blind Garnett audit found no exact presentation-row text
mapping before outcome access, the reliability-stage nuisance set is the
model-blind subset of the historical Little Prince nuisance family that is
available at the frozen unit: within-chapter row/order difference and
presentation-duration difference. Text-length, punctuation, lexical Jaccard,
and chapter-identity terms are not fabricated or inferred post hoc. The full
text-derived nuisance family remains required for later model validation once
an exact row-text mapping is frozen.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
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
    mu = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - mu) / sd


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
    if not values:
        return float("nan")
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
    stats = []
    for signs in itertools.product((-1.0, 1.0), repeat=len(arr)):
        stats.append(float(np.mean(arr * np.asarray(signs))))
    stats_arr = np.asarray(stats)
    return {
        "observed_mean": obs,
        "one_sided_greater_p": float(np.mean(stats_arr >= obs - 1e-15)),
        "two_sided_p": float(np.mean(np.abs(stats_arr) >= abs(obs) - 1e-15)),
        "n_sign_patterns": int(len(stats_arr)),
    }


def companion_vhdr_by_run(inventory: list[dict[str, str]]) -> dict[tuple[str, int, int], str]:
    out = {}
    for r in inventory:
        path = r.get("path", "")
        if path.endswith("_eeg.vhdr") and r.get("status") == "materialized":
            key = (str(r["subject"]), int(r["run"]), int(r["chapter"]))
            out[key] = path
    return out


def features_for_run(
    data_root: Path,
    vhdr_rel: str,
    item_rows: list[dict[str, str]],
) -> tuple[dict[str, np.ndarray], np.ndarray, list[str]]:
    vhdr = data_root / vhdr_rel
    events_path = Path(str(vhdr_rel).replace("_eeg.vhdr", "_events.tsv"))
    events = read_tsv(data_root / events_path)

    # Preserve the worktree path; BrainVision companion references are relative.
    raw = mne.io.read_raw_brainvision(vhdr.absolute(), preload=True, verbose="ERROR")
    picks = mne.pick_types(raw.info, eeg=True, meg=False, eog=False, ecg=False, stim=False, exclude=[])
    if len(picks) < 100:
        raise ValueError(f"Unexpectedly few EEG channels: {len(picks)} for {vhdr_rel}")
    channels = [raw.ch_names[int(i)] for i in picks]
    sfreq = float(raw.info["sfreq"])

    means = []
    stds = []
    rel8 = []
    durations = []

    rows_sorted = sorted(item_rows, key=lambda r: int(r["item_index"]))
    expected = list(range(1, len(rows_sorted) + 1))
    got = [int(r["item_index"]) for r in rows_sorted]
    if got != expected:
        raise ValueError("Non-contiguous frozen item_index sequence")

    for r in rows_sorted:
        si = int(r["rows_event_row"]) - 1
        ei = int(r["rowe_event_row"]) - 1
        if not (0 <= si < len(events) and 0 <= ei < len(events)):
            raise ValueError("Frozen event row outside event table")
        if str(events[si].get("trial_type", "")).strip() != "ROWS" or str(events[ei].get("trial_type", "")).strip() != "ROWE":
            raise ValueError("Frozen ROWS/ROWE identity no longer matches event table")
        start_sec = float(events[si]["onset"])
        stop_sec = float(events[ei]["onset"])
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
        bins = [x[:, edges[b]:edges[b + 1]].mean(axis=1) for b in range(8)]
        rel8.append(np.concatenate(bins, axis=0))
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
    items_by_key: dict[tuple[str, int, int], list[dict[str, str]]] = defaultdict(list)
    for r in items:
        items_by_key[(str(r["subject"]), int(r["run"]), int(r["chapter"]))].append(r)

    candidate_names = ["row_mean_all", "row_std_all", "relative_8bin_all"]
    chapter_data: dict[int, dict[str, dict[str, np.ndarray]]] = defaultdict(dict)
    chapter_durations: dict[int, dict[str, np.ndarray]] = defaultdict(dict)
    chapter_channels: dict[int, list[str]] = {}
    run_records = []

    for key, vhdr_rel in sorted(vhdrs.items(), key=lambda kv: (kv[0][2], kv[0][0])):
        sub, run, chapter = key
        feats, durations, channels = features_for_run(data_root, vhdr_rel, items_by_key[key])
        if chapter in chapter_channels and chapter_channels[chapter] != channels:
            raise ValueError(f"Channel identity mismatch within chapter {chapter}")
        chapter_channels.setdefault(chapter, channels)
        chapter_data[chapter][sub] = feats
        chapter_durations[chapter][sub] = durations
        run_records.append({"subject": sub, "run": run, "chapter": chapter, "n_items": len(durations), "n_eeg_channels": len(channels)})

    chapter_metric_rows = []
    subject_values: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for chapter in sorted(chapter_data):
        subs = sorted(chapter_data[chapter])
        if len(subs) < 8:
            raise ValueError(f"Chapter {chapter} has too few participants: {len(subs)}")
        n_items = {chapter_data[chapter][s]["row_mean_all"].shape[0] for s in subs}
        if len(n_items) != 1:
            raise ValueError(f"Item-count mismatch in chapter {chapter}: {sorted(n_items)}")
        n = next(iter(n_items))
        order_rdm = pdist(np.arange(1, n + 1, dtype=float)[:, None], metric="cityblock")

        for candidate in candidate_names:
            raw_rdms = {}
            resid_rdms = {}
            for s in subs:
                rdm = rdm_from_features(chapter_data[chapter][s][candidate])
                duration_rdm = pdist(chapter_durations[chapter][s][:, None], metric="cityblock")
                raw_rdms[s] = rdm
                resid_rdms[s] = residualize(rdm, [order_rdm, duration_rdm])

            for s in subs:
                others = [o for o in subs if o != s]
                raw_consensus = np.mean(np.stack([raw_rdms[o] for o in others]), axis=0)
                resid_consensus = np.mean(np.stack([resid_rdms[o] for o in others]), axis=0)
                raw_rho = safe_spearman(raw_rdms[s], raw_consensus)
                resid_rho = safe_spearman(resid_rdms[s], resid_consensus)
                subject_values[s][candidate]["raw"].append(raw_rho)
                subject_values[s][candidate]["residual"].append(resid_rho)
                chapter_metric_rows.append({
                    "subject": s,
                    "chapter": chapter,
                    "candidate": candidate,
                    "n_items": n,
                    "n_reference_subjects": len(others),
                    "raw_loo_spearman": raw_rho,
                    "residual_loo_spearman": resid_rho,
                })

    subject_rows = []
    candidate_summaries = {}
    for candidate in candidate_names:
        participant_resid = []
        participant_raw = []
        for s in sorted(subject_values):
            raw = fisher_mean(subject_values[s][candidate]["raw"])
            resid = fisher_mean(subject_values[s][candidate]["residual"])
            participant_raw.append(raw)
            participant_resid.append(resid)
            subject_rows.append({
                "subject": s,
                "candidate": candidate,
                "n_chapters": len(subject_values[s][candidate]["residual"]),
                "raw_fisher_mean_loo": raw,
                "residual_fisher_mean_loo": resid,
            })
        candidate_summaries[candidate] = {
            "n_subjects": len(participant_resid),
            "mean_raw_loo": float(np.mean(participant_raw)),
            "median_raw_loo": float(np.median(participant_raw)),
            "mean_residual_loo": float(np.mean(participant_resid)),
            "median_residual_loo": float(np.median(participant_resid)),
            "fraction_positive_residual_loo": float(np.mean(np.asarray(participant_resid) > 0)),
            "participant_bootstrap_95ci_residual_mean": bootstrap_ci(participant_resid),
            "exact_signflip_residual_mean": exact_signflip(participant_resid),
        }

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / "chapter_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["subject", "chapter", "candidate", "n_items", "n_reference_subjects", "raw_loo_spearman", "residual_loo_spearman"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(chapter_metric_rows)
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
        "frozen_input": str(args.input_freeze),
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
            "future_model_validation_requirement": "Freeze exact presentation-row text mapping and restore the applicable text-derived nuisance family before any neural-model validation."
        },
        "cohort": freeze.get("ready_subjects"),
        "n_ready_runs": freeze.get("n_ready_runs"),
        "chapter_support_runs": freeze.get("chapter_support_runs"),
        "candidate_summaries": candidate_summaries,
        "primary_result": candidate_summaries["row_mean_all"],
        "guardrails": [
            "No participant, chapter, item, sensor, time window, or representation is selected from Garnett reliability outcomes.",
            "row_mean_all is primary; row_std_all and relative_8bin_all are sensitivity analyses only.",
            "No language-model embeddings or neural-guided adapters are loaded.",
            "A null primary result narrows same-participant/new-text generalization rather than triggering feature searches."
        ]
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "primary": candidate_summaries["row_mean_all"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
