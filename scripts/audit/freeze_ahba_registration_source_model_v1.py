#!/usr/bin/env python3
"""Model-blind freeze audit for the AHBA/ChineseEEG registration and source model.

This script uses only ChineseEEG spatial metadata plus template-anatomy resources.
It never opens EEG signal samples, downloads AHBA, loads model quantities, or
computes NeuroSem / gene-expression outcomes.

The goal is to freeze all source-model conventions that can be defended before
molecular weighting, and to fail closed if the measured CapTrak geometry lacks
sufficient registration information.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

FID_ALIASES = {
    "nasion": {"nasion", "nas", "nz", "fidnz"},
    "lpa": {"lpa", "leftpreauricular", "leftauricular", "fidt9"},
    "rpa": {"rpa", "rightpreauricular", "rightauricular", "fidt10"},
}


def git_lines(root: Path, *args: str) -> list[str]:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        return []
    return [x for x in cp.stdout.splitlines() if x.strip()]


def annex_get_small(root: Path, rel: str) -> bool:
    p = root / rel
    if p.exists() and p.is_file() and p.stat().st_size > 0:
        return True
    cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True, check=False)
    return cp.returncode == 0 and p.exists() and p.is_file() and p.stat().st_size > 0


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def finite_xyz(row: dict[str, str]) -> tuple[float, float, float] | None:
    try:
        xyz = tuple(float(row[k]) for k in ("x", "y", "z"))
    except Exception:
        return None
    return xyz if all(math.isfinite(v) for v in xyz) else None


def norm_name(v: str) -> str:
    return "".join(ch for ch in v.lower() if ch.isalnum())


def sha_rows(rows: list[dict[str, str]]) -> str:
    payload = []
    for r in rows:
        xyz = finite_xyz(r)
        if xyz is None:
            continue
        payload.append([str(r.get("name", "")), *[round(x, 9) for x in xyz]])
    return hashlib.sha256(json.dumps(payload, sort_keys=False).encode("utf-8")).hexdigest()


def extract_fiducials_from_json(d: dict) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for key in ("AnatomicalLandmarkCoordinates", "FiducialsCoordinates", "FiducialCoordinates"):
        value = d.get(key)
        if not isinstance(value, dict):
            continue
        for raw_name, xyz in value.items():
            n = norm_name(str(raw_name))
            for canonical, aliases in FID_ALIASES.items():
                if n in aliases and isinstance(xyz, (list, tuple)) and len(xyz) == 3:
                    try:
                        vals = [float(x) for x in xyz]
                    except Exception:
                        continue
                    if all(math.isfinite(x) for x in vals):
                        out[canonical] = vals
    return out


def extract_fiducials_from_electrodes(rows: list[dict[str, str]]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for r in rows:
        n = norm_name(str(r.get("name", "")))
        xyz = finite_xyz(r)
        if xyz is None:
            continue
        for canonical, aliases in FID_ALIASES.items():
            if n in aliases:
                out[canonical] = list(xyz)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--feasibility-summary", type=Path, default=Path("outputs/ahba_forward_model_feasibility_v1/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_registration_source_model_freeze_v1/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    feasibility = json.loads(args.feasibility_summary.read_text(encoding="utf-8"))
    if not feasibility.get("template_forward_model_feasible", False):
        raise SystemExit("forward-model feasibility gate is not positive")

    tracked = git_lines(root, "ls-files")
    spatial = [
        p for p in tracked
        if ("littleprince" in p.lower() or "garnettdream" in p.lower() or "granett" in p.lower())
        and (p.lower().endswith("_electrodes.tsv") or p.lower().endswith("_coordsystem.json"))
    ]
    possible_headshape = [
        p for p in tracked
        if any(tok in p.lower() for tok in ("headshape", "fiducial", "digitiz", ".hsp", ".elp", ".pos"))
    ]

    electrode_records = []
    coords_records = []
    representative_rows = None
    representative_path = None
    all_fiducials: list[dict] = []

    for rel in spatial:
        if not annex_get_small(root, rel):
            continue
        p = root / rel
        if rel.lower().endswith("_electrodes.tsv"):
            rows = read_tsv(p)
            finite = [r for r in rows if finite_xyz(r) is not None]
            fids = extract_fiducials_from_electrodes(rows)
            electrode_records.append({
                "path": rel,
                "n_rows": len(rows),
                "n_finite_xyz": len(finite),
                "coordinate_sha256": sha_rows(rows),
                "fiducials_in_electrodes": sorted(fids),
            })
            if len(finite) == 128 and representative_rows is None:
                representative_rows = rows
                representative_path = rel
            if fids:
                all_fiducials.append({"path": rel, "source": "electrodes.tsv", "fiducials": fids})
        else:
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                d = {}
            fids = extract_fiducials_from_json(d)
            coords_records.append({
                "path": rel,
                "coordinate_system": d.get("EEGCoordinateSystem"),
                "coordinate_units": d.get("EEGCoordinateUnits"),
                "anatomical_landmark_coordinate_system": d.get("AnatomicalLandmarkCoordinateSystem"),
                "anatomical_landmark_coordinate_units": d.get("AnatomicalLandmarkCoordinateUnits"),
                "keys": sorted(d),
                "fiducials": sorted(fids),
            })
            if fids:
                all_fiducials.append({"path": rel, "source": "coordsystem.json", "fiducials": fids})

    complete_fiducial_sets = [x for x in all_fiducials if set(x["fiducials"]) >= {"nasion", "lpa", "rpa"}]
    coordinate_hashes = sorted({r["coordinate_sha256"] for r in electrode_records if r["n_finite_xyz"] == 128})

    fsaverage_dir = None
    source_space_path = None
    bem_solution_path = None
    template_error = None
    try:
        import mne
        fsaverage_dir = Path(mne.datasets.fetch_fsaverage(verbose=False))
        src = fsaverage_dir / "bem" / "fsaverage-ico-5-src.fif"
        bem = fsaverage_dir / "bem" / "fsaverage-5120-5120-5120-bem-sol.fif"
        if src.exists():
            source_space_path = str(src)
        if bem.exists():
            bem_solution_path = str(bem)
    except Exception as exc:
        template_error = f"{type(exc).__name__}: {exc}"

    frozen_conventions = {
        "template_anatomy": "MNE fsaverage",
        "cortical_source_space": "fsaverage ico-5 surface source space",
        "bem": "precomputed fsaverage 3-layer EEG BEM, 5120-5120-5120",
        "registration": "explicit measured-head-to-fsaverage transform; never trans='fsaverage' shortcut",
        "registration_initialization": "NAS/LPA/RPA fiducials when a complete measured set is available",
        "registration_refinement": "model-blind sensor-to-scalp geometric alignment; no EEG/model/gene outcomes",
        "eeg_reference_for_leadfield": "average-reference projection applied to sensor lead field",
        "source_orientation": "surface-normal cortical orientation",
        "primary_channel_sensitivity": "absolute fixed-normal lead-field magnitude |G(e,v)|",
        "channel_sensitivity_normalization": "L1 normalize each channel over cortical vertices so sum_v L(e,v)=1",
        "molecular_projection": "w_e = sum_v L(e,v) X(v)",
        "primary_molecular_map_scaling": "spatially standardize each gene map before gene-set averaging",
    }

    blockers = []
    if representative_rows is None:
        blockers.append("No representative measured 128-position electrode file was materialized.")
    if not complete_fiducial_sets:
        blockers.append("No complete measured NAS/LPA/RPA fiducial set was found in electrodes.tsv or coordsystem.json metadata.")
    if source_space_path is None:
        blockers.append("The frozen fsaverage ico-5 source-space file was not available after template materialization.")
    if bem_solution_path is None:
        blockers.append("The frozen fsaverage 3-layer BEM solution was not available after template materialization.")

    ready = len(blockers) == 0
    payload = {
        "schema_version": 1,
        "analysis": "model-blind AHBA registration/source-model freeze v1",
        "loads_eeg_samples": False,
        "downloads_ahba": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_expression_outcomes": False,
        "feasibility_gate_reused": True,
        "n_spatial_metadata_files": len(spatial),
        "n_electrode_records": len(electrode_records),
        "n_coordsystem_records": len(coords_records),
        "n_distinct_exact_128_coordinate_geometries": len(coordinate_hashes),
        "representative_electrode_path": representative_path,
        "complete_measured_fiducial_sets": complete_fiducial_sets,
        "possible_headshape_or_digitization_paths": possible_headshape[:200],
        "template_resources": {
            "fsaverage_dir": str(fsaverage_dir) if fsaverage_dir else None,
            "source_space_path": source_space_path,
            "bem_solution_path": bem_solution_path,
            "error": template_error,
        },
        "frozen_conventions": frozen_conventions,
        "registration_transform_frozen": False,
        "ready_for_registration_implementation": ready,
        "blockers": blockers,
        "next_step_if_ready": "Construct the explicit measured-head-to-fsaverage transform, render/quantify sensor-to-scalp alignment, then freeze the transform before building any molecular-sensitivity matrix.",
        "guardrails": [
            "Measured ChineseEEG CapTrak positions remain the sensor geometry; a standard montage must not replace them.",
            "No EEG signal samples, reliability values, RSA values, model embeddings, or AHBA expression values may be used to choose registration/source-model conventions.",
            "The transform is not frozen merely because fsaverage resources exist; alignment must be rendered and quantitatively checked first.",
            "No 128 x G molecular-sensitivity matrix may be computed until registration_transform_frozen becomes true in a later model-blind artifact.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if ready else "blocked",
        "ready_for_registration_implementation": ready,
        "blockers": blockers,
        "n_complete_fiducial_sets": len(complete_fiducial_sets),
        "source_space_available": source_space_path is not None,
        "bem_available": bem_solution_path is not None,
    }, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
