#!/usr/bin/env python3
"""Build the transfer-first NeuroSem NMI Figure 1 from committed frozen snapshots.

This is a presentation-only builder. A fresh clone can regenerate the figure without
workstation-only analysis outputs because the safe values displayed in the figure are
committed under paper/figure_data/nmi_redesign_v2/. The snapshot manifest preserves
lineage to the exact RunRelay job and upstream output hashes from which those values
were exported.

No model fitting, model evaluation, target selection, neural analysis, dose search,
representation selection, or new scientific inference is performed here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
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

SNAPSHOT_DIR = ROOT / "paper" / "figure_data" / "nmi_redesign_v2"
REL_SNAPSHOT = SNAPSHOT_DIR / "figure1_reliability_source.csv"
TRANSFER_SNAPSHOT = SNAPSHOT_DIR / "figure1_transfer_source.csv"
SEED_SNAPSHOT = SNAPSHOT_DIR / "figure1_seed_source.csv"
PROVENANCE = SNAPSHOT_DIR / "figure1_source_snapshot_manifest.json"
INPUTS = [REL_SNAPSHOT, TRANSFER_SNAPSHOT, SEED_SNAPSHOT, PROVENANCE]
OUT = ROOT / "outputs" / "nmi_figure1_transfer_redesign_v2" / "latest"

BLUE = "#356AC3"
ORANGE = "#E76F00"
BLUE_PALE = "#F4F8FF"
ORANGE_PALE = "#FFF7F1"
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


def load_data() -> tuple[dict, dict]:
    meta = read_json(PROVENANCE)
    rel_rows = read_csv(REL_SNAPSHOT)
    transfer_rows = read_csv(TRANSFER_SNAPSHOT)
    seed_rows = read_csv(SEED_SNAPSHOT)

    data: dict[str, dict] = {}
    definitions = {
        "zuco": ("ZuCo EEG", "English reading", BLUE, BLUE_PALE, 17),
        "fmri": ("SMN4Lang fMRI", "Mandarin listening", ORANGE, ORANGE_PALE, 12),
    }
    for key, (label, context, color, pale, expected_n) in definitions.items():
        rr = [r for r in rel_rows if r["dataset"] == key]
        tr = [r for r in transfer_rows if r["dataset"] == key]
        sr = [r for r in seed_rows if r["dataset"] == key]
        assert len(rr) == len(tr) == expected_n
        assert [int(r["participant_index"]) for r in rr] == list(range(1, expected_n + 1))
        assert [int(r["participant_index"]) for r in tr] == list(range(1, expected_n + 1))
        assert [r["training_run"] for r in sr] == ["Primary", "29", "30", "31"]

        rel = np.asarray([float(r["residual_loo_reliability"]) for r in rr], float)
        a0 = np.asarray([float(r["text_only_residual_rsa"]) for r in tr], float)
        a1 = np.asarray([float(r["neural_guided_residual_rsa"]) for r in tr], float)
        delta = np.asarray([float(r["delta_rsa"]) for r in tr], float)
        seed_means = np.asarray([float(r["mean_delta_rsa"]) for r in sr], float)
        seed_counts = [int(r["positive_participants"]) for r in sr]
        seed_n = [int(r["n_participants"]) for r in sr]
        statuses = [r["evidence_status"] for r in sr]

        summary = meta["displayed_summary"][key]
        delta_ci = np.asarray(summary["primary_bootstrap_95ci"], float)
        assert np.allclose(a1 - a0, delta, atol=5e-12)
        assert np.all(delta > 0)
        assert np.isclose(rel.mean(), float(summary["reliability_mean"]), atol=5e-12)
        assert np.isclose(delta.mean(), float(summary["primary_mean_delta"]), atol=5e-12)
        assert int(np.sum(delta > 0)) == int(summary["primary_positive"]) == expected_n
        assert np.allclose(seed_means, np.asarray(summary["four_run_means"], float), atol=5e-12)
        assert seed_counts == [int(x) for x in summary["four_run_positive_counts"]]
        assert all(n == expected_n for n in seed_n)
        assert statuses[0] == "prospective primary"
        assert all(s == "post-confirmatory optimization robustness" for s in statuses[1:])
        assert delta_ci[0] <= delta.mean() <= delta_ci[1]

        data[key] = {
            "label": label,
            "context": context,
            "color": color,
            "pale": pale,
            "n": expected_n,
            "rel": rel,
            "rel_mean": float(rel.mean()),
            "a0": a0,
            "a1": a1,
            "delta": delta,
            "delta_mean": float(delta.mean()),
            "delta_ci": delta_ci,
            "seed_labels": ["Primary", "29", "30", "31"],
            "seed_means": seed_means,
            "seed_counts": seed_counts,
            "seed_status": statuses,
        }
    return data, meta


def deterministic_offsets(n: int, width: float = 0.07) -> np.ndarray:
    if n <= 1:
        return np.zeros(n)
    values = np.linspace(-width, width, n)
    order: list[int] = []
    lo, hi = 0, n - 1
    while lo <= hi:
        order.append(lo)
        lo += 1
        if lo <= hi:
            order.append(hi)
            hi -= 1
    return values[np.asarray(order[:n], int)]


def kde_half_violin(ax, values: np.ndarray, x: float, width: float, color: str,
                    alpha: float = 0.27) -> None:
    """Draw a deterministic Gaussian-kernel half violin as a secondary visual layer."""
    values = np.asarray(values, float)
    if values.size < 4 or np.unique(values).size < 2:
        return
    sd = float(np.std(values, ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return
    bandwidth = max(1.06 * sd * values.size ** (-1 / 5), np.finfo(float).eps)
    span = max(float(np.ptp(values)), 4 * bandwidth)
    grid = np.linspace(float(values.min() - 0.15 * span), float(values.max() + 0.15 * span), 240)
    z = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * z * z).sum(axis=1) / (values.size * bandwidth * math.sqrt(2 * math.pi))
    density /= density.max()
    ax.fill_betweenx(grid, x, x + width * density, facecolor=color, alpha=alpha,
                     linewidth=0, zorder=1)


def rounded_background(ax, face: str = "white", edge: str = GREY_LIGHT) -> None:
    ax.set_axis_off()
    ax.add_patch(FancyBboxPatch(
        (0, 0), 1, 1, transform=ax.transAxes,
        boxstyle="round,pad=0.006,rounding_size=0.02",
        facecolor=face, edgecolor=edge, linewidth=0.65, clip_on=False,
    ))


def panel_header(ax, letter: str, title: str) -> None:
    ax.text(-0.02, 1.05, letter, transform=ax.transAxes, fontsize=8.5,
            fontweight="bold", ha="left", va="bottom", color=INK, clip_on=False)
    ax.text(0.04, 1.05, title, transform=ax.transAxes, fontsize=7.15,
            fontweight="bold", ha="left", va="bottom", color=INK, clip_on=False)


def flow_box(ax, x: float, y: float, w: float, h: float, title: str, subtitle: str,
             edge: str, face: str, title_color: str = INK, body_color: str = GREY) -> None:
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=0.75, zorder=2,
    ))
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
            fontsize=6.5, fontweight="bold", color=title_color, zorder=3)
    ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center",
            fontsize=5.15, color=body_color, linespacing=1.2, zorder=3)


def flow_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = INK) -> None:
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=7, linewidth=0.75,
        color=color, shrinkA=2, shrinkB=2, zorder=1,
    ))


def draw_schematic(ax) -> None:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    panel_header(ax, "a", "Frozen intervention tested in two independent neural systems")
    flow_box(ax, 0.02, 0.28, 0.25, 0.42, "ChineseEEG neural geometry",
             "Mandarin reading EEG\nsource relational geometry", GREY_LIGHT, "#F6F7F8")
    flow_box(ax, 0.42, 0.25, 0.19, 0.47, "FROZEN",
             "train once at fixed\nrelational-loss dose", BLUE, "#4D90FE", "white", "white")
    flow_box(ax, 0.72, 0.54, 0.25, 0.25, "ZuCo EEG",
             "English reading · n=17\nindependent external test", "#9CBDF0", BLUE_PALE, BLUE, GREY)
    flow_box(ax, 0.72, 0.15, 0.25, 0.25, "SMN4Lang fMRI",
             "Mandarin listening · n=12\nprospective cross-modal test", "#F0B381", ORANGE_PALE, ORANGE, GREY)
    flow_arrow(ax, (0.28, 0.49), (0.41, 0.49))
    ax.text(0.345, 0.535, "train once", ha="center", va="bottom", fontsize=5.9,
            fontweight="bold", color=INK)
    ax.text(0.345, 0.44, "same frozen E5 comparison", ha="center", va="top",
            fontsize=4.9, color=GREY)
    ax.plot([0.62, 0.66, 0.66], [0.49, 0.49, 0.665], color=INK, lw=0.75)
    flow_arrow(ax, (0.66, 0.665), (0.71, 0.665))
    ax.plot([0.62, 0.66, 0.66], [0.49, 0.49, 0.275], color=INK, lw=0.75)
    flow_arrow(ax, (0.66, 0.275), (0.71, 0.275))
    ax.text(0.515, 0.67, "✻", color="white", fontsize=15, ha="center", va="center",
            fontweight="bold")
    ax.text(0.98, 0.94,
            "No external outcome enters training, checkpointing,\nrepresentation choice, or dose selection.",
            ha="right", va="top", fontsize=4.9, color=GREY, linespacing=1.2)


def reliability_panel(ax, d: dict, show_ylabel: bool) -> None:
    values = d["rel"]
    color = d["color"]
    kde_half_violin(ax, values, 1.13, 0.20, color)
    xs = 0.88 + deterministic_offsets(d["n"], 0.055)
    ax.scatter(xs, values, s=9.5, color=color, edgecolor="white", linewidth=0.25, zorder=3)
    ax.scatter([1.13], [d["rel_mean"]], s=20, color=color, edgecolor="white",
               linewidth=0.35, zorder=4)
    ax.axhline(0, color=S.ZERO, lw=0.5, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(0.70, 1.42)
    ax.set_ylim((-0.005, 0.118) if d["label"].startswith("ZuCo") else (0.58, 0.735))
    ax.set_xticks([])
    ax.set_title(f"{d['label']} ($n={d['n']}$)", fontsize=6.0, fontweight="bold",
                 color=color, pad=2)
    ax.text(0.98, 0.97, f"{d['n']}/{d['n']}\npositive", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.1, fontweight="bold", color=color,
            linespacing=1.0)
    ax.text(0.98, 0.05, f"mean {d['rel_mean']:.3f}", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=4.7, color=GREY)
    if show_ylabel:
        ax.set_ylabel("Residual LOO reliability")
    ax.spines["bottom"].set_visible(False)
    S.offset_ticks(ax, "y")


def paired_arrow_panel(ax, d: dict, show_ylabel: bool) -> None:
    """Participant-level displacement: baseline is zero for each participant by definition."""
    delta = d["delta"] * 1e3
    x = np.arange(1, d["n"] + 1)
    y0 = np.zeros_like(delta)
    for xi, start, end in zip(x, y0, delta):
        arrow_color = d["color"] if end >= start else NEGATIVE
        ax.add_patch(FancyArrowPatch(
            (xi, start), (xi, end), arrowstyle="-|>", mutation_scale=5.2,
            linewidth=0.70, color=arrow_color, shrinkA=2, shrinkB=2, zorder=2,
        ))
    ax.scatter(x, y0, s=13, facecolor="white", edgecolor=d["color"], linewidth=0.65,
               zorder=3, label="Text-only baseline")
    ax.scatter(x, delta, s=14, facecolor=d["color"], edgecolor="white", linewidth=0.3,
               zorder=4, label="Neural-guided displacement")
    ax.axhline(0, color=GREY_LIGHT, lw=0.5, zorder=0)
    ax.set_xlim(0.45, d["n"] + 0.55)
    ax.set_xticks(x)
    ax.set_xlabel("Participant")
    ymax = max(delta.max() * 1.14, 1.0)
    ax.set_ylim(-0.08 * ymax, ymax)
    if show_ylabel:
        ax.set_ylabel("Within-participant ΔRSA\n(×10$^{-3}$)")
    ax.set_title(f"{d['label']} ($n={d['n']}$)", fontsize=6.1, fontweight="bold",
                 color=d["color"], pad=2)
    ax.legend(loc="upper left", fontsize=4.55, frameon=False, handletextpad=0.30,
              labelspacing=0.20)
    S.offset_ticks(ax, "both")


def delta_distribution_panel(ax, d: dict) -> None:
    values = d["delta"] * 1e3
    mean = d["delta_mean"] * 1e3
    ci = d["delta_ci"] * 1e3
    kde_half_violin(ax, values, 1.10, 0.21, d["color"])
    xs = 0.87 + deterministic_offsets(d["n"], 0.055)
    ax.scatter(xs, values, s=9.5, color=d["color"], edgecolor="white", linewidth=0.25, zorder=3)
    ax.errorbar([1.10], [mean], yerr=[[mean - ci[0]], [ci[1] - mean]], fmt="o",
                ms=3.7, color=d["color"], mfc=d["color"], mec="white", mew=0.25,
                capsize=1.8, lw=0.8, zorder=4)
    ax.axhline(0, color=S.ZERO, lw=0.5, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(0.68, 1.42)
    span = max(float(np.ptp(values)), mean)
    ax.set_ylim(min(0, values.min() - 0.12 * span), max(values.max(), ci[1]) + 0.14 * span)
    ax.set_xticks([])
    ax.set_title("Δ distribution", fontsize=5.5, fontweight="bold", pad=2)
    ax.text(0.98, 0.05, f"mean {mean:+.2f}\n95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}]",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=4.55,
            color=GREY, linespacing=1.15)
    ax.spines["bottom"].set_visible(False)
    S.offset_ticks(ax, "y")


def optimization_panel(ax, d: dict, show_ylabel: bool) -> None:
    values = d["seed_means"] * 1e3
    x = np.arange(4)
    ax.axhline(0, color=GREY_LIGHT, lw=0.5, ls=(0, (3, 3)), zorder=0)
    ax.axvline(0.5, color=GREY_LIGHT, lw=0.55, ls=(0, (5, 4)), zorder=0)
    ax.scatter([0], [values[0]], s=24, marker="D", facecolor=d["color"],
               edgecolor="white", linewidth=0.35, zorder=4)
    ax.scatter(x[1:], values[1:], s=22, marker="o", facecolor="white",
               edgecolor=d["color"], linewidth=0.75, zorder=4)
    for xi, yi, count in zip(x, values, d["seed_counts"]):
        ax.text(xi, yi + 0.08 * max(values), f"{count}/{d['n']}", ha="center", va="bottom",
                fontsize=4.8, color=d["color"], fontweight="bold")
    ax.set_xlim(-0.45, 3.45)
    ax.set_ylim(-0.05 * max(values), 1.34 * max(values))
    ax.set_xticks(x)
    ax.set_xticklabels(d["seed_labels"])
    ax.tick_params(axis="x", length=0)
    if show_ylabel:
        ax.set_ylabel("Mean ΔRSA\n(×10$^{-3}$)")
    ax.text(-0.12, 0.50, f"{d['label']}\n($n={d['n']}$)", transform=ax.transAxes,
            ha="right", va="center", fontsize=5.9, color=d["color"], fontweight="bold")
    ax.text(0.08, 0.98, "prospective primary", transform=ax.transAxes, ha="left", va="top",
            fontsize=4.6, color=GREY, fontweight="bold")
    ax.text(0.55, 0.98, "post-confirmatory optimization runs", transform=ax.transAxes,
            ha="left", va="top", fontsize=4.6, color=GREY, fontweight="bold")
    S.offset_ticks(ax, "y")


def build_figure(data: dict) -> plt.Figure:
    S.apply()
    fig = plt.figure(figsize=(S.W2 * S.MM, 151 * S.MM), constrained_layout=False)
    fig.suptitle("Frozen brain-derived supervision transfers across independent neural datasets",
                 x=0.055, y=0.992, ha="left", va="top", fontsize=8.5, fontweight="bold")
    gs = GridSpec(17, 16, figure=fig, left=0.055, right=0.985, bottom=0.055, top=0.955,
                  hspace=0.66, wspace=0.62)

    draw_schematic(fig.add_subplot(gs[0:5, 0:10]))

    b_bg = fig.add_subplot(gs[0:5, 10:16]); rounded_background(b_bg)
    panel_header(b_bg, "b", "Reliability gates in target datasets")
    bgs = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[1:4, 11:15], wspace=0.42)
    reliability_panel(fig.add_subplot(bgs[0, 0]), data["zuco"], True)
    reliability_panel(fig.add_subplot(bgs[0, 1]), data["fmri"], False)

    c_title = fig.add_subplot(gs[5:6, 0:16]); c_title.axis("off")
    panel_header(c_title, "c", "Participant-level transfer: every primary participant moves in the predicted direction")
    c1_bg = fig.add_subplot(gs[6:12, 0:8]); rounded_background(c1_bg, "#F9FBFF", "#C9D9F0")
    c2_bg = fig.add_subplot(gs[6:12, 8:16]); rounded_background(c2_bg, "#FFF9F4", "#F0CFB1")
    c1 = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[7:11, 1:8], width_ratios=[5.4, 1.35], wspace=0.22)
    c2 = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[7:11, 9:16], width_ratios=[5.4, 1.35], wspace=0.22)
    paired_arrow_panel(fig.add_subplot(c1[0, 0]), data["zuco"], True)
    delta_distribution_panel(fig.add_subplot(c1[0, 1]), data["zuco"])
    paired_arrow_panel(fig.add_subplot(c2[0, 0]), data["fmri"], False)
    delta_distribution_panel(fig.add_subplot(c2[0, 1]), data["fmri"])

    d_title = fig.add_subplot(gs[12:13, 0:16]); d_title.axis("off")
    panel_header(d_title, "d", "Optimization-run consistency")
    d1_bg = fig.add_subplot(gs[13:15, 0:16]); rounded_background(d1_bg, "#F9FBFF", "#C9D9F0")
    d2_bg = fig.add_subplot(gs[15:17, 0:16]); rounded_background(d2_bg, "#FFF9F4", "#F0CFB1")
    optimization_panel(fig.add_subplot(gs[13:15, 2:16]), data["zuco"], True)
    optimization_panel(fig.add_subplot(gs[15:17, 2:16]), data["fmri"], True)
    return fig


def copy_source_snapshots() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = {
        REL_SNAPSHOT: OUT / "figure1_reliability_source.csv",
        TRANSFER_SNAPSHOT: OUT / "figure1_transfer_source.csv",
        SEED_SNAPSHOT: OUT / "figure1_seed_source.csv",
        PROVENANCE: OUT / "figure1_source_snapshot_manifest.json",
    }
    for src, dst in mapping.items():
        shutil.copyfile(src, dst)
    return list(mapping.values())


def main() -> int:
    missing = [str(path.relative_to(ROOT)) for path in INPUTS if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing committed Figure 1 source snapshot(s): " + ", ".join(missing))

    data, snapshot_meta = load_data()
    OUT.mkdir(parents=True, exist_ok=True)
    fig = build_figure(data)
    outputs: list[Path] = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        path = OUT / f"figure1.{ext}"
        fig.savefig(path, **kwargs)
        outputs.append(path)
    plt.close(fig)

    copied_sources = copy_source_snapshots()
    builder = Path(__file__)
    manifest = {
        "schema_version": 3,
        "status": "ok",
        "figure": "NeuroSem NMI Figure 1 transfer-first redesign v2",
        "scientific_values_changed": False,
        "builder": str(builder.relative_to(ROOT)),
        "builder_sha256": sha256(builder),
        "committed_inputs": {str(path.relative_to(ROOT)): sha256(path) for path in INPUTS},
        "copied_source_data": {str(path.relative_to(ROOT)): sha256(path) for path in copied_sources},
        "outputs": {str(path.relative_to(ROOT)): sha256(path) for path in outputs},
        "source_runrelay_job": snapshot_meta["source_runrelay_job"],
        "source_artifacts": snapshot_meta["source_artifacts"],
        "original_upstream_input_hashes": snapshot_meta["original_upstream_input_hashes"],
        "guardrails": [
            "Fresh-clone reproducible from committed safe snapshots.",
            "Presentation-only; no model fitting, model evaluation, target selection, neural analysis, dose search, or new inference.",
            "Reliability panels show participant observations and the arithmetic mean; no new reliability CI is computed.",
            "Primary transfer delta panels use the already-frozen participant-bootstrap 95% CI recorded in the source snapshot manifest.",
            "Optimization-run panels show run means and positive-participant counts only; no CI is invented for added runs.",
            "Participant identifiers are not committed; source tables use sequential participant indices only."
        ],
        "displayed_summary": snapshot_meta["displayed_summary"],
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        "NeuroSem NMI Figure 1 transfer-first redesign v2",
        "Status: ok",
        "Scientific values changed: no",
        f"Source RunRelay job: {snapshot_meta['source_runrelay_job']['job_id']} at {snapshot_meta['source_runrelay_job']['exact_commit']}",
        f"ZuCo: n={data['zuco']['n']}, mean delta={data['zuco']['delta_mean']:.12g}, positive={int(np.sum(data['zuco']['delta'] > 0))}/{data['zuco']['n']}",
        f"SMN4Lang fMRI: n={data['fmri']['n']}, mean delta={data['fmri']['delta_mean']:.12g}, positive={int(np.sum(data['fmri']['delta'] > 0))}/{data['fmri']['n']}",
        "Reliability: raw participant points + arithmetic mean; no new CI computed.",
        "Optimization runs: frozen run means + positive-participant counts; no synthetic CI.",
        f"PNG SHA256: {sha256(OUT / 'figure1.png')}",
        f"SVG SHA256: {sha256(OUT / 'figure1.svg')}",
        f"PDF SHA256: {sha256(OUT / 'figure1.pdf')}",
    ]
    (OUT / "report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "output": str((OUT / "figure1.png").relative_to(ROOT)),
        "png_sha256": sha256(OUT / "figure1.png"),
        "source_runrelay_job": snapshot_meta["source_runrelay_job"]["job_id"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
