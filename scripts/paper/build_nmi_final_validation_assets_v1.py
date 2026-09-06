#!/usr/bin/env python3
"""Build publication-ready NeuroSem final-validation figures and tables.

Presentation only. This script consumes already-completed frozen post-confirmatory
outputs. It performs no model training, neural re-analysis, ROI selection,
hypothesis search, or new inferential testing. Derived participant averages used
for plotting are deterministic presentation transforms of frozen CSV outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts" / "paper" / "nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

OUT = ROOT / "outputs" / "nmi_final_validation_assets_v1" / "latest"
FIG_OUT = OUT / "figures"
TABLE_OUT = OUT / "tables"

LANG_SPEC_SUM = ROOT / "outputs/smn4lang_fmri_language_specificity_v1/latest/summary.json"
LANG_SPEC_PART = ROOT / "outputs/smn4lang_fmri_language_specificity_v1/latest/participant_contrasts.csv"
SPATIAL_SUM = ROOT / "outputs/smn4lang_fmri_spatial_extensions_v1/latest/summary.json"
SPATIAL_PART = ROOT / "outputs/smn4lang_fmri_spatial_extensions_v1/latest/participant_spatial_extensions.csv"
FINAL_SUM = ROOT / "outputs/nmi_final_spatial_validation_v1/latest/summary.json"
STORY_LOO = ROOT / "outputs/nmi_final_spatial_validation_v1/latest/story_leave_one_out.csv"
SPATIAL_NULL = ROOT / "outputs/nmi_final_spatial_validation_v1/latest/spatial_surrogate_null.csv"
SHUFFLED_PART = ROOT / "outputs/nmi_final_spatial_validation_v1/latest/shuffled_regional_participant_results.csv"
DOSE_SUM = ROOT / "outputs/nmi_remaining_regional_ideas_v1/latest/dose_system_summary.csv"
MODEL_SUM = ROOT / "outputs/nmi_remaining_regional_ideas_v1/latest/model_backbone_enrichment_summary.csv"

INPUTS = [
    LANG_SPEC_SUM, LANG_SPEC_PART, SPATIAL_SUM, SPATIAL_PART, FINAL_SUM,
    STORY_LOO, SPATIAL_NULL, SHUFFLED_PART, DOSE_SUM, MODEL_SUM,
]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_p(p: float) -> str:
    p = float(p)
    if p < 1e-4:
        return f"{p:.2e}"
    if p < 0.01:
        return f"{p:.4f}"
    return f"{p:.3f}"


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    FIG_OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        p = FIG_OUT / f"{stem}.{ext}"
        fig.savefig(p, **kwargs)
        paths.append(p)
    plt.close(fig)
    return paths


def mean_bar(ax, x: float, y: float, color: str, width: float = 0.24) -> None:
    ax.plot([x - width / 2, x + width / 2], [y, y], color=color, lw=2.0, zorder=5)


def figure5() -> list[Path]:
    lang_sum = read_json(LANG_SPEC_SUM)
    lang_rows = read_csv(LANG_SPEC_PART)
    spatial_rows = read_csv(SPATIAL_PART)
    final = read_json(FINAL_SUM)
    null_rows = read_csv(SPATIAL_NULL)
    shuffled_rows = read_csv(SHUFFLED_PART)

    subjects = [r["subject"] for r in lang_rows]
    if len(subjects) != 12 or len(set(subjects)) != 12:
        raise RuntimeError("Figure 5 expects 12 unique SMN4Lang participants")

    # Panel a: broad positive shift with larger language-system magnitude.
    system_keys = [
        ("functional_language_mean_delta", "Language", S.BLUE, "o"),
        ("left_sensorimotor_mean_delta", "Sensorimotor", S.GREY, "s"),
        ("left_visual_mean_delta", "Visual", S.ORANGE, "^"),
    ]
    system_matrix = np.asarray(
        [[float(r[key]) for key, _label, _color, _marker in system_keys] for r in lang_rows],
        dtype=float,
    ) * 1e4

    # Panel b: the two strongest spatial effects from the frozen extension family.
    beta = np.asarray(
        [float(r["full_cortex_reliability_adjusted_language_coefficient"]) for r in spatial_rows],
        dtype=float,
    ) * 1e4
    tf = np.asarray(
        [float(r["functional_temporal_minus_frontal_language"]) for r in spatial_rows],
        dtype=float,
    ) * 1e4
    final_story = final["story_robustness"]
    beta_ci = np.asarray([
        final_story["reliability_adjusted_language"]["twofactor_bootstrap_ci_low"],
        final_story["reliability_adjusted_language"]["twofactor_bootstrap_ci_high"],
    ]) * 1e4
    tf_ci = np.asarray([
        final_story["temporal_minus_frontal"]["twofactor_bootstrap_ci_low"],
        final_story["temporal_minus_frontal"]["twofactor_bootstrap_ci_high"],
    ]) * 1e4

    # Panel c: frozen spatial-autocorrelation-aware surrogate null.
    null_beta = np.asarray([float(r["language_beta"]) for r in null_rows], dtype=float) * 1e4
    spatial_null = final["spatial_autocorrelation_null"]
    observed_beta = float(spatial_null["observed_reliability_adjusted_language_beta"]) * 1e4

    # Panel d: average genuine and shuffled specificity across the three fixed seeds per participant.
    by_subject: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in shuffled_rows:
        by_subject[r["subject"]]["genuine"].append(float(r["genuine_specificity"]))
        by_subject[r["subject"]]["shuffled"].append(float(r["shuffled_specificity"]))
    if set(by_subject) != set(subjects):
        raise RuntimeError("shuffled regional control participant set differs from primary participant set")
    genuine = np.asarray([np.mean(by_subject[s]["genuine"]) for s in subjects], dtype=float) * 1e4
    shuffled = np.asarray([np.mean(by_subject[s]["shuffled"]) for s in subjects], dtype=float) * 1e4
    shuf_summary = final["regional_shuffled_target_control"]["primary_genuine_minus_shuffled_language_specificity"]

    S.apply()
    fig = S.figure(S.W2, 116)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.02, 0.98], height_ratios=[1.0, 1.0])
    axa = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, 0])
    axd = fig.add_subplot(gs[1, 1])

    # a
    x = np.arange(3, dtype=float)
    for row in system_matrix:
        axa.plot(x, row, color=S.GREY_XL, lw=0.65, zorder=1)
    for j, (_key, label, color, marker) in enumerate(system_keys):
        axa.scatter(np.full(len(subjects), j), system_matrix[:, j], s=15, marker=marker,
                    facecolor=color, edgecolor="white", linewidth=0.35, zorder=3, label=label)
        mean_bar(axa, float(j), float(np.mean(system_matrix[:, j])), color)
    axa.set_xticks(x)
    axa.set_xticklabels([x[1] for x in system_keys])
    axa.set_ylabel(r"Transfer $\Delta$RSA ($\times 10^{4}$)")
    axa.set_title("Broad cortical transfer with language-system enrichment")
    axa.set_ylim(bottom=0)
    axa.tick_params(axis="x", length=0)
    p_sm = lang_sum["primary"]["functional_language_minus_left_sensorimotor"]["familywise_maxstat_p"]
    p_vis = lang_sum["primary"]["functional_language_minus_left_visual"]["familywise_maxstat_p"]
    S.annotate(axa, f"language - sensorimotor: FWER P={fmt_p(p_sm)}\nlanguage - visual: FWER P={fmt_p(p_vis)}", "upper right")

    # b
    effects = [(beta, beta_ci, "Reliability-adjusted\nlanguage", S.BLUE),
               (tf, tf_ci, "Temporal - frontal\nlanguage", S.ORANGE)]
    jitter = np.linspace(-0.075, 0.075, len(subjects))
    for j, (vals, ci, label, color) in enumerate(effects):
        axb.scatter(j + jitter, vals, s=13, facecolor=S.GREY_L, edgecolor="white", linewidth=0.3, zorder=2)
        m = float(np.mean(vals))
        yerr = np.asarray([[m - ci[0]], [ci[1] - m]])
        axb.errorbar(j, m, yerr=yerr, fmt="o", color=color, ecolor=color,
                     elinewidth=1.1, capsize=2.2, markersize=4.2, zorder=4)
    S.zeroline(axb)
    axb.set_xticks([0, 1])
    axb.set_xticklabels([e[2] for e in effects])
    axb.set_ylabel(r"Spatial effect ($\Delta$RSA $\times 10^{4}$)")
    axb.set_title("Spatial enrichment is reliable and temporally weighted")
    axb.tick_params(axis="x", length=0)
    spatial_focal = read_json(SPATIAL_SUM)["focal_tests"]
    p_beta = spatial_focal["full_cortex_reliability_adjusted_language_coefficient"]["familywise_maxstat_p"]
    p_tf = spatial_focal["functional_temporal_minus_frontal_language"]["familywise_maxstat_p"]
    S.annotate(axb, f"five-test FWER P={fmt_p(p_beta)}\nFWER P={fmt_p(p_tf)}", "upper right")

    # c
    axc.hist(null_beta, bins=42, color=S.GREY_XL, edgecolor="white", linewidth=0.25)
    axc.axvline(observed_beta, color=S.BLUE, lw=1.5, zorder=4)
    axc.axvline(0, color=S.ZERO, lw=0.6, zorder=2)
    axc.set_xlabel(r"Reliability-adjusted language coefficient ($\Delta$RSA $\times 10^{4}$)")
    axc.set_ylabel("Spatial surrogates")
    axc.set_title("Language enrichment exceeds a spatially autocorrelated null")
    S.annotate(axc, f"10,000 surrogates\nP={fmt_p(spatial_null['two_sided_spatial_surrogate_p'])}", "upper right")

    # d
    for i in range(len(subjects)):
        axd.plot([0, 1], [genuine[i], shuffled[i]], color=S.GREY_XL, lw=0.7, zorder=1)
    axd.scatter(np.zeros(len(subjects)), genuine, s=16, marker="o", facecolor=S.BLUE,
                edgecolor="white", linewidth=0.35, zorder=3)
    axd.scatter(np.ones(len(subjects)), shuffled, s=16, marker="s", facecolor=S.GREY,
                edgecolor="white", linewidth=0.35, zorder=3)
    mean_bar(axd, 0, float(np.mean(genuine)), S.BLUE)
    mean_bar(axd, 1, float(np.mean(shuffled)), S.GREY)
    S.zeroline(axd)
    axd.set_xticks([0, 1])
    axd.set_xticklabels(["Genuine neural\nguidance", "Shuffled neural\nguidance"])
    axd.set_ylabel(r"Language specificity ($\Delta$RSA $\times 10^{4}$)")
    axd.set_title("Regional specificity depends on the genuine neural target")
    axd.tick_params(axis="x", length=0)
    S.annotate(axd, f"genuine - shuffled\nFWER P={fmt_p(shuf_summary['two_test_familywise_maxstat_p'])}", "upper right")

    for ax, letter in ((axa, "a"), (axb, "b"), (axc, "c"), (axd, "d")):
        S.panel(ax, letter, dx=-0.16, dy=1.10)

    return save_figure(fig, "figure5_spatial_validation")


def extended_data_figure2() -> list[Path]:
    final = read_json(FINAL_SUM)
    story_rows = read_csv(STORY_LOO)
    dose_rows = read_csv(DOSE_SUM)
    model_rows = read_csv(MODEL_SUM)

    story = np.asarray([int(r["story_omitted"]) for r in story_rows], dtype=int)
    beta = np.asarray([float(r["reliability_adjusted_language_mean"]) for r in story_rows]) * 1e4
    tf = np.asarray([float(r["temporal_minus_frontal_mean"]) for r in story_rows]) * 1e4
    full_beta = float(final["story_robustness"]["reliability_adjusted_language"]["participant_mean"]) * 1e4
    full_tf = float(final["story_robustness"]["temporal_minus_frontal"]["participant_mean"]) * 1e4

    doses = np.asarray([float(r["lambda"]) for r in dose_rows], dtype=float)
    dose_series = [
        ("language_mean_delta", "Language", S.BLUE, "o"),
        ("sensorimotor_mean_delta", "Sensorimotor", S.GREY, "s"),
        ("visual_mean_delta", "Visual", S.ORANGE, "^"),
    ]

    model_order = ["e5_large", "e5_base", "multilingual_mpnet", "multilingual_minilm", "xlmr_base", "mbert"]
    model_label = {
        "e5_large": "E5-large", "e5_base": "E5-base", "multilingual_mpnet": "mMPNet",
        "multilingual_minilm": "mMiniLM", "xlmr_base": "XLM-R", "mbert": "mBERT",
    }
    by_model = {r["model_key"]: r for r in model_rows}
    if set(model_order) - set(by_model):
        raise RuntimeError("missing model rows for Extended Data Figure 2")

    S.apply()
    fig = S.figure(S.W2, 112)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[0.92, 1.08])
    axa = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, 0])
    axd = fig.add_subplot(gs[1, 1])

    # a, b: leave-one-story-out stability.
    axa.plot(story, beta, color=S.BLUE, lw=0.8, marker="o", markersize=2.1)
    axa.axhline(full_beta, color=S.INK, lw=0.7, ls="--")
    S.zeroline(axa)
    axa.set_xlabel("Story omitted")
    axa.set_ylabel(r"Reliability-adjusted language ($\times 10^{4}$)")
    axa.set_title("Language enrichment is stable across stories")
    axa.set_xticks([1, 10, 20, 30, 40, 50, 60])
    S.annotate(axa, "60/60 leave-one-story-out\nestimates > 0", "lower right")

    axb.plot(story, tf, color=S.ORANGE, lw=0.8, marker="o", markersize=2.1)
    axb.axhline(full_tf, color=S.INK, lw=0.7, ls="--")
    S.zeroline(axb)
    axb.set_xlabel("Story omitted")
    axb.set_ylabel(r"Temporal - frontal ($\Delta$RSA $\times 10^{4}$)")
    axb.set_title("Temporal weighting is stable across stories")
    axb.set_xticks([1, 10, 20, 30, 40, 50, 60])
    S.annotate(axb, "60/60 leave-one-story-out\nestimates > 0", "lower right")

    # c: dose x system boundary condition.
    for key, label, color, marker in dose_series:
        vals = np.asarray([float(r[key]) for r in dose_rows], dtype=float) * 1e3
        axc.plot(doses, vals, color=color, marker=marker, markersize=3.2, lw=1.0, label=label)
    axc.set_xscale("log")
    axc.set_xticks(doses)
    axc.set_xticklabels(["0.01", "0.03", "0.10", "0.30", "1.0"])
    S.zeroline(axc)
    axc.set_xlabel(r"Neural-loss dose $\lambda$")
    axc.set_ylabel(r"Transfer $\Delta$RSA ($\times 10^{3}$)")
    axc.set_title("Dose changes the cortical distribution of transfer")
    axc.legend(loc="upper left", ncol=1)
    dose_p = final["hierarchical_synthesis"]["dose_by_system"]["two_model_holm_p"]
    S.annotate(axc, f"dose x system\nHolm P={fmt_p(dose_p)}", "lower left")

    # d: backbone-specific language enrichment with participant bootstrap CIs.
    y = np.arange(len(model_order))[::-1]
    for yi, key in zip(y, model_order):
        r = by_model[key]
        mean = float(r["mean_language_specificity_across_seeds"]) * 1e4
        lo = float(r["participant_avg_specificity_ci_low"]) * 1e4
        hi = float(r["participant_avg_specificity_ci_high"]) * 1e4
        cls = r["model_class"]
        if cls == "generic multilingual MLM encoder":
            color, marker = S.ORANGE, "s"
        elif cls == "E5 retrieval/sentence embedding":
            color, marker = S.BLUE, "o"
        else:
            color, marker = S.TEAL, "o"
        axd.plot([lo, hi], [yi, yi], color=color, lw=1.2)
        axd.scatter([mean], [yi], s=20, marker=marker, facecolor=color, edgecolor="white", linewidth=0.35, zorder=3)
    axd.axvline(0, color=S.ZERO, lw=0.6)
    axd.set_yticks(y)
    axd.set_yticklabels([model_label[k] for k in model_order])
    axd.set_xlabel(r"Language specificity ($\Delta$RSA $\times 10^{4}$)")
    axd.set_title("Architecture strongly shapes spatial specificity")
    model_p = final["hierarchical_synthesis"]["backbone_by_system"]["two_model_holm_p"]
    S.annotate(axd, f"backbone x system\nHolm P={fmt_p(model_p)}", "lower right")

    for ax, letter in ((axa, "a"), (axb, "b"), (axc, "c"), (axd, "d")):
        S.panel(ax, letter, dx=-0.16, dy=1.10)

    return save_figure(fig, "extended_data_figure2_robustness_boundary_conditions")


def build_tables() -> list[Path]:
    spatial = read_json(SPATIAL_SUM)
    final = read_json(FINAL_SUM)
    focal = spatial["focal_tests"]
    story = final["story_robustness"]
    shuf = final["regional_shuffled_target_control"]
    spatial_null = final["spatial_autocorrelation_null"]

    table12 = [
        {
            "Analysis": "Full-cortex reliability-adjusted language coefficient",
            "Estimate": focal["full_cortex_reliability_adjusted_language_coefficient"]["mean"],
            "Positive_participants": focal["full_cortex_reliability_adjusted_language_coefficient"]["n_positive"],
            "N_participants": 12,
            "CI_type": "participant x story bootstrap 95% CI",
            "CI_low": story["reliability_adjusted_language"]["twofactor_bootstrap_ci_low"],
            "CI_high": story["reliability_adjusted_language"]["twofactor_bootstrap_ci_high"],
            "Exact_P": focal["full_cortex_reliability_adjusted_language_coefficient"]["exact_two_sided_signflip_p"],
            "Adjusted_or_spatial_P": focal["full_cortex_reliability_adjusted_language_coefficient"]["familywise_maxstat_p"],
            "Adjustment_or_null": "five-test exact max-stat FWER",
            "Story_LOO_positive": story["reliability_adjusted_language"]["leave_one_story_out_positive"],
            "Story_LOO_total": story["reliability_adjusted_language"]["leave_one_story_out_total"],
            "Status": "post-confirmatory focal",
        },
        {
            "Analysis": "Functional temporal minus frontal language",
            "Estimate": focal["functional_temporal_minus_frontal_language"]["mean"],
            "Positive_participants": focal["functional_temporal_minus_frontal_language"]["n_positive"],
            "N_participants": 12,
            "CI_type": "participant x story bootstrap 95% CI",
            "CI_low": story["temporal_minus_frontal"]["twofactor_bootstrap_ci_low"],
            "CI_high": story["temporal_minus_frontal"]["twofactor_bootstrap_ci_high"],
            "Exact_P": focal["functional_temporal_minus_frontal_language"]["exact_two_sided_signflip_p"],
            "Adjusted_or_spatial_P": focal["functional_temporal_minus_frontal_language"]["familywise_maxstat_p"],
            "Adjustment_or_null": "five-test exact max-stat FWER",
            "Story_LOO_positive": story["temporal_minus_frontal"]["leave_one_story_out_positive"],
            "Story_LOO_total": story["temporal_minus_frontal"]["leave_one_story_out_total"],
            "Status": "post-confirmatory focal",
        },
        {
            "Analysis": "Reliability-adjusted language coefficient versus spatial surrogate null",
            "Estimate": spatial_null["observed_reliability_adjusted_language_beta"],
            "Positive_participants": "",
            "N_participants": 12,
            "CI_type": "",
            "CI_low": "",
            "CI_high": "",
            "Exact_P": "",
            "Adjusted_or_spatial_P": spatial_null["two_sided_spatial_surrogate_p"],
            "Adjustment_or_null": f"{spatial_null['n_surrogates']} centroid-distance variogram-matched spatial surrogates",
            "Story_LOO_positive": "",
            "Story_LOO_total": "",
            "Status": "post-confirmatory spatial-null validation",
        },
        {
            "Analysis": "Genuine minus shuffled neural guidance language specificity",
            "Estimate": shuf["primary_genuine_minus_shuffled_language_specificity"]["mean"],
            "Positive_participants": shuf["primary_genuine_minus_shuffled_language_specificity"]["n_positive"],
            "N_participants": 12,
            "CI_type": "participant bootstrap 95% CI",
            "CI_low": shuf["primary_genuine_minus_shuffled_language_specificity"]["bootstrap_ci_low"],
            "CI_high": shuf["primary_genuine_minus_shuffled_language_specificity"]["bootstrap_ci_high"],
            "Exact_P": shuf["primary_genuine_minus_shuffled_language_specificity"]["exact_two_sided_signflip_p"],
            "Adjusted_or_spatial_P": shuf["primary_genuine_minus_shuffled_language_specificity"]["two_test_familywise_maxstat_p"],
            "Adjustment_or_null": "two-test exact max-stat FWER",
            "Story_LOO_positive": "",
            "Story_LOO_total": "",
            "Status": "post-confirmatory focal control",
        },
        {
            "Analysis": "Shuffled neural guidance minus text-only language specificity",
            "Estimate": shuf["secondary_shuffled_minus_text_language_specificity"]["mean"],
            "Positive_participants": shuf["secondary_shuffled_minus_text_language_specificity"]["n_positive"],
            "N_participants": 12,
            "CI_type": "participant bootstrap 95% CI",
            "CI_low": shuf["secondary_shuffled_minus_text_language_specificity"]["bootstrap_ci_low"],
            "CI_high": shuf["secondary_shuffled_minus_text_language_specificity"]["bootstrap_ci_high"],
            "Exact_P": shuf["secondary_shuffled_minus_text_language_specificity"]["exact_two_sided_signflip_p"],
            "Adjusted_or_spatial_P": shuf["secondary_shuffled_minus_text_language_specificity"]["two_test_familywise_maxstat_p"],
            "Adjustment_or_null": "two-test exact max-stat FWER",
            "Story_LOO_positive": "",
            "Story_LOO_total": "",
            "Status": "post-confirmatory secondary control",
        },
    ]
    p12 = TABLE_OUT / "supplementary_table12_final_spatial_validation.csv"
    write_csv(p12, table12)

    h = final["hierarchical_synthesis"]
    table13 = []
    for label, key in (("Dose x cortical system", "dose_by_system"), ("Backbone x cortical system", "backbone_by_system")):
        r = h[key]
        table13.append({
            "Interaction": label,
            "Rows": r["n_rows"],
            "Participant_clusters": r["n_subject_clusters"],
            "Region_clusters": r["n_region_clusters"],
            "Interaction_df": r["interaction_df"],
            "Wald_chi2": r["interaction_wald_chi2"],
            "Raw_P": r["interaction_wald_p"],
            "Holm_P": r["two_model_holm_p"],
            "Incremental_OLS_R2": r["incremental_ols_r2_interaction"],
            "Inference": r["inference"],
            "Model_seed_handling": h["model_seed_handling"] if key == "backbone_by_system" else "not applicable",
            "Status": h["status"],
        })
    p13 = TABLE_OUT / "supplementary_table13_system_interactions.csv"
    write_csv(p13, table13)
    return [p12, p13]


def build_captions() -> list[Path]:
    lang = read_json(LANG_SPEC_SUM)
    spatial = read_json(SPATIAL_SUM)
    final = read_json(FINAL_SUM)

    f5 = (
        "Figure 5 | Spatial organization and neural-target specificity of fMRI transfer. "
        "a, Participant-level transfer at lambda=0.10 in the six predefined functional language parcels and fixed left-hemisphere sensorimotor and visual controls (n=12 participants); thin lines connect participant-specific system means and thick horizontal bars show participant means. "
        f"The two primary language-control contrasts used exact max-statistic familywise correction (sensorimotor FWER P={fmt_p(lang['primary']['functional_language_minus_left_sensorimotor']['familywise_maxstat_p'])}; visual FWER P={fmt_p(lang['primary']['functional_language_minus_left_visual']['familywise_maxstat_p'])}). "
        "b, Participant-level full-cortex reliability-adjusted language coefficient and functional temporal-minus-frontal language contrast. Large points and whiskers show the mean and participant x story bootstrap 95% CI; small points show participants. "
        "c, Null distribution from 10,000 centroid-distance variogram-matched spatial surrogates; the vertical line marks the observed reliability-adjusted language coefficient. "
        "d, Participant-level language specificity under genuine and shuffled neural guidance, each averaged across three prespecified optimization seeds; lines connect participants. The displayed control P value is from the frozen two-test exact max-statistic family. All analyses are post-confirmatory."
    )
    ed2 = (
        "Extended Data Figure 2 | Stimulus robustness and boundary conditions of spatial transfer. "
        "a,b, Leave-one-story-out estimates after omitting each of the 60 SMN4Lang stories for the reliability-adjusted language coefficient (a) and functional temporal-minus-frontal language contrast (b). Dashed horizontal lines show the estimate using all 60 stories; all 60 leave-one-story-out estimates were positive for both effects. "
        "c, Mean participant-level transfer across functional language, left sensorimotor and left visual systems over the five frozen nonzero neural-loss doses. The omnibus dose x system test used participant and region two-way clustered covariance and was Holm-corrected across the two synthesis models. "
        "d, Mean language specificity across three prespecified seeds for six multilingual backbones; whiskers show participant bootstrap 95% CIs. The omnibus backbone x system test used the same two-way clustered synthesis and Holm correction. All analyses are post-confirmatory."
    )
    FIG_OUT.mkdir(parents=True, exist_ok=True)
    p1 = FIG_OUT / "figure5_caption.txt"
    p2 = FIG_OUT / "extended_data_figure2_caption.txt"
    p1.write_text(f5 + "\n", encoding="utf-8")
    p2.write_text(ed2 + "\n", encoding="utf-8")
    return [p1, p2]


def main() -> int:
    missing = [str(p) for p in INPUTS if not p.exists()]
    if missing:
        raise FileNotFoundError("missing frozen inputs: " + ", ".join(missing))

    FIG_OUT.mkdir(parents=True, exist_ok=True)
    TABLE_OUT.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    outputs.extend(figure5())
    outputs.extend(extended_data_figure2())
    outputs.extend(build_tables())
    outputs.extend(build_captions())

    # Mechanical presentation checks that do not alter scientific content.
    for p in outputs:
        if not p.exists() or p.stat().st_size == 0:
            raise RuntimeError(f"empty output: {p}")
    for png in [p for p in outputs if p.suffix == ".png"]:
        from PIL import Image
        with Image.open(png) as im:
            if im.width < 3000 or im.height < 1500:
                raise RuntimeError(f"unexpectedly small 600-dpi figure raster: {png} {im.size}")

    S.apply()
    manifest = {
        "schema_version": 1,
        "analysis": "NeuroSem NMI v1.16 final-validation presentation assets",
        "status": "ok",
        "presentation_only": True,
        "visual_thesis": "Cortex-wide transfer is spatially structured, robust across stories, dependent on genuine neural supervision, and modulated by dose and architecture.",
        "design": {
            "main_figure": "four-panel evidence sequence: system-level phenotype -> reliability/within-language effects -> spatial null -> shuffled-target control",
            "extended_data_figure": "robustness and boundary-condition sequence: two story leave-one-out panels -> dose-by-system -> backbone specificity",
            "main_width_mm": S.W2,
            "main_height_mm": 116,
            "extended_width_mm": S.W2,
            "extended_height_mm": 112,
            "font_family_first_choice": plt.rcParams["font.sans-serif"][0],
            "pdf_fonttype": plt.rcParams["pdf.fonttype"],
            "svg_fonttype": plt.rcParams["svg.fonttype"],
            "png_dpi": 600,
        },
        "guardrails": [
            "All quantitative panels and tables are generated from already-completed frozen derived outputs.",
            "No new inferential test, model fit, neural preprocessing, ROI selection, dose search, backbone search or rescue tuning is performed.",
            "Participant and seed averaging used for display is deterministic and does not alter the frozen inference.",
            "The spatial null is labelled as a centroid-distance variogram-matched surrogate analysis, not a surface-sphere spin test.",
            "No generative image assets are used; the figures are reproducible Matplotlib vector/raster exports.",
        ],
        "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in INPUTS},
        "output_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
    }
    manifest_path = OUT / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "figures": ["figure5_spatial_validation", "extended_data_figure2_robustness_boundary_conditions"],
        "tables": ["supplementary_table12_final_spatial_validation", "supplementary_table13_system_interactions"],
        "output": str(OUT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
