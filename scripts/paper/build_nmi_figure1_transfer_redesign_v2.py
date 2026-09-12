#!/usr/bin/env python3
"""Build the re-architected NeuroSem NMI Figure 1 from frozen derived outputs.

The figure is presentation-only. It exposes the frozen intervention chronology,
participant-level reliability gates, paired external transfer, and optimization-run
consistency. It performs no model fitting, model evaluation, target selection,
neural analysis, dose search, representation selection, or new inference.

All scientific values are loaded from already-completed provenance-linked outputs.
The builder validates displayed summary values against the frozen summaries and writes
source-data tables plus a hash manifest beside the figure outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts" / "paper" / "nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

OUT = ROOT / "outputs" / "nmi_figure1_transfer_redesign_v2" / "latest"

ZUCO_REL = ROOT / "outputs/zuco2_nr_primary_representation_reliability/latest/subject_metrics.csv"
ZUCO_REL_SUM = ROOT / "outputs/zuco2_nr_primary_representation_reliability/latest/summary.json"
ZUCO_TRANSFER = ROOT / "outputs/zuco2_nr_e5_transfer_v1/latest/subject_results.csv"
ZUCO_TRANSFER_SUM = ROOT / "outputs/zuco2_nr_e5_transfer_v1/latest/summary.json"
FMRI_REL = ROOT / "outputs/smn4lang_fmri_reliability/latest/participant_results.csv"
FMRI_REL_SUM = ROOT / "outputs/smn4lang_fmri_reliability/latest/summary.json"
FMRI_TRANSFER = ROOT / "outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv"
FMRI_TRANSFER_SUM = ROOT / "outputs/smn4lang_fmri_e5_transfer_v1/latest/summary.json"
MULTISEED = ROOT / "outputs/nmi_multiseed_e5_v1/latest/summary.json"
INPUTS = [
    ZUCO_REL, ZUCO_REL_SUM, ZUCO_TRANSFER, ZUCO_TRANSFER_SUM,
    FMRI_REL, FMRI_REL_SUM, FMRI_TRANSFER, FMRI_TRANSFER_SUM, MULTISEED,
]

BLUE = "#356AC3"
ORANGE = "#E76F00"
BLUE_FAINT = "#EAF2FD"
ORANGE_FAINT = "#FFF1E6"
INK = "#20242A"
GREY = "#6B7280"
GREY_LIGHT = "#D1D5DB"
NEGATIVE = "#B44747"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_data() -> dict:
    zr_rows = [r for r in read_csv(ZUCO_REL) if r.get("candidate") == "row_mean_all"]
    zr_sum = read_json(ZUCO_REL_SUM)
    zr_metric = next(x for x in zr_sum["metrics"] if x["candidate"] == "row_mean_all")
    zt_rows = read_csv(ZUCO_TRANSFER)
    zt_sum = read_json(ZUCO_TRANSFER_SUM)["primary_result"]

    fr_rows = read_csv(FMRI_REL)
    fr_sum = read_json(FMRI_REL_SUM)
    ft_rows = read_csv(FMRI_TRANSFER)
    ft_sum = read_json(FMRI_TRANSFER_SUM)

    data = {
        "zuco": {
            "label": "ZuCo EEG",
            "context": "English reading",
            "color": BLUE,
            "faint": BLUE_FAINT,
            "rel": np.asarray([float(r["resid_loo"]) for r in zr_rows], float),
            "rel_mean": float(zr_metric["mean_resid_loo"]),
            "rel_ci": np.asarray(zr_metric["resid_loo_bootstrap_95ci"], float),
            "a0": np.asarray([float(r["lambda_0_resid_rsa"]) for r in zt_rows], float),
            "a1": np.asarray([float(r["lambda_0p10_resid_rsa"]) for r in zt_rows], float),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in zt_rows], float),
            "delta_mean": float(zt_sum["mean_delta"]),
            "delta_ci": np.asarray(zt_sum["bootstrap_95ci"], float),
        },
        "fmri": {
            "label": "SMN4Lang fMRI",
            "context": "Mandarin listening",
            "color": ORANGE,
            "faint": ORANGE_FAINT,
            "rel": np.asarray([float(r["primary_residual_reliability"]) for r in fr_rows], float),
            "rel_mean": float(fr_sum["primary_mean"]),
            "rel_ci": np.asarray(fr_sum["primary_bootstrap_95_ci"], float),
            "a0": np.asarray([float(r["lambda_0_residual_rsa"]) for r in ft_rows], float),
            "a1": np.asarray([float(r["lambda_0p10_residual_rsa"]) for r in ft_rows], float),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in ft_rows], float),
            "delta_mean": float(ft_sum["primary_mean_delta"]),
            "delta_ci": np.asarray(ft_sum["primary_bootstrap_95_ci_mean_delta"], float),
        },
    }

    for key, expected_n in (("zuco", 17), ("fmri", 12)):
        d = data[key]
        d["n"] = len(d["delta"])
        assert d["n"] == expected_n
        assert len(d["rel"]) == expected_n
        assert len(d["a0"]) == len(d["a1"]) == expected_n
        assert np.allclose(d["a1"] - d["a0"], d["delta"], atol=5e-12)
        assert np.all(d["delta"] > 0)
        assert math.isclose(float(np.mean(d["delta"])), d["delta_mean"], abs_tol=5e-12)
        assert d["delta_ci"][0] <= d["delta_mean"] <= d["delta_ci"][1]
        assert d["rel_ci"][0] <= d["rel_mean"] <= d["rel_ci"][1]

    multiseed = read_json(MULTISEED)["results"]
    assert [int(r["seed"]) for r in multiseed] == [20260829, 20260830, 20260831]
    for key, mean_field, frac_field in (
        ("zuco", "zuco_mean_delta", "zuco_fraction_positive"),
        ("fmri", "smn4lang_fmri_mean_delta", "smn4lang_fmri_fraction_positive"),
    ):
        n = data[key]["n"]
        data[key]["seed_labels"] = ["Primary", "29", "30", "31"]
        data[key]["seed_means"] = np.asarray(
            [data[key]["delta_mean"]] + [float(r[mean_field]) for r in multiseed], float
        )
        data[key]["seed_counts"] = [
            int(np.sum(data[key]["delta"] > 0)),
            *[int(round(float(r[frac_field]) * n)) for r in multiseed],
        ]
        assert np.all(data[key]["seed_means"] > 0)
    return data


def kde_half_violin(ax, values: np.ndarray, x: float, width: float, color: str, alpha: float = 0.26) -> None:
    """Deterministic Gaussian-kernel half violin, used only as a secondary density layer."""
    values = np.asarray(values, float)
    if values.size < 4 or np.unique(values).size < 2:
        return
    sd = float(np.std(values, ddof=1))
    if not np.isfinite(sd) or sd == 0:
        return
    bw = max(1.06 * sd * values.size ** (-1 / 5), np.finfo(float).eps)
    span = max(float(np.ptp(values)), 4 * bw)
    y = np.linspace(float(values.min() - 0.15 * span), float(values.max() + 0.15 * span), 220)
    z = (y[:, None] - values[None, :]) / bw
    density = np.exp(-0.5 * z * z).sum(axis=1) / (values.size * bw * math.sqrt(2 * math.pi))
    density /= density.max()
    ax.fill_betweenx(y, x, x + width * density, color=color, alpha=alpha, lw=0, zorder=1)


def deterministic_offsets(n: int, width: float = 0.08) -> np.ndarray:
    if n <= 1:
        return np.zeros(n)
    vals = np.linspace(-width, width, n)
    idx = []
    lo, hi = 0, n - 1
    while lo <= hi:
        idx.append(lo)
        lo += 1
        if lo <= hi:
            idx.append(hi)
            hi -= 1
    return vals[np.asarray(idx[:n], int)]


def rounded_panel(ax, face: str = "white", edge: str = GREY_LIGHT) -> None:
    ax.set_axis_off()
    ax.add_patch(FancyBboxPatch(
        (0, 0), 1, 1, transform=ax.transAxes,
        boxstyle="round,pad=0.006,rounding_size=0.02",
        facecolor=face, edgecolor=edge, linewidth=0.65, clip_on=False,
    ))


def figure_header(ax, letter: str, title: str) -> None:
    ax.text(-0.02, 1.06, letter, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8.5, fontweight="bold", color=INK, clip_on=False)
    ax.text(0.04, 1.06, title, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=7.2, fontweight="bold", color=INK, clip_on=False)


def flow_box(ax, x: float, y: float, w: float, h: float, title: str, subtitle: str,
             edge: str, face: str, title_color: str = INK, body_color: str = GREY) -> None:
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=0.75, zorder=2,
    ))
    ax.text(x + w / 2, y + 0.62 * h, title, ha="center", va="center",
            fontsize=6.7, fontweight="bold", color=title_color, zorder=3)
    ax.text(x + w / 2, y + 0.31 * h, subtitle, ha="center", va="center",
            fontsize=5.45, color=body_color, linespacing=1.25, zorder=3)


def flow_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = GREY) -> None:
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=7, linewidth=0.75,
        color=color, shrinkA=2, shrinkB=2, zorder=1,
    ))


def panel_a(ax) -> None:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    figure_header(ax, "a", "Study schematic")
    flow_box(ax, 0.02, 0.27, 0.25, 0.43, "ChineseEEG neural geometry", "Mandarin reading EEG\nsource relational geometry", GREY_LIGHT, "#F6F7F8")
    flow_box(ax, 0.42, 0.25, 0.19, 0.47, "FROZEN", "train once at fixed\nrelational-loss dose", BLUE, "#4D90FE", "white", "white")
    flow_box(ax, 0.72, 0.54, 0.25, 0.25, "ZuCo EEG", "English reading · n=17\nindependent external test", "#9CBDF0", "#F5F8FF", BLUE, GREY)
    flow_box(ax, 0.72, 0.15, 0.25, 0.25, "SMN4Lang fMRI", "Mandarin listening · n=12\nprospective cross-modal test", "#F0B381", "#FFF7F1", ORANGE, GREY)
    flow_arrow(ax, (0.28, 0.485), (0.41, 0.485), INK)
    ax.text(0.345, 0.53, "train once", ha="center", va="bottom", fontsize=6.2, fontweight="bold", color=INK)
    ax.text(0.345, 0.435, "same frozen E5 comparison", ha="center", va="top", fontsize=5.2, color=GREY)
    ax.plot([0.62, 0.66, 0.66], [0.485, 0.485, 0.665], color=INK, lw=0.75)
    flow_arrow(ax, (0.66, 0.665), (0.71, 0.665), INK)
    ax.plot([0.62, 0.66, 0.66], [0.485, 0.485, 0.275], color=INK, lw=0.75)
    flow_arrow(ax, (0.66, 0.275), (0.71, 0.275), INK)
    ax.text(0.515, 0.67, "✻", color="white", fontsize=15, ha="center", va="center", fontweight="bold")
    ax.text(0.98, 0.94, "No external outcome enters training, checkpointing,\nrepresentation choice, or dose selection.", ha="right", va="top", fontsize=5.15, color=GREY, linespacing=1.25)


def reliability_mini(ax, d: dict, show_ylabel: bool) -> None:
    vals = d["rel"]
    color = d["color"]
    x_raw = 0.88 + deterministic_offsets(d["n"], 0.055)
    kde_half_violin(ax, vals, 1.13, 0.20, color, alpha=0.25)
    ax.scatter(x_raw, vals, s=9.5, color=color, edgecolor="white", linewidth=0.25, zorder=3)
    ax.errorbar(
        [1.13], [d["rel_mean"]],
        yerr=[[d["rel_mean"] - d["rel_ci"][0]], [d["rel_ci"][1] - d["rel_mean"]]],
        fmt="o", ms=3.5, color=color, mfc=color, mec="white", mew=0.25,
        capsize=1.7, lw=0.75, zorder=4,
    )
    ax.axhline(0, color=S.ZERO, lw=0.5, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(0.70, 1.42)
    if d["label"].startswith("ZuCo"):
        ax.set_ylim(-0.005, 0.118)
    else:
        ax.set_ylim(0.58, 0.735)
    ax.set_xticks([])
    ax.set_title(f"{d['label']} ($n={d['n']}$)", color=color, fontsize=6.15, fontweight="bold", pad=2)
    ax.text(0.98, 0.97, f"{d['n']}/{d['n']}\npositive", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.4, fontweight="bold", color=color, linespacing=1.05)
    if show_ylabel:
        ax.set_ylabel("Residual LOO reliability")
    ax.spines["bottom"].set_visible(False)
    S.offset_ticks(ax, "y")


def panel_c_main(ax, d: dict, show_ylabel: bool) -> None:
    scale = 1e3
    a0 = d["a0"] * scale
    a1 = d["a1"] * scale
    x = np.arange(1, d["n"] + 1)
    left = x - 0.11
    right = x + 0.11
    for xi0, xi1, y0, y1 in zip(left, right, a0, a1):
        c = d["color"] if y1 >= y0 else NEGATIVE
        ax.add_patch(FancyArrowPatch(
            (xi0, y0), (xi1, y1), arrowstyle="-|>", mutation_scale=5.5,
            linewidth=0.7, color=c, shrinkA=2, shrinkB=2, zorder=2,
        ))
    ax.scatter(left, a0, s=14, facecolor="white", edgecolor=d["color"], linewidth=0.65, zorder=3, label="Text-only")
    ax.scatter(right, a1, s=15, facecolor=d["color"], edgecolor="white", linewidth=0.3, zorder=4, label="Neural-guided")
    ax.axhline(0, color=GREY_LIGHT, lw=0.45, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(0.45, d["n"] + 0.55)
    ax.set_xticks(x)
    ax.set_xlabel("Participant")
    if show_ylabel:
        ax.set_ylabel("Residual RSA (×10$^{-3}$)")
    lo = min(a0.min(), a1.min())
    hi = max(a0.max(), a1.max())
    pad = max(0.10 * (hi - lo), 0.8)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_title(f"{d['label']} ($n={d['n']}$)", color=d["color"], fontsize=6.2, fontweight="bold", pad=2)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend([handles[1], handles[0]], ["Neural-guided (frozen)", "Text-only (baseline)"],
              loc="upper left", fontsize=4.9, frameon=True, framealpha=0.94,
              borderpad=0.25, handletextpad=0.3, labelspacing=0.2)
    S.offset_ticks(ax, "both")


def panel_c_delta(ax, d: dict) -> None:
    vals = d["delta"] * 1e3
    mean = d["delta_mean"] * 1e3
    ci = d["delta_ci"] * 1e3
    x_raw = 0.87 + deterministic_offsets(d["n"], 0.055)
    kde_half_violin(ax, vals, 1.10, 0.21, d["color"], alpha=0.24)
    ax.scatter(x_raw, vals, s=10, color=d["color"], edgecolor="white", linewidth=0.25, zorder=3)
    ax.errorbar([1.10], [mean], yerr=[[mean - ci[0]], [ci[1] - mean]], fmt="o", ms=3.8,
                color=d["color"], mfc=d["color"], mec="white", mew=0.25,
                capsize=1.8, lw=0.8, zorder=4)
    ax.axhline(0, color=S.ZERO, lw=0.5, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(0.67, 1.42)
    top = max(vals.max(), ci[1])
    span = float(np.ptp(vals))
    ax.set_ylim(min(0, vals.min() - 0.15 * span), top + 0.15 * max(span, top))
    ax.set_xticks([])
    ax.set_title("Δ (neural − text)", fontsize=5.6, fontweight="bold", pad=2)
    ax.text(0.98, 0.05, f"mean {mean:+.2f}\n95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}]",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=4.7,
            color=GREY, linespacing=1.15)
    ax.spines["bottom"].set_visible(False)
    S.offset_ticks(ax, "y")


def seed_row(ax, d: dict, show_ylabel: bool) -> None:
    vals = d["seed_means"] * 1e3
    x = np.arange(4)
    ax.axhline(0, color=GREY_LIGHT, lw=0.5, ls=(0, (3, 3)), zorder=0)
    ax.axvline(0.5, color=GREY_LIGHT, lw=0.55, ls=(0, (5, 4)), zorder=0)
    ax.scatter([0], [vals[0]], s=24, marker="D", facecolor=d["color"], edgecolor="white", linewidth=0.35, zorder=4)
    ax.scatter(x[1:], vals[1:], s=22, marker="o", facecolor="white", edgecolor=d["color"], linewidth=0.75, zorder=4)
    for xi, yi, count in zip(x, vals, d["seed_counts"]):
        ax.text(xi, yi + 0.08 * max(vals), f"{count}/{d['n']}", ha="center", va="bottom",
                fontsize=4.9, color=d["color"], fontweight="bold")
    ax.set_xlim(-0.45, 3.45)
    ax.set_ylim(-0.05 * max(vals), 1.34 * max(vals))
    ax.set_xticks(x)
    ax.set_xticklabels(["Primary", "29", "30", "31"])
    ax.tick_params(axis="x", length=0)
    if show_ylabel:
        ax.set_ylabel("Mean ΔRSA\n(×10$^{-3}$)")
    ax.text(-0.12, 0.50, f"{d['label']}\n($n={d['n']}$)", transform=ax.transAxes,
            ha="right", va="center", fontsize=6.0, color=d["color"], fontweight="bold")
    ax.text(0.09, 0.98, "prospective primary", transform=ax.transAxes, ha="left", va="top",
            fontsize=4.8, color=GREY, fontweight="bold")
    ax.text(0.56, 0.98, "post-confirmatory optimization runs", transform=ax.transAxes, ha="left", va="top",
            fontsize=4.8, color=GREY, fontweight="bold")
    S.offset_ticks(ax, "y")


def write_source_tables(data: dict) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    p = OUT / "figure1_reliability_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "participant_index", "residual_loo_reliability"])
        for key in ("zuco", "fmri"):
            for i, value in enumerate(data[key]["rel"], 1):
                w.writerow([key, i, f"{float(value):.12g}"])
    paths.append(p)

    p = OUT / "figure1_transfer_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "participant_index", "text_only_residual_rsa", "neural_guided_residual_rsa", "delta_rsa"])
        for key in ("zuco", "fmri"):
            d = data[key]
            for i, (a0, a1, delta) in enumerate(zip(d["a0"], d["a1"], d["delta"]), 1):
                w.writerow([key, i, f"{float(a0):.12g}", f"{float(a1):.12g}", f"{float(delta):.12g}"])
    paths.append(p)

    p = OUT / "figure1_seed_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "training_run", "mean_delta_rsa", "positive_participants", "n_participants", "evidence_status"])
        for key in ("zuco", "fmri"):
            d = data[key]
            for label, mean, count in zip(d["seed_labels"], d["seed_means"], d["seed_counts"]):
                status = "prospective primary" if label == "Primary" else "post-confirmatory optimization robustness"
                w.writerow([key, label, f"{float(mean):.12g}", count, d["n"], status])
    paths.append(p)
    return paths


def build_figure(data: dict) -> plt.Figure:
    S.apply()
    fig = plt.figure(figsize=(S.W2 * S.MM, 153 * S.MM), constrained_layout=False)
    gs = GridSpec(17, 16, figure=fig, left=0.055, right=0.985, bottom=0.055, top=0.975, hspace=0.65, wspace=0.65)

    ax_a = fig.add_subplot(gs[0:5, 0:10])
    panel_a(ax_a)

    ax_b_bg = fig.add_subplot(gs[0:5, 10:16])
    rounded_panel(ax_b_bg)
    figure_header(ax_b_bg, "b", "Reliability gates in target datasets")
    bgs = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[1:4, 11:15], wspace=0.46)
    reliability_mini(fig.add_subplot(bgs[0, 0]), data["zuco"], True)
    reliability_mini(fig.add_subplot(bgs[0, 1]), data["fmri"], False)

    ax_c_title = fig.add_subplot(gs[5:6, 0:16]); ax_c_title.axis("off")
    figure_header(ax_c_title, "c", "Participant-level transfer: neural-guided vs. text-only")
    left_bg = fig.add_subplot(gs[6:12, 0:8]); rounded_panel(left_bg, "#F9FBFF", "#C9D9F0")
    right_bg = fig.add_subplot(gs[6:12, 8:16]); rounded_panel(right_bg, "#FFF9F4", "#F0CFB1")
    lgs = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[7:11, 1:8], width_ratios=[5.4, 1.35], wspace=0.22)
    rgs = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[7:11, 9:16], width_ratios=[5.4, 1.35], wspace=0.22)
    panel_c_main(fig.add_subplot(lgs[0, 0]), data["zuco"], True)
    panel_c_delta(fig.add_subplot(lgs[0, 1]), data["zuco"])
    panel_c_main(fig.add_subplot(rgs[0, 0]), data["fmri"], False)
    panel_c_delta(fig.add_subplot(rgs[0, 1]), data["fmri"])

    ax_d_title = fig.add_subplot(gs[12:13, 0:16]); ax_d_title.axis("off")
    figure_header(ax_d_title, "d", "Optimization-run consistency")
    d1_bg = fig.add_subplot(gs[13:15, 0:16]); rounded_panel(d1_bg, "#F9FBFF", "#C9D9F0")
    d2_bg = fig.add_subplot(gs[15:17, 0:16]); rounded_panel(d2_bg, "#FFF9F4", "#F0CFB1")
    seed_row(fig.add_subplot(gs[13:15, 2:16]), data["zuco"], True)
    seed_row(fig.add_subplot(gs[15:17, 2:16]), data["fmri"], True)
    return fig


def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing frozen Figure 1 input(s): " + ", ".join(missing))

    data = load_data()
    OUT.mkdir(parents=True, exist_ok=True)
    fig = build_figure(data)
    outputs: list[Path] = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        path = OUT / f"figure1.{ext}"
        fig.savefig(path, **kwargs)
        outputs.append(path)
    plt.close(fig)

    source_paths = write_source_tables(data)
    builder = Path(__file__)
    manifest = {
        "schema_version": 2,
        "status": "ok",
        "figure": "NeuroSem NMI Figure 1 transfer-first redesign",
        "scientific_values_changed": False,
        "builder": str(builder.relative_to(ROOT)),
        "builder_sha256": sha256(builder),
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in INPUTS},
        "source_data": {str(p.relative_to(ROOT)): sha256(p) for p in source_paths},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "guardrails": [
            "Presentation-only figure build from frozen derived outputs.",
            "No model fitting, model evaluation, target selection, neural analysis, dose search, or new inference.",
            "All displayed primary participant-level deltas are checked against the frozen summary means and confidence intervals.",
            "Optimization-run panel shows run-level means and sign counts only; it does not invent confidence intervals where participant-level run data are unavailable.",
            "Participant identifiers are not exported; source tables use sequential participant indices only.",
        ],
        "displayed_summary": {
            "zuco": {
                "n": int(data["zuco"]["n"]),
                "mean_delta_rsa": float(data["zuco"]["delta_mean"]),
                "bootstrap_95ci": [float(x) for x in data["zuco"]["delta_ci"]],
                "positive_participants": int(np.sum(data["zuco"]["delta"] > 0)),
                "reliability_mean": float(data["zuco"]["rel_mean"]),
            },
            "fmri": {
                "n": int(data["fmri"]["n"]),
                "mean_delta_rsa": float(data["fmri"]["delta_mean"]),
                "bootstrap_95ci": [float(x) for x in data["fmri"]["delta_ci"]],
                "positive_participants": int(np.sum(data["fmri"]["delta"] > 0)),
                "reliability_mean": float(data["fmri"]["rel_mean"]),
            },
        },
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = [
        "NeuroSem NMI Figure 1 transfer-first redesign v2",
        "Status: ok",
        "Scientific values changed: no",
        f"ZuCo: n={data['zuco']['n']}, mean delta={data['zuco']['delta_mean']:.12g}, positive={int(np.sum(data['zuco']['delta'] > 0))}/{data['zuco']['n']}",
        f"SMN4Lang fMRI: n={data['fmri']['n']}, mean delta={data['fmri']['delta_mean']:.12g}, positive={int(np.sum(data['fmri']['delta'] > 0))}/{data['fmri']['n']}",
        "Panel d reports run-level means and positive-participant counts only; no synthetic CI is drawn.",
        f"PNG SHA256: {sha256(OUT / 'figure1.png')}",
        f"SVG SHA256: {sha256(OUT / 'figure1.svg')}",
        f"PDF SHA256: {sha256(OUT / 'figure1.pdf')}",
    ]
    (OUT / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str((OUT / 'figure1.png').relative_to(ROOT)), "png_sha256": sha256(OUT / 'figure1.png')}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
