#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import nmi_style as S

RUNS = np.array([0.0057, 0.0034, 0.0145, 0.0045, 0.0174, 0.0056])
RUN07 = {"Base": [0.0319, 0.0319], "Text-only": [0.0354, 0.0341], "Neural-guided": [0.0371, 0.0375], "Shuffled-neural": [0.0353, 0.0338]}
SEM = {"Base": [0.283464, 0.283464], "Text-only": [0.308486, 0.305020], "Neural-guided": [0.308575, 0.301607], "Shuffled-neural": [0.307943, 0.305266]}
RELIABILITY = {"Raw LOO": 0.220, "Residual LOO": 0.121}
ARM_SHORT = ["base", "text-only", "neural-\nguided", "shuffled-\nneural"]


def panel_a(ax):
    S.schematic(ax)
    S.flowbox(ax, 0.00, 0.80, 0.45, 0.16, "Natural-reading EEG\nreproducible neural RDM")
    S.flowbox(ax, 0.55, 0.80, 0.45, 0.16, "Language-model\npairwise geometry")
    S.flowbox(ax, 0.06, 0.44, 0.88, 0.17, "Auxiliary neural relational objective\n+ matched text-learning objective", fc="#eef3f8")
    S.arrow(ax, (0.225, 0.795), (0.35, 0.615)); S.arrow(ax, (0.775, 0.795), (0.65, 0.615))
    S.flowbox(ax, 0.06, 0.14, 0.88, 0.15, "Sealed development test $\\rightarrow$\nfrozen external transfer")
    S.arrow(ax, (0.50, 0.435), (0.50, 0.295))


def panel_b(ax):
    vals = list(RELIABILITY.values()); x = np.arange(len(vals))
    ax.bar(x, vals, width=0.5, color=[S.GREY_L, S.BLUE], zorder=3)
    for xi, v in zip(x, vals): ax.text(xi, v + 0.006, f"{v:.3f}", ha="center", va="bottom", fontsize=6)
    ax.set_xticks(x); ax.set_xticklabels(["raw\nLOO", "residual\nLOO"])
    ax.set_ylabel("Cross-participant reliability"); ax.set_ylim(0, 0.25); ax.tick_params(axis="x", length=0); S.offset_ticks(ax, "y")


def panel_c(ax):
    x = np.arange(1, len(RUNS) + 1)
    ax.plot(x, RUNS, "-o", color=S.BLUE, markersize=3.0, zorder=3); S.zeroline(ax)
    ax.set_xticks(x); ax.set_xticklabels([f"{i:02d}" for i in x]); ax.set_xlabel("Held-out narrative run")
    ax.set_ylabel("Partial Spearman"); ax.set_ylim(0, RUNS.max() * 1.18); S.offset_ticks(ax, "y")


def _arm_dots(ax, table, ylabel, ylim):
    names = list(table); x = np.arange(len(names))
    for xi, name in zip(x, names):
        seeds = np.asarray(table[name], float); colour = S.BLUE if name == "Neural-guided" else S.GREY
        jitter = np.linspace(-0.09, 0.09, len(seeds)); ax.plot(xi + jitter, seeds, "o", color=colour, markersize=2.8, alpha=0.8, zorder=3)
        ax.plot([xi - 0.19, xi + 0.19], [seeds.mean()] * 2, "-", color=colour, lw=1.3, zorder=4)
    ax.set_xticks(x); ax.set_xticklabels(ARM_SHORT); ax.set_xlim(-0.55, len(names) - 0.45); ax.set_ylabel(ylabel); ax.set_ylim(*ylim)
    ax.tick_params(axis="x", length=0); ax.grid(axis="y", zorder=0); S.offset_ticks(ax, "y")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--development-json", type=Path); ap.add_argument("--out-prefix", type=Path, required=True); ap.add_argument("--demo", action="store_true"); args = ap.parse_args()
    global RUNS, RUN07, RELIABILITY
    if args.development_json is not None:
        dev = json.loads(args.development_json.read_text(encoding="utf-8")); RUNS = np.asarray(dev["heldout_residual_correspondence"], float)
        RELIABILITY = {"Raw LOO": float(dev["reliability"]["raw_loo"]), "Residual LOO": float(dev["reliability"]["residual_loo"])}
        sealed = dev["sealed_run07"]; RUN07 = {arm: [float(sealed["seed_1"][i]), float(sealed["seed_2"][i])] for i, arm in enumerate(sealed["arms"])}
    elif not args.demo: ap.error("--development-json required unless --demo")
    S.apply(); fig = S.figure(S.W2, 100); gs = fig.add_gridspec(2, 6)
    ax_a = fig.add_subplot(gs[0, 0:2]); ax_b = fig.add_subplot(gs[0, 2:4]); ax_c = fig.add_subplot(gs[0, 4:6]); ax_d = fig.add_subplot(gs[1, 0:3]); ax_e = fig.add_subplot(gs[1, 3:6])
    panel_a(ax_a); panel_b(ax_b); panel_c(ax_c); _arm_dots(ax_d, RUN07, "Residual neural alignment (run 07)", (0.0305, 0.0385)); _arm_dots(ax_e, SEM, "Eight-task mean Spearman", (0.278, 0.313))
    S.panel(ax_a, "a", dx=-0.06)
    for ax, letter in ((ax_b, "b"), (ax_c, "c")): S.panel(ax, letter, dx=-0.26)
    for ax, letter in ((ax_d, "d"), (ax_e, "e")): S.panel(ax, letter, dx=-0.15)
    written = S.save(fig, args.out_prefix); print(json.dumps({"status":"ok","run_mean":float(RUNS.mean()), **written}, indent=2))


if __name__ == "__main__": main()
