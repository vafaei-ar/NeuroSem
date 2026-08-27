#!/usr/bin/env python3
"""Build donor-level 128 x G AHBA molecular-sensitivity matrices.

This stage combines only previously frozen spatial ingredients:
- the 128 x V EEG forward-sensitivity matrix,
- the frozen DK-to-ico5 vertex mapping,
- donor-level DK AHBA expression matrices from the frozen preprocessing stage.

No EEG signal samples, NeuroSem reliability/RSA outcomes, model embeddings, or
biological gene-set hypotheses are loaded or tested here.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_vertex_map(path: Path):
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    if not rows:
        raise RuntimeError("vertex mapping is empty")
    rows.sort(key=lambda r: int(r["source_column"]))
    source_columns = np.asarray([int(r["source_column"]) for r in rows], dtype=np.int64)
    if not np.array_equal(source_columns, np.arange(len(rows), dtype=np.int64)):
        raise RuntimeError("vertex mapping source_column is not contiguous 0..V-1")
    mapped = np.asarray([str(r["mapped_to_dk68"]).strip().lower() == "true" for r in rows], dtype=bool)
    parcel_ids = np.asarray([int(r["parcel_id"]) for r in rows], dtype=np.int64)
    return rows, mapped, parcel_ids


def read_bundle(bundle_dir: Path):
    gene_symbols = load_json(bundle_dir / "gene_symbols.json")
    region_ids = [int(x) for x in load_json(bundle_dir / "region_ids.json")]
    donor_ids = [str(x) for x in load_json(bundle_dir / "donor_ids.json")]
    donor_files = {str(k): str(v) for k, v in load_json(bundle_dir / "donor_files.json").items()}
    if len(region_ids) != 68:
        raise RuntimeError(f"expected 68 DK regions, got {len(region_ids)} in {bundle_dir}")
    if len(donor_ids) != 6:
        raise RuntimeError(f"expected 6 donors, got {len(donor_ids)} in {bundle_dir}")
    return gene_symbols, region_ids, donor_ids, donor_files


def project_bundle(
    name: str,
    bundle_dir: Path,
    out_root: Path,
    L_mapped: np.ndarray,
    mapped_parcel_ids: np.ndarray,
    channel_names: np.ndarray,
    chunk_size: int,
):
    genes, region_ids, donor_ids, donor_files = read_bundle(bundle_dir)
    region_to_row = {rid: i for i, rid in enumerate(region_ids)}
    missing_parcels = sorted(set(int(x) for x in np.unique(mapped_parcel_ids)) - set(region_to_row))
    if missing_parcels:
        raise RuntimeError(f"mapped DK parcel IDs absent from expression bundle: {missing_parcels}")
    vertex_rows = np.asarray([region_to_row[int(pid)] for pid in mapped_parcel_ids], dtype=np.int64)

    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gene_symbols.json").write_text(json.dumps(genes, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "donor_ids.json").write_text(json.dumps(donor_ids, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "channel_names.json").write_text(json.dumps([str(x) for x in channel_names], ensure_ascii=False) + "\n", encoding="utf-8")

    qc = []
    for donor_id in donor_ids:
        source_file = bundle_dir / donor_files[donor_id]
        with np.load(source_file, allow_pickle=False) as z:
            expr = np.asarray(z["expression"], dtype=np.float64)
        if expr.shape != (68, len(genes)):
            raise RuntimeError(f"unexpected expression shape for donor {donor_id}: {expr.shape}")
        if not np.isfinite(expr).all():
            raise RuntimeError(f"non-finite expression values for donor {donor_id}")

        W = np.empty((L_mapped.shape[0], len(genes)), dtype=np.float32)
        zero_variance = []
        z_mean_abs_max = 0.0
        z_std_dev_max = 0.0
        for start in range(0, len(genes), chunk_size):
            stop = min(start + chunk_size, len(genes))
            X = expr[vertex_rows, start:stop]
            mu = X.mean(axis=0, keepdims=True)
            sd = X.std(axis=0, ddof=0, keepdims=True)
            bad = np.where((~np.isfinite(sd[0])) | (sd[0] <= 0))[0]
            if bad.size:
                zero_variance.extend((start + int(i)) for i in bad)
                sd[:, bad] = 1.0
            Z = (X - mu) / sd
            if bad.size:
                Z[:, bad] = 0.0
            z_mean_abs_max = max(z_mean_abs_max, float(np.max(np.abs(Z.mean(axis=0)))))
            z_std_dev_max = max(z_std_dev_max, float(np.max(np.abs(Z.std(axis=0, ddof=0) - 1.0))))
            W[:, start:stop] = (L_mapped @ Z).astype(np.float32)

        if zero_variance:
            raise RuntimeError(
                f"{len(zero_variance)} zero-variance spatial gene maps for donor {donor_id}; "
                f"first indices={zero_variance[:10]}"
            )
        if not np.isfinite(W).all():
            raise RuntimeError(f"non-finite molecular sensitivity values for donor {donor_id}")

        out_file = out_dir / donor_files[donor_id]
        np.savez_compressed(out_file, molecular_sensitivity=W)
        qc.append({
            "analysis": name,
            "donor_id": donor_id,
            "n_genes": len(genes),
            "n_channels": int(W.shape[0]),
            "n_mapped_vertices": int(L_mapped.shape[1]),
            "zero_variance_genes": 0,
            "max_abs_spatial_z_mean": z_mean_abs_max,
            "max_abs_spatial_z_sd_minus_1": z_std_dev_max,
            "matrix_min": float(W.min()),
            "matrix_max": float(W.max()),
            "matrix_mean": float(W.mean()),
            "matrix_sd": float(W.std()),
            "local_file": str(out_file),
        })

    return {
        "n_donors": len(donor_ids),
        "donor_ids": donor_ids,
        "n_genes": len(genes),
        "n_channels": int(L_mapped.shape[0]),
        "n_mapped_vertices": int(L_mapped.shape[1]),
        "local_data_dir": str(out_dir),
    }, qc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forward-freeze", type=Path, default=Path("outputs/ahba_forward_sensitivity_v1/latest/summary.json"))
    ap.add_argument("--forward-matrix", type=Path, default=Path("outputs/ahba_forward_sensitivity_v1/latest/forward_sensitivity.npz"))
    ap.add_argument("--mapping-freeze", type=Path, default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/summary.json"))
    ap.add_argument("--vertex-map", type=Path, default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/vertex_parcel_map.csv"))
    ap.add_argument("--expression-summary", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest/summary.json"))
    ap.add_argument("--expression-root", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_molecular_sensitivity_matrix_v1/latest"))
    ap.add_argument("--chunk-size", type=int, default=256)
    args = ap.parse_args()

    f_gate = load_json(args.forward_freeze)
    m_gate = load_json(args.mapping_freeze)
    e_gate = load_json(args.expression_summary)
    if not f_gate.get("ready_for_expression_projection", False):
        raise SystemExit("forward-sensitivity gate is not ready")
    if not m_gate.get("ready_for_dk_expression_projection", False):
        raise SystemExit("DK-to-ico5 mapping gate is not ready")
    if not e_gate.get("ready_for_molecular_sensitivity_matrix", False):
        raise SystemExit("AHBA expression preprocessing gate is not ready")

    with np.load(args.forward_matrix, allow_pickle=False) as z:
        L = np.asarray(z["sensitivity"], dtype=np.float64)
        channel_names = np.asarray(z["channel_names"])
    rows, mapped, parcel_ids = load_vertex_map(args.vertex_map)
    if L.shape != (128, len(rows)):
        raise RuntimeError(f"forward/mapping shape mismatch: L={L.shape}, mapping={len(rows)}")
    if int(mapped.sum()) != int(m_gate["source_vertices"]["n_mapped_to_dk68"]):
        raise RuntimeError("mapped vertex count disagrees with mapping freeze summary")

    L_raw_mapped = L[:, mapped]
    mapped_mass = L_raw_mapped.sum(axis=1)
    if np.any(~np.isfinite(mapped_mass)) or np.any(mapped_mass <= 0):
        raise RuntimeError("invalid mapped-domain sensitivity mass")
    L_mapped = L_raw_mapped / mapped_mass[:, None]
    mapped_parcel_ids = parcel_ids[mapped]
    renorm_sums = L_mapped.sum(axis=1)
    if not np.allclose(renorm_sums, 1.0, atol=1e-10, rtol=1e-10):
        raise RuntimeError("mapped-domain renormalized sensitivity rows do not sum to one")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    primary, qc_primary = project_bundle(
        "primary_leftright",
        args.expression_root / "primary_leftright",
        out,
        L_mapped,
        mapped_parcel_ids,
        channel_names,
        args.chunk_size,
    )
    sensitivity, qc_sens = project_bundle(
        "sensitivity_no_mirror",
        args.expression_root / "sensitivity_no_mirror",
        out,
        L_mapped,
        mapped_parcel_ids,
        channel_names,
        args.chunk_size,
    )

    qc_rows = qc_primary + qc_sens
    qc_path = out / "projection_qc.csv"
    with qc_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(qc_rows[0]))
        writer.writeheader()
        writer.writerows(qc_rows)

    payload = {
        "schema_version": 1,
        "analysis": "model-blind AHBA molecular-sensitivity matrix construction v1",
        "loads_eeg_samples": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_set_outcomes": False,
        "uses_frozen_ahba_expression": True,
        "uses_frozen_forward_sensitivity": True,
        "uses_frozen_dk_ico5_mapping": True,
        "projection_domain": {
            "full_source_vertices": int(L.shape[1]),
            "dk_mapped_vertices": int(mapped.sum()),
            "unmapped_vertices_excluded": int((~mapped).sum()),
            "mapped_fraction": float(mapped.mean()),
            "full_cortex_mapped_sensitivity_mass_min": float(mapped_mass.min()),
            "full_cortex_mapped_sensitivity_mass_median": float(np.median(mapped_mass)),
            "full_cortex_mapped_sensitivity_mass_max": float(mapped_mass.max()),
            "sensitivity_treatment": "renormalize each channel within the DK-mapped vertex domain before molecular projection",
            "reason": "AHBA DK expression is undefined on unmapped aparc territory; preserving channel-specific missing-domain mass would introduce atlas-coverage attenuation unrelated to molecular expression.",
        },
        "gene_map_scaling": "expand each donor DK parcel map to frozen ico-5 vertices, then z-score each gene spatially across the DK-mapped vertices (population SD, ddof=0)",
        "molecular_projection": "W(e,g) = sum_v L_DK(e,v) * Z_g(v)",
        "primary": primary,
        "sensitivity_no_mirror": sensitivity,
        "ready_for_prespecified_biological_testing": True,
        "blockers": [],
        "next_step_if_ready": "Test only the prespecified frozen biological systems (GABA-A receptor subunits, broader GABA machinery, serotonin receptor/machinery, published human cell-type markers, and small curated pathways) with donor-aware robustness, spatial-autocorrelation-preserving nulls, matched random gene sets, multiple-testing control, bilateral sensitivity, and broad-gradient controls.",
        "guardrails": [
            "Do not use EEG signal samples, NeuroSem reliability/RSA, model embeddings, or biological gene-set outcomes to alter the frozen AHBA preprocessing, forward model, DK mapping, or projection convention.",
            "The original full-cortex 128 x V forward-sensitivity matrix remains unchanged; mapped-domain renormalization is applied only for the DK-defined molecular projection.",
            "Keep donor-level molecular matrices separate for leave-one-donor-out robustness; do not collapse donor identity before mechanistic testing.",
            "Primary bilateral handling remains left-to-right mirroring; no-mirror remains the prespecified sensitivity analysis.",
            "Do not broaden gene sets, tune pathways, or select genes based on NeuroSem association results.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready",
        "ready_for_prespecified_biological_testing": True,
        "primary_n_genes": primary["n_genes"],
        "sensitivity_n_genes": sensitivity["n_genes"],
        "n_mapped_vertices": int(mapped.sum()),
        "mapped_mass_min": float(mapped_mass.min()),
        "mapped_mass_median": float(np.median(mapped_mass)),
        "mapped_mass_max": float(mapped_mass.max()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
