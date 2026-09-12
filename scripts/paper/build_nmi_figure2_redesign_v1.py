#!/usr/bin/env python3
"""Build redesigned NeuroSem NMI Figure 2 from frozen derived outputs only.

Presentation-only. No model fitting, target selection, neural analysis, dose selection,
or new inference is performed. The figure exposes participant-level evidence and the
post-confirmatory optimization-seed robustness already reported in the manuscript.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts" / "paper" / "nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

OUT = ROOT / "outputs" / "nmi_figure2_redesign_v1" / "latest"

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
    ZUCO_REL,
    ZUCO_REL_SUM,
    ZUCO_TRANSFER,
    ZUCO_TRANSFER_SUM,
    FMRI_REL,
    FMRI_REL_SUM,
    FMRI_TRANSFER,
    FMRI_TRANSFER_SUM,
    MULTISEED,
]


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


def save(fig: plt.Figure) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        p = OUT / f"figure2.{ext}"
        fig.savefig(p, **kwargs)
        written.append(p)
    plt.close(fig)
    return written


def box(ax, x, y, w, h, title, subtitle, edge, face="white", title_color=None):
    title_color = S.INK if title_color is None else title_color
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor=face,
            edgecolor=edge,
            linewidth=0.8,
            zorder=2,
        )
    )
    ax.text(x + 0.05 * w, y + 0.66 * h, title, ha="left", va="center", fontsize=7.0,
            fontweight="bold", color=title_color, zorder=3)
    ax.text(x + 0.05 * w, y + 0.29 * h, subtitle, ha="left", va="center", fontsize=5.8,
            color=S.GREY, linespacing=1.25, zorder=3)


def arrow(ax, start, end, color=S.GREY, lw=0.75):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=7,
            linewidth=lw,
            color=color,
            shrinkA=3,
            shrinkB=3,
            zorder=1,
        )
    )


def _primary_data() -> dict:
    zr = [r for r in read_csv(ZUCO_REL) if r.get("candidate") == "row_mean_all"]
    zrs = read_json(ZUCO_REL_SUM)
    zmetric = next(x for x in zrs["metrics"] if x["candidate"] == "row_mean_all")
    zt = read_csv(ZUCO_TRANSFER)
    zts = read_json(ZUCO_TRANSFER_SUM)["primary_result"]

    fr = read_csv(FMRI_REL)
    frs = read_json(FMRI_REL_SUM)
    ft = read_csv(FMRI_TRANSFER)
    fts = read_json(FMRI_TRANSFER_SUM)

    out = {
        "zuco": {
            "label": "ZuCo EEG",
            "context": "English reading",
            "n": len(zt),
            "color": S.BLUE,
            "rel": np.asarray([float(r["resid_loo"]) for r in zr], dtype=float),
            "rel_mean": float(zmetric["mean_resid_loo"]),
            "rel_ci": np.asarray(zmetric["resid_loo_bootstrap_95ci"], dtype=float),
            "a0": np.asarray([float(r["lambda_0_resid_rsa"]) for r in zt], dtype=float),
            "a1": np.asarray([float(r["lambda_0p10_resid_rsa"]) for r in zt], dtype=float),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in zt], dtype=float),
            "delta_mean": float(zts["mean_delta"]),
            "delta_ci": np.asarray(zts["bootstrap_95ci"], dtype=float),
        },
        "fmri": {
            "label": "SMN4Lang fMRI",
            "context": "Mandarin listening",
            "n": len(ft),
            "color": S.ORANGE,
            "rel": np.asarray([float(r["primary_residual_reliability"]) for r in fr], dtype=float),
            "rel_mean": float(frs["primary_mean"]),
            "rel_ci": np.asarray(frs["primary_bootstrap_95_ci"], dtype=float),
            "a0": np.asarray([float(r["lambda_0_residual_rsa"]) for r in ft], dtype=float),
            "a1": np.asarray([float(r["lambda_0p10_residual_rsa"]) for r in ft], dtype=float),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in ft], dtype=float),
            "delta_mean": float(fts["primary_mean_delta"]),
            "delta_ci": np.asarray(fts["primary_bootstrap_95_ci_mean_delta"], dtype=float),
        },
    }

    assert out["zuco"]["n"] == 17, f"Expected 17 ZuCo participants, found {out['zuco']['n']}"
    assert out["fmri"]["n"] == 12, f"Expected 12 fMRI participants, found {out['fmri']['n']}"
    assert len(out["zuco"]["rel"]) == 17
    assert len(out["fmri"]["rel"]) == 12
    assert np.all(out["zuco"]["delta"] > 0), "Primary ZuCo participant deltas are not all positive"
    assert np.all(out["fmri"]["delta"] > 0), "Primary fMRI participant deltas are not all positive"
    return out


def _seed_data(d: dict) -> dict:
    payload = read_json(MULTISEED)
    rows = payload["results"]
    assert len(rows) == 3, f"Expected three added seeds, found {len(rows)}"
    expected = [20260829, 20260830, 20260831]
    observed = [int(r["seed"]) for r in rows]
    assert observed == expected, f"Unexpected added seed order: {observed}"

    out = {}
    for key, mean_field, frac_field in (
        ("zuco", "zuco_mean_delta", "zuco_fraction_positive"),
        ("fmri", "smn4lang_fmri_mean_delta", "smn4lang_fmri_fraction_positive"),
    ):
        n = int(d[key]["n"])
        means = [float(d[key]["delta_mean"])] + [float(r[mean_field]) for r in rows]
        counts = [int(np.sum(d[key]["delta"] > 0))] + [int(round(float(r[frac_field]) * n)) for r in rows]
        out[key] = {
            "labels": ["Prospective", "29", "30", "31"],
            "means": np.asarray(means, dtype=float),
            "positive_counts": counts,
            "n": n,
        }
        assert np.all(out[key]["means"] > 0), f"Expected all four {key} seed means to be positive"
    return out


def _deterministic_jitter(n: int, amplitude: float = 0.055) -> np.ndarray:
    if n <= 1:
        return np.zeros(n)
    base = np.linspace(-amplitude, amplitude, n)
    order = np.ravel(np.column_stack((np.arange((n + 1) // 2), np.arange(n - 1, n // 2 - 1, -1))))[:n]
    return base[order]


def reliability_panel(ax, data: dict, show_xlabel: bool):
    vals = np.sort(data["rel"])
    jitter = _deterministic_jitter(len(vals))
    c = data["color"]
    ax.scatter(vals, jitter, s=12, facecolor="white", edgecolor=c, linewidth=0.65, zorder=3)
    ax.errorbar(
        [data["rel_mean"]], [0.15],
        xerr=[[data["rel_mean"] - data["rel_ci"][0]], [data["rel_ci"][1] - data["rel_mean"]]],
        fmt="D", ms=4.0, color=c, mfc=c, mec="white", mew=0.4, capsize=2.0, lw=0.8, zorder=4,
    )
    ax.axvline(0, color=S.ZERO, lw=0.55, zorder=0)
    ax.set_yticks([])
    ax.set_ylim(-0.12, 0.22)
    ax.set_title(f"{data['label']}  ·  n={data['n']}", loc="left", fontsize=6.4, fontweight="bold")
    if show_xlabel:
        ax.set_xlabel("Residual LOO reliability")
    ax.text(
        0.98, 0.88,
        f"{data['n']}/{data['n']} positive\nmean {data['rel_mean']:.3f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=5.5, color=S.GREY, linespacing=1.3,
    )
    S.offset_ticks(ax, axis="x")


def paired_transfer_panel(ax, data: dict, show_ylabel: bool):
    a0 = data["a0"]
    a1 = data["a1"]
    c = data["color"]
    x0, x1 = 0.0, 1.0
    for u, v in zip(a0, a1):
        ax.plot([x0, x1], [u, v], color=c, alpha=0.22, lw=0.65, zorder=1)
        ax.scatter([x0], [u], s=9, facecolor="white", edgecolor=S.GREY, linewidth=0.5, zorder=2)
        ax.scatter([x1], [v], s=10, facecolor=c, edgecolor="white", linewidth=0.35, zorder=3)
    means = [float(np.mean(a0)), float(np.mean(a1))]
    ax.plot([x0, x1], means, color=S.INK, lw=1.45, zorder=4)
    ax.scatter([x0, x1], means, s=24, facecolor=["white", c], edgecolor=S.INK, linewidth=0.65, zorder=5)
    ax.set_xlim(-0.28, 1.28)
    lo = min(float(np.min(a0)), float(np.min(a1)))
    hi = max(float(np.max(a0)), float(np.max(a1)))
    pad = max((hi - lo) * 0.18, 1e-5)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Text-only", "Neural-guided"])
    ax.tick_params(axis="x", length=0)
    if show_ylabel:
        ax.set_ylabel("Participant residual RSA")
    ax.set_title(f"{data['label']}  ·  {data['context']}", loc="left", fontsize=6.4, fontweight="bold")
    pos = int(np.sum(data["delta"] > 0))
    ax.text(
        0.03, 0.97,
        f"{pos}/{data['n']} shift upward",
        transform=ax.transAxes, ha="left", va="top", fontsize=5.7, fontweight="bold", color=c,
    )
    mean = data["delta_mean"]
    ci = data["delta_ci"]
    power = -3 if data["label"].startswith("ZuCo") else -4
    scale = 10.0 ** (-power)
    ax.text(
        0.97, 0.04,
        f"Δ {mean * scale:+.2f} × 10$^{{{power}}}$\n95% CI [{ci[0] * scale:+.2f}, {ci[1] * scale:+.2f}]",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=5.4, color=S.GREY, linespacing=1.25,
    )
    S.offset_ticks(ax, axis="y")


def seed_panel(ax, data: dict, dataset: dict, power: int, show_ylabel: bool):
    x = np.arange(4, dtype=float)
    scale = 10.0 ** (-power)
    y = data["means"] * scale
    c = dataset["color"]
    ax.axhline(0, color=S.ZERO, lw=0.55, zorder=0)
    ax.axvline(0.5, color=S.GREY_L, lw=0.55, ls="--", zorder=0)
    ax.scatter([0], [y[0]], s=28, marker="D", facecolor=c, edgecolor="white", linewidth=0.45, zorder=4)
    ax.scatter(x[1:], y[1:], s=23, marker="o", facecolor="white", edgecolor=c, linewidth=0.85, zorder=4)
    span = max(float(np.ptp(y)), float(np.max(np.abs(y))) * 0.35, 0.2)
    label_offset = 0.09 * span
    for xi, yi, k in zip(x, y, data["positive_counts"]):
        ax.text(xi, yi + label_offset, f"{k}/{data['n']}", ha="center", va="bottom", fontsize=5.1, color=S.GREY)
    ax.set_xticks(x)
    ax.set_xticklabels(data["labels"])
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.45, 3.45)
    ymin = min(0.0, float(np.min(y)) - 0.25 * span)
    ymax = float(np.max(y)) + 0.42 * span
    ax.set_ylim(ymin, ymax)
    if show_ylabel:
        ax.set_ylabel(f"Mean ΔRSA (×10$^{{{power}}}$)")
    ax.set_title(dataset["label"], loc="left", fontsize=6.4, fontweight="bold")
    ax.text(0.03, 0.91, "prospective", transform=ax.transAxes, fontsize=5.1, color=c, ha="left")
    ax.text(0.98, 0.91, "post-confirmatory seeds", transform=ax.transAxes, fontsize=5.1, color=S.GREY, ha="right")
    S.offset_ticks(ax, axis="y")


def write_source_tables(d: dict, seeds: dict) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    p = OUT / "figure2_reliability_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "participant_index", "residual_loo_reliability"])
        for key in ("zuco", "fmri"):
            for i, v in enumerate(d[key]["rel"], start=1):
                w.writerow([key, i, f"{float(v):.12g}"])
    paths.append(p)

    p = OUT / "figure2_primary_transfer_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "participant_index", "text_only_residual_rsa", "neural_guided_residual_rsa", "delta_rsa"])
        for key in ("zuco", "fmri"):
            for i, (a0, a1, dd) in enumerate(zip(d[key]["a0"], d[key]["a1"], d[key]["delta"]), start=1):
                w.writerow([key, i, f"{float(a0):.12g}", f"{float(a1):.12g}", f"{float(dd):.12g}"])
    paths.append(p)

    p = OUT / "figure2_seed_robustness_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "training_run", "mean_delta_rsa", "positive_participants", "n_participants", "evidence_status"])
        for key in ("zuco", "fmri"):
            for i, (label, mean, count) in enumerate(zip(seeds[key]["labels"], seeds[key]["means"], seeds[key]["positive_counts"])):
                status = "prospective primary" if i == 0 else "post-confirmatory optimization robustness"
                w.writerow([key, label, f"{float(mean):.12g}", count, seeds[key]["n"], status])
    paths.append(p)
    return paths


def build_figure() -> tuple[list[Path], list[Path], dict]:
    d = _primary_data()
    seeds = _seed_data(d)
    S.apply()

    fig = S.figure(S.W2, 129)
    outer = fig.add_gridspec(2, 3, height_ratios=[0.40, 1.0], hspace=0.14, wspace=0.30)

    axa = fig.add_subplot(outer[0, :])
    axa.set_xlim(0, 1)
    axa.set_ylim(0, 1)
    axa.axis("off")
    S.panel(axa, "a", dx=-0.02, dy=1.03)
    axa.text(0.01, 0.95, "One frozen intervention, two independent neural tests", ha="left", va="top",
             fontsize=7.0, fontweight="bold")
    box(axa, 0.03, 0.21, 0.20, 0.48, "ChineseEEG source", "Mandarin reading EEG\nrelational geometry", S.BLUE, "#f4f7fb")
    box(axa, 0.31, 0.21, 0.20, 0.48, "Train once", "multilingual E5\nλ=0.10 vs λ=0", S.INK, "#ffffff")
    axa.plot([0.57, 0.57], [0.08, 0.82], color=S.INK, lw=0.8, ls=(0, (2.4, 2.4)), zorder=0)
    axa.text(0.57, 0.86, "FROZEN", ha="center", va="bottom", fontsize=5.8, fontweight="bold", color=S.INK)
    box(axa, 0.66, 0.50, 0.30, 0.31, "ZuCo EEG", "English reading · n=17\nindependent external test", S.BLUE, "#f4f7fb")
    box(axa, 0.66, 0.10, 0.30, 0.31, "SMN4Lang fMRI", "Mandarin listening · n=12\nprospective cross-modal test", S.ORANGE, "#fff6f2")
    arrow(axa, (0.23, 0.45), (0.31, 0.45))
    arrow(axa, (0.51, 0.45), (0.57, 0.45), color=S.INK)
    arrow(axa, (0.58, 0.45), (0.66, 0.65), color=S.BLUE)
    arrow(axa, (0.58, 0.45), (0.66, 0.25), color=S.ORANGE)
    axa.text(0.57, 0.02, "No external outcome used to retune λ, checkpoint, representation or target",
             ha="center", va="bottom", fontsize=5.5, color=S.GREY)

    gsb = outer[1, 0].subgridspec(2, 1, hspace=0.42)
    axb1 = fig.add_subplot(gsb[0, 0])
    axb2 = fig.add_subplot(gsb[1, 0])
    S.panel(axb1, "b", dx=-0.18, dy=1.28)
    axb1.text(0.0, 1.20, "Reliable external targets", transform=axb1.transAxes, ha="left", va="top",
              fontsize=7.0, fontweight="bold")
    reliability_panel(axb1, d["zuco"], show_xlabel=False)
    reliability_panel(axb2, d["fmri"], show_xlabel=True)

    gsc = outer[1, 1].subgridspec(2, 1, hspace=0.42)
    axc1 = fig.add_subplot(gsc[0, 0])
    axc2 = fig.add_subplot(gsc[1, 0])
    S.panel(axc1, "c", dx=-0.18, dy=1.28)
    axc1.text(0.0, 1.20, "Participant-level external transfer", transform=axc1.transAxes, ha="left", va="top",
              fontsize=7.0, fontweight="bold")
    paired_transfer_panel(axc1, d["zuco"], show_ylabel=True)
    paired_transfer_panel(axc2, d["fmri"], show_ylabel=True)

    gsd = outer[1, 2].subgridspec(2, 1, hspace=0.42)
    axd1 = fig.add_subplot(gsd[0, 0])
    axd2 = fig.add_subplot(gsd[1, 0])
    S.panel(axd1, "d", dx=-0.18, dy=1.28)
    axd1.text(0.0, 1.20, "Optimization consistency", transform=axd1.transAxes, ha="left", va="top",
              fontsize=7.0, fontweight="bold")
    seed_panel(axd1, seeds["zuco"], d["zuco"], power=-3, show_ylabel=True)
    seed_panel(axd2, seeds["fmri"], d["fmri"], power=-4, show_ylabel=True)

    outputs = save(fig)
    source_tables = write_source_tables(d, seeds)
    summary = {
        "zuco": {
            "n": d["zuco"]["n"],
            "reliability_mean": d["zuco"]["rel_mean"],
            "primary_mean_delta": d["zuco"]["delta_mean"],
            "primary_ci": d["zuco"]["delta_ci"].tolist(),
            "primary_positive": int(np.sum(d["zuco"]["delta"] > 0)),
            "four_run_means": seeds["zuco"]["means"].tolist(),
            "four_run_positive_counts": seeds["zuco"]["positive_counts"],
        },
        "fmri": {
            "n": d["fmri"]["n"],
            "reliability_mean": d["fmri"]["rel_mean"],
            "primary_mean_delta": d["fmri"]["delta_mean"],
            "primary_ci": d["fmri"]["delta_ci"].tolist(),
            "primary_positive": int(np.sum(d["fmri"]["delta"] > 0)),
            "four_run_means": seeds["fmri"]["means"].tolist(),
            "four_run_positive_counts": seeds["fmri"]["positive_counts"],
        },
    }
    return outputs, source_tables, summary


def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing frozen Figure 2 input(s): " + ", ".join(missing))

    outputs, source_tables, summary = build_figure()
    manifest = {
        "schema_version": 1,
        "analysis": "NeuroSem NMI Figure 2 scientific-graphic redesign",
        "status": "ok",
        "scientific_values_changed": False,
        "design_intent": [
            "Show participant-level evidence rather than only group summaries.",
            "Separate measurement reliability from transfer inference.",
            "Make the frozen intervention chronology explicit.",
            "Distinguish the prospective primary run from post-confirmatory optimization-seed robustness.",
            "Avoid connecting categorical seed indices with trend lines.",
        ],
        "guardrails": [
            "Presentation-only build from frozen derived outputs.",
            "No model fitting, model evaluation, neural analysis, dose selection or new inference.",
            "Participant identifiers are not exported; source-data tables use sequential indices only.",
            "The original prospective and added-seed evidential statuses are preserved visually and in source data.",
        ],
        "builder": str(Path(__file__).relative_to(ROOT)),
        "builder_sha256": sha256(Path(__file__)),
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in INPUTS},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "source_data": {str(p.relative_to(ROOT)): sha256(p) for p in source_tables},
        "displayed_summary": summary,
    }
    manifest_path = OUT / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "output_dir": str(OUT.relative_to(ROOT)),
        "figure_png_sha256": sha256(OUT / "figure2.png"),
        "summary": summary,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
