#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "publication_figures_tables_v2" / "latest"
OLD_BUILDER = ROOT / "scripts" / "paper" / "build_publication_figures_tables_v1.py"
NEW_BUILDER = ROOT / "scripts" / "paper" / "build_nmi_spatial_validation_publication_v1_1.py"

EXPECTED = [
    ROOT / "outputs" / "publication_figures_tables_v1" / "latest" / "reproducibility_manifest.json",
    ROOT / "outputs" / "publication_figures_tables_v1" / "latest" / "reproducibility_report.txt",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "figure5_spatial_validation.pdf",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "figure5_spatial_validation.svg",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "figure5_spatial_validation.png",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "figure5_spatial_validation_caption.txt",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure2_story_robustness.pdf",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure2_story_robustness.svg",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure2_story_robustness.png",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure2_story_robustness_caption.txt",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure3_system_interactions.pdf",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure3_system_interactions.svg",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure3_system_interactions.png",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "extended_data_figure3_system_interactions_caption.txt",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "supplementary_table12_spatial_validation.csv",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "supplementary_table13_dose_by_system.csv",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "supplementary_table14_backbone_by_system.csv",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "asset_index.json",
    ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest" / "source_manifest.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(path: Path) -> None:
    proc = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Publication builder failed: {path.relative_to(ROOT)} (exit {proc.returncode})")


def main() -> int:
    for builder in [OLD_BUILDER, NEW_BUILDER]:
        if not builder.exists():
            raise FileNotFoundError(builder)
        run(builder)

    missing = [str(p.relative_to(ROOT)) for p in EXPECTED if not p.exists()]
    if missing:
        raise RuntimeError("Missing expected publication outputs after v2 rebuild: " + ", ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 2,
        "status": "ok",
        "purpose": "single-command reproducibility audit for the complete current NeuroSem NMI figure/table package, including final-size spatial-validation assets",
        "builders": [str(OLD_BUILDER.relative_to(ROOT)), str(NEW_BUILDER.relative_to(ROOT))],
        "builder_sha256": {
            str(OLD_BUILDER.relative_to(ROOT)): sha256(OLD_BUILDER),
            str(NEW_BUILDER.relative_to(ROOT)): sha256(NEW_BUILDER),
        },
        "outputs_verified": {str(p.relative_to(ROOT)): sha256(p) for p in EXPECTED},
        "n_outputs_verified": len(EXPECTED),
        "guardrails": {
            "presentation_only": True,
            "no_model_training": True,
            "no_new_model_evaluation": True,
            "no_new_neural_analysis": True,
            "no_new_hypothesis_testing": True,
            "uses_completed_frozen_derived_outputs": True,
            "spatial_validation_target_width_mm": 180,
            "spatial_validation_ordinary_text_pt": "6-7",
            "spatial_validation_panel_label_pt": 8,
        },
    }
    manifest = OUT / "reproducibility_manifest.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    txt = OUT / "reproducibility_report.txt"
    txt.write_text(
        "NeuroSem publication figure/table reproducibility report v2\n"
        "Status: ok\n"
        f"Builders executed: 2\nOutputs verified: {len(EXPECTED)}\n"
        "Includes final-size spatial-validation main, Extended Data, and supplementary table assets.\n"
        "Spatial-validation target width: 180 mm; ordinary text: 6-7 pt; panel labels: 8 pt.\n"
        "New scientific analyses performed by this build: 0\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "outputs_verified": len(EXPECTED), "manifest": str(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
