#!/usr/bin/env python3
"""Build frozen AHBA 128 x G molecular-sensitivity matrices.

Uses only frozen AHBA donor expression, frozen EEG forward sensitivity, and the
frozen DK-to-ico5 mapping. Missing donor-by-parcel values are never imputed.
The full 68-parcel population map follows the frozen abagen region_agg='donors',
agg_metric='mean' convention. LODO robustness uses a fixed common-support parcel
domain defined only from donor coverage: every retained parcel/gene cell must
have at least two finite donor values, so every single-donor exclusion remains
estimable on the same spatial domain. No NeuroSem or biological outcomes are
accessed.
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
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("vertex mapping is empty")
    rows.sort(key=lambda r: int(r["source_column"]))
    cols = np.asarray([int(r["source_column"]) for r in rows], dtype=np.int64)
    if not np.array_equal(cols, np.arange(len(rows), dtype=np.int64)):
        raise RuntimeError("vertex mapping source_column is not contiguous 0..V-1")
    mapped = np.asarray([str(r["mapped_to_dk68"]).strip().lower() == "true" for r in rows], dtype=bool)
    parcel_ids = np.asarray([int(r["parcel_id"]) for r in rows], dtype=np.int64)
    return rows, mapped, parcel_ids


def read_bundle(bundle_dir: Path):
    genes = [str(x) for x in load_json(bundle_dir / "gene_symbols.json")]
    region_ids = [int(x) for x in load_json(bundle_dir / "region_ids.json")]
    donor_ids = [str(x) for x in load_json(bundle_dir / "donor_ids.json")]
    donor_files = {str(k): str(v) for k, v in load_json(bundle_dir / "donor_files.json").items()}
    if len(region_ids) != 68 or len(donor_ids) != 6:
        raise RuntimeError(f"unexpected bundle dimensions in {bundle_dir}")
    mats = []
    for donor_id in donor_ids:
        with np.load(bundle_dir / donor_files[donor_id], allow_pickle=False) as z:
            arr = np.asarray(z["expression"], dtype=np.float64)
        if arr.shape != (68, len(genes)):
            raise RuntimeError(f"unexpected expression shape for donor {donor_id}: {arr.shape}")
        if np.isinf(arr).any():
            raise RuntimeError(f"infinite expression values for donor {donor_id}")
        mats.append(arr)
    return genes, region_ids, donor_ids, np.stack(mats, axis=0)


def donor_mean(stack: np.ndarray, keep: np.ndarray):
    sub = stack[keep]
    counts = np.sum(np.isfinite(sub), axis=0)
    summed = np.nansum(sub, axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = summed / counts
    return mean, counts


def make_domain_sensitivity(L_mapped_full: np.ndarray, vertex_rows: np.ndarray, domain_rows: np.ndarray):
    vertex_keep = domain_rows[vertex_rows]
    if not np.any(vertex_keep):
        raise RuntimeError("projection domain has no source vertices")
    raw = L_mapped_full[:, vertex_keep]
    mass = raw.sum(axis=1)
    if np.any(~np.isfinite(mass)) or np.any(mass <= 0):
        raise RuntimeError("invalid projection-domain sensitivity mass")
    Ld = raw / mass[:, None]
    if not np.allclose(Ld.sum(axis=1), 1.0, atol=1e-10, rtol=1e-10):
        raise RuntimeError("projection-domain sensitivity renormalization failed")
    return Ld, vertex_rows[vertex_keep], mass


def project_complete_map(expr68: np.ndarray, domain_vertex_rows: np.ndarray, L_domain: np.ndarray, chunk_size: int):
    if not np.isfinite(expr68[domain_vertex_rows]).all():
        raise RuntimeError("projection received non-finite expression inside active domain")
    n_genes = expr68.shape[1]
    W = np.empty((L_domain.shape[0], n_genes), dtype=np.float32)
    z_mean_abs_max = 0.0
    z_sd_dev_max = 0.0
    zero_variance = []
    for start in range(0, n_genes, chunk_size):
        stop = min(start + chunk_size, n_genes)
        X = expr68[domain_vertex_rows, start:stop]
        mu = X.mean(axis=0, keepdims=True)
        sd = X.std(axis=0, ddof=0, keepdims=True)
        bad = np.where((~np.isfinite(sd[0])) | (sd[0] <= 0))[0]
        if bad.size:
            zero_variance.extend(start + int(i) for i in bad)
            sd[:, bad] = 1.0
        Z = (X - mu) / sd
        if bad.size:
            Z[:, bad] = 0.0
        z_mean_abs_max = max(z_mean_abs_max, float(np.max(np.abs(Z.mean(axis=0)))))
        z_sd_dev_max = max(z_sd_dev_max, float(np.max(np.abs(Z.std(axis=0, ddof=0) - 1.0))))
        W[:, start:stop] = (L_domain @ Z).astype(np.float32)
    if zero_variance:
        raise RuntimeError(f"{len(zero_variance)} zero-variance spatial gene maps; first={zero_variance[:10]}")
    if not np.isfinite(W).all():
        raise RuntimeError("non-finite molecular sensitivity matrix")
    return W, z_mean_abs_max, z_sd_dev_max


def save_matrix(path: Path, W: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, molecular_sensitivity=W)


def qc_row(name, domain, matrix, excluded, status, n_genes, Ld, n_parcels, min_donors, zm="", zs="", W=None):
    return {
        "analysis": name,
        "domain": domain,
        "matrix": matrix,
        "excluded_donor": excluded,
        "status": status,
        "n_genes": n_genes,
        "n_channels": int(Ld.shape[0]),
        "n_domain_parcels": int(n_parcels),
        "n_domain_vertices": int(Ld.shape[1]),
        "min_donors_per_parcel_gene": int(min_donors),
        "max_abs_spatial_z_mean": zm,
        "max_abs_spatial_z_sd_minus_1": zs,
        "matrix_min": "" if W is None else float(W.min()),
        "matrix_max": "" if W is None else float(W.max()),
        "matrix_mean": "" if W is None else float(W.mean()),
        "matrix_sd": "" if W is None else float(W.std()),
    }


def build_bundle(name: str, bundle_dir: Path, out_root: Path, L_mapped_full: np.ndarray,
                 mapped_parcel_ids: np.ndarray, channel_names: np.ndarray, chunk_size: int):
    genes, region_ids, donor_ids, stack = read_bundle(bundle_dir)
    region_to_row = {rid: i for i, rid in enumerate(region_ids)}
    missing = sorted(set(int(x) for x in np.unique(mapped_parcel_ids)) - set(region_to_row))
    if missing:
        raise RuntimeError(f"mapped DK parcel IDs absent from expression bundle: {missing}")
    vertex_rows = np.asarray([region_to_row[int(pid)] for pid in mapped_parcel_ids], dtype=np.int64)

    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gene_symbols.json").write_text(json.dumps(genes, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "channel_names.json").write_text(json.dumps([str(x) for x in channel_names]) + "\n", encoding="utf-8")
    (out_dir / "donor_ids.json").write_text(json.dumps(donor_ids) + "\n", encoding="utf-8")

    qc = []
    all_keep = np.ones(len(donor_ids), dtype=bool)
    pop, pop_counts = donor_mean(stack, all_keep)
    if not np.isfinite(pop).all():
        bad_rows = np.where(~np.isfinite(pop).all(axis=1))[0]
        raise RuntimeError(f"population donor mean does not cover all DK parcels; region rows={bad_rows.tolist()}")

    full_rows = np.ones(68, dtype=bool)
    L_full, vrows_full, full_mass = make_domain_sensitivity(L_mapped_full, vertex_rows, full_rows)
    W, zm, zs = project_complete_map(pop, vrows_full, L_full, chunk_size)
    save_matrix(out_dir / "population_all_donors.npz", W)
    qc.append(qc_row(name, "full_68", "population_all_donors", "", "written", len(genes), L_full, 68, pop_counts.min(), zm, zs, W))

    finite_donors = np.sum(np.isfinite(stack), axis=0)
    common_rows = np.all(finite_donors >= 2, axis=1)
    n_common = int(common_rows.sum())
    if n_common < 2:
        raise RuntimeError(f"common-support LODO domain too small: {n_common} parcels")
    common_region_ids = [region_ids[i] for i in np.where(common_rows)[0]]
    excluded_region_ids = [region_ids[i] for i in np.where(~common_rows)[0]]
    (out_dir / "common_support_region_ids.json").write_text(json.dumps(common_region_ids) + "\n", encoding="utf-8")
    (out_dir / "common_support_excluded_region_ids.json").write_text(json.dumps(excluded_region_ids) + "\n", encoding="utf-8")

    L_common, vrows_common, common_mass = make_domain_sensitivity(L_mapped_full, vertex_rows, common_rows)
    Wc, zmc, zsc = project_complete_map(pop, vrows_common, L_common, chunk_size)
    save_matrix(out_dir / "population_common_support.npz", Wc)
    qc.append(qc_row(name, "common_support", "population_common_support", "", "written", len(genes), L_common, n_common, finite_donors[common_rows].min(), zmc, zsc, Wc))

    lodo_files = {}
    for i, donor_id in enumerate(donor_ids):
        keep = np.ones(len(donor_ids), dtype=bool)
        keep[i] = False
        mean, counts = donor_mean(stack, keep)
        if not np.isfinite(mean[common_rows]).all():
            bad = np.where(~np.isfinite(mean[common_rows]).all(axis=1))[0]
            raise RuntimeError(f"common-support LODO unexpectedly incomplete after excluding {donor_id}; rows={bad.tolist()}")
        Wl, zml, zsl = project_complete_map(mean, vrows_common, L_common, chunk_size)
        filename = f"lodo_common_support_without_{donor_id}.npz"
        save_matrix(out_dir / filename, Wl)
        lodo_files[donor_id] = str(out_dir / filename)
        qc.append(qc_row(name, "common_support", f"lodo_without_{donor_id}", donor_id, "written", len(genes), L_common, n_common, counts[common_rows].min(), zml, zsl, Wl))

    return {
        "n_source_donors": len(donor_ids),
        "donor_ids": donor_ids,
        "n_genes": len(genes),
        "n_channels": int(L_mapped_full.shape[0]),
        "full_domain": {
            "n_parcels": 68,
            "n_vertices": int(L_full.shape[1]),
            "population_matrix": str(out_dir / "population_all_donors.npz"),
            "min_available_donors_per_parcel_gene": int(pop_counts.min()),
            "mapped_sensitivity_mass_before_domain_renorm_min": float(full_mass.min()),
            "mapped_sensitivity_mass_before_domain_renorm_median": float(np.median(full_mass)),
            "mapped_sensitivity_mass_before_domain_renorm_max": float(full_mass.max()),
        },
        "common_support_lodo_domain": {
            "definition": "retain DK parcel iff every gene has at least two finite donor values before exclusion",
            "n_parcels": n_common,
            "region_ids": common_region_ids,
            "excluded_region_ids": excluded_region_ids,
            "n_vertices": int(L_common.shape[1]),
            "population_common_support_matrix": str(out_dir / "population_common_support.npz"),
            "lodo_matrices": lodo_files,
            "all_six_lodo_written": len(lodo_files) == 6,
            "mapped_sensitivity_mass_before_domain_renorm_min": float(common_mass.min()),
            "mapped_sensitivity_mass_before_domain_renorm_median": float(np.median(common_mass)),
            "mapped_sensitivity_mass_before_domain_renorm_max": float(common_mass.max()),
        },
        "missing_value_policy": "no imputation; parcel-wise donor mean over available finite donor values",
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
    frozen = e_gate.get("frozen_primary_preprocessing", {})
    if frozen.get("region_agg") != "donors" or frozen.get("agg_metric") != "mean":
        raise RuntimeError("expression preprocessing donor aggregation convention is not frozen to donors/mean")

    with np.load(args.forward_matrix, allow_pickle=False) as z:
        L = np.asarray(z["sensitivity"], dtype=np.float64)
        channel_names = np.asarray(z["channel_names"])
    rows, mapped, parcel_ids = load_vertex_map(args.vertex_map)
    if L.shape != (128, len(rows)):
        raise RuntimeError(f"forward/mapping shape mismatch: {L.shape} vs {len(rows)}")
    if int(mapped.sum()) != int(m_gate["source_vertices"]["n_mapped_to_dk68"]):
        raise RuntimeError("mapped vertex count disagrees with freeze")

    raw = L[:, mapped]
    mass = raw.sum(axis=1)
    if np.any(~np.isfinite(mass)) or np.any(mass <= 0):
        raise RuntimeError("invalid DK-mapped sensitivity mass")
    Lm = raw / mass[:, None]
    if not np.allclose(Lm.sum(axis=1), 1.0, atol=1e-10, rtol=1e-10):
        raise RuntimeError("DK-domain sensitivity renormalization failed")
    mapped_parcel_ids = parcel_ids[mapped]

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    primary, q1 = build_bundle("primary_leftright", args.expression_root / "primary_leftright", out, Lm, mapped_parcel_ids, channel_names, args.chunk_size)
    sensitivity, q2 = build_bundle("sensitivity_no_mirror", args.expression_root / "sensitivity_no_mirror", out, Lm, mapped_parcel_ids, channel_names, args.chunk_size)
    qrows = q1 + q2
    with (out / "projection_qc.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(qrows[0]))
        writer.writeheader()
        writer.writerows(qrows)

    blockers = []
    if not primary["common_support_lodo_domain"]["all_six_lodo_written"]:
        blockers.append("Primary common-support LODO did not produce all six donor exclusions.")
    if not sensitivity["common_support_lodo_domain"]["all_six_lodo_written"]:
        blockers.append("No-mirror common-support LODO did not produce all six donor exclusions.")
    ready = len(blockers) == 0

    payload = {
        "schema_version": 3,
        "analysis": "model-blind AHBA molecular-sensitivity matrix construction v1",
        "loads_eeg_samples": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_set_outcomes": False,
        "uses_frozen_ahba_expression": True,
        "uses_frozen_forward_sensitivity": True,
        "uses_frozen_dk_ico5_mapping": True,
        "donor_missingness_policy": "Never impute donor-parcel expression. Full population uses the frozen donors/mean aggregation over available finite donors. LODO uses a fixed common-support parcel domain defined by at least two finite donors for every gene before exclusion.",
        "projection_domain": {
            "full_source_vertices": int(L.shape[1]),
            "dk_mapped_vertices": int(mapped.sum()),
            "unmapped_vertices_excluded": int((~mapped).sum()),
            "mapped_fraction": float(mapped.mean()),
            "full_cortex_mapped_sensitivity_mass_min": float(mass.min()),
            "full_cortex_mapped_sensitivity_mass_median": float(np.median(mass)),
            "full_cortex_mapped_sensitivity_mass_max": float(mass.max()),
            "sensitivity_treatment": "renormalize channels within each active molecular projection domain",
        },
        "gene_map_scaling": "expand aggregated DK parcel map to active frozen ico-5 vertices, then z-score each gene spatially across that domain (ddof=0)",
        "molecular_projection": "W(e,g) = sum_v L_domain(e,v) * Z_g(v)",
        "primary": primary,
        "sensitivity_no_mirror": sensitivity,
        "ready_for_prespecified_biological_testing": ready,
        "blockers": blockers,
        "next_step_if_ready": "Use the full 68-parcel primary population matrix for the prespecified biological tests. Use the matched primary common-support population matrix plus all six common-support LODO matrices for donor robustness. Use no-mirror full population and common-support LODO matrices as bilateral sensitivity. Do not impute excluded parcels or tune domains from biological outcomes.",
        "guardrails": [
            "Never fill unsampled donor-parcel expression by interpolation, zero, or outcome-informed imputation.",
            "Primary full population aggregation matches frozen abagen region_agg=donors, agg_metric=mean.",
            "Common-support LODO domains are determined only from donor coverage, before biological or NeuroSem testing.",
            "All LODO matrices within a workflow use exactly the same parcel/vertex domain and channel renormalization.",
            "The original full-cortex forward sensitivity remains unchanged; molecular-domain renormalization is projection-specific.",
            "Do not broaden gene sets or alter spatial conventions based on later association results.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if ready else "blocked",
        "ready_for_prespecified_biological_testing": ready,
        "primary_full_parcels": primary["full_domain"]["n_parcels"],
        "primary_common_support_parcels": primary["common_support_lodo_domain"]["n_parcels"],
        "sensitivity_common_support_parcels": sensitivity["common_support_lodo_domain"]["n_parcels"],
        "primary_n_genes": primary["n_genes"],
        "sensitivity_n_genes": sensitivity["n_genes"],
        "blockers": blockers,
    }, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
