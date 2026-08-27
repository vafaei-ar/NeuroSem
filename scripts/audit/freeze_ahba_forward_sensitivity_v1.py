#!/usr/bin/env python3
"""Freeze the model-blind ChineseEEG EEG forward-sensitivity matrix for AHBA projection.

This stage uses only frozen spatial metadata, the frozen measured-head-to-fsaverage
transform, and frozen fsaverage source/BEM resources. It never opens EEG signal
samples, AHBA expression, model embeddings, NeuroSem outcomes, or gene-set outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np


def annex_get(root: Path, rel: str) -> Path:
    p = root / rel
    if not p.exists() or p.stat().st_size == 0:
        cp = subprocess.run(
            ["git", "-C", str(root), "annex", "get", "--", rel],
            capture_output=True,
            text=True,
            check=False,
        )
        if cp.returncode != 0:
            raise RuntimeError(f"could not materialize {rel}: {cp.stderr[-1000:]}")
    return p


def read_electrodes(path: Path) -> dict[str, tuple[float, float, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    ch_pos: dict[str, tuple[float, float, float]] = {}
    for row in rows:
        try:
            xyz = tuple(float(row[k]) for k in ("x", "y", "z"))
        except Exception:
            continue
        if len(xyz) == 3 and all(math.isfinite(v) for v in xyz):
            ch_pos[str(row.get("name", "")).strip()] = xyz
    return ch_pos


def get_fids(d: dict) -> dict[str, tuple[float, float, float]]:
    src = (
        d.get("AnatomicalLandmarkCoordinates")
        or d.get("FiducialsCoordinates")
        or d.get("FiducialCoordinates")
        or {}
    )
    aliases = {
        "nasion": ["nasion", "nas", "nz", "fidnz"],
        "lpa": ["lpa", "leftpreauricular", "leftauricular", "fidt9"],
        "rpa": ["rpa", "rightpreauricular", "rightauricular", "fidt10"],
    }
    norm = lambda s: "".join(c for c in str(s).lower() if c.isalnum())
    out: dict[str, tuple[float, float, float]] = {}
    for canonical, names in aliases.items():
        for key, value in src.items():
            if norm(key) in names and isinstance(value, (list, tuple)) and len(value) == 3:
                vals = tuple(float(x) for x in value)
                if all(math.isfinite(x) for x in vals):
                    out[canonical] = vals
    return out


def sha256_array(a: np.ndarray) -> str:
    arr = np.ascontiguousarray(a)
    return hashlib.sha256(arr.view(np.uint8)).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument(
        "--source-freeze",
        type=Path,
        default=Path("outputs/ahba_registration_source_model_freeze_v1/latest/summary.json"),
    )
    ap.add_argument(
        "--transform-freeze",
        type=Path,
        default=Path("outputs/ahba_registration_transform_freeze_v1/latest/summary.json"),
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/ahba_forward_sensitivity_v1/latest"),
    )
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    source_gate = json.loads(args.source_freeze.read_text(encoding="utf-8"))
    transform_gate = json.loads(args.transform_freeze.read_text(encoding="utf-8"))
    if not source_gate.get("ready_for_registration_implementation", False):
        raise SystemExit("source-model freeze gate is not ready")
    if not transform_gate.get("registration_transform_frozen", False):
        raise SystemExit("registration transform is not frozen")

    frozen = source_gate.get("frozen_conventions", {})
    required_conventions = {
        "eeg_reference_for_leadfield": "average-reference projection applied to sensor lead field",
        "source_orientation": "surface-normal cortical orientation",
        "primary_channel_sensitivity": "absolute fixed-normal lead-field magnitude |G(e,v)|",
        "channel_sensitivity_normalization": "L1 normalize each channel over cortical vertices so sum_v L(e,v)=1",
    }
    for key, expected in required_conventions.items():
        if frozen.get(key) != expected:
            raise RuntimeError(f"Frozen convention mismatch for {key}: {frozen.get(key)!r}")

    e_rel = transform_gate["representative_electrode_path"]
    c_rel = transform_gate["coordsystem_path"]
    e_path = annex_get(root, e_rel)
    c_path = annex_get(root, c_rel)
    ch_pos = read_electrodes(e_path)
    fids = get_fids(json.loads(c_path.read_text(encoding="utf-8")))
    if len(ch_pos) != 128:
        raise RuntimeError(f"Expected 128 EEG positions, got {len(ch_pos)}")
    if set(fids) != {"nasion", "lpa", "rpa"}:
        raise RuntimeError("Expected complete NAS/LPA/RPA fiducials")

    import mne

    montage = mne.channels.make_dig_montage(
        ch_pos=ch_pos,
        nasion=fids["nasion"],
        lpa=fids["lpa"],
        rpa=fids["rpa"],
        coord_frame="head",
    )
    info = mne.create_info(list(ch_pos), sfreq=1.0, ch_types="eeg")
    info.set_montage(montage, on_missing="raise")

    trans_path = Path(transform_gate["transform_path"])
    src_path = Path(transform_gate["source_space_path"])
    bem_path = Path(transform_gate["bem_solution_path"])
    for label, path in (("transform", trans_path), ("source space", src_path), ("BEM", bem_path)):
        if not path.exists():
            raise FileNotFoundError(f"Frozen {label} path does not exist: {path}")

    # MNE's standard EEG forward mindist default is frozen here before any
    # molecular or NeuroSem outcome is consulted.
    mindist_mm = 5.0
    fwd = mne.make_forward_solution(
        info,
        trans=str(trans_path),
        src=str(src_path),
        bem=str(bem_path),
        meg=False,
        eeg=True,
        mindist=mindist_mm,
        n_jobs=1,
        verbose=False,
    )
    fwd_fixed = mne.convert_forward_solution(
        fwd,
        surf_ori=True,
        force_fixed=True,
        use_cps=True,
        copy=True,
        verbose=False,
    )

    G = np.asarray(fwd_fixed["sol"]["data"], dtype=np.float64)
    if G.ndim != 2 or G.shape[0] != 128:
        raise RuntimeError(f"Unexpected fixed forward shape: {G.shape}")
    if not np.isfinite(G).all():
        raise RuntimeError("Forward lead field contains non-finite values")

    # Explicit average-reference projection on the sensor dimension:
    # P = I - 11^T / n, so P@G is equivalent to subtracting each source column's
    # channel mean. This is applied before absolute-value sensitivity extraction.
    G_ref = G - G.mean(axis=0, keepdims=True)
    abs_G = np.abs(G_ref)
    row_sum = abs_G.sum(axis=1)
    if np.any(~np.isfinite(row_sum)) or np.any(row_sum <= 0):
        raise RuntimeError("At least one channel has invalid/zero absolute lead-field mass")
    L = abs_G / row_sum[:, None]

    # Persist the exact source-space ordering used by the fixed forward.
    src_vertices = [np.asarray(s["vertno"], dtype=np.int32) for s in fwd_fixed["src"]]
    if len(src_vertices) != 2:
        raise RuntimeError(f"Expected two cortical hemispheres, got {len(src_vertices)}")
    n_vertices = int(sum(len(v) for v in src_vertices))
    if G.shape[1] != n_vertices:
        raise RuntimeError(f"Forward/source vertex mismatch: G={G.shape[1]} vertices={n_vertices}")

    sums = L.sum(axis=1)
    blockers: list[str] = []
    if not np.allclose(sums, 1.0, atol=1e-10, rtol=1e-10):
        blockers.append("Per-channel L1-normalized sensitivity does not sum to one.")
    if not np.isfinite(L).all():
        blockers.append("Sensitivity matrix contains non-finite values.")
    if np.any(L < 0):
        blockers.append("Sensitivity matrix contains negative values after absolute-value projection.")

    matrix_path = out / "forward_sensitivity.npz"
    np.savez_compressed(
        matrix_path,
        sensitivity=L.astype(np.float32),
        leadfield_fixed_average_ref=G_ref.astype(np.float32),
        channel_names=np.asarray(info.ch_names, dtype="U"),
        lh_vertices=src_vertices[0],
        rh_vertices=src_vertices[1],
    )

    qc_rows = []
    for idx, name in enumerate(info.ch_names):
        qc_rows.append(
            {
                "channel_index": idx,
                "channel_name": name,
                "l1_sum": float(sums[idx]),
                "max_weight": float(L[idx].max()),
                "nonzero_vertices": int(np.count_nonzero(L[idx])),
                "leadfield_l2": float(np.linalg.norm(G_ref[idx])),
            }
        )
    qc_path = out / "channel_sensitivity_qc.csv"
    with qc_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(qc_rows[0]))
        w.writeheader()
        w.writerows(qc_rows)

    ready = len(blockers) == 0
    payload = {
        "schema_version": 1,
        "analysis": "model-blind AHBA forward-sensitivity freeze v1",
        "loads_eeg_samples": False,
        "downloads_ahba": False,
        "loads_gene_expression": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_set_outcomes": False,
        "registration_transform_gate_reused": True,
        "source_model_gate_reused": True,
        "mne_version": mne.__version__,
        "representative_electrode_path": e_rel,
        "coordsystem_path": c_rel,
        "transform_path": str(trans_path),
        "source_space_path": str(src_path),
        "bem_solution_path": str(bem_path),
        "forward": {
            "n_channels": int(G.shape[0]),
            "n_vertices": int(G.shape[1]),
            "lh_vertices": int(len(src_vertices[0])),
            "rh_vertices": int(len(src_vertices[1])),
            "mindist_mm": mindist_mm,
            "surface_orientation": True,
            "force_fixed": True,
            "use_cps": True,
            "eeg_only": True,
            "average_reference_projection": "G_ref = G - mean_channels(G) for each source column",
            "primary_sensitivity": "L(e,v) = abs(G_ref(e,v))",
            "normalization": "per-channel L1 over cortical vertices",
        },
        "matrix": {
            "path": str(matrix_path),
            "shape": [int(x) for x in L.shape],
            "dtype_saved": "float32",
            "sha256_float64_pre_save": sha256_array(L),
            "channel_order": list(info.ch_names),
            "lh_vertex_count": int(len(src_vertices[0])),
            "rh_vertex_count": int(len(src_vertices[1])),
            "row_sum_min": float(sums.min()),
            "row_sum_max": float(sums.max()),
            "min_weight": float(L.min()),
            "max_weight": float(L.max()),
        },
        "ready_for_expression_projection": ready,
        "blockers": blockers,
        "next_step_if_ready": "Map the frozen Desikan-Killiany donor-level AHBA expression matrices onto these exact fsaverage ico-5 source vertices, spatially standardize each gene map, then combine with this frozen 128 x V sensitivity matrix to build donor-level 128 x G molecular-sensitivity matrices without testing biological gene sets yet.",
        "guardrails": [
            "Do not load EEG signal samples, NeuroSem reliability/RSA, model embeddings, AHBA expression, or gene-set outcomes in this forward-sensitivity freeze.",
            "Use the exact dataset-provided 128-channel CapTrak geometry and explicit frozen head-to-fsaverage transform; do not substitute a standard montage or trans='fsaverage'.",
            "Average-reference projection, fixed surface-normal orientation, absolute lead-field sensitivity, and per-channel L1 normalization are frozen model-blind conventions.",
            "Do not build or test any molecular gene-set association until this matrix and the expression-to-source mapping are frozen.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if ready else "blocked",
        "ready_for_expression_projection": ready,
        "shape": list(L.shape),
        "row_sum_min": float(sums.min()),
        "row_sum_max": float(sums.max()),
        "blockers": blockers,
    }, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
