#!/usr/bin/env python3
"""Model-blind feasibility audit for an AHBA-to-ChineseEEG forward model.

This script never opens EEG signal samples and never computes NeuroSem, model, or
gene-expression outcomes. It checks whether the already-frozen ChineseEEG spatial
metadata can support a defensible template-MRI EEG forward model and records the
remaining registration choices that must be frozen before constructing a 128 x G
molecular-sensitivity matrix.
"""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
from pathlib import Path


def pkg_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--preflight-summary",
        type=Path,
        default=Path("outputs/ahba_chineseeeg_preflight_v1/latest/summary.json"),
    )
    ap.add_argument(
        "--spatial-inventory",
        type=Path,
        default=Path("outputs/ahba_chineseeeg_preflight_v1/latest/spatial_metadata_inventory.csv"),
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/ahba_forward_model_feasibility_v1/latest"),
    )
    args = ap.parse_args()

    preflight = json.loads(args.preflight_summary.read_text(encoding="utf-8"))
    inventory = read_csv(args.spatial_inventory)

    electrode_rows = [r for r in inventory if r.get("kind") == "electrodes"]
    coordsystem_rows = [r for r in inventory if r.get("kind") == "coordsystem"]
    channel_rows = [r for r in inventory if r.get("kind") == "channels"]

    exact_128 = [r for r in electrode_rows if int(r.get("n_rows_with_finite_xyz") or 0) == 128]
    coordinate_systems = sorted({r.get("eeg_coordinate_system", "").strip() for r in coordsystem_rows if r.get("eeg_coordinate_system", "").strip()})
    coordinate_units = sorted({r.get("eeg_coordinate_units", "").strip() for r in coordsystem_rows if r.get("eeg_coordinate_units", "").strip()})
    eeg_128 = [r for r in channel_rows if int(r.get("n_eeg_channels") or 0) == 128]

    try:
        import mne
        mne_import_ok = True
        fetch_fsaverage_available = hasattr(mne.datasets, "fetch_fsaverage")
        make_forward_available = hasattr(mne, "make_forward_solution")
        coreg_available = hasattr(mne, "coreg") and hasattr(mne.coreg, "Coregistration")
    except Exception:
        mne_import_ok = False
        fetch_fsaverage_available = False
        make_forward_available = False
        coreg_available = False

    # A measured CapTrak montage is head-space geometry. MNE's built-in
    # trans='fsaverage' shortcut is appropriate only when electrodes are already
    # represented in fsaverage/MNI space. We therefore do not silently apply it.
    measured_head_geometry = any("captrak" in s.lower() for s in coordinate_systems)
    exact_spatial_gate = bool(exact_128 and eeg_128 and coordinate_units)

    blockers = []
    if not exact_spatial_gate:
        blockers.append("Exact 128-channel measured spatial metadata is incomplete.")
    if not mne_import_ok or not make_forward_available:
        blockers.append("MNE forward-model support is unavailable in the project environment.")
    if measured_head_geometry and not coreg_available:
        blockers.append("Measured head-space CapTrak coordinates require an explicit head-to-template registration path, but MNE Coregistration support is unavailable.")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    decision = {
        "schema_version": 1,
        "analysis": "model-blind AHBA forward-model feasibility audit",
        "loads_eeg_samples": False,
        "downloads_fsaverage": False,
        "downloads_ahba": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_expression_outcomes": False,
        "software": {
            "mne": pkg_version("mne"),
            "nibabel": pkg_version("nibabel"),
            "abagen": pkg_version("abagen"),
        },
        "preflight_gate": preflight.get("preflight_gate", {}),
        "exact_128_coordinate_files": len(exact_128),
        "exact_128_eeg_channel_files": len(eeg_128),
        "coordinate_systems": coordinate_systems,
        "coordinate_units": coordinate_units,
        "mne_capabilities": {
            "import_ok": mne_import_ok,
            "fetch_fsaverage_available": fetch_fsaverage_available,
            "make_forward_solution_available": make_forward_available,
            "coregistration_available": coreg_available,
        },
        "measured_head_geometry_detected": measured_head_geometry,
        "template_forward_model_feasible": len(blockers) == 0,
        "blockers": blockers,
        "frozen_guardrails": [
            "Use measured ChineseEEG CapTrak coordinates rather than replacing them with a standard montage.",
            "Do not use trans='fsaverage' merely because fsaverage is the template; measured head-space electrodes require explicit coregistration to template anatomy.",
            "Do not open EEG signal samples or any NeuroSem/model outcome while choosing the registration, source space, BEM, reference, orientation, or sensitivity metric.",
            "Do not construct molecular weights until the forward-model convention is frozen and reproducible.",
        ],
        "next_freeze_items": [
            "Freeze the head-to-fsaverage registration procedure using measured fiducials/head-shape metadata where available.",
            "Freeze the fsaverage cortical source space and BEM resolution.",
            "Freeze EEG reference handling for forward/inverse compatibility.",
            "Freeze lead-field orientation reduction and channel-sensitivity normalization.",
            "Render/inspect sensor-to-head alignment before computing any molecular sensitivity matrix.",
        ],
    }

    (out / "summary.json").write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok" if not blockers else "blocked",
        "template_forward_model_feasible": decision["template_forward_model_feasible"],
        "blockers": blockers,
    }, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
