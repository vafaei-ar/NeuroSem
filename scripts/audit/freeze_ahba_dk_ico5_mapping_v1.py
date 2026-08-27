#!/usr/bin/env python3
"""Freeze the Desikan-Killiany-to-fsaverage-ico5 vertex mapping.

Model-blind spatial bookkeeping only. This script never opens EEG signal samples,
AHBA gene-expression matrices, NeuroSem/model outcomes, or biological gene sets.
It maps the already-frozen ico-5 source vertices to MNE fsaverage ``aparc`` labels
and reconciles those labels against the cortical atlas metadata saved by the
AHBA preprocessing stage. It fails closed on ambiguous or incomplete parcel-name
matching and quantifies vertices outside the 68 cortical DK parcels.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


def norm_label(value: str) -> str:
    s = str(value).strip().lower()
    s = re.sub(r"-(lh|rh)$", "", s)
    s = re.sub(r"^(ctx[-_]?lh[-_]?|ctx[-_]?rh[-_]?)", "", s)
    return "".join(ch for ch in s if ch.isalnum())


def choose_name_column(info: pd.DataFrame) -> str:
    preferred = ["name", "label", "region", "parcel", "description"]
    for col in preferred:
        if col in info.columns:
            vals = info[col].astype(str).map(norm_label)
            if vals.nunique() >= 30:
                return col
    # Last resort: choose a non-required string-like column with high uniqueness.
    for col in info.columns:
        if col in {"id", "hemisphere", "structure"}:
            continue
        vals = info[col].astype(str).map(norm_label)
        if vals.nunique() >= 30:
            return col
    raise RuntimeError(f"Could not identify a parcel-name column in atlas metadata: {list(info.columns)}")


def hemi_code(value: str) -> str:
    s = str(value).strip().lower()
    if s in {"l", "lh", "left"}:
        return "lh"
    if s in {"r", "rh", "right"}:
        return "rh"
    raise RuntimeError(f"Unrecognized hemisphere value: {value!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-freeze", type=Path, default=Path("outputs/ahba_registration_source_model_freeze_v1/latest/summary.json"))
    ap.add_argument("--forward-freeze", type=Path, default=Path("outputs/ahba_forward_sensitivity_v1/latest/summary.json"))
    ap.add_argument("--forward-matrix", type=Path, default=Path("outputs/ahba_forward_sensitivity_v1/latest/forward_sensitivity.npz"))
    ap.add_argument("--expression-summary", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest/summary.json"))
    ap.add_argument("--atlas-info", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest/primary_leftright/atlas_info.csv"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_dk_ico5_mapping_v1/latest"))
    args = ap.parse_args()

    source = json.loads(args.source_freeze.read_text(encoding="utf-8"))
    forward = json.loads(args.forward_freeze.read_text(encoding="utf-8"))
    expr = json.loads(args.expression_summary.read_text(encoding="utf-8"))
    if not forward.get("ready_for_expression_projection", False):
        raise SystemExit("forward-sensitivity freeze is not ready for expression projection")
    if not expr.get("ready_for_molecular_sensitivity_matrix", False):
        raise SystemExit("AHBA expression preprocessing gate is not ready")

    z = np.load(args.forward_matrix, allow_pickle=False)
    lh_vertices = np.asarray(z["lh_vertices"], dtype=int)
    rh_vertices = np.asarray(z["rh_vertices"], dtype=int)
    channel_names = np.asarray(z["channel_names"]).astype(str)
    sensitivity = np.asarray(z["sensitivity"])
    if sensitivity.shape != (128, len(lh_vertices) + len(rh_vertices)):
        raise RuntimeError(f"Unexpected forward matrix shape {sensitivity.shape}")
    if channel_names.tolist() != [f"E{i}" for i in range(1, 129)]:
        raise RuntimeError("Unexpected channel ordering in frozen forward matrix")

    info = pd.read_csv(args.atlas_info)
    required = {"id", "hemisphere", "structure"}
    if not required.issubset(info.columns):
        raise RuntimeError(f"Atlas metadata missing required columns: {sorted(required - set(info.columns))}")
    info = info[info["structure"].astype(str).str.lower().eq("cortex")].copy()
    if len(info) != 68:
        raise RuntimeError(f"Expected 68 cortical DK parcels, got {len(info)}")
    info["id"] = pd.to_numeric(info["id"], errors="raise").astype(int)
    name_col = choose_name_column(info)
    info["hemi_code"] = info["hemisphere"].map(hemi_code)
    info["norm_name"] = info[name_col].astype(str).map(norm_label)
    if info[["hemi_code", "norm_name"]].duplicated().any():
        dup = info.loc[info[["hemi_code", "norm_name"]].duplicated(False), ["id", "hemisphere", name_col]].to_dict("records")
        raise RuntimeError(f"Ambiguous normalized DK parcel names: {dup[:10]}")

    fs_dir = Path(source["template_resources"]["fsaverage_dir"])
    subjects_dir = fs_dir.parent
    import mne
    labels = mne.read_labels_from_annot(
        subject="fsaverage", parc="aparc", subjects_dir=subjects_dir, verbose=False
    )

    label_lookup: dict[tuple[str, str], object] = {}
    excluded_label_names: list[str] = []
    for label in labels:
        hemi = getattr(label, "hemi", None)
        if hemi not in {"lh", "rh"}:
            continue
        key = (hemi, norm_label(label.name))
        if key[1] in {"unknown", "corpuscallosum"}:
            excluded_label_names.append(label.name)
            continue
        if key in label_lookup:
            raise RuntimeError(f"Duplicate aparc label after normalization: {key}")
        label_lookup[key] = label

    atlas_keys = {(r.hemi_code, r.norm_name): int(r.id) for r in info.itertuples(index=False)}
    unmatched_atlas = sorted([key for key in atlas_keys if key not in label_lookup])
    extra_aparc = sorted([key for key in label_lookup if key not in atlas_keys])
    if unmatched_atlas or extra_aparc:
        raise RuntimeError(
            "DK/aparc parcel-name reconciliation failed; "
            f"unmatched_atlas={unmatched_atlas[:20]} extra_aparc={extra_aparc[:20]}"
        )

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    coverage_rows = []
    offset = 0
    for hemi, vertices in (("lh", lh_vertices), ("rh", rh_vertices)):
        parcel_ids = np.full(len(vertices), -1, dtype=int)
        parcel_names = np.full(len(vertices), "", dtype=object)
        pos = {int(v): i for i, v in enumerate(vertices.tolist())}
        for key, parcel_id in sorted(atlas_keys.items()):
            if key[0] != hemi:
                continue
            label = label_lookup[key]
            hits = [pos[int(v)] for v in np.asarray(label.vertices, dtype=int) if int(v) in pos]
            if not hits:
                coverage_rows.append({"parcel_id": parcel_id, "hemisphere": hemi, "parcel_name": key[1], "n_source_vertices": 0})
                continue
            if np.any(parcel_ids[hits] != -1):
                raise RuntimeError(f"Overlapping aparc labels on source vertices for parcel {parcel_id}")
            parcel_ids[hits] = parcel_id
            parcel_names[hits] = key[1]
            coverage_rows.append({"parcel_id": parcel_id, "hemisphere": hemi, "parcel_name": key[1], "n_source_vertices": len(hits)})

        for local_idx, vertex in enumerate(vertices.tolist()):
            rows.append({
                "source_column": offset + local_idx,
                "hemisphere": hemi,
                "surface_vertex": int(vertex),
                "parcel_id": int(parcel_ids[local_idx]),
                "parcel_name": str(parcel_names[local_idx]) if parcel_ids[local_idx] >= 0 else "UNMAPPED_APARC",
                "mapped_to_dk68": bool(parcel_ids[local_idx] >= 0),
            })
        offset += len(vertices)

    mapping = pd.DataFrame(rows)
    coverage = pd.DataFrame(coverage_rows).sort_values(["hemisphere", "parcel_id"]).reset_index(drop=True)
    mapping.to_csv(out / "vertex_parcel_map.csv", index=False)
    coverage.to_csv(out / "parcel_coverage.csv", index=False)

    mapped_mask = mapping["mapped_to_dk68"].to_numpy(bool)
    mapped_fraction = float(mapped_mask.mean())
    mapped_sensitivity_mass = sensitivity[:, mapped_mask].sum(axis=1, dtype=np.float64)
    blockers = []
    if len(coverage) != 68 or int((coverage["n_source_vertices"] > 0).sum()) != 68:
        blockers.append("Not all 68 DK parcels contain at least one frozen ico-5 source vertex.")
    if mapped_fraction < 0.90:
        blockers.append(f"Less than 90% of ico-5 vertices map to the 68 DK cortical parcels: {mapped_fraction:.4f}")
    if not np.isfinite(mapped_sensitivity_mass).all() or np.any(mapped_sensitivity_mass <= 0):
        blockers.append("Mapped DK sensitivity mass is invalid for one or more channels.")

    payload = {
        "schema_version": 1,
        "analysis": "model-blind AHBA DK-to-fsaverage-ico5 mapping freeze v1",
        "loads_eeg_samples": False,
        "loads_ahba_gene_expression_values": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_set_outcomes": False,
        "mne_version": mne.__version__,
        "forward_gate_reused": True,
        "expression_preprocessing_gate_reused": True,
        "atlas": {
            "name": "Desikan-Killiany / aparc",
            "n_cortical_parcels": 68,
            "atlas_info_name_column": name_col,
            "excluded_aparc_labels": sorted(excluded_label_names),
        },
        "source_vertices": {
            "n_total": int(len(mapping)),
            "n_lh": int(len(lh_vertices)),
            "n_rh": int(len(rh_vertices)),
            "n_mapped_to_dk68": int(mapped_mask.sum()),
            "n_unmapped": int((~mapped_mask).sum()),
            "mapped_fraction": mapped_fraction,
        },
        "mapped_sensitivity_mass_by_channel": {
            "min": float(mapped_sensitivity_mass.min()),
            "median": float(np.median(mapped_sensitivity_mass)),
            "max": float(mapped_sensitivity_mass.max()),
        },
        "ready_for_dk_expression_projection": len(blockers) == 0,
        "blockers": blockers,
        "next_step_if_ready": "Use this exact vertex-to-parcel mapping to expand each donor-level DK gene-expression matrix onto the frozen ico-5 source vertices. Quantify the unmapped aparc domain explicitly before deciding whether molecular projection should preserve full-cortex L1 mass or renormalize sensitivity within the DK-mapped domain. Do not test biological gene sets yet.",
        "guardrails": [
            "Do not assume abagen fsaverage5 atlas vertex indices equal the frozen MNE ico-5 source-space indices.",
            "Do not use EEG signal samples, NeuroSem/RSA outcomes, model embeddings, gene-expression values, or biological gene-set results to alter this spatial mapping.",
            "Unknown/corpus-callosum aparc territory is not silently assigned to a DK cortical parcel; it remains explicitly unmapped and is quantified.",
            "Do not construct or test the 128 x G biological matrix until the treatment of unmapped DK territory is explicitly frozen from this mapping QC.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ready" if not blockers else "blocked",
        "ready_for_dk_expression_projection": not blockers,
        "mapped_fraction": mapped_fraction,
        "n_unmapped": int((~mapped_mask).sum()),
        "mapped_sensitivity_mass_min": float(mapped_sensitivity_mass.min()),
        "mapped_sensitivity_mass_max": float(mapped_sensitivity_mass.max()),
        "blockers": blockers,
    }, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
