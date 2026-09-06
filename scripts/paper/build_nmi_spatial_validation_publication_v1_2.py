#!/usr/bin/env python3
"""Final presentation-only QA wrapper for frozen NMI spatial-validation assets.

Preserves all scientific inputs, estimands and inferential results. This wrapper
only fixes final-render typography/annotation issues detected during visual QA:
(1) use a sans-serif font with complete glyph coverage for the scientific labels,
(2) report the near-threshold language-sensorimotor P value at four decimals, and
(3) move the spatial-null annotation away from the negative observed-magnitude line.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.ft2font import FT2Font

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "scripts" / "paper" / "build_nmi_spatial_validation_publication_v1_1.py"
OUT = ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest"
FINAL_FONT = "DejaVu Sans"
REQUIRED_GLYPHS = "Δλ×−⁻³"


def load_base():
    spec = importlib.util.spec_from_file_location("neurosem_nmi_spatial_validation_v1_1", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load base presentation wrapper: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_font_coverage() -> str:
    props = font_manager.FontProperties(family=[FINAL_FONT])
    path = font_manager.findfont(props, fallback_to_default=False)
    cmap = FT2Font(path).get_charmap()
    missing = [ch for ch in REQUIRED_GLYPHS if ord(ch) not in cmap]
    if missing:
        raise RuntimeError(f"{FINAL_FONT} is missing required figure glyphs: {missing}")
    return path


def main() -> int:
    font_path = assert_font_coverage()
    wrapper = load_base()

    # The workstation's Nimbus Sans and Liberation Sans lack U+207B SUPERSCRIPT
    # MINUS. DejaVu Sans has complete coverage for the labels used here, avoiding
    # silent missing-glyph boxes in raster exports while remaining sans-serif.
    wrapper.preferred_sans = lambda: FINAL_FONT

    original_load = wrapper.load_base

    def patched_load_base():
        base = original_load()

        # Preserve exact P values around the conventional 0.05 boundary instead
        # of rounding 0.0498046875 to the visually ambiguous "0.050".
        def fmt_p(p: float) -> str:
            if p < 1e-4:
                return f"{p:.2e}"
            if p < 0.1:
                return f"{p:.4f}"
            return f"{p:.3f}"

        base.fmt_p = fmt_p
        return base

    wrapper.load_base = patched_load_base

    original_text = Axes.text

    def qa_text(self, x, y, s, *args, **kwargs):
        # Panel c's dashed line at the negative observed magnitude crossed the
        # top-left annotation in the inspected final-size render. Move only that
        # annotation inward; no data or axes change.
        if isinstance(s, str) and "Spatial-surrogate P=" in s:
            x = 0.24
        return original_text(self, x, y, s, *args, **kwargs)

    Axes.text = qa_text
    try:
        rc = int(wrapper.main())
    finally:
        Axes.text = original_text

    if rc != 0:
        return rc

    manifest_path = OUT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["final_visual_qa_wrapper"] = str(Path(__file__).resolve().relative_to(ROOT))
    manifest["final_visual_qa_adjustments"] = {
        "scientific_values_changed": False,
        "font_family": FINAL_FONT,
        "font_file_basename": Path(font_path).name,
        "required_glyphs_verified": REQUIRED_GLYPHS,
        "near_threshold_p_display_four_decimals": True,
        "spatial_null_annotation_repositioned": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "presentation_only": True,
        "font_family": FINAL_FONT,
        "required_glyphs_verified": REQUIRED_GLYPHS,
        "spatial_null_annotation_repositioned": True,
        "near_threshold_p_display_four_decimals": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
