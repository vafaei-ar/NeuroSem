#!/usr/bin/env python3
"""Orchestrate the frozen post-confirmatory final spatial validation suite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.analysis.nmi_final_validation_shuffled_v1 import shuffled_regional_control
from scripts.analysis.nmi_final_validation_story_spatial_v1 import spatial_surrogate_test, story_robustness
from scripts.analysis.nmi_final_validation_synthesis_v1 import hierarchical_synthesis
from scripts.analysis.nmi_remaining_regional_core_v1 import atomic_progress, write_csv

PROTOCOL = "docs/30_NMI_FINAL_SPATIAL_VALIDATION_V1.md"
OUT = Path("outputs/nmi_final_spatial_validation_v1/latest")
MAIN_REGIONAL = Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest")
REMAINING = Path("outputs/nmi_remaining_regional_ideas_v1/latest")
PREFLIGHT = Path("outputs/smn4lang_regional_atlas_preflight_v1/latest/dk68_parcels.csv")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_figures(loo_rows, spatial_summary, null_beta, shuffled_seed_rows, synthesis_summary) -> None:
    import matplotlib.pyplot as plt

    x = np.arange(len(loo_rows))
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.plot(x, [r["reliability_adjusted_language_mean"] * 1e3 for r in loo_rows], label="Reliability-adjusted language")
    ax.plot(x, [r["temporal_minus_frontal_mean"] * 1e3 for r in loo_rows], label="Temporal - frontal")
    ax.axhline(0, linewidth=0.8)
    ax.set_xlabel("Leave-one-story-out iteration")
    ax.set_ylabel("Effect x 10^-3")
    ax.set_title("Story robustness of spatial effects")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "figure_story_robustness.png", dpi=600)
    fig.savefig(OUT / "figure_story_robustness.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.hist(np.asarray(null_beta) * 1e3, bins=50)
    ax.axvline(spatial_summary["observed_reliability_adjusted_language_beta"] * 1e3, linewidth=1.2)
    ax.set_xlabel("Spatial-null language coefficient x 10^-3")
    ax.set_ylabel("Count")
    ax.set_title("Spatial-autocorrelation-aware null")
    fig.tight_layout()
    fig.savefig(OUT / "figure_spatial_surrogate.png", dpi=600)
    fig.savefig(OUT / "figure_spatial_surrogate.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    sx = np.arange(len(shuffled_seed_rows))
    ax.plot(sx, [r["genuine_specificity_mean"] * 1e3 for r in shuffled_seed_rows], marker="o", label="Genuine guidance")
    ax.plot(sx, [r["shuffled_specificity_mean"] * 1e3 for r in shuffled_seed_rows], marker="o", label="Shuffled guidance")
    ax.axhline(0, linewidth=0.8)
    ax.set_xticks(sx, [str(r["seed"])[-2:] for r in shuffled_seed_rows])
    ax.set_xlabel("Prespecified seed")
    ax.set_ylabel("Language specificity x 10^-3")
    ax.set_title("Regional shuffled-target control")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "figure_shuffled_regional_control.png", dpi=600)
    fig.savefig(OUT / "figure_shuffled_regional_control.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    vals = [
        synthesis_summary["dose_by_system"]["incremental_ols_r2_interaction"],
        synthesis_summary["backbone_by_system"]["incremental_ols_r2_interaction"],
    ]
    ax.bar(np.arange(2), vals)
    ax.set_xticks(np.arange(2), ["Dose x system", "Backbone x system"])
    ax.set_ylabel("Incremental OLS R^2")
    ax.set_title("Multilevel synthesis interaction contribution")
    fig.tight_layout()
    fig.savefig(OUT / "figure_hierarchical_synthesis.png", dpi=600)
    fig.savefig(OUT / "figure_hierarchical_synthesis.pdf")
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    required = [
        MAIN_REGIONAL / "story_results.csv",
        MAIN_REGIONAL / "region_summary.csv",
        REMAINING / "regional_participant_results.csv",
        PREFLIGHT,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("missing frozen inputs: " + ", ".join(missing))

    atomic_progress(0, 12, "story-robustness", "starting final spatial validation suite")
    story_summary, loo_rows = story_robustness()
    write_csv(OUT / "story_leave_one_out.csv", loo_rows)
    atomic_progress(1, 12, "spatial-surrogate", "story robustness complete")

    spatial_summary, null_beta = spatial_surrogate_test()
    write_csv(OUT / "spatial_surrogate_null.csv", [{"surrogate": i, "language_beta": b} for i, b in enumerate(null_beta)])
    atomic_progress(2, 12, "regional-shuffled-control", "spatial surrogate test complete")

    shuffled_summary, shuffled_participant_rows, shuffled_seed_rows = shuffled_regional_control()
    write_csv(OUT / "shuffled_regional_participant_results.csv", shuffled_participant_rows)
    write_csv(OUT / "shuffled_regional_seed_summary.csv", shuffled_seed_rows)
    atomic_progress(11, 12, "hierarchical-synthesis", "regional shuffled-target control complete")

    synthesis_summary, synthesis_coeffs = hierarchical_synthesis()
    write_csv(OUT / "hierarchical_synthesis_coefficients.csv", synthesis_coeffs)
    make_figures(loo_rows, spatial_summary, null_beta, shuffled_seed_rows, synthesis_summary)

    summary = {
        "schema_version": 1,
        "analysis": "NeuroSem frozen final spatial validation suite",
        "protocol": PROTOCOL,
        "status": "ok",
        "post_confirmatory": True,
        "story_robustness": story_summary,
        "spatial_autocorrelation_null": spatial_summary,
        "regional_shuffled_target_control": shuffled_summary,
        "hierarchical_synthesis": synthesis_summary,
        "input_sha256": {str(p): sha256(p) for p in required},
        "guardrails": {
            "definitions_frozen_before_execution": True,
            "no_new_model_training": True,
            "no_new_roi_selection": True,
            "no_new_dose_or_backbone_selection": True,
            "story_analysis_uses_all_60_stories": True,
            "spatial_null_uses_all_34_left_dk_parcels": True,
            "shuffled_control_uses_all_three_prespecified_reviewer_seeds": True,
            "synthesis_uses_all_five_nonzero_doses_and_all_six_backbones": True,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = [
        "NeuroSem final spatial validation suite v1",
        "Status: ok",
        "Post-confirmatory: yes",
        "",
        f"Story bootstrap reliability-adjusted language CI: [{story_summary['reliability_adjusted_language']['twofactor_bootstrap_ci_low']:.12g}, {story_summary['reliability_adjusted_language']['twofactor_bootstrap_ci_high']:.12g}]",
        f"Story bootstrap temporal-minus-frontal CI: [{story_summary['temporal_minus_frontal']['twofactor_bootstrap_ci_low']:.12g}, {story_summary['temporal_minus_frontal']['twofactor_bootstrap_ci_high']:.12g}]",
        f"Spatial surrogate P: {spatial_summary['two_sided_spatial_surrogate_p']:.12g}",
        f"Genuine-minus-shuffled specificity: {shuffled_summary['primary_genuine_minus_shuffled_language_specificity']['mean']:.12g}; FWER P={shuffled_summary['primary_genuine_minus_shuffled_language_specificity']['two_test_familywise_maxstat_p']:.12g}",
        f"Shuffled-minus-text specificity: {shuffled_summary['secondary_shuffled_minus_text_language_specificity']['mean']:.12g}; FWER P={shuffled_summary['secondary_shuffled_minus_text_language_specificity']['two_test_familywise_maxstat_p']:.12g}",
        f"Dose x system synthesis Wald P: {synthesis_summary['dose_by_system']['interaction_wald_p']:.12g}; Holm P={synthesis_summary['dose_by_system']['two_model_holm_p']:.12g}",
        f"Backbone x system synthesis Wald P: {synthesis_summary['backbone_by_system']['interaction_wald_p']:.12g}; Holm P={synthesis_summary['backbone_by_system']['two_model_holm_p']:.12g}",
    ]
    (OUT / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    atomic_progress(12, 12, "complete", "final spatial validation suite complete")
    print(json.dumps({"status": "ok", "output": str(OUT / "summary.json")}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
