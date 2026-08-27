#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_chineseeeg_reliability(root: Path) -> tuple[Path, Path]:
    candidates = []
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and (d / "summary.json").exists() and (d / "subject_summary.csv").exists():
                candidates.append(d)
    if not candidates:
        raise FileNotFoundError(f"No completed ChineseEEG residual reliability output under {root}")
    d = sorted(candidates)[-1]
    return d / "summary.json", d / "subject_summary.csv"


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load_reliability(outputs: Path) -> tuple[list[dict], list[dict], dict[str, str]]:
    source_files: dict[str, str] = {}
    rows: list[dict] = []
    summary_rows: list[dict] = []

    lp_summary_path, lp_subject_path = latest_chineseeeg_reliability(outputs / "chineseeeg_rowmean_residual_reliability")
    lp_summary = read_json(lp_summary_path)
    lp_subjects = read_csv(lp_subject_path)
    vals = np.asarray([float(r["residual_loo"]) for r in lp_subjects], float)
    for r in lp_subjects:
        rows.append({"dataset": "Little Prince", "subject": r["subject"], "residual_loo": float(r["residual_loo"])})
    summary_rows.append({
        "dataset": "Little Prince",
        "n": int(len(vals)),
        "mean_residual_loo": float(lp_summary["residual_loo_mean"]),
        "ci_low": "",
        "ci_high": "",
        "ci_source": "not frozen for this historical checkpoint",
    })
    source_files["little_prince_summary"] = str(lp_summary_path)
    source_files["little_prince_subjects"] = str(lp_subject_path)

    tm_summary_path = require(outputs / "tmnred_primary_representation_reliability/latest/summary.json")
    tm_subject_path = require(outputs / "tmnred_primary_representation_reliability/latest/subject_metrics.csv")
    tm = read_json(tm_summary_path)
    tm_metric = next(m for m in tm["metrics"] if m["candidate"] == "row_mean_all")
    tm_rows = [r for r in read_csv(tm_subject_path) if r["candidate"] == "row_mean_all"]
    for r in tm_rows:
        rows.append({"dataset": "TMNRED", "subject": r["subject"], "residual_loo": float(r["resid_loo"])})
    summary_rows.append({
        "dataset": "TMNRED", "n": len(tm_rows), "mean_residual_loo": float(tm_metric["mean_resid_loo"]),
        "ci_low": float(tm_metric["resid_loo_bootstrap_95ci"][0]), "ci_high": float(tm_metric["resid_loo_bootstrap_95ci"][1]),
        "ci_source": "locked participant bootstrap",
    })
    source_files["tmnred_summary"] = str(tm_summary_path)
    source_files["tmnred_subjects"] = str(tm_subject_path)

    zu_summary_path = require(outputs / "zuco2_nr_primary_representation_reliability/latest/summary.json")
    zu_subject_path = require(outputs / "zuco2_nr_primary_representation_reliability/latest/subject_metrics.csv")
    zu = read_json(zu_summary_path)
    if "primary_result" in zu:
        zu_metric = zu["primary_result"]
    else:
        zu_metric = next(m for m in zu.get("metrics", []) if m.get("candidate") == "row_mean_all")
    zu_rows_all = read_csv(zu_subject_path)
    zu_rows = [r for r in zu_rows_all if r.get("candidate") == "row_mean_all"]
    for r in zu_rows:
        key = "residual_fisher_mean_loo" if "residual_fisher_mean_loo" in r else "resid_loo"
        rows.append({"dataset": "ZuCo 2.0", "subject": r["subject"], "residual_loo": float(r[key])})
    zmean = zu_metric.get("mean_residual_loo", zu_metric.get("mean_resid_loo"))
    zci = zu_metric.get("participant_bootstrap_95ci_residual_mean", zu_metric.get("resid_loo_bootstrap_95ci"))
    summary_rows.append({
        "dataset": "ZuCo 2.0", "n": len(zu_rows), "mean_residual_loo": float(zmean),
        "ci_low": float(zci[0]), "ci_high": float(zci[1]), "ci_source": "locked participant bootstrap",
    })
    source_files["zuco_summary"] = str(zu_summary_path)
    source_files["zuco_subjects"] = str(zu_subject_path)

    ga_summary_path = require(outputs / "garnett_dream_primary_reliability/latest/summary.json")
    ga_subject_path = require(outputs / "garnett_dream_primary_reliability/latest/subject_metrics.csv")
    ga = read_json(ga_summary_path)
    ga_metric = ga["primary_result"]
    ga_rows = [r for r in read_csv(ga_subject_path) if r["candidate"] == "row_mean_all"]
    for r in ga_rows:
        rows.append({"dataset": "Garnett Dream", "subject": r["subject"], "residual_loo": float(r["residual_fisher_mean_loo"])})
    gci = ga_metric["participant_bootstrap_95ci_residual_mean"]
    summary_rows.append({
        "dataset": "Garnett Dream", "n": len(ga_rows), "mean_residual_loo": float(ga_metric["mean_residual_loo"]),
        "ci_low": float(gci[0]), "ci_high": float(gci[1]), "ci_source": "locked participant bootstrap",
    })
    source_files["garnett_summary"] = str(ga_summary_path)
    source_files["garnett_subjects"] = str(ga_subject_path)
    return rows, summary_rows, source_files


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def figure_reliability(participants: list[dict], summaries: list[dict], out: Path) -> None:
    order = ["Little Prince", "TMNRED", "ZuCo 2.0", "Garnett Dream"]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    rng = np.random.default_rng(20260827)
    for i, ds in enumerate(order):
        vals = np.asarray([r["residual_loo"] for r in participants if r["dataset"] == ds], float)
        jitter = rng.uniform(-0.10, 0.10, size=len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals, s=25, alpha=0.65, edgecolors="none")
        s = next(r for r in summaries if r["dataset"] == ds)
        mean = float(s["mean_residual_loo"])
        ax.scatter([i], [mean], marker="D", s=58, zorder=4)
        if s["ci_low"] != "":
            lo, hi = float(s["ci_low"]), float(s["ci_high"])
            ax.vlines(i, lo, hi, linewidth=2.0, zorder=3)
    ax.axhline(0, linewidth=0.9)
    ax.set_xticks(range(len(order)), order)
    ax.set_ylabel("Residual LOO neural-geometry reliability (Spearman)")
    ax.set_title("Reproducible reading-related neural geometry")
    ax.text(0.01, 0.01, "Points: participants; diamonds: means; intervals: locked 95% bootstrap CIs where available.",
            transform=ax.transAxes, fontsize=8, va="bottom")
    fig.tight_layout()
    fig.savefig(out / "fig2_reading_reliability.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / "fig2_reading_reliability.pdf", bbox_inches="tight")
    plt.close(fig)


def load_ahba(outputs: Path) -> tuple[list[dict], dict[str, str]]:
    set_path = require(outputs / "ahba_frozen_gene_set_association_v1/latest/set_results.csv")
    rows = read_csv(set_path)
    for r in rows:
        for k in ["n_genes", "mean_spearman", "mean_fisher_z", "signflip_p_two_sided", "size_matched_random_p_two_sided", "bh_fdr_q_within_family"]:
            if k in r and r[k] != "":
                r[k] = int(r[k]) if k == "n_genes" else float(r[k])
    return rows, {"ahba_set_results": str(set_path)}


def figure_ahba(rows: list[dict], out: Path) -> None:
    primary = [r for r in rows if r["family"] == "primary_mechanistic"]
    controls = [r for r in rows if r["family"] == "specificity_control"]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), sharex=True)
    for ax, data, title in zip(axes, [primary, controls], ["Prespecified molecular systems", "Specificity controls"]):
        y = np.arange(len(data))
        vals = [float(r["mean_spearman"]) for r in data]
        ax.axvline(0, linewidth=0.9)
        ax.scatter(vals, y, s=44)
        ax.set_yticks(y, [r["set"].replace("_", " ") for r in data])
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel("Mean participant Spearman rho")
        for yi, r in enumerate(data):
            p = float(r["signflip_p_two_sided"])
            q = float(r["bh_fdr_q_within_family"])
            rp = float(r["size_matched_random_p_two_sided"])
            ax.text(0.99, yi, f"p={p:.3f}, q={q:.3f}, rand={rp:.3f}", transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=7)
    fig.suptitle("Frozen AHBA gene-set associations: prespecified systems were not supported", y=1.01)
    fig.text(0.5, 0.01, "Participant-level sign-flip inference; all prespecified families shown. Population AHBA is a spatial prior, not participant molecular data.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / "fig4_ahba_frozen_molecular_nulls.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / "fig4_ahba_frozen_molecular_nulls.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-root", type=Path, default=Path("outputs"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/manuscript_figures_v1/latest"))
    args = ap.parse_args()
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    outputs = args.outputs_root.resolve()

    participants, rel_summary, rel_sources = load_reliability(outputs)
    ahba_rows, ahba_sources = load_ahba(outputs)
    figure_reliability(participants, rel_summary, out)
    figure_ahba(ahba_rows, out)
    write_csv(out / "table2_reliability_summary.csv", rel_summary)
    write_csv(out / "table3_ahba_gene_sets.csv", ahba_rows)

    manifest = {
        "schema_version": 1,
        "analysis": "NeuroSem manuscript figures v1",
        "generated_from_locked_outputs_only": True,
        "figures": ["fig2_reading_reliability.png", "fig2_reading_reliability.pdf", "fig4_ahba_frozen_molecular_nulls.png", "fig4_ahba_frozen_molecular_nulls.pdf"],
        "tables": ["table2_reliability_summary.csv", "table3_ahba_gene_sets.csv"],
        "sources": {**rel_sources, **ahba_sources},
        "guardrails": [
            "No model fitting, feature selection, gene-set selection, or hypothesis testing is performed here.",
            "The script visualizes already-locked analysis outputs and fails when required outputs are missing.",
            "Little Prince historical reliability has no newly invented confidence interval.",
            "AHBA primary and specificity-control families are both plotted in full."
        ],
    }
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": str(out), "n_reliability_participants": len(participants), "n_ahba_sets": len(ahba_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
