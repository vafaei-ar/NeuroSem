#!/usr/bin/env python3
"""Freeze an AHBA-blind DK68 cortical semantic-contribution phenotype.

The input neural phenotype is the already-frozen participant-level 128-channel
semantic contribution map. The cortical back-projection uses only the frozen EEG
forward-sensitivity matrix and the frozen DK68 vertex mapping. No AHBA expression,
gene sets, or transcriptomic outcomes are opened here.

For channel e and DK parcel p, A[e,p] is the fraction of that channel's frozen
DK-mapped cortical sensitivity falling in parcel p. For participant s, the parcel
phenotype is the sensitivity-weighted mean channel contribution:

    Y[s,p] = sum_e A[e,p] * C[s,e] / sum_e A[e,p]

This is a deterministic back-projection, not an inverse solution: there is no
regularization parameter, source localization fitting, or AHBA-informed tuning.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_participant_target(path: Path):
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        raise RuntimeError("participant channel target is empty")
    subjects = sorted({r["subject"] for r in rows})
    channels = [f"E{i}" for i in range(1, 129)]
    out = {}
    for subject in subjects:
        rr = [r for r in rows if r["subject"] == subject]
        m = {r["channel"]: float(r["mean_contribution_runs_01_06"]) for r in rr}
        if set(m) != set(channels):
            raise RuntimeError(f"{subject}: channel target does not contain E1-E128 exactly")
        v = np.asarray([m[c] for c in channels], dtype=np.float64)
        if not np.isfinite(v).all():
            raise RuntimeError(f"{subject}: non-finite channel target")
        out[subject] = v
    if len(subjects) != 9:
        raise RuntimeError(f"expected 9 frozen participants, got {len(subjects)}")
    return subjects, channels, out


def read_vertex_map(path: Path):
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        raise RuntimeError("vertex map is empty")
    rows.sort(key=lambda r: int(r["source_column"]))
    cols = np.asarray([int(r["source_column"]) for r in rows], dtype=int)
    if not np.array_equal(cols, np.arange(len(rows))):
        raise RuntimeError("source_column is not contiguous")
    mapped = np.asarray([r["mapped_to_dk68"].strip().lower() == "true" for r in rows], dtype=bool)
    parcel_id = np.asarray([int(r["parcel_id"]) for r in rows], dtype=int)
    parcel_name = [r["parcel_name"] for r in rows]
    hemi = [r["hemisphere"] for r in rows]
    return rows, mapped, parcel_id, parcel_name, hemi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel-target-summary", type=Path, default=Path("outputs/chineseeeg_semantic_channel_target_v1/latest/summary.json"))
    ap.add_argument("--participant-target", type=Path, default=Path("outputs/chineseeeg_semantic_channel_target_v1/latest/participant_channel_target.csv"))
    ap.add_argument("--forward-summary", type=Path, default=Path("outputs/ahba_forward_sensitivity_v1/latest/summary.json"))
    ap.add_argument("--forward-matrix", type=Path, default=Path("outputs/ahba_forward_sensitivity_v1/latest/forward_sensitivity.npz"))
    ap.add_argument("--mapping-summary", type=Path, default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/summary.json"))
    ap.add_argument("--vertex-map", type=Path, default=Path("outputs/ahba_dk_ico5_mapping_v1/latest/vertex_parcel_map.csv"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/chineseeeg_semantic_parcel_target_v1/latest"))
    args = ap.parse_args()

    tsum = load_json(args.channel_target_summary)
    fsum = load_json(args.forward_summary)
    msum = load_json(args.mapping_summary)
    if not tsum.get("ready_for_frozen_molecular_association", False):
        raise RuntimeError("frozen semantic channel target is not ready")
    if not fsum.get("ready_for_expression_projection", False):
        raise RuntimeError("frozen forward sensitivity is not ready")
    if not msum.get("ready_for_dk_expression_projection", False):
        raise RuntimeError("frozen DK mapping is not ready")

    subjects, channels, target = read_participant_target(args.participant_target)
    with np.load(args.forward_matrix, allow_pickle=False) as z:
        L = np.asarray(z["sensitivity"], dtype=np.float64)
        fchannels = [str(x) for x in z["channel_names"]]
    if L.shape[0] != 128 or fchannels != channels:
        raise RuntimeError("forward/channel target channel mismatch")

    rows, mapped, pids_all, pnames_all, hemis_all = read_vertex_map(args.vertex_map)
    if L.shape[1] != len(rows):
        raise RuntimeError("forward/vertex-map source dimension mismatch")
    if int(mapped.sum()) != int(msum["source_vertices"]["n_mapped_to_dk68"]):
        raise RuntimeError("mapped vertex count disagrees with mapping freeze")

    raw = L[:, mapped]
    mass = raw.sum(axis=1)
    if np.any(~np.isfinite(mass)) or np.any(mass <= 0):
        raise RuntimeError("invalid DK-mapped channel sensitivity mass")
    Lm = raw / mass[:, None]
    mapped_pids = pids_all[mapped]
    parcel_ids = sorted(int(x) for x in np.unique(mapped_pids))
    if len(parcel_ids) != 68:
        raise RuntimeError(f"expected 68 mapped DK parcels, got {len(parcel_ids)}")

    meta = {}
    for pid in parcel_ids:
        idx = np.where(pids_all == pid)[0]
        names = sorted({pnames_all[i] for i in idx})
        hemis = sorted({hemis_all[i] for i in idx})
        if len(names) != 1 or len(hemis) != 1:
            raise RuntimeError(f"ambiguous metadata for parcel {pid}: names={names}, hemis={hemis}")
        meta[pid] = (hemis[0], names[0])

    A = np.column_stack([Lm[:, mapped_pids == pid].sum(axis=1) for pid in parcel_ids])
    if A.shape != (128, 68) or not np.isfinite(A).all():
        raise RuntimeError("invalid channel-by-parcel sensitivity matrix")
    if not np.allclose(A.sum(axis=1), 1.0, atol=1e-10, rtol=1e-10):
        raise RuntimeError("parcel sensitivity fractions do not sum to one per channel")
    parcel_sensor_mass = A.sum(axis=0)
    if np.any(parcel_sensor_mass <= 0):
        raise RuntimeError("one or more parcels have zero aggregate sensor sensitivity")

    participant_maps = {}
    for subject in subjects:
        y = (A.T @ target[subject]) / parcel_sensor_mass
        if y.shape != (68,) or not np.isfinite(y).all():
            raise RuntimeError(f"invalid parcel target for {subject}")
        participant_maps[subject] = y
    population = np.mean(np.vstack([participant_maps[s] for s in subjects]), axis=0)
    if not np.isfinite(population).all() or population.std(ddof=0) <= 0:
        raise RuntimeError("population parcel target is degenerate")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    with (out / "participant_parcel_target.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subject", "parcel_id", "hemisphere", "parcel_name", "semantic_contribution_backprojection"])
        for subject in subjects:
            for j, pid in enumerate(parcel_ids):
                hemi, name = meta[pid]
                w.writerow([subject, pid, hemi, name, float(participant_maps[subject][j])])

    with (out / "population_parcel_target.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["parcel_id", "hemisphere", "parcel_name", "mean_semantic_contribution_backprojection", "n_subjects", "aggregate_sensor_sensitivity"])
        for j, pid in enumerate(parcel_ids):
            hemi, name = meta[pid]
            w.writerow([pid, hemi, name, float(population[j]), len(subjects), float(parcel_sensor_mass[j])])

    with (out / "channel_parcel_sensitivity.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["channel", "parcel_id", "hemisphere", "parcel_name", "dk_normalized_sensitivity_fraction"])
        for ei, channel in enumerate(channels):
            for j, pid in enumerate(parcel_ids):
                hemi, name = meta[pid]
                w.writerow([channel, pid, hemi, name, float(A[ei, j])])

    payload = {
        "schema_version": 1,
        "analysis": "AHBA-blind ChineseEEG semantic DK68 parcel target freeze v1",
        "loads_ahba_expression": False,
        "loads_gene_sets": False,
        "computes_transcriptomic_outcomes": False,
        "uses_frozen_semantic_channel_target": True,
        "uses_frozen_forward_sensitivity": True,
        "uses_frozen_dk_vertex_mapping": True,
        "n_subjects": len(subjects),
        "subjects": subjects,
        "n_channels": 128,
        "n_parcels": 68,
        "backprojection": "A[e,p] is the fraction of channel e DK-mapped sensitivity in parcel p after per-channel DK renormalization; participant parcel target is sum_e A[e,p]C[s,e] / sum_e A[e,p]",
        "inverse_solver_used": False,
        "regularization_or_tuning_used": False,
        "population_target_min": float(population.min()),
        "population_target_max": float(population.max()),
        "population_target_mean": float(population.mean()),
        "population_target_sd": float(population.std(ddof=0)),
        "aggregate_sensor_sensitivity_min": float(parcel_sensor_mass.min()),
        "aggregate_sensor_sensitivity_median": float(np.median(parcel_sensor_mass)),
        "aggregate_sensor_sensitivity_max": float(parcel_sensor_mass.max()),
        "ready_for_exploratory_transcriptomics": True,
        "blockers": [],
        "guardrails": [
            "This map is a deterministic sensitivity-weighted back-projection, not anatomical source localization.",
            "Do not alter the back-projection after inspecting AHBA transcriptomic associations.",
            "Keep the previous prespecified GABA/serotonin analysis as a separate frozen null.",
            "Any subsequent whole-transcriptome or language-gene analysis is exploratory and requires spatially constrained nulls."
        ]
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ready", "n_subjects": len(subjects), "n_parcels": 68, "ready_for_exploratory_transcriptomics": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
