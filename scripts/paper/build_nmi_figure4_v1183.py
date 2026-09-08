#!/usr/bin/env python3
"""Rebuild NeuroSem NMI Figure 4 for manuscript v1.18.3.

Presentation-only. This script reads the same frozen derived outputs used by the
submission figure system and changes no scientific value, analysis, model, target,
or inference. The sole manuscript-facing wording change is the Figure 4c title,
which describes the added optimization seeds as directionally consistent rather
than population-level seed robustness.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "scripts" / "paper" / "nmi_visualizations_v4"
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
import nmi_style as S  # noqa: E402

MODELS = ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv"
SPEC = ROOT / "outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json"
REVERSE = ROOT / "outputs/nmi_bidirectional_fmri_to_zuco_v1/latest/summary.json"
REVERSE_MULTI = ROOT / "outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json"
INPUTS = [MODELS, SPEC, REVERSE, REVERSE_MULTI]

OUT = ROOT / "outputs/nmi_v1183_figure4/latest"
CANONICAL_OUT = ROOT / "outputs/nmi_main_figures_v3/latest"


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
    paths: list[Path] = []
    for ext, kwargs in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        p = OUT / f"figure4.{ext}"
        fig.savefig(p, **kwargs)
        paths.append(p)
    plt.close(fig)
    return paths


def build_figure4() -> list[Path]:
    rows = read_csv(MODELS)
    order = [
        ("e5_large", "E5-large"),
        ("e5_base", "E5-base"),
        ("multilingual_mpnet", "mMPNet"),
        ("multilingual_minilm", "mMiniLM"),
        ("xlmr_base", "XLM-R"),
        ("mbert", "mBERT"),
    ]
    directions = [("eeg_to_fmri", "EEG → fMRI"), ("fmri_to_eeg", "fMRI → EEG")]
    matrix = np.zeros((len(order), 2))
    signs: list[list[int]] = []
    for i, (key, _) in enumerate(order):
        sr: list[int] = []
        for j, (direction, _) in enumerate(directions):
            rr = sorted(
                [r for r in rows if r["model_key"] == key and r["direction"] == direction],
                key=lambda r: int(r["seed"]),
            )
            v = np.array([float(r["external_mean_delta"]) for r in rr]) * 1e3
            matrix[i, j] = v.mean()
            sr.append(int(np.sum(v > 0)))
        signs.append(sr)

    spec = read_json(SPEC)["specificity_control"]["seed_results"]
    reverse = read_json(REVERSE)["primary_result"]
    rmulti = read_json(REVERSE_MULTI)

    S.apply()
    fig = S.figure(S.W2, 112)
    gs = fig.add_gridspec(2, 12, height_ratios=[1.05, .95])
    axa = fig.add_subplot(gs[:, 0:6])
    axb = fig.add_subplot(gs[0, 6:12])
    axc = fig.add_subplot(gs[1, 6:12])

    vmax = max(abs(matrix.min()), abs(matrix.max()))
    norm = colors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im = axa.imshow(matrix, cmap=S.DIVERGING, norm=norm, aspect="auto")
    axa.set_yticks(np.arange(len(order)))
    axa.set_yticklabels([x[1] for x in order])
    axa.set_xticks([0, 1])
    axa.set_xticklabels([x[1] for x in directions])
    axa.tick_params(axis="both", length=0)
    axa.set_title(
        "Common λ=0.10 protocol: transfer depends on backbone and direction",
        fontsize=7,
        loc="left",
        pad=6,
    )
    for i in range(len(order)):
        for j in range(2):
            col = "white" if abs(matrix[i, j]) > 0.55 * vmax else S.INK
            axa.text(
                j,
                i,
                f"{matrix[i, j]:+.2f}\n{signs[i][j]}/3 +",
                ha="center",
                va="center",
                fontsize=6,
                color=col,
            )
    cb = fig.colorbar(im, ax=axa, fraction=.04, pad=.03)
    cb.set_label("Three-seed mean ΔRSA (×10$^{-3}$)", fontsize=6)
    cb.ax.tick_params(labelsize=5.3)
    for sp in axa.spines.values():
        sp.set_visible(False)

    datasets = [
        ("zuco", "ZuCo EEG", S.BLUE),
        ("smn4lang_fmri", "SMN4Lang fMRI", S.ORANGE),
    ]
    xbase = np.arange(3)
    for di, (ds, label, c) in enumerate(datasets):
        genuine: list[float] = []
        shuffled: list[float] = []
        for rec in spec:
            target = rec["targets"][ds]
            genuine.append(float(target["genuine_minus_shuffled"]["mean_delta"]) * 1e3)
            shuffled.append(float(target["shuffled_minus_text"]["mean_delta"]) * 1e3)
        offset = di * 3.8
        axb.plot(
            xbase + offset,
            genuine,
            "-o",
            color=c,
            markersize=3.2,
            label=f"{label}: genuine − shuffled",
        )
        axb.plot(
            xbase + offset,
            shuffled,
            "--o",
            color=c,
            alpha=.55,
            markersize=2.8,
            label=f"{label}: shuffled − text",
        )
    axb.axhline(0, color=S.ZERO, lw=.6)
    axb.set_xticks([0, 1, 2, 3.8, 4.8, 5.8])
    axb.set_xticklabels(["seed 1", "2", "3", "seed 1", "2", "3"])
    axb.set_ylabel("Mean contrast ΔRSA (×10$^{-3}$)")
    axb.set_title("Preserved neural item correspondence matters", fontsize=7, loc="left")
    axb.legend(loc="upper right", fontsize=5.3)

    labels = ["source-selected\noriginal"] + [str(r["seed"])[-2:] for r in rmulti["seed_results"]]
    means = [float(reverse["mean_delta"])] + [float(r["zuco"]["mean_delta"]) for r in rmulti["seed_results"]]
    cis = [reverse["bootstrap_95ci"]] + [r["zuco"]["bootstrap_95ci"] for r in rmulti["seed_results"]]
    x = np.arange(len(means))
    m = np.asarray(means) * 1e5
    ci = np.asarray(cis, float) * 1e5
    err = np.vstack([m - ci[:, 0], ci[:, 1] - m])
    axc.errorbar(
        x,
        m,
        yerr=err,
        fmt="o",
        color=S.TEAL,
        mfc="white",
        mec=S.TEAL,
        mew=1,
        capsize=2,
        lw=.8,
    )
    axc.axhline(0, color=S.ZERO, lw=.6)
    axc.set_xticks(x)
    axc.set_xticklabels(labels)
    axc.set_ylabel("Reverse ΔRSA (×10$^{-5}$)")
    axc.set_title(
        "Reverse transfer is small and directionally consistent across tested seeds",
        fontsize=7,
        loc="left",
    )
    axc.text(
        .98,
        .05,
        "λ=0.01 · 14/17 positive in each added seed",
        transform=axc.transAxes,
        ha="right",
        fontsize=5.8,
        color=S.TEAL,
    )

    for ax, letter, dx in ((axa, "a", -.11), (axb, "b", -.12), (axc, "c", -.12)):
        S.panel(ax, letter, dx=dx, dy=1.08)

    return save(fig)


def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in INPUTS if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing frozen Figure 4 input(s): " + ", ".join(missing))

    outputs = build_figure4()
    CANONICAL_OUT.mkdir(parents=True, exist_ok=True)
    canonical: list[Path] = []
    for src in outputs:
        dst = CANONICAL_OUT / src.name
        shutil.copy2(src, dst)
        canonical.append(dst)

    png_path = OUT / "figure4.png"
    png_transport = OUT / "figure4_png_base64.txt"
    png_transport.write_text(base64.encodebytes(png_path.read_bytes()).decode("ascii"), encoding="ascii")

    source_script = Path(__file__)
    manifest = {
        "schema_version": 1,
        "analysis": "NeuroSem NMI v1.18.3 Figure 4 presentation rebuild",
        "status": "ok",
        "wording_change": {
            "panel": "4c",
            "new_title": "Reverse transfer is small and directionally consistent across tested seeds",
            "scientific_values_changed": False,
        },
        "guardrails": [
            "Presentation-only rebuild from already-completed frozen derived outputs.",
            "No model fitting, model evaluation, neural analysis, target selection, dose selection or hypothesis testing is performed.",
            "All quantitative panels are read from the four frozen Figure 4 input files listed in inputs.",
            "The generated Figure 4 is copied into the canonical nmi_main_figures_v3 output location after rendering.",
            "The base64 text artifact is a byte-preserving transport copy of the generated PNG for artifact retrieval only.",
        ],
        "builder": str(source_script.relative_to(ROOT)),
        "builder_sha256": sha256(source_script),
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in INPUTS},
        "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in outputs},
        "canonical_outputs": {str(p.relative_to(ROOT)): sha256(p) for p in canonical},
        "png_transport": {
            "path": str(png_transport.relative_to(ROOT)),
            "decoded_sha256": sha256(png_path),
            "encoding": "base64",
        },
    }
    manifest_path = OUT / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "figure": 4,
                "panel_4c_title": manifest["wording_change"]["new_title"],
                "output_dir": str(OUT.relative_to(ROOT)),
                "canonical_output_dir": str(CANONICAL_OUT.relative_to(ROOT)),
                "png_sha256": sha256(png_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
