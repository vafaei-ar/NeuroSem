#!/usr/bin/env python3
"""Build a fresh September-inclusive safe derived artifact bundle for NMI v1.18.

The bundle is presentation/provenance only. It collects hash-pinned aggregate summaries,
provenance ledgers and publication assets already present in the NeuroSem project. It does
not read raw neural data, participant-level restricted data, model weights or credentials.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/NMI_V117_CLAIM_MANIFEST_V1.json"
V2 = ROOT / "docs/NMI_V118_PROVENANCE_OVERLAY_V2.json"
V3 = ROOT / "docs/NMI_V118_FINAL_OVERLAY_V3.json"
DOC_MANIFEST = ROOT / "docs/NMI_V118_DOCUMENT_MANIFEST_V1.json"
OUT = ROOT / "outputs/nmi_v118_submission_bundle_v1/latest"

EXTRA_FILES = [
    ROOT / "outputs/nmi_v118_provenance_ledger_v1/latest/claim_to_source.csv",
    ROOT / "outputs/nmi_v118_provenance_ledger_v1/latest/output_to_manuscript.csv",
    ROOT / "outputs/nmi_v118_provenance_ledger_v1/latest/exceptions.csv",
    ROOT / "outputs/nmi_v118_provenance_ledger_v1/latest/source_manifest.csv",
    ROOT / "outputs/nmi_v118_provenance_ledger_v1/latest/summary.json",
    ROOT / "outputs/nmi_v118_provenance_ledger_v1/latest/report.txt",
    ROOT / "outputs/nmi_v118_run07_history_audit_v1/latest/history.csv",
    ROOT / "outputs/nmi_v118_run07_history_audit_v1/latest/summary.json",
    ROOT / "outputs/nmi_v118_run07_history_audit_v1/latest/report.txt",
    ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest/figure1.pdf",
    ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest/figure1.svg",
    ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest/figure1.png",
    ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest/source_manifest.json",
    ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest/report.txt",
    ROOT / "outputs/nmi_mpnet_model_space_comparison_v1/latest/report.txt",
    ROOT / "outputs/nmi_mpnet_model_space_comparison_v1/latest/seed_comparison_metrics.csv",
    ROOT / "outputs/nmi_mpnet_model_space_comparison_v1/latest/representation_metrics.csv",
    ROOT / "outputs/nmi_alternative_signal_e5_v1/latest/report.txt",
    ROOT / "outputs/nmi_alternative_signal_e5_v1/latest/seed_target_results.csv",
    ROOT / "outputs/nmi_forward_external_dose_characterization_v1/latest/dose_summary.csv",
    ROOT / "outputs/publication_figures_tables_v2/latest/reproducibility_manifest.json",
    ROOT / "outputs/publication_figures_tables_v2/latest/reproducibility_report.txt",
    ROOT / "outputs/nmi_main_figures_v3/latest/source_manifest.json",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure1.pdf",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure1.svg",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure1.png",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure2.pdf",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure2.svg",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure3.pdf",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure3.svg",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure4.pdf",
    ROOT / "outputs/nmi_main_figures_v3/latest/figure4.svg",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/figure5_spatial_validation.pdf",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/figure5_spatial_validation.svg",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/extended_data_figure2_story_robustness.pdf",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/extended_data_figure2_story_robustness.svg",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/extended_data_figure3_system_interactions.pdf",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/extended_data_figure3_system_interactions.svg",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/supplementary_table12_spatial_validation.csv",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/supplementary_table13_dose_by_system.csv",
    ROOT / "outputs/nmi_spatial_validation_publication_v1/latest/supplementary_table14_backbone_by_system.csv",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def merged_sources() -> dict[str, dict]:
    base = load(BASE)
    v2 = load(V2)
    v3 = load(V3)
    out = {k: dict(v) for k, v in base["sources"].items()}
    for key, patch in v2.get("source_overrides", {}).items():
        out[key].update(patch)
    for key, rec in v2.get("source_additions", {}).items():
        out[key] = dict(rec)
    for key, rec in v3.get("source_additions", {}).items():
        out[key] = dict(rec)
    return out


def main() -> int:
    sources = merged_sources()
    paths = [ROOT / rec["path"] for rec in sources.values()]
    paths.extend([BASE, V2, V3, DOC_MANIFEST])
    paths.extend(EXTRA_FILES)
    unique = []
    seen = set()
    for path in paths:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key); unique.append(path)

    missing = [str(p.relative_to(ROOT)) for p in unique if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing v1.18 bundle inputs: " + ", ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    zip_path = OUT / "NeuroSem_NMI_v1.18_safe_derived_bundle.zip"
    rows = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(unique, key=lambda p: str(p.relative_to(ROOT))):
            rel = str(path.relative_to(ROOT))
            data = path.read_bytes()
            info = zipfile.ZipInfo(rel, date_time=(2026, 9, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
            rows.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})

    manifest = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "Fresh September-inclusive NMI v1.18 safe derived artifact bundle",
        "bundle": str(zip_path.relative_to(ROOT)),
        "bundle_sha256": sha256(zip_path),
        "n_files": len(rows),
        "files": rows,
        "source_keys": sorted(sources),
        "guardrails": {
            "raw_neural_data_included": False,
            "participant_identifiers_intentionally_included": False,
            "model_weights_included": False,
            "credentials_or_environment_files_included": False,
            "document_bytes_included": False,
            "document_hash_manifest_included": True,
            "september_provenance_and_postconfirmatory_outputs_included": True,
        },
    }
    manifest_path = OUT / "bundle_manifest.json"
    report_path = OUT / "report.txt"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(
        "NeuroSem NMI v1.18 safe derived submission bundle\n"
        "Status: ok\n"
        f"Files: {len(rows)}\n"
        f"Bundle SHA256: {manifest['bundle_sha256']}\n"
        "Scope: aggregate/hash-pinned scientific sources, provenance ledgers, Figure 1 provenance, September post-confirmatory summaries and final publication assets.\n"
        "DOCX bytes are not included in this public-repository-derived bundle; exact DOCX hashes and QA state are recorded in docs/NMI_V118_DOCUMENT_MANIFEST_V1.json.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "ok", "n_files": len(rows), "bundle": str(zip_path), "bundle_sha256": manifest["bundle_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
