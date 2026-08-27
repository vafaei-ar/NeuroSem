#!/usr/bin/env python3
"""Run the first frozen NeuroSem-AHBA gene-set association analysis.

This outcome-bearing stage uses only prospectively frozen inputs:
- the AHBA molecular-sensitivity matrices;
- the frozen biological gene-set memberships; and
- the AHBA-blind ChineseEEG semantic channel-contribution target.

Primary inferential unit is participant. Channels are used only to compute each
participant's spatial Spearman association with a molecular gene-set vector.
Seven neurochemical/pathway sets form the primary mechanistic family. Seven broad
cell-type marker sets form a separate specificity-control family. Benjamini-Hochberg
FDR is applied within each family. Two-sided exact sign-flip inference across
participants is primary. Donor-LODO, no-mirror bilateral sensitivity, and
size-matched random-gene-set nulls are computed here. Spatial-autocorrelation nulls
and broad cortical-gradient controls remain required before any mechanistic claim.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

PRIMARY_SETS = [
    "gaba_a_receptor_subunits",
    "gaba_b_receptors",
    "gaba_machinery_nonreceptor",
    "serotonin_receptors",
    "serotonin_machinery_nonreceptor",
    "pathway_gaba_receptor_activation",
    "pathway_serotonin_receptors",
]
CONTROL_SETS = [
    "celltype_excitatory_neuron",
    "celltype_inhibitory_neuron",
    "celltype_astrocyte",
    "celltype_oligodendrocyte",
    "celltype_opc",
    "celltype_microglia",
    "celltype_endothelial",
]
ALL_SETS = PRIMARY_SETS + CONTROL_SETS
DONOR_IDS = ["9861", "10021", "12876", "14380", "15496", "15697"]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_target(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("participant channel target is empty")
    subjects = sorted({r["subject"] for r in rows})
    channels = [f"E{i}" for i in range(1, 129)]
    by_subject = {}
    for subject in subjects:
        rr = [r for r in rows if r["subject"] == subject]
        m = {r["channel"]: float(r["mean_contribution_runs_01_06"]) for r in rr}
        if set(m) != set(channels):
            raise RuntimeError(f"{subject}: channel target does not contain E1-E128 exactly")
        by_subject[subject] = np.asarray([m[c] for c in channels], dtype=np.float64)
        if not np.isfinite(by_subject[subject]).all():
            raise RuntimeError(f"{subject}: non-finite channel target")
    if len(subjects) != 9:
        raise RuntimeError(f"expected 9 frozen participants, got {len(subjects)}")
    return subjects, channels, by_subject


def load_matrix_bundle(root: Path, name: str):
    d = root / name
    genes = [str(x) for x in load_json(d / "gene_symbols.json")]
    channels = [str(x) for x in load_json(d / "channel_names.json")]
    if channels != [f"E{i}" for i in range(1, 129)]:
        raise RuntimeError(f"{name}: unexpected channel order")
    paths = {
        "full": d / "population_all_donors.npz",
        "common": d / "population_common_support.npz",
    }
    for donor in DONOR_IDS:
        paths[f"lodo_{donor}"] = d / f"lodo_common_support_without_{donor}.npz"
    matrices = {}
    for key, path in paths.items():
        with np.load(path, allow_pickle=False) as z:
            W = np.asarray(z["molecular_sensitivity"], dtype=np.float64)
        if W.shape != (128, len(genes)) or not np.isfinite(W).all():
            raise RuntimeError(f"{name} {key}: invalid matrix shape/values {W.shape}")
        matrices[key] = W
    return genes, channels, matrices


def rank_z(x: np.ndarray):
    r = rankdata(np.asarray(x, dtype=np.float64), method="average")
    r -= r.mean()
    sd = r.std(ddof=0)
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("zero-variance rank vector")
    return r / sd


def spearman_fast(a: np.ndarray, b_rankz: np.ndarray):
    return float(np.mean(rank_z(a) * b_rankz))


def fisher_z(r: float):
    return float(np.arctanh(np.clip(r, -0.999999999, 0.999999999)))


def exact_two_sided_signflip(values: np.ndarray):
    values = np.asarray(values, dtype=np.float64)
    observed = abs(float(values.mean()))
    stats = []
    for signs in itertools.product([-1.0, 1.0], repeat=len(values)):
        stats.append(abs(float(np.mean(values * np.asarray(signs, dtype=float)))))
    null = np.asarray(stats)
    return float(np.mean(null >= observed - 1e-15))


def bh_adjust(pvals: list[float]):
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0.0, 1.0)
    out = np.empty(n, dtype=float)
    out[order] = q
    return out.tolist()


def set_genes(gene_sets: dict, set_name: str, mode: str):
    key = "primary_genes" if mode == "primary" else "no_mirror_genes"
    genes = [str(x) for x in gene_sets[set_name][key]]
    if len(genes) < 2:
        raise RuntimeError(f"{set_name}: fewer than 2 retained genes for {mode}")
    return genes


def molecular_vector(W: np.ndarray, genes: list[str], gene_index: dict[str, int]):
    missing = [g for g in genes if g not in gene_index]
    if missing:
        raise RuntimeError(f"gene set missing from matrix gene universe: {missing}")
    idx = np.asarray([gene_index[g] for g in genes], dtype=int)
    v = W[:, idx].mean(axis=1)
    if v.shape != (128,) or not np.isfinite(v).all() or v.std() <= 0:
        raise RuntimeError("invalid gene-set molecular vector")
    return v


def evaluate_vector(v: np.ndarray, target_rankz: dict[str, np.ndarray]):
    corr = {s: spearman_fast(v, rz) for s, rz in target_rankz.items()}
    z = np.asarray([fisher_z(corr[s]) for s in sorted(corr)], dtype=float)
    return corr, z, {
        "mean_fisher_z": float(z.mean()),
        "median_fisher_z": float(np.median(z)),
        "mean_spearman": float(np.mean(list(corr.values()))),
        "median_spearman": float(np.median(list(corr.values()))),
        "n_positive": int(np.sum(z > 0)),
        "n_subjects": int(len(z)),
        "signflip_p_two_sided": exact_two_sided_signflip(z),
    }


def random_set_p(W: np.ndarray, observed_z: float, k: int, target_rankz: dict[str, np.ndarray], n_random: int, rng):
    n_genes = W.shape[1]
    null = np.empty(n_random, dtype=np.float64)
    subjects = sorted(target_rankz)
    for i in range(n_random):
        idx = rng.choice(n_genes, size=k, replace=False)
        v = W[:, idx].mean(axis=1)
        zvals = [fisher_z(spearman_fast(v, target_rankz[s])) for s in subjects]
        null[i] = float(np.mean(zvals))
    p = float((1 + np.sum(np.abs(null) >= abs(observed_z))) / (n_random + 1))
    return p, float(null.mean()), float(null.std(ddof=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-root", type=Path, default=Path("outputs/ahba_molecular_sensitivity_matrix_v1/latest"))
    ap.add_argument("--matrix-summary", type=Path, default=Path("outputs/ahba_molecular_sensitivity_matrix_v1/latest/summary.json"))
    ap.add_argument("--gene-set-summary", type=Path, default=Path("outputs/ahba_biological_gene_sets_v1/latest/summary.json"))
    ap.add_argument("--gene-sets", type=Path, default=Path("outputs/ahba_biological_gene_sets_v1/latest/gene_sets.json"))
    ap.add_argument("--channel-target-summary", type=Path, default=Path("outputs/chineseeeg_semantic_channel_target_v1/latest/summary.json"))
    ap.add_argument("--participant-target", type=Path, default=Path("outputs/chineseeeg_semantic_channel_target_v1/latest/participant_channel_target.csv"))
    ap.add_argument("--random-sets", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260827)
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_frozen_gene_set_association_v1/latest"))
    args = ap.parse_args()

    if args.random_sets != 5000 or args.seed != 20260827:
        raise SystemExit("frozen random-set design requires 5000 random sets and seed 20260827")

    msum = load_json(args.matrix_summary)
    gsum = load_json(args.gene_set_summary)
    tsum = load_json(args.channel_target_summary)
    if not msum.get("ready_for_prespecified_biological_testing", False):
        raise RuntimeError("molecular matrix gate is not ready for prespecified biological testing")
    if not gsum.get("ready_for_frozen_biological_testing", False):
        raise RuntimeError("gene-set gate is not ready")
    if not tsum.get("ready_for_frozen_molecular_association", False):
        raise RuntimeError("semantic channel target gate is not ready")

    gene_sets = load_json(args.gene_sets)
    if sorted(gene_sets) != sorted(ALL_SETS):
        extra = sorted(set(gene_sets) - set(ALL_SETS))
        missing = sorted(set(ALL_SETS) - set(gene_sets))
        raise RuntimeError(f"frozen gene-set keys changed; missing={missing}, extra={extra}")

    subjects, target_channels, target = read_target(args.participant_target)
    target_rankz = {s: rank_z(target[s]) for s in subjects}

    pg, pc, pm = load_matrix_bundle(args.matrix_root, "primary_leftright")
    ng, nc, nm = load_matrix_bundle(args.matrix_root, "sensitivity_no_mirror")
    if pc != target_channels or nc != target_channels:
        raise RuntimeError("channel target/molecular matrix order mismatch")
    pindex = {g: i for i, g in enumerate(pg)}
    nindex = {g: i for i, g in enumerate(ng)}

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    result_rows = []
    participant_rows = []
    lodo_rows = []
    random_rows = []
    rng = np.random.default_rng(args.seed)

    for family, names in [("primary_mechanistic", PRIMARY_SETS), ("specificity_control", CONTROL_SETS)]:
        family_rows = []
        for set_name in names:
            genes = set_genes(gene_sets, set_name, "primary")
            v = molecular_vector(pm["full"], genes, pindex)
            corr, zvals, stats = evaluate_vector(v, target_rankz)
            row = {"family": family, "set": set_name, "n_genes": len(genes), **stats}
            family_rows.append(row)
            for s in subjects:
                participant_rows.append({"analysis": "primary_full_68", "set": set_name, "subject": s, "spearman": corr[s], "fisher_z": fisher_z(corr[s])})

            rp, rmean, rsd = random_set_p(pm["full"], stats["mean_fisher_z"], len(genes), target_rankz, args.random_sets, rng)
            row["size_matched_random_p_two_sided"] = rp
            random_rows.append({"set": set_name, "n_genes": len(genes), "n_random": args.random_sets, "seed": args.seed, "observed_mean_fisher_z": stats["mean_fisher_z"], "empirical_p_two_sided": rp, "null_mean": rmean, "null_sd": rsd})

            vc = molecular_vector(pm["common"], genes, pindex)
            _, _, cstats = evaluate_vector(vc, target_rankz)
            lodo_rows.append({"analysis": "primary_common_support_population", "set": set_name, "excluded_donor": "", **cstats})
            for donor in DONOR_IDS:
                vl = molecular_vector(pm[f"lodo_{donor}"], genes, pindex)
                _, _, lstats = evaluate_vector(vl, target_rankz)
                lodo_rows.append({"analysis": "primary_common_support_lodo", "set": set_name, "excluded_donor": donor, **lstats})

            ngenes = set_genes(gene_sets, set_name, "no_mirror")
            vn = molecular_vector(nm["full"], ngenes, nindex)
            _, _, nstats = evaluate_vector(vn, target_rankz)
            lodo_rows.append({"analysis": "no_mirror_full_68", "set": set_name, "excluded_donor": "", **nstats})
            vnc = molecular_vector(nm["common"], ngenes, nindex)
            _, _, ncstats = evaluate_vector(vnc, target_rankz)
            lodo_rows.append({"analysis": "no_mirror_common_support_population", "set": set_name, "excluded_donor": "", **ncstats})
            for donor in DONOR_IDS:
                vnl = molecular_vector(nm[f"lodo_{donor}"], ngenes, nindex)
                _, _, nlstats = evaluate_vector(vnl, target_rankz)
                lodo_rows.append({"analysis": "no_mirror_common_support_lodo", "set": set_name, "excluded_donor": donor, **nlstats})

        q = bh_adjust([float(r["signflip_p_two_sided"]) for r in family_rows])
        for r, qq in zip(family_rows, q):
            r["bh_fdr_q_within_family"] = qq
            result_rows.append(r)

    def write_csv(path: Path, rows: list[dict]):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)

    write_csv(out / "set_results.csv", result_rows)
    write_csv(out / "participant_results.csv", participant_rows)
    write_csv(out / "donor_and_bilateral_sensitivity.csv", lodo_rows)
    write_csv(out / "size_matched_random_set_nulls.csv", random_rows)

    payload = {
        "schema_version": 1,
        "analysis": "frozen NeuroSem-AHBA gene-set association v1",
        "n_subjects": len(subjects),
        "subjects": subjects,
        "n_channels": 128,
        "primary_mechanistic_family": PRIMARY_SETS,
        "specificity_control_family": CONTROL_SETS,
        "primary_statistic": "Spearman across 128 matched channels per participant; Fisher-z participant summary; exact two-sided sign-flip across 9 participants",
        "multiplicity": "Benjamini-Hochberg FDR separately within the 7-set primary mechanistic family and 7-set specificity-control family",
        "gene_set_vector": "unweighted arithmetic mean across the frozen retained molecular-sensitivity gene columns; each gene map was spatially standardized upstream before projection",
        "primary_domain": "primary leftright-mirrored AHBA population matrix on full 68 DK parcels",
        "donor_robustness": "fixed common-support population matrix and six leave-one-donor-out matrices",
        "bilateral_sensitivity": "no-mirror full population plus fixed common-support population and six donor LODO matrices",
        "random_gene_set_control": {"n_random_per_set": args.random_sets, "seed": args.seed, "sampling": "without replacement from the exact primary AHBA gene universe, matched to retained gene-set size", "statistic": "absolute participant-mean Fisher-z association"},
        "spatial_autocorrelation_null_completed": False,
        "broad_cortical_gradient_control_completed": False,
        "claim_ready": False,
        "claim_blockers": ["spatial-autocorrelation-preserving null maps not yet run", "broad cortical-gradient/nonspecific spatial control not yet run"],
        "guardrails": [
            "Do not change gene-set membership, channel target, family assignment, statistic, or multiplicity after inspecting these results.",
            "Channels are not inferential units; participant-level sign-flip inference is primary.",
            "Donor LODO and no-mirror analyses are robustness checks, not replacement primary analyses.",
            "A positive association is spatial correspondence with a population postmortem transcriptomic prior, not causal receptor evidence."
        ],
        "results": result_rows,
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "n_primary_sets": len(PRIMARY_SETS), "n_control_sets": len(CONTROL_SETS), "claim_ready": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
