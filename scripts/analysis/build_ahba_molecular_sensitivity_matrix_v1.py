#!/usr/bin/env python3
"""Build frozen AHBA 128 x G molecular-sensitivity matrices.

Uses only frozen AHBA donor expression, frozen EEG forward sensitivity, and the
frozen DK-to-ico5 mapping. Missing donor-by-parcel values are never imputed.
Population parcel expression follows the frozen abagen region_agg='donors',
agg_metric='mean' convention by averaging available donors. Leave-one-donor-out
(LODO) means are constructed only when every DK parcel remains observed after
excluding that donor. No NeuroSem or biological gene-set outcomes are accessed.
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
            a = np.asarray(z["expression"], dtype=np.float64)
        if a.shape != (68, len(genes)):
            raise RuntimeError(f"unexpected expression shape for donor {donor_id}: {a.shape}")
        if np.isinf(a).any():
            raise RuntimeError(f"infinite expression values for donor {donor_id}")
        mats.append(a)
    return genes, region_ids, donor_ids, np.stack(mats, axis=0)


def donor_mean(stack: np.ndarray, keep: np.ndarray):
    sub = stack[keep]
    finite_counts = np.sum(np.isfinite(sub), axis=0)
    summed = np.nansum(sub, axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = summed / finite_counts
    return mean, finite_counts


def project_complete_map(expr68: np.ndarray, vertex_rows: np.ndarray, L_mapped: np.ndarray, chunk_size: int):
    if not np.isfinite(expr68).all():
        raise RuntimeError("project_complete_map received non-finite parcel expression")
    n_genes = expr68.shape[1]
    W = np.empty((L_mapped.shape[0], n_genes), dtype=np.float32)
    z_mean_abs_max = 0.0
    z_sd_dev_max = 0.0
    zero_variance = []
    for start in range(0, n_genes, chunk_size):
        stop = min(start + chunk_size, n_genes)
        X = expr68[vertex_rows, start:stop]
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
        W[:, start:stop] = (L_mapped @ Z).astype(np.float32)
    if zero_variance:
        raise RuntimeError(f"{len(zero_variance)} zero-variance spatial gene maps; first={zero_variance[:10]}")
    if not np.isfinite(W).all():
        raise RuntimeError("non-finite molecular sensitivity matrix")
    return W, z_mean_abs_max, z_sd_dev_max


def save_matrix(path: Path, W: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, molecular_sensitivity=W)


def build_bundle(name: str, bundle_dir: Path, out_root: Path, L_mapped: np.ndarray,
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
    W, zm, zs = project_complete_map(pop, vertex_rows, L_mapped, chunk_size)
    save_matrix(out_dir / "population_all_donors.npz", W)
    qc.append({
        "analysis": name, "matrix": "population_all_donors", "excluded_donor": "",
        "status": "written", "n_genes": len(genes), "n_channels": int(W.shape[0]),
        "n_mapped_vertices": int(L_mapped.shape[1]), "min_donors_per_parcel_gene": int(pop_counts.min()),
        "max_abs_spatial_z_mean": zm, "max_abs_spatial_z_sd_minus_1": zs,
        "matrix_min": float(W.min()), "matrix_max": float(W.max()),
        "matrix_mean": float(W.mean()), "matrix_sd": float(W.std()), "uncovered_region_rows": "",
    })

    valid_lodo = []
    skipped_lodo = []
    for i, donor_id in enumerate(donor_ids):
        keep = np.ones(len(donor_ids), dtype=bool); keep[i] = False
        mean, counts = donor_mean(stack, keep)
        bad_rows = np.where(~np.isfinite(mean).all(axis=1))[0]
        if bad_rows.size:
            skipped_lodo.append(donor_id)
            qc.append({
                "analysis": name, "matrix": f"lodo_without_{donor_id}", "excluded_donor": donor_id,
                "status": "skipped_incomplete_domain", "n_genes": len(genes), "n_channels": 128,
                "n_mapped_vertices": int(L_mapped.shape[1]), "min_donors_per_parcel_gene": int(counts.min()),
                "max_abs_spatial_z_mean": "", "max_abs_spatial_z_sd_minus_1": "",
                "matrix_min": "", "matrix_max": "", "matrix_mean": "", "matrix_sd": "",
                "uncovered_region_rows": ";".join(str(int(x)) for x in bad_rows),
            })
            continue
        Wl, zm, zs = project_complete_map(mean, vertex_rows, L_mapped, chunk_size)
        save_matrix(out_dir / f"lodo_without_{donor_id}.npz", Wl)
        valid_lodo.append(donor_id)
        qc.append({
            "analysis": name, "matrix": f"lodo_without_{donor_id}", "excluded_donor": donor_id,
            "status": "written", "n_genes": len(genes), "n_channels": int(Wl.shape[0]),
            "n_mapped_vertices": int(L_mapped.shape[1]), "min_donors_per_parcel_gene": int(counts.min()),
            "max_abs_spatial_z_mean": zm, "max_abs_spatial_z_sd_minus_1": zs,
            "matrix_min": float(Wl.min()), "matrix_max": float(Wl.max()),
            "matrix_mean": float(Wl.mean()), "matrix_sd": float(Wl.std()), "uncovered_region_rows": "",
        })

    return {
        "n_source_donors": len(donor_ids), "donor_ids": donor_ids, "n_genes": len(genes),
        "n_channels": int(L_mapped.shape[0]), "n_mapped_vertices": int(L_mapped.shape[1]),
        "population_matrix": str(out_dir / "population_all_donors.npz"),
        "population_min_available_donors_per_parcel_gene": int(pop_counts.min()),
        "valid_lodo_excluded_donors": valid_lodo, "skipped_lodo_excluded_donors": skipped_lodo,
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

    f_gate, m_gate, e_gate = load_json(args.forward_freeze), load_json(args.mapping_freeze), load_json(args.expression_summary)
    if not f_gate.get("ready_for_expression_projection", False): raise SystemExit("forward-sensitivity gate is not ready")
    if not m_gate.get("ready_for_dk_expression_projection", False): raise SystemExit("DK-to-ico5 mapping gate is not ready")
    if not e_gate.get("ready_for_molecular_sensitivity_matrix", False): raise SystemExit("AHBA expression preprocessing gate is not ready")
    frozen = e_gate.get("frozen_primary_preprocessing", {})
    if frozen.get("region_agg") != "donors" or frozen.get("agg_metric") != "mean":
        raise RuntimeError("expression preprocessing donor aggregation convention is not frozen to donors/mean")

    with np.load(args.forward_matrix, allow_pickle=False) as z:
        L = np.asarray(z["sensitivity"], dtype=np.float64); channel_names = np.asarray(z["channel_names"])
    rows, mapped, parcel_ids = load_vertex_map(args.vertex_map)
    if L.shape != (128, len(rows)): raise RuntimeError(f"forward/mapping shape mismatch: {L.shape} vs {len(rows)}")
    if int(mapped.sum()) != int(m_gate["source_vertices"]["n_mapped_to_dk68"]): raise RuntimeError("mapped vertex count disagrees with freeze")

    raw = L[:, mapped]; mass = raw.sum(axis=1)
    if np.any(~np.isfinite(mass)) or np.any(mass <= 0): raise RuntimeError("invalid mapped-domain sensitivity mass")
    Lm = raw / mass[:, None]
    if not np.allclose(Lm.sum(axis=1), 1.0, atol=1e-10, rtol=1e-10): raise RuntimeError("DK-domain sensitivity renormalization failed")
    mapped_parcel_ids = parcel_ids[mapped]

    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    primary, q1 = build_bundle("primary_leftright", args.expression_root / "primary_leftright", out, Lm, mapped_parcel_ids, channel_names, args.chunk_size)
    sensitivity, q2 = build_bundle("sensitivity_no_mirror", args.expression_root / "sensitivity_no_mirror", out, Lm, mapped_parcel_ids, channel_names, args.chunk_size)
    qrows = q1 + q2
    with (out / "projection_qc.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(qrows[0])); w.writeheader(); w.writerows(qrows)

    blockers = []
    if len(primary["valid_lodo_excluded_donors"]) != 6:
        blockers.append("Primary mirrored workflow does not support complete-domain LODO for all six donors.")
    ready = len(blockers) == 0
    payload = {
        "schema_version": 2, "analysis": "model-blind AHBA molecular-sensitivity matrix construction v1",
        "loads_eeg_samples": False, "computes_neurosem_outcomes": False, "computes_model_quantities": False,
        "computes_gene_set_outcomes": False, "uses_frozen_ahba_expression": True,
        "uses_frozen_forward_sensitivity": True, "uses_frozen_dk_ico5_mapping": True,
        "donor_missingness_policy": "Do not impute missing donor-parcel values. Reconstruct the frozen abagen donors/mean regional aggregation from available finite donors; generate LODO only when all 68 parcels remain observed after exclusion.",
        "projection_domain": {
            "full_source_vertices": int(L.shape[1]), "dk_mapped_vertices": int(mapped.sum()),
            "unmapped_vertices_excluded": int((~mapped).sum()), "mapped_fraction": float(mapped.mean()),
            "full_cortex_mapped_sensitivity_mass_min": float(mass.min()),
            "full_cortex_mapped_sensitivity_mass_median": float(np.median(mass)),
            "full_cortex_mapped_sensitivity_mass_max": float(mass.max()),
            "sensitivity_treatment": "renormalize each channel within the DK-mapped domain before molecular projection",
        },
        "gene_map_scaling": "expand aggregated DK parcel map to frozen ico-5 vertices, then z-score each gene spatially across DK-mapped vertices (ddof=0)",
        "molecular_projection": "W(e,g) = sum_v L_DK(e,v) * Z_g(v)",
        "primary": primary, "sensitivity_no_mirror": sensitivity,
        "ready_for_prespecified_biological_testing": ready, "blockers": blockers,
        "next_step_if_ready": "Test only prespecified biological systems using the primary population matrix plus all six primary LODO matrices; use no-mirror as bilateral sensitivity and report any unavailable no-mirror LODO exclusions rather than imputing them.",
        "guardrails": [
            "Never fill unsampled donor-parcel expression by interpolation, zero, or outcome-informed imputation.",
            "Primary population aggregation matches the frozen abagen region_agg=donors, agg_metric=mean convention.",
            "The original full-cortex forward sensitivity remains unchanged; DK-domain renormalization is projection-specific.",
            "Do not broaden gene sets or alter spatial conventions based on NeuroSem association results.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ready" if ready else "blocked", "primary_valid_lodo": len(primary["valid_lodo_excluded_donors"]), "primary_skipped_lodo": primary["skipped_lodo_excluded_donors"], "sensitivity_valid_lodo": len(sensitivity["valid_lodo_excluded_donors"]), "sensitivity_skipped_lodo": sensitivity["skipped_lodo_excluded_donors"], "blockers": blockers}, indent=2))
    return 0 if ready else 2


if __name__ == "__main__": raise SystemExit(main())
