#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "publication_figures_tables_v2" / "latest"
OLD_BUILDER = ROOT / "scripts" / "paper" / "build_publication_figures_tables_v1.py"
NEW_BUILDER = ROOT / "scripts" / "paper" / "build_nmi_spatial_validation_publication_v1_2.py"
REDESIGN_BUILDER = ROOT / "scripts" / "paper" / "build_nmi_figure5_redesign_v1.py"
REDESIGN_OUT = ROOT / "outputs" / "nmi_figure5_redesign_v1" / "latest"
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


def install_redesigned_figure5() -> None:
    for ext in ("pdf", "svg", "png"):
        src = REDESIGN_OUT / f"figure5.{ext}"
        dst = SPATIAL_OUT / f"figure5_spatial_validation.{ext}"
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, dst)
    caption = (
        "Figure 5 | Post-confirmatory spatial expression of fMRI transfer. "
        "a, Complete bilateral DK68 mean neural-guided minus text-only residual-RSA phenotype at lambda=0.10 "
        "rendered on the standard fsaverage inflated cortical surface. All 68 parcel means were positive. The map "
        "is unthresholded and is a spatial characterization, not a 68-region significance screen. "
        "b, Participant-level mean DeltaRSA for the six predefined functional language parcels and fixed "
        "left-hemisphere sensorimotor and visual controls. Thin lines connect the same participant; large markers "
        "show group means. The two predefined language-versus-control contrasts use exact max-statistic family-wise "
        "correction. c, Participant-level functional frontal and temporal language-system DeltaRSA; the temporal-minus-"
        "frontal contrast uses the frozen five-test spatial-extension family. d, Null distribution from 10,000 "
        "centroid-distance, variogram-matched left-DK spatial surrogates for the reliability-adjusted language "
        "coefficient. The orange line marks the observed coefficient and the dashed line its negative magnitude; "
        "this is a spatial-autocorrelation-aware surrogate test, not a surface-sphere spin test. e, Participant-level "
        "language specificity after averaging the three prespecified reviewer seeds for genuine and shuffled neural-"
        "target guidance. Genuine guidance exceeded shuffled guidance under the frozen two-test family. All spatial "
        "analyses are post-confirmatory."
    )
    (SPATIAL_OUT / "figure5_spatial_validation_caption.txt").write_text(caption + "\n", encoding="utf-8")


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
    run(REDESIGN_BUILDER)
    install_redesigned_figure5()

    missing = [str(p.relative_to(ROOT)) for p in EXPECTED if not p.exists()]
    if missing:
        raise RuntimeError("Missing expected publication outputs after v2 rebuild: " + ", ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    builders = [OLD_BUILDER, NEW_BUILDER, REDESIGN_BUILDER]
    report = {
        "schema_version": 3,
        "status": "ok",
        "purpose": "single-command reproducibility audit for the complete current NeuroSem NMI figure/table package, including the anatomically rendered Figure 5 redesign",
        "builders": [str(p.relative_to(ROOT)) for p in builders],
        "builder_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in builders},
        "outputs_verified": {str(p.relative_to(ROOT)): sha256(p) for p in EXPECTED},
        "n_outputs_verified": len(EXPECTED),
        "redesigned_figure5_source_manifest": str((REDESIGN_OUT / "source_manifest.json").relative_to(ROOT)),
        "redesigned_figure5_source_manifest_sha256": sha256(REDESIGN_OUT / "source_manifest.json"),
        "guardrails": {
            "presentation_only": True,
            "no_model_training": True,
            "no_new_model_evaluation": True,
            "no_new_neural_analysis": True,
            "no_new_hypothesis_testing": True,
            "uses_completed_frozen_derived_outputs": True,
            "dk68_surface_complete_unthresholded": True,
            "fsaverage_used_as_visualization_scaffold_only": True,
            "spatial_validation_target_width_mm": 183,
            "spatial_validation_ordinary_text_pt": "5.4-7",
            "spatial_validation_panel_label_pt": 8,
            "supplementary_table12_neural_target_n_total": 12,
        },
    }
    manifest = OUT / "reproducibility_manifest.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    qa_payload = visual_qa_payload()
    txt = OUT / "reproducibility_report.txt"
    txt.write_text(
        "NeuroSem publication figure/table reproducibility report v2\n"
        "Status: ok\n"
        f"Builders executed: {len(builders)}\nOutputs verified: {len(EXPECTED)}\n"
        "Includes the cortical Figure 5 redesign plus the existing frozen Extended Data and supplementary assets.\n"
        "New scientific analyses performed by this build: 0\n\n"
        "Visual QA transport payload (gzip+base64 SVG):\n"
        + qa_payload,
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "ok",
        "outputs_verified": len(EXPECTED),
        "manifest": str(manifest),
        "figure5_redesign_installed": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
