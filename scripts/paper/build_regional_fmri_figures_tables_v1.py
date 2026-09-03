#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "outputs" / "smn4lang_regional_fmri_e5_transfer_v1" / "latest"
OUT_DIR = ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest"

LANGUAGE_ORDER = ["IFGorb", "IFG", "MFG", "AntTemp", "PostTemp", "AngG"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    outputs = []
    for ext, kwargs in [
        ("pdf", {}),
        ("svg", {}),
        ("png", {"dpi": 600}),
    ]:
        path = OUT_DIR / f"{stem}.{ext}"
        fig.savefig(path, bbox_inches="tight", **kwargs)
        outputs.append(path)
    return outputs


def main() -> int:
    summary_path = SOURCE_DIR / "summary.json"
    region_path = SOURCE_DIR / "region_summary.csv"
    twofactor_path = SOURCE_DIR / "language_twofactor_bootstrap.csv"
    dk_matrix_path = SOURCE_DIR / "dk68_participant_delta_matrix.csv"
    required = [summary_path, region_path, twofactor_path, dk_matrix_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing completed Stage-2 source outputs: " + ", ".join(missing))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    regions = pd.read_csv(region_path)
    twofactor = pd.read_csv(twofactor_path)
    dk_matrix = pd.read_csv(dk_matrix_path)

    if summary.get("n_language_regions") != 6 or summary.get("n_dk68_regions") != 68:
        raise RuntimeError("Unexpected regional family size in frozen Stage-2 summary")

    lang = regions.loc[regions["family"] == "language"].copy()
    if set(lang["region_name"]) != set(LANGUAGE_ORDER):
        raise RuntimeError("Language parcel family does not match the frozen six-region set")
    lang["order"] = lang["region_name"].map({name: i for i, name in enumerate(LANGUAGE_ORDER)})
    lang = lang.sort_values("order").reset_index(drop=True)

    tf = twofactor.rename(columns={"ci_low": "twofactor_ci_low", "ci_high": "twofactor_ci_high", "fraction_mean_delta_gt_0": "twofactor_fraction_gt0"})
    lang_table = lang.merge(
        tf[["region_name", "twofactor_ci_low", "twofactor_ci_high", "twofactor_fraction_gt0"]],
        on="region_name",
        how="left",
        validate="one_to_one",
    )
    lang_cols = [
        "region_name", "model_blind_reliability_mean", "lambda_0_mean", "lambda_0p10_mean",
        "delta_mean", "delta_bootstrap_ci_low", "delta_bootstrap_ci_high", "delta_n_positive",
        "delta_exact_two_sided_signflip_p", "language_family_fwer_p",
        "twofactor_ci_low", "twofactor_ci_high", "twofactor_fraction_gt0",
    ]
    language_table_path = OUT_DIR / "table_regional_language_parcels.csv"
    lang_table[lang_cols].to_csv(language_table_path, index=False)

    dk = regions.loc[regions["family"] == "dk68"].copy()
    dk_cols = [
        "parcel_id", "region_name", "hemisphere", "atlas_voxels", "model_blind_reliability_mean",
        "lambda_0_mean", "lambda_0p10_mean", "delta_mean", "delta_median", "delta_n_positive",
        "delta_fraction_positive", "delta_bootstrap_ci_low", "delta_bootstrap_ci_high",
        "delta_exact_two_sided_signflip_p", "interpretation_status",
    ]
    dk_table_path = OUT_DIR / "table_supplementary_dk68_phenotype.csv"
    dk[dk_cols].to_csv(dk_table_path, index=False)

    participant_cols = [c for c in dk_matrix.columns if c.endswith("_delta") and c not in {"participant_mean_delta", "participant_median_delta"}]
    if len(participant_cols) != 12:
        raise RuntimeError(f"Expected 12 participant delta columns, found {len(participant_cols)}")

    plt.rcParams.update({
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    fig = plt.figure(figsize=(7.2, 7.0), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.25, 1.05, 1.45])

    ax1 = fig.add_subplot(gs[0, 0])
    x = np.arange(len(lang))
    y = lang["delta_mean"].to_numpy(float)
    lo = lang["delta_bootstrap_ci_low"].to_numpy(float)
    hi = lang["delta_bootstrap_ci_high"].to_numpy(float)
    ax1.bar(x, y, width=0.68, edgecolor="black", linewidth=0.5)
    ax1.errorbar(x, y, yerr=np.vstack([y - lo, hi - y]), fmt="none", ecolor="black", capsize=2.5, linewidth=0.8)
    ax1.axhline(0, linewidth=0.7, color="black")
    ax1.set_xticks(x, lang["region_name"])
    ax1.set_ylabel("ΔRSA")
    ax1.set_title("a  Neural-guided improvement across frozen language parcels", loc="left", fontweight="bold")
    for i, p in enumerate(lang["language_family_fwer_p"].to_numpy(float)):
        ax1.text(i, hi[i] + 0.000025, f"FWER p={p:.4g}", ha="center", va="bottom", fontsize=6.3, rotation=0)
    ax1.set_ylim(0, max(hi) * 1.22)

    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(x, lang["lambda_0_mean"], marker="o", linewidth=1.2, label="Text-only E5 (λ=0)")
    ax2.plot(x, lang["lambda_0p10_mean"], marker="o", linewidth=1.2, label="Neural-guided E5 (λ=.10)")
    ax2.set_xticks(x, lang["region_name"])
    ax2.set_ylabel("Residual RSA")
    ax2.set_title("b  Baseline and neural-guided regional correspondence", loc="left", fontweight="bold")
    ax2.legend(frameon=False, ncol=2, loc="upper left")

    ax3 = fig.add_subplot(gs[2, 0])
    dk_plot = dk.sort_values(["hemisphere", "parcel_id"]).copy()
    left = dk_plot.loc[dk_plot["hemisphere"] == "L", ["region_name", "delta_mean"]].reset_index(drop=True)
    right = dk_plot.loc[dk_plot["hemisphere"] == "R", ["region_name", "delta_mean"]].reset_index(drop=True)
    if len(left) != 34 or len(right) != 34:
        raise RuntimeError("Expected 34 DK parcels per hemisphere")
    matrix = np.vstack([left["delta_mean"].to_numpy(float), right["delta_mean"].to_numpy(float)])
    im = ax3.imshow(matrix, aspect="auto", interpolation="nearest")
    ax3.set_yticks([0, 1], ["Left", "Right"])
    ax3.set_xticks(np.arange(34))
    ax3.set_xticklabels(left["region_name"], rotation=90, ha="center", fontsize=5.8)
    ax3.set_title("c  Complete DK68 ΔRSA phenotype (unthresholded)", loc="left", fontweight="bold")
    cbar = fig.colorbar(im, ax=ax3, orientation="vertical", fraction=0.025, pad=0.02)
    cbar.set_label("Mean participant ΔRSA")

    figure_paths = save_figure(fig, "figure_regional_fmri_transfer")
    plt.close(fig)

    caption = (
        "Regional SMN4Lang fMRI characterization. (a) Mean participant ΔRSA, neural-guided multilingual-E5 "
        "lambda=.10 minus matched text-only lambda=0, across the six prespecified left-hemisphere EvLab language "
        "parcels. Error bars are participant-bootstrap 95% confidence intervals; labels give the frozen six-region "
        "max-stat family-wise p-values. All six parcels were positive in 12/12 participants. (b) Mean residual RSA "
        "for the text-only and neural-guided arms in the same parcels. (c) The complete bilateral DK68 mean ΔRSA "
        "phenotype, shown without significance thresholding, parcel filtering or ranking. The DK68 map is a spatial "
        "characterization phenotype and is not interpreted as a 68-region significance screen."
    )
    caption_path = OUT_DIR / "figure_regional_fmri_transfer_caption.txt"
    caption_path.write_text(caption + "\n", encoding="utf-8")

    outputs = figure_paths + [language_table_path, dk_table_path, caption_path]
    manifest = {
        "schema_version": 1,
        "analysis": "Regional SMN4Lang fMRI publication figures and tables v1",
        "source_analysis": summary.get("analysis_stage"),
        "source_protocol": summary.get("protocol"),
        "source_files": {str(p.relative_to(ROOT)): sha256(p) for p in required},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "guardrails": {
            "presentation_only": True,
            "no_new_model_fitting": True,
            "no_new_hypothesis_testing": True,
            "no_roi_selection": True,
            "dk68_unthresholded": True,
            "language_order_is_frozen_anatomical_order": True,
        },
    }
    manifest_path = OUT_DIR / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": str(OUT_DIR), "n_outputs": len(outputs) + 1}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
