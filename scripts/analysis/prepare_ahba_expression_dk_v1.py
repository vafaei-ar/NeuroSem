#!/usr/bin/env python3
"""Prepare frozen AHBA cortical expression inputs for NeuroSem.

Model-blind stage only. This script does not open EEG samples, model embeddings,
RSA/reliability outcomes, or gene-set outcomes. It requires the previously frozen
ChineseEEG-to-fsaverage transform gate, downloads/processes public AHBA microarray
data with pinned abagen settings, and stores donor-level Desikan-Killiany surface
expression matrices locally for later molecular projection.

Primary bilateral strategy is left-to-right sample mirroring because four of the
six AHBA donors lack right-hemisphere sampling. An unmirrored sensitivity dataset
is prepared under identical preprocessing. No association with NeuroSem is run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _save_donor_bundle(outdir: Path, name: str, donors: list[pd.DataFrame], counts: pd.DataFrame, info: pd.DataFrame) -> dict:
    sub = outdir / name
    sub.mkdir(parents=True, exist_ok=True)
    if not donors:
        raise RuntimeError(f"No donor matrices returned for {name}")

    gene_symbols = [str(c) for c in donors[0].columns]
    region_ids = [int(x) for x in donors[0].index]
    for idx, df in enumerate(donors):
        if [str(c) for c in df.columns] != gene_symbols:
            raise RuntimeError(f"Gene columns differ across donors for {name}")
        if [int(x) for x in df.index] != region_ids:
            raise RuntimeError(f"Region indices differ across donors for {name}")
        arr = df.to_numpy(dtype=np.float32)
        np.savez_compressed(sub / f"donor_{idx + 1:02d}.npz", expression=arr)

    (sub / "gene_symbols.json").write_text(json.dumps(gene_symbols, ensure_ascii=False) + "\n", encoding="utf-8")
    (sub / "region_ids.json").write_text(json.dumps(region_ids) + "\n", encoding="utf-8")
    counts.to_csv(sub / "sample_counts.csv")
    info.to_csv(sub / "atlas_info.csv", index=False)

    counts_num = counts.apply(pd.to_numeric, errors="coerce").fillna(0)
    donor_nonzero = {str(c): int((counts_num[c] > 0).sum()) for c in counts_num.columns}
    region_total = counts_num.sum(axis=1)
    hemi = info.set_index("id")["hemisphere"].astype(str)
    by_hemi = {}
    for h in sorted(hemi.unique()):
        ids = [i for i in region_total.index if int(i) in hemi.index and hemi.loc[int(i)] == h]
        by_hemi[h] = {
            "n_regions": len(ids),
            "n_regions_with_any_sample": int(sum(float(region_total.loc[i]) > 0 for i in ids)),
            "total_assigned_samples": int(sum(float(region_total.loc[i]) for i in ids)),
        }

    return {
        "n_donors": len(donors),
        "n_regions": len(region_ids),
        "n_genes": len(gene_symbols),
        "n_regions_with_any_sample": int((region_total > 0).sum()),
        "donor_regions_with_samples": donor_nonzero,
        "hemisphere_coverage": by_hemi,
        "local_data_dir": str(sub),
    }


def _run_abagen(abagen, atlas, atlas_info: pd.DataFrame, data_dir: Path, mirror):
    kwargs = dict(
        atlas_info=atlas_info,
        ibf_threshold=0.5,
        probe_selection="diff_stability",
        donor_probes="aggregate",
        lr_mirror=mirror,
        missing=None,
        tolerance=2,
        sample_norm="srs",
        gene_norm="srs",
        norm_matched=True,
        norm_structures=False,
        region_agg="donors",
        agg_metric="mean",
        corrected_mni=True,
        reannotated=True,
        return_counts=True,
        return_donors=True,
        return_report=True,
        donors="all",
        data_dir=str(data_dir),
        verbose=1,
        n_proc=1,
    )
    result = abagen.get_expression_data(atlas, **kwargs)
    if not isinstance(result, tuple) or len(result) != 3:
        raise RuntimeError("Unexpected abagen return shape; expected expression, counts, report")
    donors, counts, report = result
    return donors, counts, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transform-freeze", type=Path, default=Path("outputs/ahba_registration_transform_freeze_v1/latest/summary.json"))
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/ahba"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest"))
    args = ap.parse_args()

    gate = json.loads(args.transform_freeze.read_text(encoding="utf-8"))
    if not gate.get("registration_transform_frozen", False):
        raise SystemExit("registration transform is not frozen")

    import abagen

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    data_dir = args.data_dir.resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    atlas = abagen.fetch_desikan_killiany(surface=True)
    image = atlas["image"]
    info = pd.read_csv(atlas["info"])
    required = {"id", "hemisphere", "structure"}
    if not required.issubset(info.columns):
        raise RuntimeError(f"Desikan-Killiany atlas info missing required columns: {sorted(required - set(info.columns))}")

    # The atlas-info table shipped with abagen is intentionally broader than the
    # cortical surface analysis target. Use its documented structure metadata to
    # constrain sample matching to cortex instead of assuming every info-table
    # row is cortical. The surface GIFTIs themselves remain unchanged.
    cortex_info = info[info["structure"].astype(str).str.lower().eq("cortex")].copy()
    if cortex_info.empty:
        raise RuntimeError("Desikan-Killiany atlas info contains no cortical parcels")
    cortex_info["id"] = pd.to_numeric(cortex_info["id"], errors="raise").astype(int)
    hemis = set(cortex_info["hemisphere"].astype(str))
    if not {"L", "R"}.issubset(hemis):
        raise RuntimeError(f"Expected bilateral cortical DK metadata; observed hemispheres={sorted(hemis)}")

    primary_donors, primary_counts, primary_report = _run_abagen(
        abagen, image, cortex_info, data_dir, "leftright"
    )
    sens_donors, sens_counts, sens_report = _run_abagen(
        abagen, image, cortex_info, data_dir, None
    )

    primary = _save_donor_bundle(out, "primary_leftright", primary_donors, primary_counts, cortex_info)
    sensitivity = _save_donor_bundle(out, "sensitivity_no_mirror", sens_donors, sens_counts, cortex_info)

    (out / "abagen_primary_methods.txt").write_text(str(primary_report).strip() + "\n", encoding="utf-8")
    (out / "abagen_sensitivity_methods.txt").write_text(str(sens_report).strip() + "\n", encoding="utf-8")

    blockers = []
    if primary["n_donors"] != 6:
        blockers.append(f"Expected 6 AHBA donors, got {primary['n_donors']}")
    if primary["n_regions_with_any_sample"] != primary["n_regions"]:
        blockers.append("Primary left-to-right mirrored workflow does not cover every DK cortical parcel.")
    if primary["n_genes"] < 10000:
        blockers.append(f"Unexpectedly low retained gene count: {primary['n_genes']}")

    payload = {
        "schema_version": 1,
        "analysis": "model-blind AHBA Desikan-Killiany expression preparation v1",
        "loads_eeg_samples": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_set_outcomes": False,
        "downloads_public_ahba": True,
        "registration_transform_gate_reused": True,
        "abagen_version": getattr(abagen, "__version__", None),
        "atlas": {
            "name": "Desikan-Killiany",
            "space": "fsaverage5 surface",
            "n_info_rows_total": int(len(info)),
            "n_cortical_regions": int(len(cortex_info)),
            "cortical_info_filter": "structure == cortex",
        },
        "frozen_primary_preprocessing": {
            "donors": "all six AHBA donors",
            "ibf_threshold": 0.5,
            "probe_selection": "diff_stability",
            "donor_probes": "aggregate",
            "lr_mirror": "leftright",
            "missing": None,
            "tolerance_mm": 2,
            "sample_norm": "srs",
            "gene_norm": "srs",
            "norm_matched": True,
            "norm_structures": False,
            "region_agg": "donors",
            "agg_metric": "mean",
            "corrected_mni": True,
            "reannotated": True,
            "return_donors": True,
        },
        "prespecified_sensitivity": {
            "lr_mirror": None,
            "all_other_preprocessing_identical": True,
        },
        "primary": primary,
        "sensitivity_no_mirror": sensitivity,
        "ready_for_molecular_sensitivity_matrix": len(blockers) == 0,
        "blockers": blockers,
        "next_step_if_ready": "Project donor-level DK expression onto fsaverage ico-5 vertices, combine with the frozen fixed-normal EEG lead-field sensitivity, and build the 128 x G molecular-sensitivity matrix without testing biological gene sets yet.",
        "guardrails": [
            "Do not use NeuroSem, EEG reliability/RSA, model embeddings, or gene-set association outcomes to alter AHBA preprocessing.",
            "Primary bilateral handling is left-to-right mirroring fixed before molecular association testing; no-mirror remains a prespecified sensitivity analysis.",
            "Keep donor-level matrices for leave-one-donor-out robustness; do not collapse away donor identity before mechanistic testing.",
            "Do not test GABA, serotonin, cell-type, or pathway hypotheses in this preprocessing stage.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if not blockers else "blocked",
        "ready_for_molecular_sensitivity_matrix": not blockers,
        "primary_n_donors": primary["n_donors"],
        "primary_n_regions": primary["n_regions"],
        "primary_n_genes": primary["n_genes"],
        "blockers": blockers,
    }, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
