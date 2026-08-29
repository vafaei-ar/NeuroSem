#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_v1_module():
    path = Path(__file__).with_name("build_manuscript_figures_v1.py")
    spec = importlib.util.spec_from_file_location("neurosem_manuscript_figures_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load_meg_boundary(outputs: Path) -> tuple[list[dict], dict[str, str]]:
    primary_path = require(outputs / "smn4lang_meg_primary_reliability/latest/summary.json")
    exploratory_path = require(outputs / "smn4lang_meg_exploratory_granularity/latest/summary.json")
    primary = read_json(primary_path)
    exploratory = read_json(exploratory_path)

    if primary.get("gate_pass") is not False:
        raise RuntimeError("expected completed failed primary MEG reliability gate")
    if exploratory.get("passing_candidates") != []:
        raise RuntimeError("expected no passing exploratory MEG candidate")
    if exploratory.get("selected_finest_passing_candidate") is not None:
        raise RuntimeError("unexpected selected exploratory MEG candidate")

    rows: list[dict] = []
    for metric in exploratory["candidate_metrics"]:
        rows.append({
            "n_bins": int(metric["n_bins"]),
            "analysis_status": "post-confirmatory exploratory",
            "mean_loo_spearman": float(metric["mean"]),
            "median_loo_spearman": float(metric["median"]),
            "n_positive": int(metric["n_positive"]),
            "n_subjects": 12,
            "ci_level": 0.95,
            "ci_low": float(metric["bootstrap_95_ci_low"]),
            "ci_high": float(metric["bootstrap_95_ci_high"]),
            "exact_one_sided_signflip_p": float(metric["exact_one_sided_signflip_p"]),
            "familywise_pass": bool(metric["familywise_reliability_pass"]),
            "model_evaluated": False,
        })

    rel = primary["reliability"]
    rows.append({
        "n_bins": 32,
        "analysis_status": "prospectively frozen primary",
        "mean_loo_spearman": float(rel["mean"]),
        "median_loo_spearman": float(rel["median"]),
        "n_positive": int(rel["n_positive"]),
        "n_subjects": 12,
        "ci_level": 0.95,
        "ci_low": float(rel["bootstrap_95_ci"][0]),
        "ci_high": float(rel["bootstrap_95_ci"][1]),
        "exact_one_sided_signflip_p": float(rel["exact_one_sided_signflip_p"]),
        "familywise_pass": False,
        "model_evaluated": False,
    })
    rows.sort(key=lambda r: r["n_bins"])
    return rows, {
        "smn4lang_meg_primary_summary": str(primary_path),
        "smn4lang_meg_exploratory_summary": str(exploratory_path),
    }


def figure_meg_boundary(rows: list[dict], out: Path) -> None:
    bins = np.asarray([r["n_bins"] for r in rows], dtype=int)
    means = np.asarray([r["mean_loo_spearman"] for r in rows], dtype=float)
    lows = np.asarray([r["ci_low"] for r in rows], dtype=float)
    highs = np.asarray([r["ci_high"] for r in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    x = np.arange(len(rows))
    yerr = np.vstack([means - lows, highs - means])
    ax.errorbar(x, means, yerr=yerr, fmt="o", capsize=4, linewidth=1.6, markersize=6)
    ax.axhline(0, linewidth=0.9)
    ax.set_xticks(x, [str(v) for v in bins])
    ax.set_xlabel("Normalized-time RMS bins per MEG channel type")
    ax.set_ylabel("Cross-participant story-geometry reliability\n(LOO Spearman rho)")
    ax.set_title("SMN4Lang MEG did not yield a reliable cross-participant target")

    for i, row in enumerate(rows):
        label = "prospective primary" if row["n_bins"] == 32 else "exploratory"
        ax.text(i, highs[i] + 0.0025, f"{row['n_positive']}/12 positive\n{label}", ha="center", va="bottom", fontsize=7.5)

    ax.text(
        0.01,
        0.01,
        "Points: participant-mean LOO reliability; bars: locked 95% participant-bootstrap CIs. "
        "No representation passed its reliability criterion; no model evaluation was performed.",
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        wrap=True,
    )
    margin = max(0.01, float((highs.max() - lows.min()) * 0.15))
    ax.set_ylim(float(min(lows.min(), 0.0) - margin), float(highs.max() + margin * 2.5))
    fig.tight_layout()
    fig.savefig(out / "fig4b_smn4lang_meg_reliability_boundary.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / "fig4b_smn4lang_meg_reliability_boundary.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-root", type=Path, default=Path("outputs"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/manuscript_figures_v2/latest"))
    args = ap.parse_args()

    outputs = args.outputs_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    v1 = load_v1_module()
    participants, rel_summary, rel_sources = v1.load_reliability(outputs)
    ahba_rows, ahba_sources = v1.load_ahba(outputs)
    meg_rows, meg_sources = load_meg_boundary(outputs)

    v1.figure_reliability(participants, rel_summary, out)
    v1.figure_ahba(ahba_rows, out)
    figure_meg_boundary(meg_rows, out)

    write_csv(out / "table2_reliability_summary.csv", rel_summary)
    write_csv(out / "table3_ahba_gene_sets.csv", ahba_rows)
    write_csv(out / "table4_smn4lang_meg_reliability_boundary.csv", meg_rows)

    manifest = {
        "schema_version": 1,
        "analysis": "NeuroSem manuscript figures v2",
        "generated_from_locked_outputs_only": True,
        "figures": [
            "fig2_reading_reliability.png",
            "fig2_reading_reliability.pdf",
            "fig4b_smn4lang_meg_reliability_boundary.png",
            "fig4b_smn4lang_meg_reliability_boundary.pdf",
            "fig4_ahba_frozen_molecular_nulls.png",
            "fig4_ahba_frozen_molecular_nulls.pdf",
        ],
        "tables": [
            "table2_reliability_summary.csv",
            "table3_ahba_gene_sets.csv",
            "table4_smn4lang_meg_reliability_boundary.csv",
        ],
        "sources": {**rel_sources, **meg_sources, **ahba_sources},
        "guardrails": [
            "No model fitting, feature selection, representation search, or hypothesis testing is performed here.",
            "The MEG panel visualizes the already-completed prospective 32-bin reliability result and already-completed frozen post-confirmatory 4/8/16-bin exploratory family.",
            "The failed MEG reliability gate is not represented as a negative model-transfer result because no model evaluation was performed.",
            "AHBA remains a supplementary/Extended Data candidate rather than a required main Figure 4 component.",
        ],
    }
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "output_dir": str(out),
        "n_reliability_participants": len(participants),
        "n_ahba_sets": len(ahba_rows),
        "n_meg_reliability_points": len(meg_rows),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
