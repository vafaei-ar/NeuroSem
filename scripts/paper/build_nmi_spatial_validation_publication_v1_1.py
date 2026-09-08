#!/usr/bin/env python3
"""Presentation-only compliance wrapper for the frozen NMI spatial-validation assets.

This wrapper preserves every scientific input, estimand and inferential result from
build_nmi_spatial_validation_publication_v1.py. It only standardizes final physical
size/typography and completes participant denominators in Supplementary Table 12.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from matplotlib import font_manager
from matplotlib.axes import Axes
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "scripts" / "paper" / "build_nmi_spatial_validation_publication_v1.py"
OUT = ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest"
MM = 1.0 / 25.4
FIGURE_WIDTH_MM = 180.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("neurosem_nmi_spatial_validation_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load base builder: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preferred_sans() -> str:
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Arial", "Helvetica", "Nimbus Sans", "Liberation Sans"):
        if name in available:
            return name
    return "DejaVu Sans"


def main() -> int:
    base = load_base()

    # Nature/NMI-oriented final-size typography: ordinary figure text 5-7 pt,
    # with 8-pt bold lowercase panel labels kept separate from panel titles.
    def configure_style() -> None:
        font = preferred_sans()
        base.plt.rcParams.update({
            "font.family": "sans-serif",
            "font.sans-serif": [font, "DejaVu Sans"],
            "font.size": 7,
            "axes.titlesize": 7,
            "axes.labelsize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 6,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.bbox": None,
            "savefig.pad_inches": 0.01,
        })

    base.configure_style = configure_style

    # Preserve an exact 180-mm canvas. bbox_inches='tight' can silently change
    # physical figure dimensions, so publication export intentionally omits it.
    def save_figure(fig, stem: str):
        paths = []
        for ext, kwargs in [("pdf", {}), ("svg", {}), ("png", {"dpi": 600})]:
            path = OUT / f"{stem}.{ext}"
            fig.savefig(path, **kwargs)
            paths.append(path)
        return paths

    base.save_figure = save_figure

    original_figure = base.plt.figure
    original_subplots = base.plt.subplots
    size_map = {
        (7.2, 6.5): (FIGURE_WIDTH_MM * MM, 162.5 * MM),
        (7.2, 3.25): (FIGURE_WIDTH_MM * MM, 81.25 * MM),
        (7.2, 3.45): (FIGURE_WIDTH_MM * MM, 86.25 * MM),
    }

    def mapped_figsize(figsize):
        if figsize is None:
            return None
        key = tuple(float(x) for x in figsize)
        for old, new in size_map.items():
            if all(abs(a - b) < 1e-9 for a, b in zip(key, old)):
                return new
        return figsize

    def figure(*args, **kwargs):
        if "figsize" in kwargs:
            kwargs["figsize"] = mapped_figsize(kwargs["figsize"])
        return original_figure(*args, **kwargs)

    def subplots(*args, **kwargs):
        if "figsize" in kwargs:
            kwargs["figsize"] = mapped_figsize(kwargs["figsize"])
        return original_subplots(*args, **kwargs)

    base.plt.figure = figure
    base.plt.subplots = subplots

    original_set_title = Axes.set_title
    original_text = Axes.text

    def panel_title(self, label, *args, **kwargs):
        if isinstance(label, str) and len(label) >= 3 and label[0].islower() and label[1:3] == "  ":
            panel = label[0]
            label = label[3:]
            original_text(
                self, -0.10, 1.03, panel,
                transform=self.transAxes,
                fontsize=8,
                fontweight="bold",
                fontstyle="normal",
                ha="left",
                va="top",
                clip_on=False,
            )
            kwargs["fontsize"] = 7
        return original_set_title(self, label, *args, **kwargs)

    def text(self, x, y, s, *args, **kwargs):
        if s == "*" and float(kwargs.get("fontsize", 8)) > 8:
            kwargs["fontsize"] = 8
        return original_text(self, x, y, s, *args, **kwargs)

    Axes.set_title = panel_title
    Axes.text = text

    original_build_tables = base.build_tables

    def build_tables(lang_summary, spatial_summary, final_summary, dose, backbone):
        paths = original_build_tables(lang_summary, spatial_summary, final_summary, dose, backbone)
        table12 = OUT / "supplementary_table12_spatial_validation.csv"
        frame = base.pd.read_csv(table12, dtype=str, keep_default_na=False)
        dose_n = int(final_summary["hierarchical_synthesis"]["dose_by_system"]["n_subject_clusters"])
        backbone_n = int(final_summary["hierarchical_synthesis"]["backbone_by_system"]["n_subject_clusters"])
        if dose_n != backbone_n or dose_n != 12:
            raise RuntimeError(f"Unexpected participant denominator for validation table: {dose_n}, {backbone_n}")
        mask = frame["family"].eq("Neural-target specificity")
        if int(mask.sum()) != 2:
            raise RuntimeError("Expected exactly two neural-target-specificity rows")
        frame.loc[mask, "n_total"] = str(dose_n)
        frame.to_csv(table12, index=False)
        return paths

    base.build_tables = build_tables

    try:
        rc = int(base.main())
    finally:
        Axes.set_title = original_set_title
        Axes.text = original_text
        base.plt.figure = original_figure
        base.plt.subplots = original_subplots

    if rc != 0:
        return rc

    # Mechanical canvas preflight using the canonical 600-dpi raster exports.
    expected_width_px = round(FIGURE_WIDTH_MM / 25.4 * 600)
    pngs = [
        OUT / "figure5_spatial_validation.png",
        OUT / "extended_data_figure2_story_robustness.png",
        OUT / "extended_data_figure3_system_interactions.png",
    ]
    raster_preflight = {}
    for path in pngs:
        with Image.open(path) as image:
            if abs(image.width - expected_width_px) > 1:
                raise RuntimeError(
                    f"Unexpected raster width for {path.name}: {image.width}px; expected {expected_width_px}px"
                )
            raster_preflight[path.name] = {
                "width_px": image.width,
                "height_px": image.height,
                "target_width_mm": FIGURE_WIDTH_MM,
                "export_dpi": 600,
            }

    manifest_path = OUT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["presentation_wrapper"] = str(Path(__file__).resolve().relative_to(ROOT))
    manifest["presentation_wrapper_sha256"] = sha256(Path(__file__).resolve())
    manifest["presentation_adjustments"] = {
        "scientific_values_changed": False,
        "target_figure_width_mm": FIGURE_WIDTH_MM,
        "ordinary_text_pt": "6-7",
        "panel_label_pt": 8,
        "pdf_fonttype": 42,
        "svg_text_editable": True,
        "bbox_tight_disabled_to_preserve_physical_canvas": True,
        "supplementary_table12_neural_target_n_total": 12,
        "raster_preflight": raster_preflight,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "presentation_only": True,
        "figure_width_mm": FIGURE_WIDTH_MM,
        "ordinary_text_pt": "6-7",
        "panel_label_pt": 8,
        "supplementary_table12_neural_target_n_total": 12,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
