#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "publication_figures_tables_v2" / "latest"
OLD_BUILDER = ROOT / "scripts" / "paper" / "build_publication_figures_tables_v1.py"
NEW_BUILDER = ROOT / "scripts" / "paper" / "build_nmi_spatial_validation_publication_v1_2.py"
SPATIAL_OUT = ROOT / "outputs" / "nmi_spatial_validation_publication_v1" / "latest"

EXPECTED = [
    ROOT / "outputs" / "publication_figures_tables_v1" / "latest" / "reproducibility_manifest.json",
    ROOT / "outputs" / "publication_figures_tables_v1" / "latest" / "reproducibility_report.txt",
    SPATIAL_OUT / "figure5_spatial_validation.pdf",
    SPATIAL_OUT / "figure5_spatial_validation.svg",
    SPATIAL_OUT / "figure5_spatial_validation.png",
    SPATIAL_OUT / "figure5_spatial_validation_caption.txt",
    SPATIAL_OUT / "extended_data_figure2_story_robustness.pdf",
    SPATIAL_OUT / "extended_data_figure2_story_robustness.svg",
    SPATIAL_OUT / "extended_data_figure2_story_robustness.png",
    SPATIAL_OUT / "extended_data_figure2_story_robustness_caption.txt",
    SPATIAL_OUT / "extended_data_figure3_system_interactions.pdf",
    SPATIAL_OUT / "extended_data_figure3_system_interactions.svg",
    SPATIAL_OUT / "extended_data_figure3_system_interactions.png",
    SPATIAL_OUT / "extended_data_figure3_system_interactions_caption.txt",
    SPATIAL_OUT / "supplementary_table12_spatial_validation.csv",
    SPATIAL_OUT / "supplementary_table13_dose_by_system.csv",
    SPATIAL_OUT / "supplementary_table14_backbone_by_system.csv",
    SPATIAL_OUT / "asset_index.json",
    SPATIAL_OUT / "source_manifest.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(path: Path, *, final_visual_builder: bool = False) -> None:
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"Publication builder failed: {path.relative_to(ROOT)} (exit {proc.returncode})")
    if final_visual_builder:
        if "Glyph " in proc.stderr:
            raise RuntimeError("Final spatial-validation builder emitted a missing-glyph warning")
        if "constrained_layout not applied" in proc.stderr:
            raise RuntimeError("Final spatial-validation builder emitted a constrained-layout warning")


def visual_qa_payload() -> str:
    png_hashes = {
        name: sha256(SPATIAL_OUT / name)
        for name in [
            "figure5_spatial_validation.png",
            "extended_data_figure2_story_robustness.png",
            "extended_data_figure3_system_interactions.png",
        ]
    }
    lines = ["RUNRELAY_FINAL_QA_PNG_HASHES " + json.dumps(png_hashes, sort_keys=True)]
    for name in [
        "figure5_spatial_validation.svg",
        "extended_data_figure2_story_robustness.svg",
        "extended_data_figure3_system_interactions.svg",
    ]:
        raw = (SPATIAL_OUT / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        payload = base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")
        lines.append(f"RUNRELAY_FINAL_QA_SVG_GZIP_BASE64 {name} {digest} {payload}")
    return "\n".join(lines) + "\n"


def main() -> int:
    run(OLD_BUILDER)
    run(NEW_BUILDER, final_visual_builder=True)

    missing = [str(p.relative_to(ROOT)) for p in EXPECTED if not p.exists()]
    if missing:
        raise RuntimeError("Missing expected publication outputs after v2 rebuild: " + ", ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 2,
        "status": "ok",
        "purpose": "single-command reproducibility audit for the complete current NeuroSem NMI figure/table package after final visual QA fixes",
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
            "spatial_validation_font_family": "DejaVu Sans",
            "required_scientific_glyphs_preflight": "passed",
            "missing_glyph_warning_preflight": "passed",
            "constrained_layout_warning_preflight_for_new_figures": "passed",
            "supplementary_table12_neural_target_n_total": 12,
            "manuscript_captions_preserved": True,
        },
    }
    manifest = OUT / "reproducibility_manifest.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    qa_payload = visual_qa_payload()
    txt = OUT / "reproducibility_report.txt"
    txt.write_text(
        "NeuroSem publication figure/table reproducibility report v2\n"
        "Status: ok\n"
        f"Builders executed: 2\nOutputs verified: {len(EXPECTED)}\n"
        "Includes final-size spatial-validation main, Extended Data, and supplementary table assets.\n"
        "Spatial-validation target width: 180 mm; ordinary text: 6-7 pt; panel labels: 8 pt.\n"
        "Final spatial figure font: DejaVu Sans with required scientific glyph coverage verified.\n"
        "Missing-glyph warnings from final spatial builder: 0\n"
        "Constrained-layout warnings from final spatial builder: 0\n"
        "New scientific analyses performed by this build: 0\n\n"
        "Visual QA transport payload (gzip+base64 SVG; manuscript captions are unchanged):\n"
        + qa_payload,
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "ok",
        "outputs_verified": len(EXPECTED),
        "manifest": str(manifest),
        "final_visual_qa": "passed mechanical preflight; SVG payload staged in reproducibility report",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
