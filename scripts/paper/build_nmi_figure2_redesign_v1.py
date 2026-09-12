#!/usr/bin/env python3
"""Build redesigned NeuroSem NMI Figure 2 from frozen derived outputs only.

Presentation-only. No model fitting, target selection, neural analysis, dose selection,
or new inference is performed. The figure exposes participant-level evidence and the
post-confirmatory optimization-seed robustness already reported in the manuscript.
"""
from __future__ import annotations

import base64
import csv
import gzip
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
    ZUCO_REL, ZUCO_REL_SUM, ZUCO_TRANSFER, ZUCO_TRANSFER_SUM,
    FMRI_REL, FMRI_REL_SUM, FMRI_TRANSFER, FMRI_TRANSFER_SUM, MULTISEED,
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


def box(ax, x, y, w, h, title, subtitle, edge, face="white"):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=0.8, zorder=2,
    ))
    ax.text(x + 0.05*w, y + 0.66*h, title, ha="left", va="center",
            fontsize=7.0, fontweight="bold", color=S.INK, zorder=3)
    ax.text(x + 0.05*w, y + 0.29*h, subtitle, ha="left", va="center",
            fontsize=5.8, color=S.GREY, linespacing=1.25, zorder=3)


def arrow(ax, start, end, color=S.GREY):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=7, linewidth=0.75,
        color=color, shrinkA=3, shrinkB=3, zorder=1,
    ))


def primary_data() -> dict:
    zr = [r for r in read_csv(ZUCO_REL) if r.get("candidate") == "row_mean_all"]
    zrs = read_json(ZUCO_REL_SUM)
    zmetric = next(x for x in zrs["metrics"] if x["candidate"] == "row_mean_all")
    zt = read_csv(ZUCO_TRANSFER)
    zts = read_json(ZUCO_TRANSFER_SUM)["primary_result"]
    fr = read_csv(FMRI_REL)
    frs = read_json(FMRI_REL_SUM)
    ft = read_csv(FMRI_TRANSFER)
    fts = read_json(FMRI_TRANSFER_SUM)

    d = {
        "zuco": {
            "label": "ZuCo EEG", "context": "English reading", "color": S.BLUE,
            "rel": np.asarray([float(r["resid_loo"]) for r in zr], float),
            "rel_mean": float(zmetric["mean_resid_loo"]),
            "rel_ci": np.asarray(zmetric["resid_loo_bootstrap_95ci"], float),
            "a0": np.asarray([float(r["lambda_0_resid_rsa"]) for r in zt], float),
            "a1": np.asarray([float(r["lambda_0p10_resid_rsa"]) for r in zt], float),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in zt], float),
            "delta_mean": float(zts["mean_delta"]),
            "delta_ci": np.asarray(zts["bootstrap_95ci"], float),
        },
        "fmri": {
            "label": "SMN4Lang fMRI", "context": "Mandarin listening", "color": S.ORANGE,
            "rel": np.asarray([float(r["primary_residual_reliability"]) for r in fr], float),
            "rel_mean": float(frs["primary_mean"]),
            "rel_ci": np.asarray(frs["primary_bootstrap_95_ci"], float),
            "a0": np.asarray([float(r["lambda_0_residual_rsa"]) for r in ft], float),
            "a1": np.asarray([float(r["lambda_0p10_residual_rsa"]) for r in ft], float),
            "delta": np.asarray([float(r["delta_0p10_minus_0"]) for r in ft], float),
            "delta_mean": float(fts["primary_mean_delta"]),
            "delta_ci": np.asarray(fts["primary_bootstrap_95_ci_mean_delta"], float),
        },
    }
    d["zuco"]["n"] = len(d["zuco"]["delta"])
    d["fmri"]["n"] = len(d["fmri"]["delta"])
    assert d["zuco"]["n"] == len(d["zuco"]["rel"]) == 17
    assert d["fmri"]["n"] == len(d["fmri"]["rel"]) == 12
    assert np.all(d["zuco"]["delta"] > 0)
    assert np.all(d["fmri"]["delta"] > 0)
    return d


def seed_data(d: dict) -> dict:
    rows = read_json(MULTISEED)["results"]
    assert [int(r["seed"]) for r in rows] == [20260829, 20260830, 20260831]
    out = {}
    for key, mean_field, frac_field in (
        ("zuco", "zuco_mean_delta", "zuco_fraction_positive"),
        ("fmri", "smn4lang_fmri_mean_delta", "smn4lang_fmri_fraction_positive"),
    ):
        n = int(d[key]["n"])
        out[key] = {
            "labels": ["Primary", "29", "30", "31"],
            "means": np.asarray([d[key]["delta_mean"]] + [float(r[mean_field]) for r in rows]),
            "counts": [int(np.sum(d[key]["delta"] > 0))] + [int(round(float(r[frac_field])*n)) for r in rows],
            "n": n,
        }
        assert np.all(out[key]["means"] > 0)
    return out


def jitter(n: int, amplitude: float = 0.11) -> np.ndarray:
    if n <= 1:
        return np.zeros(n)
    base = np.linspace(-amplitude, amplitude, n)
    order = np.ravel(np.column_stack((np.arange((n+1)//2), np.arange(n-1, n//2-1, -1))))[:n]
    return base[order]


def column_header(ax, letter: str, title: str):
    ax.text(-0.20, 1.15, letter, transform=ax.transAxes, fontsize=8, fontweight="bold",
            ha="left", va="bottom", clip_on=False)
    ax.text(0.00, 1.15, title, transform=ax.transAxes, fontsize=7, fontweight="bold",
            ha="left", va="bottom", clip_on=False)


def dataset_label(ax, d: dict):
    ax.text(0.02, 0.96, d["label"], transform=ax.transAxes, ha="left", va="top",
            fontsize=6.2, fontweight="bold", color=S.INK)


def reliability_panel(ax, d: dict, upper: bool):
    c = d["color"]
    x = jitter(d["n"], 0.09)
    ax.axhline(0, color=S.ZERO, lw=0.55, zorder=0)
    ax.scatter(x, d["rel"], s=12, facecolor="white", edgecolor=c, linewidth=0.65, zorder=3)
    ax.errorbar([0.28], [d["rel_mean"]],
                yerr=[[d["rel_mean"]-d["rel_ci"][0]], [d["rel_ci"][1]-d["rel_mean"]]],
                fmt="D", ms=4, color=c, mfc=c, mec="white", mew=0.4, capsize=2, lw=0.8, zorder=4)
    ax.set_xlim(-0.16, 0.39)
    ax.set_ylim(0, 0.12 if d["label"].startswith("ZuCo") else 0.75)
    ax.set_xticks([0, 0.28])
    ax.set_xticklabels(["Participants", "Mean ± CI"])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Residual LOO reliability")
    dataset_label(ax, d)
    ax.text(0.98, 0.96, f"{d['n']}/{d['n']} positive", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.4, color=c)
    if upper:
        column_header(ax, "b", "Measurement gates")
    S.offset_ticks(ax, axis="y")


def delta_panel(ax, d: dict, power: int, upper: bool):
    c = d["color"]
    scale = 10.0**(-power)
    vals = d["delta"] * scale
    mean = d["delta_mean"] * scale
    ci = d["delta_ci"] * scale
    x = jitter(d["n"], 0.09)
    ax.axhline(0, color=S.ZERO, lw=0.55, zorder=0)
    ax.scatter(x, vals, s=13, facecolor="white", edgecolor=c, linewidth=0.7, zorder=3)
    ax.errorbar([0.28], [mean], yerr=[[mean-ci[0]], [ci[1]-mean]], fmt="D", ms=4.4,
                color=c, mfc=c, mec="white", mew=0.4, capsize=2, lw=0.9, zorder=4)
    ymax = 4.0 if power == -3 else 11.0
    ax.set_xlim(-0.16, 0.39); ax.set_ylim(0, ymax)
    ax.set_xticks([0, 0.28]); ax.set_xticklabels(["Participants", "Mean ± CI"])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel(f"Paired ΔRSA (×10$^{{{power}}}$)")
    dataset_label(ax, d)
    ax.text(0.98, 0.96, f"{d['n']}/{d['n']} positive", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.4, fontweight="bold", color=c)
    ax.text(0.98, 0.08, f"mean {mean:+.2f}\n95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}]",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.15,
            color=S.GREY, linespacing=1.25)
    if upper:
        column_header(ax, "c", "Primary paired displacement")
    S.offset_ticks(ax, axis="y")


def seed_panel(ax, s: dict, d: dict, power: int, upper: bool):
    c = d["color"]
    scale = 10.0**(-power)
    y = s["means"] * scale
    x = np.arange(4)
    ax.axhline(0, color=S.ZERO, lw=0.55, zorder=0)
    ax.axvline(0.5, color=S.GREY_L, lw=0.55, ls="--", zorder=0)
    ax.scatter([0], [y[0]], s=28, marker="D", facecolor=c, edgecolor="white", linewidth=0.45, zorder=4)
    ax.scatter(x[1:], y[1:], s=24, marker="o", facecolor="white", edgecolor=c, linewidth=0.85, zorder=4)
    ymax = 4.0 if power == -3 else 11.0
    for xi, yi, k in zip(x, y, s["counts"]):
        ax.text(xi, min(yi + 0.07*ymax, ymax*0.94), f"{k}/{s['n']}", ha="center", va="bottom",
                fontsize=5.1, color=S.GREY)
    ax.set_xlim(-0.45, 3.45); ax.set_ylim(0, ymax)
    ax.set_xticks(x); ax.set_xticklabels(s["labels"]); ax.tick_params(axis="x", length=0)
    ax.set_ylabel(f"Mean ΔRSA (×10$^{{{power}}}$)")
    dataset_label(ax, d)
    ax.text(0.03, 0.80, "prospective", transform=ax.transAxes, fontsize=5.1, color=c)
    ax.text(0.98, 0.80, "post-confirmatory", transform=ax.transAxes, fontsize=5.1,
            color=S.GREY, ha="right")
    if upper:
        column_header(ax, "d", "Optimization consistency")
    S.offset_ticks(ax, axis="y")


def write_source_tables(d: dict, seeds: dict) -> list[Path]:
    paths = []
    p = OUT / "figure2_reliability_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["dataset", "participant_index", "residual_loo_reliability"])
        for key in ("zuco", "fmri"):
            for i, v in enumerate(d[key]["rel"], 1): w.writerow([key, i, f"{float(v):.12g}"])
    paths.append(p)
    p = OUT / "figure2_primary_transfer_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["dataset", "participant_index", "text_only_residual_rsa", "neural_guided_residual_rsa", "delta_rsa"])
        for key in ("zuco", "fmri"):
            for i, (a0, a1, dd) in enumerate(zip(d[key]["a0"], d[key]["a1"], d[key]["delta"]), 1):
                w.writerow([key, i, f"{float(a0):.12g}", f"{float(a1):.12g}", f"{float(dd):.12g}"])
    paths.append(p)
    p = OUT / "figure2_seed_robustness_source.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["dataset", "training_run", "mean_delta_rsa", "positive_participants", "n_participants", "evidence_status"])
        for key in ("zuco", "fmri"):
            for i, (label, mean, count) in enumerate(zip(seeds[key]["labels"], seeds[key]["means"], seeds[key]["counts"])):
                status = "prospective primary" if i == 0 else "post-confirmatory optimization robustness"
                w.writerow([key, label, f"{float(mean):.12g}", count, seeds[key]["n"], status])
    paths.append(p)
    return paths


def build_figure() -> tuple[list[Path], list[Path], dict]:
    d = primary_data(); seeds = seed_data(d); S.apply()
    fig = S.figure(S.W2, 122)
    outer = fig.add_gridspec(2, 3, height_ratios=[0.36, 1.0], hspace=0.24, wspace=0.30)

    axa = fig.add_subplot(outer[0, :]); axa.set_xlim(0, 1); axa.set_ylim(0, 1); axa.axis("off")
    axa.text(-0.02, 1.02, "a", transform=axa.transAxes, fontsize=8, fontweight="bold", va="top", clip_on=False)
    axa.text(0.01, 0.96, "Frozen intervention tested in two independent neural systems",
             ha="left", va="top", fontsize=7, fontweight="bold")
    box(axa, 0.03, 0.20, 0.20, 0.48, "ChineseEEG source", "Mandarin reading EEG\nrelational geometry", S.BLUE, "#f4f7fb")
    box(axa, 0.31, 0.20, 0.20, 0.48, "Train once", "multilingual E5\nλ=0.10 vs λ=0", S.INK, "white")
    axa.plot([0.57, 0.57], [0.07, 0.80], color=S.INK, lw=0.8, ls=(0, (2.4, 2.4)))
    axa.text(0.57, 0.84, "FROZEN", ha="center", va="bottom", fontsize=5.8, fontweight="bold")
    box(axa, 0.66, 0.48, 0.30, 0.31, "ZuCo EEG", "English reading · n=17\nindependent external test", S.BLUE, "#f4f7fb")
    box(axa, 0.66, 0.08, 0.30, 0.31, "SMN4Lang fMRI", "Mandarin listening · n=12\nprospective cross-modal test", S.ORANGE, "#fff6f2")
    arrow(axa, (0.23, 0.44), (0.31, 0.44)); arrow(axa, (0.51, 0.44), (0.57, 0.44), S.INK)
    arrow(axa, (0.58, 0.44), (0.66, 0.63), S.BLUE); arrow(axa, (0.58, 0.44), (0.66, 0.23), S.ORANGE)
    axa.text(0.57, 0.01, "No external outcome used to retune λ, checkpoint, representation or target",
             ha="center", va="bottom", fontsize=5.4, color=S.GREY)

    gb = outer[1, 0].subgridspec(2, 1, hspace=0.34)
    gc = outer[1, 1].subgridspec(2, 1, hspace=0.34)
    gd = outer[1, 2].subgridspec(2, 1, hspace=0.34)
    b1, b2 = fig.add_subplot(gb[0]), fig.add_subplot(gb[1])
    c1, c2 = fig.add_subplot(gc[0]), fig.add_subplot(gc[1])
    d1, d2 = fig.add_subplot(gd[0]), fig.add_subplot(gd[1])
    reliability_panel(b1, d["zuco"], True); reliability_panel(b2, d["fmri"], False)
    delta_panel(c1, d["zuco"], -3, True); delta_panel(c2, d["fmri"], -4, False)
    seed_panel(d1, seeds["zuco"], d["zuco"], -3, True); seed_panel(d2, seeds["fmri"], d["fmri"], -4, False)

    outputs = save(fig); source_tables = write_source_tables(d, seeds)
    summary = {}
    for key in ("zuco", "fmri"):
        summary[key] = {
            "n": int(d[key]["n"]), "reliability_mean": float(d[key]["rel_mean"]),
            "primary_mean_delta": float(d[key]["delta_mean"]), "primary_ci": d[key]["delta_ci"].tolist(),
            "primary_positive": int(np.sum(d[key]["delta"] > 0)),
            "four_run_means": seeds[key]["means"].tolist(), "four_run_positive_counts": seeds[key]["counts"],
        }
    return outputs, source_tables, summary


def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing: raise FileNotFoundError("Missing frozen Figure 2 input(s): " + ", ".join(missing))
    outputs, source_tables, summary = build_figure()
    svg_path = OUT / "figure2.svg"
    svg_transport = base64.b64encode(gzip.compress(svg_path.read_bytes(), compresslevel=9, mtime=0)).decode("ascii")
    manifest = {
        "schema_version": 2,
        "analysis": "NeuroSem NMI Figure 2 scientific-graphic redesign",
        "status": "ok", "scientific_values_changed": False,
        "design_intent": [
            "Show participant-level evidence rather than only group summaries.",
            "Separate measurement reliability from the paired transfer estimand.",
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
        "builder": str(Path(__file__).relative_to(ROOT)), "builder_sha256": sha256(Path(__file__)),
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in INPUTS},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "source_data": {str(p.relative_to(ROOT)): sha256(p) for p in source_tables},
        "displayed_summary": summary,
        "svg_transport": {"encoding": "gzip+base64", "decoded_sha256": sha256(svg_path), "base64": svg_transport},
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status":"ok", "output_dir":str(OUT.relative_to(ROOT)), "png_sha256":sha256(OUT/"figure2.png"), "svg_sha256":sha256(svg_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
