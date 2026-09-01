#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.lines import Line2D


def load_v33():
    path = Path(__file__).with_name("build_nmi_main_figures_v3_3.py")
    spec = importlib.util.spec_from_file_location("neurosem_nmi_figures_v33", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    v33 = load_v33()
    original_load_v3 = v33.load_v3
    original_set_title = Axes.set_title

    def patched_set_title(self, label, *args, **kwargs):
        if label == "Neural geometry is learnable across held-out runs":
            label = "Neural geometry is learnable\nacross held-out runs"
            kwargs.setdefault("linespacing", 1.0)
        return original_set_title(self, label, *args, **kwargs)

    def patched_load_v3():
        m = original_load_v3()
        original_save_figure = m.save_figure

        def save_figure(fig, out_dir, stem):
            if stem == "figure4":
                handles = [
                    Line2D(
                        [0], [0], marker="o", linestyle="None", markersize=4.4,
                        markerfacecolor=m.GRAY, markeredgecolor="white",
                        markeredgewidth=0.35, label="Individual seed",
                    ),
                    Line2D(
                        [0], [0], marker="o", linestyle="None", markersize=5.8,
                        markerfacecolor="white", markeredgecolor=m.GRAY,
                        markeredgewidth=1.1, label="3-seed mean",
                    ),
                ]
                fig.legend(
                    handles=handles,
                    loc="lower center",
                    bbox_to_anchor=(0.555, 0.012),
                    ncol=2,
                    frameon=False,
                    fontsize=6.3,
                    handletextpad=0.45,
                    columnspacing=1.1,
                    borderaxespad=0.0,
                )
            return original_save_figure(fig, out_dir, stem)

        m.save_figure = save_figure
        return m

    v33.load_v3 = patched_load_v3
    Axes.set_title = patched_set_title
    try:
        rc = v33.main()
    finally:
        Axes.set_title = original_set_title

    manifest_path = Path("outputs/nmi_main_figures_v3/latest/source_manifest.json").resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["analysis"] = "NMI main figures v3.4"
    fixes = manifest.setdefault("qa_fixes", [])
    for fix in [
        "Figure 1 panel-c title wrapped to prevent c/d heading collision",
        "Figure 4 marker key explicitly distinguishes individual seeds from 3-seed means",
    ]:
        if fix not in fixes:
            fixes.append(fix)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
