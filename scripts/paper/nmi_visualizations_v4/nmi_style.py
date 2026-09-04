#!/usr/bin/env python3
"""Shared Nature-Portfolio-compliant style for NeuroSem manuscript figures."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

MM = 1.0 / 25.4
W1 = 89.0
W15 = 120.0
W2 = 183.0

INK = "#1a1a1a"
GREY = "#6e6e6e"
GREY_L = "#b8b8b8"
GREY_XL = "#e4e4e4"
BLUE = "#2166ac"
ORANGE = "#d6604d"
TEAL = "#35978f"
PURPLE = "#762a83"
ZERO = "#8c8c8c"
DIVERGING = "RdBu_r"


def _pick_font() -> str:
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Arial", "Helvetica", "Nimbus Sans", "Liberation Sans"):
        if name in have:
            return name
    return "DejaVu Sans"


def apply() -> None:
    f = _pick_font()
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [f, "DejaVu Sans"],
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "figure.titlesize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.titlelocation": "left",
        "axes.titlepad": 3.0,
        "axes.axisbelow": True,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.2,
        "ytick.major.size": 2.2,
        "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "lines.linewidth": 1.0,
        "lines.markersize": 3.0,
        "lines.markeredgewidth": 0.0,
        "legend.frameon": False,
        "legend.handlelength": 1.2,
        "legend.handletextpad": 0.5,
        "legend.borderpad": 0.0,
        "legend.labelspacing": 0.3,
        "legend.columnspacing": 1.0,
        "grid.color": GREY_XL,
        "grid.linewidth": 0.5,
        "text.color": INK,
        "figure.dpi": 200,
        "savefig.dpi": 600,
        "savefig.bbox": None,
        "savefig.pad_inches": 0.01,
        "savefig.transparent": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def figure(width_mm: float, height_mm: float, **gridspec):
    fig = plt.figure(figsize=(width_mm * MM, height_mm * MM), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.06, hspace=0.06)
    if gridspec:
        axes = fig.subplots(**gridspec)
        return fig, axes
    return fig


def panel(ax, letter: str, dx: float = -0.22, dy: float = 1.10) -> None:
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=8,
            fontweight="bold", va="top", ha="left", clip_on=False)


def zeroline(ax, orient: str = "h") -> None:
    kw = dict(color=ZERO, lw=0.6, zorder=0)
    ax.axhline(0, **kw) if orient == "h" else ax.axvline(0, **kw)


def annotate(ax, text: str, loc: str = "lower right", **kw) -> None:
    pos = {
        "lower right": (0.98, 0.03, "right", "bottom"),
        "lower left": (0.02, 0.03, "left", "bottom"),
        "upper right": (0.98, 0.97, "right", "top"),
        "upper left": (0.02, 0.97, "left", "top"),
    }[loc]
    ax.text(pos[0], pos[1], text, transform=ax.transAxes, ha=pos[2], va=pos[3],
            fontsize=6, color=GREY, linespacing=1.35, **kw)


def offset_ticks(ax, axis: str = "both") -> None:
    if axis in ("x", "both"):
        ticks = [t for t in ax.get_xticks() if ax.get_xlim()[0] <= t <= ax.get_xlim()[1]]
        if ticks:
            ax.spines["bottom"].set_bounds(min(ticks), max(ticks))
    if axis in ("y", "both"):
        ticks = [t for t in ax.get_yticks() if ax.get_ylim()[0] <= t <= ax.get_ylim()[1]]
        if ticks:
            ax.spines["left"].set_bounds(min(ticks), max(ticks))


def flowbox(ax, x, y, w, h, text, fs=6, fc="white", ec=None, lw=0.6):
    from matplotlib.patches import FancyBboxPatch
    ec = INK if ec is None else ec
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=lw, edgecolor=ec, facecolor=fc,
                                mutation_aspect=1.0, clip_on=False, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, linespacing=1.4, zorder=3)


def arrow(ax, xy_from, xy_to, lw=0.6, color=None):
    color = INK if color is None else color
    ax.annotate("", xy=xy_to, xytext=xy_from,
                arrowprops=dict(arrowstyle="-|>", lw=lw, color=color,
                                shrinkA=1.5, shrinkB=1.5, mutation_scale=6), zorder=1)


def schematic(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def save(fig, out_prefix, png: bool = True, svg: bool = True) -> dict:
    from pathlib import Path
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    written = {}
    pdf = str(out_prefix) + ".pdf"
    fig.savefig(pdf)
    written["pdf"] = pdf
    if svg:
        s = str(out_prefix) + ".svg"
        fig.savefig(s)
        written["svg"] = s
    if png:
        p = str(out_prefix) + ".png"
        fig.savefig(p, dpi=600)
        written["png"] = p
    plt.close(fig)
    return written
