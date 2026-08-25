#!/usr/bin/env python3
"""Exploratory frozen E5 transfer evaluation for two prespecified TMNRED sensitivity representations.

This analysis follows the completed confirmatory row_mean_all TMNRED transfer test.
It evaluates only row_std_all and relative_8bin_all and cannot redefine primary success.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform

PRIMARY_SCRIPT = Path(__file__).with_name("evaluate_tmnred_e5_transfer_v1.py")
REPRESENTATIONS = ["row_std_all", "relative_8bin_all"]
ARMS = ["base", "lambda_0", "lambda_0p10", "lambda_1"]


def load_primary_module():
    spec = importlib.util.spec_from_file_location("tmnred_primary_transfer_v1", PRIMARY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {PRIMARY_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def representation_features(arr: np.ndarray, name: str) -> np.ndarray:
    """Return trials x features using definitions frozen in the EEG-only reliability analysis."""
    if name == "row_std_all":
        return arr.std(axis=1, ddof=0).T
    if name == "relative_8bin_all":
        bins = np.array_split(np.arange(arr.shape[1]), 8)
        return np.concatenate([arr[:, b, :].mean(axis=1).T for b in bins], axis=1)
    raise ValueError(name)


def session_heterogeneity(session_rows: list[dict], representation: str) -> dict:
    out = {}
    for session in [f"ses-{i}" for i in range(1, 9)]:
        vals = np.asarray(
            [
                r["delta_resid_0p10_vs_0"]
                for r in session_rows
                if r["representation"] == representation and r["session"] == session
            ],
            float,
        )
        if len(vals) != 29:
            raise RuntimeError(f"unexpected session count for {representation}/{session}: {len(vals)}")
        out[session] = {
            "mean_delta": float(vals.mean()),
            "median_delta": float(np.median(vals)),
            "fraction_positive": float(np.mean(vals > 0)),
        }
    return out


def main() -> int:
    p = load_primary_module()

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/tmnred"))
    ap.add_argument(
        "--input-freeze",
        type=Path,
        default=Path("outputs/tmnred_representation_input_materialization/latest/summary.json"),
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/tmnred_e5_alternative_representations_v1/latest"),
    )
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    import torch

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if args.device == "auto" and not torch.cuda.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    root = args.data_root.resolve()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    freeze = json.loads(args.input_freeze.read_text())
    if freeze.get("ready_subjects_all_8_sessions") != p.READY_SUBJECTS:
        raise SystemExit("frozen TMNRED subject cohort mismatch")
    if freeze.get("excluded_subjects") != ["sub-25"]:
        raise SystemExit("unexpected frozen exclusion list")
    if freeze.get("item_cohort_failures"):
        raise SystemExit("TMNRED item cohort freeze is not clean")
    for session in p.SESSIONS:
        if freeze["item_coverage_by_session"][session]["n_core_items"] != 50:
            raise SystemExit(f"unexpected frozen core size for {session}")

    blocks = p.stimulus_blocks(root / "derivatives/source material/source material.xlsx")
    model_rdms, model_provenance = p.build_model_rdms(blocks, device)

    session_rows: list[dict] = []
    subject_rows: list[dict] = []
    representation_summaries = {}

    for representation in REPRESENTATIONS:
        by_subject = {
            sub: {label: {"raw": [], "resid": []} for label in ARMS}
            for sub in p.READY_SUBJECTS
        }

        for subject in p.READY_SUBJECTS:
            for session in p.SESSIONS:
                arr, emap = p.load_signal(root, subject, session)
                items = sorted(emap)
                if len(items) < 30:
                    raise RuntimeError(f"{subject}/{session}: retained item count below frozen QC")

                epidx = [emap[i] - 1 for i in items]
                feat = p.zscore_cols(representation_features(arr, representation)[epidx, :])
                neural = pdist(feat, metric="correlation")
                X = p.nuisance_for_items(items, blocks[session])
                neural_resid = p.residualize(neural, X)

                row = {
                    "representation": representation,
                    "subject": subject,
                    "session": session,
                    "n_items": len(items),
                    "n_edges": len(neural),
                }
                ix = np.asarray(items, dtype=int) - 1
                for label in ARMS:
                    model_square = model_rdms[label][session]
                    model_vec = squareform(model_square[np.ix_(ix, ix)], checks=False)
                    if len(model_vec) != len(neural):
                        raise RuntimeError("model/neural edge count mismatch")
                    raw = p.safe_rho(neural, model_vec)
                    resid = p.safe_rho(neural_resid, p.residualize(model_vec, X))
                    row[f"raw_{label}"] = raw
                    row[f"resid_{label}"] = resid
                    by_subject[subject][label]["raw"].append(raw)
                    by_subject[subject][label]["resid"].append(resid)

                row["delta_resid_0p10_vs_0"] = row["resid_lambda_0p10"] - row["resid_lambda_0"]
                row["delta_raw_0p10_vs_0"] = row["raw_lambda_0p10"] - row["raw_lambda_0"]
                row["delta_resid_1_vs_0"] = row["resid_lambda_1"] - row["resid_lambda_0"]
                session_rows.append(row)

        rep_subject_rows = []
        for subject in p.READY_SUBJECTS:
            row = {"representation": representation, "subject": subject}
            for label in ARMS:
                row[f"raw_{label}"] = p.fisher_mean(by_subject[subject][label]["raw"])
                row[f"resid_{label}"] = p.fisher_mean(by_subject[subject][label]["resid"])
            row["delta_resid_0p10_vs_0"] = row["resid_lambda_0p10"] - row["resid_lambda_0"]
            row["delta_raw_0p10_vs_0"] = row["raw_lambda_0p10"] - row["raw_lambda_0"]
            row["delta_resid_1_vs_0"] = row["resid_lambda_1"] - row["resid_lambda_0"]
            row["delta_raw_1_vs_0"] = row["raw_lambda_1"] - row["raw_lambda_0"]
            subject_rows.append(row)
            rep_subject_rows.append(row)

        primary_delta = np.asarray([r["delta_resid_0p10_vs_0"] for r in rep_subject_rows], float)
        raw_delta = np.asarray([r["delta_raw_0p10_vs_0"] for r in rep_subject_rows], float)
        lambda1_delta = np.asarray([r["delta_resid_1_vs_0"] for r in rep_subject_rows], float)

        def arm_summary(prefix: str):
            return {
                label: float(np.mean([r[f"{prefix}_{label}"] for r in rep_subject_rows]))
                for label in ARMS
            }

        seed_offset = 0 if representation == "row_std_all" else 100
        representation_summaries[representation] = {
            "status": "exploratory_alternative_representation",
            "mean_participant_resid_rsa_by_arm": arm_summary("resid"),
            "mean_participant_raw_rsa_by_arm": arm_summary("raw"),
            "lambda_0p10_minus_lambda_0_residual_RSA": {
                "mean_delta": float(primary_delta.mean()),
                "median_delta": float(np.median(primary_delta)),
                "fraction_positive": float(np.mean(primary_delta > 0)),
                "bootstrap_95ci_mean": p.bootstrap_ci(primary_delta, seed=20260827 + seed_offset),
                "one_sided_signflip": p.signflip_mc(primary_delta, seed=20260827 + seed_offset),
            },
            "lambda_0p10_minus_lambda_0_raw_RSA": {
                "mean_delta": float(raw_delta.mean()),
                "median_delta": float(np.median(raw_delta)),
                "fraction_positive": float(np.mean(raw_delta > 0)),
                "bootstrap_95ci_mean": p.bootstrap_ci(raw_delta, seed=20260828 + seed_offset),
                "one_sided_signflip": p.signflip_mc(raw_delta, seed=20260828 + seed_offset),
            },
            "lambda_1_minus_lambda_0_residual_RSA_descriptive": {
                "mean_delta": float(lambda1_delta.mean()),
                "median_delta": float(np.median(lambda1_delta)),
                "fraction_positive": float(np.mean(lambda1_delta > 0)),
            },
            "session_heterogeneity_lambda_0p10_minus_lambda_0_residual_RSA": session_heterogeneity(
                session_rows, representation
            ),
        }

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/tmnred_e5_alternative_representation_exploratory_protocol_v1.md",
        "analysis_status": "post-confirmatory exploratory alternative-representation transfer",
        "dataset": "TMNRED",
        "openneuro_accession": "ds005383",
        "published_snapshot": "1.0.0",
        "model_id": p.MODEL_ID,
        "model_revision": p.MODEL_REVISION,
        "model_provenance": model_provenance,
        "device": device,
        "n_subjects": len(p.READY_SUBJECTS),
        "subjects": p.READY_SUBJECTS,
        "excluded_subject": "sub-25",
        "resampled_subject": "sub-23",
        "representations": {
            "row_std_all": "channel-wise standard deviation across the frozen 0.0-2.0 s interval",
            "relative_8bin_all": "eight deterministic contiguous temporal-bin mean amplitudes concatenated across all 30 channels",
        },
        "eeg_window_seconds": [0.0, 2.0],
        "participant_aggregation": "Fisher-z mean across eight within-session RSA values",
        "nuisance_rdms": [
            "absolute trial-position difference",
            "CJK character-count difference",
            "punctuation-count difference",
            "CJK character-set Jaccard distance",
        ],
        "representation_results": representation_summaries,
        "guardrails": [
            "The completed row_mean_all TMNRED transfer analysis remains the confirmatory result.",
            "Only row_std_all and relative_8bin_all are evaluated here.",
            "TMNRED is not used for model training or hyperparameter selection.",
            "No new time window, spatial group, frequency band, phase measure, model layer, pooling rule, distance metric, nuisance set, or lambda is selected from these outcomes.",
            "Any positive result requires independent confirmation in a later dataset such as ZuCo.",
        ],
    }

    p.write_csv(outdir / "session_results.csv", session_rows)
    p.write_csv(outdir / "subject_results.csv", subject_rows)
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "representation_results": representation_summaries, "output_dir": str(outdir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
