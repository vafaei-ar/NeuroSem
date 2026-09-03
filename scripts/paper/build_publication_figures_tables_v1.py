#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "publication_figures_tables_v1" / "latest"
REPORTING_VALUES = ROOT / "outputs" / "manuscript_reporting_values_v1" / "latest" / "reporting_values.json"

BUILDERS = [
    ROOT / "scripts" / "paper" / "build_nmi_main_figures_v3_4.py",
    ROOT / "scripts" / "paper" / "build_manuscript_figures_v2.py",
    ROOT / "scripts" / "paper" / "build_regional_fmri_figures_tables_v1.py",
    ROOT / "scripts" / "paper" / "export_manuscript_reporting_values_v1.py",
]

EXPECTED = [
    ROOT / "outputs" / "nmi_main_figures_v3" / "latest" / "figure1.pdf",
    ROOT / "outputs" / "nmi_main_figures_v3" / "latest" / "figure2.pdf",
    ROOT / "outputs" / "nmi_main_figures_v3" / "latest" / "figure3.pdf",
    ROOT / "outputs" / "nmi_main_figures_v3" / "latest" / "figure4.pdf",
    ROOT / "outputs" / "nmi_main_figures_v3" / "latest" / "source_manifest.json",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "fig2_reading_reliability.pdf",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "fig4_ahba_frozen_molecular_nulls.pdf",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "fig4b_smn4lang_meg_reliability_boundary.pdf",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "table2_reliability_summary.csv",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "table3_ahba_gene_sets.csv",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "table4_smn4lang_meg_reliability_boundary.csv",
    ROOT / "outputs" / "manuscript_figures_v2" / "latest" / "source_manifest.json",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "figure_regional_fmri_transfer.pdf",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "figure_regional_fmri_transfer.svg",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "figure_regional_fmri_transfer.png",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "table_regional_language_parcels.csv",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "table_supplementary_dk68_phenotype.csv",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "figure_regional_fmri_transfer_caption.txt",
    ROOT / "outputs" / "regional_fmri_figures_tables_v1" / "latest" / "source_manifest.json",
    REPORTING_VALUES,
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_builder(path: Path) -> None:
    completed = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Publication builder failed: {path.relative_to(ROOT)} (exit {completed.returncode})")


def main() -> int:
    for builder in BUILDERS:
        if not builder.exists():
            raise FileNotFoundError(f"Missing builder: {builder.relative_to(ROOT)}")
        run_builder(builder)

    missing = [str(p.relative_to(ROOT)) for p in EXPECTED if not p.exists()]
    if missing:
        raise RuntimeError("Expected publication outputs missing after rebuild: " + ", ".join(missing))

    reporting_values = json.loads(REPORTING_VALUES.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "single-command reproducibility audit for current NeuroSem publication figures, tables, and manuscript reporting values",
        "builders": [str(p.relative_to(ROOT)) for p in BUILDERS],
        "builder_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in BUILDERS},
        "outputs_verified": {str(p.relative_to(ROOT)): sha256(p) for p in EXPECTED},
        "n_outputs_verified": len(EXPECTED),
        "manuscript_reporting_values": reporting_values,
        "guardrails": {
            "presentation_only": True,
            "no_model_training": True,
            "no_new_model_evaluation": True,
            "no_new_neural_analysis": True,
            "no_new_hypothesis_testing": True,
            "uses_completed_derived_outputs": True,
        },
    }
    json_path = OUT_DIR / "reproducibility_manifest.json"
    txt_path = OUT_DIR / "reproducibility_report.txt"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    txt_path.write_text(
        "NeuroSem publication figure/table reproducibility report\n"
        "Status: ok\n"
        f"Builders executed: {len(BUILDERS)}\n"
        f"Outputs verified: {len(EXPECTED)}\n"
        "Manuscript reporting values: embedded in reproducibility_manifest.json\n"
        "New analyses performed: 0\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "builders": len(BUILDERS), "outputs_verified": len(EXPECTED)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
