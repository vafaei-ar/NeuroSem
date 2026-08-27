#!/usr/bin/env python3
"""Freeze prespecified AHBA biological gene sets before any NeuroSem outcome test.

This stage reads only retained AHBA gene symbols from the frozen expression-prep
outputs. It does not open EEG samples, molecular matrices, NeuroSem outcomes, model
embeddings, or association results. Curated receptor/machinery and broad human
brain cell-type marker panels are fixed in code. Two Reactome pathway memberships
are fetched from the public Content Service and their exact returned memberships
and database version are recorded for reproducibility.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from pathlib import Path


CURATED = {
    "gaba_a_receptor_subunits": [
        "GABRA1","GABRA2","GABRA3","GABRA4","GABRA5","GABRA6",
        "GABRB1","GABRB2","GABRB3","GABRG1","GABRG2","GABRG3",
        "GABRD","GABRE","GABRP","GABRQ","GABRR1","GABRR2","GABRR3",
    ],
    "gaba_b_receptors": ["GABBR1","GABBR2"],
    "gaba_machinery_nonreceptor": ["GAD1","GAD2","SLC6A1","SLC6A11","SLC32A1","ABAT","ALDH5A1"],
    "serotonin_receptors": [
        "HTR1A","HTR1B","HTR1D","HTR1E","HTR1F",
        "HTR2A","HTR2B","HTR2C",
        "HTR3A","HTR3B","HTR3C","HTR3D","HTR3E",
        "HTR4","HTR5A","HTR6","HTR7",
    ],
    "serotonin_machinery_nonreceptor": ["TPH2","DDC","SLC6A4","SLC18A2","MAOA","MAOB"],
    "celltype_excitatory_neuron": ["SLC17A7","CAMK2A","NRGN","SATB2"],
    "celltype_inhibitory_neuron": ["GAD1","GAD2"],
    "celltype_astrocyte": ["AQP4","GFAP","GJA1"],
    "celltype_oligodendrocyte": ["MBP","MOBP","PLP1"],
    "celltype_opc": ["OLIG1","PDGFRA","VCAN"],
    "celltype_microglia": ["C3","P2RY12","CSF1R"],
    "celltype_endothelial": ["CLDN5","FLT1"],
}

REACTOME = {
    "pathway_gaba_receptor_activation": {
        "id": "R-HSA-977443",
        "name": "GABA receptor activation",
    },
    "pathway_serotonin_receptors": {
        "id": "R-HSA-390666",
        "name": "Serotonin receptors",
    },
}

REFERENCES = [
    {
        "scope": "GABA_A receptor nomenclature",
        "citation": "Collingridge et al. A nomenclature for ligand-gated ion channels. Neuropharmacology. 2009/2010.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2847504/",
    },
    {
        "scope": "human cortical broad cell-type markers",
        "citation": "Single-nucleus transcriptomic profiling of human orbitofrontal cortex reveals convergent effects of aging and psychiatric disease. Nature Neuroscience. 2024.",
        "url": "https://www.nature.com/articles/s41593-024-01742-z",
    },
    {
        "scope": "human brain broad cell-type marker corroboration",
        "citation": "Mathys et al. Single-cell transcriptomic analysis of Alzheimer's disease. Nature. 2019.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6865822/",
    },
    {
        "scope": "Reactome pathway memberships/API",
        "citation": "Reactome Content Service; pathway memberships frozen at execution time.",
        "url": "https://reactome.org/dev/content-service",
    },
]


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "NeuroSem-AHBA-freeze/1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def get_text(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/plain", "User-Agent": "NeuroSem-AHBA-freeze/1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return raw.decode("utf-8").strip(), hashlib.sha256(raw).hexdigest()


def reactome_symbols(pathway_id: str):
    url = f"https://reactome.org/ContentService/data/participants/{pathway_id}/referenceEntities"
    data, sha = get_json(url)
    symbols = set()
    for item in data:
        for key in ("geneName", "geneNames"):
            val = item.get(key)
            if isinstance(val, str):
                symbols.add(val.strip())
            elif isinstance(val, list):
                symbols.update(str(x).strip() for x in val if str(x).strip())
        disp = str(item.get("displayName", ""))
        # Reactome reference entities often render as 'UniProt:P12345 SYMBOL'.
        if " " in disp:
            tail = disp.rsplit(" ", 1)[-1].strip()
            if tail and tail.replace("-", "").replace(".", "").isalnum():
                symbols.add(tail)
    return sorted(s for s in symbols if s), url, sha, data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expression-root", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--matrix-summary", type=Path, default=Path("outputs/ahba_molecular_sensitivity_matrix_v1/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/ahba_biological_gene_sets_v1/latest"))
    args = ap.parse_args()

    matrix_gate = json.loads(args.matrix_summary.read_text(encoding="utf-8"))
    if not matrix_gate.get("ready_for_prespecified_biological_testing", False):
        raise SystemExit("molecular matrix gate is not ready")

    primary = set(json.loads((args.expression_root / "primary_leftright" / "gene_symbols.json").read_text(encoding="utf-8")))
    no_mirror = set(json.loads((args.expression_root / "sensitivity_no_mirror" / "gene_symbols.json").read_text(encoding="utf-8")))
    if len(primary) < 10000 or len(no_mirror) < 10000:
        raise RuntimeError("unexpected retained AHBA gene universe")

    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    database_version, db_sha = get_text("https://reactome.org/ContentService/data/database/version")

    frozen = {}
    rows = []
    for name, genes in CURATED.items():
        source = list(dict.fromkeys(genes))
        p = [g for g in source if g in primary]
        n = [g for g in source if g in no_mirror]
        frozen[name] = {
            "category": "curated",
            "source_genes": source,
            "primary_genes": p,
            "no_mirror_genes": n,
            "missing_primary": [g for g in source if g not in primary],
            "missing_no_mirror": [g for g in source if g not in no_mirror],
        }
        for g in source:
            rows.append({"set": name, "gene": g, "source": "curated", "in_primary": g in primary, "in_no_mirror": g in no_mirror})

    reactome_meta = {}
    for name, meta in REACTOME.items():
        symbols, url, sha, raw = reactome_symbols(meta["id"])
        p = [g for g in symbols if g in primary]
        n = [g for g in symbols if g in no_mirror]
        frozen[name] = {
            "category": "reactome_pathway",
            "reactome_id": meta["id"],
            "reactome_name": meta["name"],
            "source_genes": symbols,
            "primary_genes": p,
            "no_mirror_genes": n,
            "missing_primary": [g for g in symbols if g not in primary],
            "missing_no_mirror": [g for g in symbols if g not in no_mirror],
        }
        reactome_meta[name] = {"url": url, "sha256_response": sha, "n_reference_entities": len(raw)}
        for g in symbols:
            rows.append({"set": name, "gene": g, "source": meta["id"], "in_primary": g in primary, "in_no_mirror": g in no_mirror})

    blockers = []
    required = ["gaba_a_receptor_subunits","gaba_machinery_nonreceptor","serotonin_receptors","serotonin_machinery_nonreceptor",
                "celltype_excitatory_neuron","celltype_inhibitory_neuron","celltype_astrocyte","celltype_oligodendrocyte",
                "celltype_opc","celltype_microglia","celltype_endothelial","pathway_gaba_receptor_activation","pathway_serotonin_receptors"]
    for name in required:
        if len(frozen[name]["primary_genes"]) < 2:
            blockers.append(f"{name} has fewer than two retained primary AHBA genes")

    (out / "gene_sets.json").write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "gene_set_membership.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["set","gene","source","in_primary","in_no_mirror"]); w.writeheader(); w.writerows(rows)
    refs = "# Frozen biological gene-set references\n\n" + "\n".join(f"- **{r['scope']}**: {r['citation']} {r['url']}" for r in REFERENCES) + "\n"
    (out / "references.md").write_text(refs, encoding="utf-8")

    summary = {
        "schema_version": 1,
        "analysis": "model-blind AHBA biological gene-set freeze v1",
        "loads_eeg_samples": False,
        "loads_molecular_sensitivity_values": False,
        "computes_neurosem_outcomes": False,
        "computes_model_quantities": False,
        "computes_gene_set_associations": False,
        "primary_gene_universe_n": len(primary),
        "no_mirror_gene_universe_n": len(no_mirror),
        "reactome_database_version": database_version,
        "reactome_database_version_sha256": db_sha,
        "reactome_queries": reactome_meta,
        "gene_sets": {k: {"category": v["category"], "n_source": len(v["source_genes"]), "n_primary": len(v["primary_genes"]), "n_no_mirror": len(v["no_mirror_genes"]), "missing_primary": v["missing_primary"], "missing_no_mirror": v["missing_no_mirror"]} for k,v in frozen.items()},
        "ready_for_frozen_biological_testing": len(blockers) == 0,
        "blockers": blockers,
        "next_step_if_ready": "Freeze the channel-level neural semantic spatial contribution target and inferential statistic before testing these gene sets. Do not alter membership after seeing NeuroSem outcomes.",
        "guardrails": [
            "Gene-set membership is frozen before any NeuroSem molecular association is computed.",
            "Do not add genes or pathways based on later association strength.",
            "Cell-type panels are compact published human-brain canonical marker panels, not exhaustive cell-state signatures.",
            "Reactome memberships are frozen to the exact database version and API response hashes recorded here.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ready" if not blockers else "blocked", "ready": not blockers, "reactome_version": database_version, "blockers": blockers}, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
