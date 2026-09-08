#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LANGSPEC = ROOT / "outputs" / "smn4lang_fmri_language_specificity_v1" / "latest"
SPATIAL = ROOT / "outputs" / "smn4lang_fmri_spatial_extensions_v1" / "latest"
FINAL = ROOT / "outputs" / "nmi_final_spatial_validation_v1" / "latest"
REMAINING = ROOT / "outputs" / "nmi_remaining_regional_ideas_v1" / "latest"
OUT = ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest"

MODEL_LABELS = {
    "e5_large": "E5-large",
    "e5_base": "E5-base",
    "multilingual_mpnet": "mMPNet",
    "multilingual_minilm": "mMiniLM",
    "xlmr_base": "XLM-R",
    "mbert": "mBERT",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    paths: list[Path] = []
    for ext, kwargs in [("pdf", {}), ("svg", {}), ("png", {"dpi": 600})]:
        p = OUT / f"{stem}.{ext}"
        fig.savefig(p, bbox_inches="tight", **kwargs)
        paths.append(p)
    return paths


def fmt_p(p: float) -> str:
    if p < 1e-4:
        return f"{p:.2e}"
    if p < 0.01:
        return f"{p:.4f}"
    return f"{p:.3f}"


def configure_style() -> None:
    plt.rcParams.update({
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def paired_panel(ax: plt.Axes, matrix: np.ndarray, labels: list[str], title: str, ylabel: str) -> None:
    x = np.arange(matrix.shape[1], dtype=float)
    for row in matrix:
        ax.plot(x, row, linewidth=0.55, alpha=0.42)
        ax.scatter(x, row, s=9, alpha=0.68)
    means = np.mean(matrix, axis=0)
    ax.plot(x, means, marker="o", linewidth=1.6, color="black", markersize=4.6, zorder=5)
    ax.axhline(0, linewidth=0.7, color="black")
    ax.set_xticks(x, labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontweight="bold")


def build_main_figure(
    lang_part: pd.DataFrame,
    spatial_part: pd.DataFrame,
    shuffled_part: pd.DataFrame,
    lang_summary: dict,
    spatial_summary: dict,
    final_summary: dict,
    null_df: pd.DataFrame,
) -> tuple[list[Path], Path]:
    fig = plt.figure(figsize=(7.2, 6.5), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)

    ax = fig.add_subplot(gs[0, 0])
    system_matrix = lang_part[[
        "functional_language_mean_delta",
        "left_sensorimotor_mean_delta",
        "left_visual_mean_delta",
    ]].to_numpy(float) * 1e3
    paired_panel(
        ax,
        system_matrix,
        ["Language", "Sensorimotor", "Visual"],
        "a  Broad positive transfer with language enrichment",
        "ΔRSA × 10⁻³",
    )
    p_sm = float(lang_summary["primary"]["functional_language_minus_left_sensorimotor"]["familywise_maxstat_p"])
    p_vis = float(lang_summary["primary"]["functional_language_minus_left_visual"]["familywise_maxstat_p"])
    ax.text(
        0.02, 0.98,
        f"Language − sensorimotor: FWER P={fmt_p(p_sm)}\nLanguage − visual: FWER P={fmt_p(p_vis)}",
        transform=ax.transAxes, ha="left", va="top", fontsize=6.6,
    )

    ax = fig.add_subplot(gs[0, 1])
    tf_matrix = spatial_part[["functional_frontal_mean_delta", "functional_temporal_mean_delta"]].to_numpy(float) * 1e3
    paired_panel(
        ax,
        tf_matrix,
        ["Frontal", "Temporal"],
        "b  Transfer is stronger in temporal language cortex",
        "ΔRSA × 10⁻³",
    )
    tf = spatial_summary["focal_tests"]["functional_temporal_minus_frontal_language"]
    ax.text(
        0.02, 0.98,
        f"Temporal − frontal = {float(tf['mean']) * 1e3:.3f} × 10⁻³\nFWER P={fmt_p(float(tf['familywise_maxstat_p']))}",
        transform=ax.transAxes, ha="left", va="top", fontsize=6.6,
    )

    ax = fig.add_subplot(gs[1, 0])
    null_vals = null_df["language_beta"].to_numpy(float) * 1e3
    spatial_null = final_summary["spatial_autocorrelation_null"]
    observed = float(spatial_null["observed_reliability_adjusted_language_beta"]) * 1e3
    ax.hist(null_vals, bins=55)
    ax.axvline(observed, linewidth=1.5, color="black")
    ax.axvline(-observed, linewidth=0.8, color="black", linestyle="--")
    ax.set_xlabel("Spatial-null language coefficient × 10⁻³")
    ax.set_ylabel("Surrogates")
    ax.set_title("c  Language enrichment exceeds a spatially autocorrelated null", loc="left", fontweight="bold")
    ax.text(
        0.02, 0.98,
        f"Observed = {observed:.3f} × 10⁻³\nSpatial-surrogate P={fmt_p(float(spatial_null['two_sided_spatial_surrogate_p']))}",
        transform=ax.transAxes, ha="left", va="top", fontsize=6.6,
    )

    ax = fig.add_subplot(gs[1, 1])
    avg = shuffled_part.groupby("subject", as_index=False)[["genuine_specificity", "shuffled_specificity"]].mean()
    shuf_matrix = avg[["genuine_specificity", "shuffled_specificity"]].to_numpy(float) * 1e3
    paired_panel(
        ax,
        shuf_matrix,
        ["Genuine", "Shuffled"],
        "d  Regional enrichment depends on genuine neural guidance",
        "Language specificity × 10⁻³",
    )
    shuf = final_summary["regional_shuffled_target_control"]["primary_genuine_minus_shuffled_language_specificity"]
    ax.text(
        0.02, 0.98,
        f"Genuine − shuffled = {float(shuf['mean']) * 1e3:.3f} × 10⁻³\nFWER P={fmt_p(float(shuf['two_test_familywise_maxstat_p']))}",
        transform=ax.transAxes, ha="left", va="top", fontsize=6.6,
    )

    paths = save_figure(fig, "figure5_spatial_validation")
    plt.close(fig)

    caption = (
        "Figure 5 | Spatial validation of fMRI transfer. "
        "a, Participant-level mean neural-guided minus text-only residual RSA (ΔRSA) for the six predefined "
        "functional language parcels and fixed left-hemisphere sensorimotor and visual controls at λ=0.10. "
        "Thin lines connect the same participant; black markers show group means. The two predefined "
        "language-versus-control contrasts use exact max-statistic family-wise correction. "
        "b, Participant-level functional temporal and frontal language-system ΔRSA. Temporal-minus-frontal "
        "was positive in 11/12 participants and survived the frozen five-test spatial-extension family. "
        "c, Null distribution from 10,000 centroid-distance, variogram-matched left-DK spatial surrogates for "
        "the reliability-adjusted language coefficient; the solid line marks the observed coefficient and the "
        "dashed line its negative magnitude. This is a spatial-autocorrelation-aware surrogate test, not a "
        "surface-sphere spin test. d, Participant-level language specificity after averaging the three "
        "prespecified reviewer seeds for genuine and shuffled neural-target guidance. Genuine guidance exceeded "
        "shuffled guidance under the frozen two-test family. All analyses are post-confirmatory."
    )
    caption_path = OUT / "figure5_spatial_validation_caption.txt"
    caption_path.write_text(caption + "\n", encoding="utf-8")
    return paths, caption_path


def build_story_figure(story_df: pd.DataFrame, final_summary: dict) -> tuple[list[Path], Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25), constrained_layout=True)
    x = np.arange(1, len(story_df) + 1)

    specs = [
        (
            axes[0],
            "reliability_adjusted_language_mean",
            final_summary["story_robustness"]["reliability_adjusted_language"],
            "a  Reliability-adjusted language enrichment",
        ),
        (
            axes[1],
            "temporal_minus_frontal_mean",
            final_summary["story_robustness"]["temporal_minus_frontal"],
            "b  Temporal − frontal language transfer",
        ),
    ]
    for ax, col, summary, title in specs:
        y = story_df[col].to_numpy(float) * 1e3
        lo = float(summary["twofactor_bootstrap_ci_low"]) * 1e3
        hi = float(summary["twofactor_bootstrap_ci_high"]) * 1e3
        mean = float(summary["participant_mean"]) * 1e3
        ax.axhspan(lo, hi, alpha=0.12)
        ax.plot(x, y, marker="o", markersize=2.2, linewidth=0.8)
        ax.axhline(mean, linewidth=1.0, color="black")
        ax.axhline(0, linewidth=0.7, color="black")
        ax.set_xlabel("Omitted story")
        ax.set_ylabel("Effect × 10⁻³")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.text(
            0.02, 0.98,
            f"60/60 leave-one-story-out estimates > 0\nParticipant × story 95% CI: [{lo:.3f}, {hi:.3f}] × 10⁻³",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.4,
        )

    paths = save_figure(fig, "extended_data_figure2_story_robustness")
    plt.close(fig)
    caption = (
        "Extended Data Figure 2 | Story-level robustness of the two strongest spatial effects. "
        "a, Reliability-adjusted left-DK language coefficient after omitting each of the 60 stories in turn. "
        "b, Functional temporal-minus-frontal language-system ΔRSA under the same leave-one-story-out analysis. "
        "The black horizontal line is the full-data participant mean and the shaded band is the prespecified "
        "participant-by-story bootstrap 95% confidence interval. All 60 leave-one-story-out estimates were positive "
        "for both effects."
    )
    caption_path = OUT / "extended_data_figure2_story_robustness_caption.txt"
    caption_path.write_text(caption + "\n", encoding="utf-8")
    return paths, caption_path


def build_interaction_figure(dose: pd.DataFrame, backbone: pd.DataFrame, final_summary: dict) -> tuple[list[Path], Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.45), constrained_layout=True)

    ax = axes[0]
    x = np.arange(len(dose), dtype=float)
    for col, label in [
        ("language_mean_delta", "Language"),
        ("sensorimotor_mean_delta", "Sensorimotor"),
        ("visual_mean_delta", "Visual"),
    ]:
        ax.plot(x, dose[col].to_numpy(float) * 1e3, marker="o", linewidth=1.2, label=label)
    ax.axhline(0, linewidth=0.7, color="black")
    ax.set_xticks(x, [f"{v:g}" for v in dose["lambda"].to_numpy(float)])
    ax.set_xlabel("Neural-loss weight λ")
    ax.set_ylabel("Mean ΔRSA × 10⁻³")
    ax.set_title("a  Dose changes the cortical transfer profile", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ds = final_summary["hierarchical_synthesis"]["dose_by_system"]
    ax.text(
        0.02, 0.98,
        f"Dose × system omnibus P={fmt_p(float(ds['interaction_wald_p']))}\nHolm P={fmt_p(float(ds['two_model_holm_p']))}",
        transform=ax.transAxes, ha="left", va="top", fontsize=6.4,
    )

    ax = axes[1]
    b = backbone.copy()
    b["label"] = b["model_key"].map(MODEL_LABELS).fillna(b["model_key"])
    bx = np.arange(len(b), dtype=float)
    y = b["mean_language_specificity_across_seeds"].to_numpy(float) * 1e3
    lo = b["participant_avg_specificity_ci_low"].to_numpy(float) * 1e3
    hi = b["participant_avg_specificity_ci_high"].to_numpy(float) * 1e3
    ax.errorbar(bx, y, yerr=np.vstack([y - lo, hi - y]), fmt="o", capsize=2.5, linewidth=0.9)
    ax.axhline(0, linewidth=0.7, color="black")
    ax.set_xticks(bx, b["label"], rotation=35, ha="right")
    ax.set_ylabel("Language specificity × 10⁻³")
    ax.set_title("b  Architecture strongly shapes cortical specificity", loc="left", fontweight="bold")
    ms = final_summary["hierarchical_synthesis"]["backbone_by_system"]
    ax.text(
        0.02, 0.98,
        f"Backbone × system omnibus P={float(ms['interaction_wald_p']):.2e}\nHolm P={float(ms['two_model_holm_p']):.2e}",
        transform=ax.transAxes, ha="left", va="top", fontsize=6.4,
    )
    for i, row in b.reset_index(drop=True).iterrows():
        if float(row["specificity_fwer_p_across_6_models"]) < 0.05:
            yy = float(row["participant_avg_specificity_ci_high"] if y[i] >= 0 else row["participant_avg_specificity_ci_low"]) * 1e3
            offset = 0.035 if y[i] >= 0 else -0.06
            ax.text(i, yy + offset, "*", ha="center", va="center", fontsize=10)

    paths = save_figure(fig, "extended_data_figure3_system_interactions")
    plt.close(fig)
    caption = (
        "Extended Data Figure 3 | Dose- and architecture-dependent cortical transfer. "
        "a, Mean participant ΔRSA for functional language, left sensorimotor and left visual systems across the "
        "five frozen nonzero E5 neural-loss weights. At λ=1 all three systems reverse sign, with a smaller negative "
        "shift in language cortex. The annotation gives the prespecified dose-by-system omnibus interaction from "
        "the two-way cluster-robust synthesis model. b, Mean language-specificity contrast across the three "
        "prespecified seeds for each backbone; error bars are participant-bootstrap 95% confidence intervals. "
        "The annotation gives the backbone-by-system omnibus interaction. The asterisk marks a backbone whose "
        "model-specific language-specificity test survived the separate six-model max-stat family. Omnibus and "
        "model-specific tests answer different questions."
    )
    caption_path = OUT / "extended_data_figure3_system_interactions_caption.txt"
    caption_path.write_text(caption + "\n", encoding="utf-8")
    return paths, caption_path


def build_tables(
    lang_summary: dict,
    spatial_summary: dict,
    final_summary: dict,
    dose: pd.DataFrame,
    backbone: pd.DataFrame,
) -> list[Path]:
    rows: list[dict] = []

    def add_row(
        family: str,
        contrast: str,
        d: dict,
        correction: str,
        corrected_key: str | None = None,
        story: dict | None = None,
        note: str = "",
    ) -> None:
        rows.append({
            "family": family,
            "contrast": contrast,
            "estimate": d.get("mean", d.get("observed_reliability_adjusted_language_beta", "")),
            "participant_ci_low": d.get("bootstrap_ci_low", ""),
            "participant_ci_high": d.get("bootstrap_ci_high", ""),
            "n_positive": d.get("n_positive", ""),
            "n_total": d.get("n_total", ""),
            "exact_two_sided_p": d.get("exact_two_sided_signflip_p", ""),
            "corrected_or_spatial_p": d.get(corrected_key, "") if corrected_key else "",
            "correction_or_null": correction,
            "story_bootstrap_ci_low": story.get("twofactor_bootstrap_ci_low", "") if story else "",
            "story_bootstrap_ci_high": story.get("twofactor_bootstrap_ci_high", "") if story else "",
            "leave_one_story_out_positive": story.get("leave_one_story_out_positive", "") if story else "",
            "leave_one_story_out_total": story.get("leave_one_story_out_total", "") if story else "",
            "note": note,
        })

    add_row(
        "Primary language vs control",
        "Functional language − left sensorimotor",
        lang_summary["primary"]["functional_language_minus_left_sensorimotor"],
        "Exact max-stat FWER across two primary language-vs-control contrasts",
        "familywise_maxstat_p",
    )
    add_row(
        "Primary language vs control",
        "Functional language − left visual",
        lang_summary["primary"]["functional_language_minus_left_visual"],
        "Exact max-stat FWER across two primary language-vs-control contrasts",
        "familywise_maxstat_p",
    )
    add_row(
        "Sensitivity",
        "DK language-associated − pooled controls, reliability-adjusted",
        lang_summary["sensitivities"]["dk_language_minus_pooled_controls_reliability_adjusted"],
        "Uncorrected exact sign-flip sensitivity",
    )
    add_row(
        "Spatial extension",
        "Full-cortex reliability-adjusted language coefficient",
        spatial_summary["focal_tests"]["full_cortex_reliability_adjusted_language_coefficient"],
        "Exact max-stat FWER across five frozen spatial-extension tests",
        "familywise_maxstat_p",
        final_summary["story_robustness"]["reliability_adjusted_language"],
        "Story-robustness columns come from the final validation suite.",
    )
    add_row(
        "Spatial extension",
        "Functional temporal − frontal language",
        spatial_summary["focal_tests"]["functional_temporal_minus_frontal_language"],
        "Exact max-stat FWER across five frozen spatial-extension tests",
        "familywise_maxstat_p",
        final_summary["story_robustness"]["temporal_minus_frontal"],
        "Story-robustness columns come from the final validation suite.",
    )

    spatial_null = final_summary["spatial_autocorrelation_null"]
    rows.append({
        "family": "Spatial validation",
        "contrast": "Reliability-adjusted language coefficient vs spatial surrogate null",
        "estimate": spatial_null["observed_reliability_adjusted_language_beta"],
        "participant_ci_low": "",
        "participant_ci_high": "",
        "n_positive": "",
        "n_total": "",
        "exact_two_sided_p": "",
        "corrected_or_spatial_p": spatial_null["two_sided_spatial_surrogate_p"],
        "correction_or_null": "10,000 centroid-distance variogram-matched left-DK spatial surrogates",
        "story_bootstrap_ci_low": "",
        "story_bootstrap_ci_high": "",
        "leave_one_story_out_positive": "",
        "leave_one_story_out_total": "",
        "note": "Not a surface-sphere spin test.",
    })

    control = final_summary["regional_shuffled_target_control"]
    add_row(
        "Neural-target specificity",
        "Genuine − shuffled language specificity",
        control["primary_genuine_minus_shuffled_language_specificity"],
        "Exact max-stat FWER across two frozen regional shuffled-control tests",
        "two_test_familywise_maxstat_p",
    )
    add_row(
        "Neural-target specificity",
        "Shuffled − text language specificity",
        control["secondary_shuffled_minus_text_language_specificity"],
        "Exact max-stat FWER across two frozen regional shuffled-control tests",
        "two_test_familywise_maxstat_p",
    )

    table12 = OUT / "supplementary_table12_spatial_validation.csv"
    pd.DataFrame(rows).to_csv(table12, index=False)

    ds = final_summary["hierarchical_synthesis"]["dose_by_system"]
    dose_out = dose.copy()
    dose_out.insert(0, "omnibus_test", "dose × cortical system")
    dose_out.insert(1, "omnibus_wald_chi2", ds["interaction_wald_chi2"])
    dose_out.insert(2, "omnibus_df", ds["interaction_df"])
    dose_out.insert(3, "omnibus_p", ds["interaction_wald_p"])
    dose_out.insert(4, "omnibus_holm_p", ds["two_model_holm_p"])
    dose_out.insert(5, "incremental_ols_r2_interaction", ds["incremental_ols_r2_interaction"])
    table13 = OUT / "supplementary_table13_dose_by_system.csv"
    dose_out.to_csv(table13, index=False)

    ms = final_summary["hierarchical_synthesis"]["backbone_by_system"]
    backbone_out = backbone.copy()
    backbone_out.insert(0, "omnibus_test", "backbone × cortical system")
    backbone_out.insert(1, "omnibus_wald_chi2", ms["interaction_wald_chi2"])
    backbone_out.insert(2, "omnibus_df", ms["interaction_df"])
    backbone_out.insert(3, "omnibus_p", ms["interaction_wald_p"])
    backbone_out.insert(4, "omnibus_holm_p", ms["two_model_holm_p"])
    backbone_out.insert(5, "incremental_ols_r2_interaction", ms["incremental_ols_r2_interaction"])
    backbone_out.insert(6, "display_label", backbone_out["model_key"].map(MODEL_LABELS).fillna(backbone_out["model_key"]))
    table14 = OUT / "supplementary_table14_backbone_by_system.csv"
    backbone_out.to_csv(table14, index=False)

    return [table12, table13, table14]


def main() -> int:
    required = [
        LANGSPEC / "summary.json",
        LANGSPEC / "participant_contrasts.csv",
        SPATIAL / "summary.json",
        SPATIAL / "participant_spatial_extensions.csv",
        FINAL / "summary.json",
        FINAL / "story_leave_one_out.csv",
        FINAL / "spatial_surrogate_null.csv",
        FINAL / "shuffled_regional_participant_results.csv",
        REMAINING / "summary.json",
        REMAINING / "dose_system_summary.csv",
        REMAINING / "model_backbone_enrichment_summary.csv",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing completed frozen source outputs: " + ", ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    configure_style()

    lang_summary = json.loads((LANGSPEC / "summary.json").read_text(encoding="utf-8"))
    spatial_summary = json.loads((SPATIAL / "summary.json").read_text(encoding="utf-8"))
    final_summary = json.loads((FINAL / "summary.json").read_text(encoding="utf-8"))
    remaining_summary = json.loads((REMAINING / "summary.json").read_text(encoding="utf-8"))

    if not all(x.get("status") == "ok" for x in [lang_summary, spatial_summary, final_summary, remaining_summary]):
        raise RuntimeError("One or more frozen source analyses are not status=ok")

    lang_part = pd.read_csv(LANGSPEC / "participant_contrasts.csv")
    spatial_part = pd.read_csv(SPATIAL / "participant_spatial_extensions.csv")
    story_df = pd.read_csv(FINAL / "story_leave_one_out.csv")
    null_df = pd.read_csv(FINAL / "spatial_surrogate_null.csv")
    shuffled_part = pd.read_csv(FINAL / "shuffled_regional_participant_results.csv")
    dose = pd.read_csv(REMAINING / "dose_system_summary.csv")
    backbone = pd.read_csv(REMAINING / "model_backbone_enrichment_summary.csv")

    if len(lang_part) != 12 or len(spatial_part) != 12:
        raise RuntimeError("Expected 12 SMN4Lang participants in publication source tables")
    if len(story_df) != 60:
        raise RuntimeError("Expected 60 leave-one-story-out rows")
    if len(null_df) != 10000:
        raise RuntimeError("Expected 10,000 spatial-surrogate rows")
    if len(dose) != 5 or len(backbone) != 6:
        raise RuntimeError("Unexpected dose or backbone family size")

    outputs: list[Path] = []
    p, c = build_main_figure(lang_part, spatial_part, shuffled_part, lang_summary, spatial_summary, final_summary, null_df)
    outputs.extend(p + [c])
    p, c = build_story_figure(story_df, final_summary)
    outputs.extend(p + [c])
    p, c = build_interaction_figure(dose, backbone, final_summary)
    outputs.extend(p + [c])
    outputs.extend(build_tables(lang_summary, spatial_summary, final_summary, dose, backbone))

    asset_index = {
        "schema_version": 1,
        "recommended_placement": {
            "figure5_spatial_validation": "Main text, after the regional fMRI specificity Results paragraph",
            "extended_data_figure2_story_robustness": "Extended Data",
            "extended_data_figure3_system_interactions": "Extended Data",
            "supplementary_table12_spatial_validation": "Supplementary Information",
            "supplementary_table13_dose_by_system": "Supplementary Information",
            "supplementary_table14_backbone_by_system": "Supplementary Information",
        },
        "numbering_assumption": "Assumes the current v1.15 Supplement ends at Supplementary Table 11 and Extended Data Figure 1.",
        "presentation_policy": "No new inferential tests are performed by this builder; plotted and tabulated inferential statistics are copied from completed frozen analyses.",
    }
    asset_index_path = OUT / "asset_index.json"
    asset_index_path.write_text(json.dumps(asset_index, indent=2) + "\n", encoding="utf-8")
    outputs.append(asset_index_path)

    manifest = {
        "schema_version": 1,
        "analysis": "NeuroSem NMI spatial-validation publication assets v1",
        "purpose": "reproducible manuscript/Extended Data figures and supplementary tables from completed frozen post-confirmatory analyses",
        "source_protocols": [
            lang_summary.get("protocol"),
            spatial_summary.get("protocol"),
            final_summary.get("protocol"),
            remaining_summary.get("protocol"),
        ],
        "builder": str(Path(__file__).resolve().relative_to(ROOT)),
        "builder_sha256": sha256(Path(__file__).resolve()),
        "source_files": {str(p.relative_to(ROOT)): sha256(p) for p in required},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "guardrails": {
            "presentation_only": True,
            "no_new_model_training": True,
            "no_new_model_evaluation": True,
            "no_new_neural_analysis": True,
            "no_new_hypothesis_testing": True,
            "no_roi_dose_backbone_or_story_selection": True,
            "uses_all_60_leave_one_story_out_rows": True,
            "uses_all_10000_spatial_surrogates": True,
            "uses_all_three_prespecified_shuffled_control_seeds": True,
            "uses_all_five_nonzero_doses": True,
            "uses_all_six_backbones": True,
        },
    }
    manifest_path = OUT / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "output_dir": str(OUT),
        "figures": 3,
        "tables": 3,
        "declared_outputs": len(outputs) + 1,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
