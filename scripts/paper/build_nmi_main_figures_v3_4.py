#!/usr/bin/env python3
"""Canonical main-figure entry point using the NMI v4 presentation-only system."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/paper/nmi_visualizations_v4/build_nmi_visualizations_v4.py"
V4_OUT = ROOT / "outputs/nmi_visualizations_v4/latest"
CANONICAL_OUT = ROOT / "outputs/nmi_main_figures_v3/latest"


def main() -> int:
    if not BUILDER.exists():
        raise FileNotFoundError(BUILDER)
    completed = subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"NMI v4 main-figure build failed with exit {completed.returncode}")

    CANONICAL_OUT.mkdir(parents=True, exist_ok=True)
    for stem in ("figure1", "figure2", "figure3", "figure4"):
        for ext in ("pdf", "svg", "png"):
            src = V4_OUT / f"{stem}.{ext}"
            if not src.exists():
                raise FileNotFoundError(src)
            shutil.copy2(src, CANONICAL_OUT / src.name)

    manifest_src = V4_OUT / "source_manifest.json"
    if not manifest_src.exists():
        raise FileNotFoundError(manifest_src)
    manifest = json.loads(manifest_src.read_text(encoding="utf-8"))
    manifest["canonical_output_dir"] = str(CANONICAL_OUT.relative_to(ROOT))
    manifest["canonical_entry_point"] = "scripts/paper/build_nmi_main_figures_v3_4.py"
    manifest["presentation_system"] = "NMI v4"
    (CANONICAL_OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
