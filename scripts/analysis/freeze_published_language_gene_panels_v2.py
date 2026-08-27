#!/usr/bin/env python3
"""Freeze exact literature-defined language-related gene panels without NeuroSem outcomes.

Source: Wong et al., PNAS 2024 (doi:10.1073/pnas.2401687121), main article text.
The paper explicitly lists:
1) six genes individually significant within the 56-gene language set for
   pars triangularis-middle temporal structural connectivity;
2) fourteen genes individually significant within the same 56-gene set for dyslexia.

This task is outcome-blind and does not load any NeuroSem target or association result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PANELS = {
    "wong_2024_language_connectivity_6": [
        "BHLHE22", "COL5A2", "NELL2", "RYR3", "SLIT1", "SLIT2",
    ],
    "wong_2024_language_dyslexia_14": [
        "BHLHE22", "CDH10", "DAB1", "DIAPH1", "FBXO32", "GABRD",
        "GPR26", "KCNH5", "KIRREL3", "NEFH", "OXR1", "SLIT1", "SLIT2", "SNCA",
    ],
}

CITATION = "Wong MMK et al. Proc Natl Acad Sci USA. 2024;121(34):e2401687121. doi:10.1073/pnas.2401687121"
SOURCE_NOTE = (
    "Main peer-reviewed article text. Structural-connectivity paragraph lists six genes "
    "individually at P<0.05 among the 26 GAUSS drivers of the significant 56-gene set-level "
    "association for pars triangularis-middle temporal connectivity. Dyslexia paragraph lists "
    "fourteen genes individually at P<0.05 among the 24 GAUSS drivers of the highly significant "
    "56-gene set-level dyslexia association."
)


def load_ahba_genes(root: Path) -> set[str]:
    for p in [root / "primary_leftright" / "gene_symbols.json", root / "primary_leftright" / "genes.json"]:
        if p.exists():
            obj = json.loads(p.read_text(encoding="utf-8"))
            vals = obj.get("genes", obj.get("gene_symbols", obj)) if isinstance(obj, dict) else obj
            return {str(x).upper() for x in vals}
    for p in sorted((root / "primary_leftright").glob("*.csv")):
        try:
            df = pd.read_csv(p, nrows=1)
        except Exception:
            continue
        genes = {str(c).upper() for c in df.columns if str(c).upper() not in {"LABEL", "REGION", "REGION_ID", "ID"}}
        if len(genes) > 10000:
            return genes
    raise FileNotFoundError("Could not locate primary AHBA gene universe")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expression-root", type=Path, default=Path("outputs/ahba_expression_dk_v1/latest"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/published_language_gene_panels_v2/latest"))
    args = ap.parse_args()

    ahba = load_ahba_genes(args.expression_root)
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    panel_obj = {}
    membership_rows = []
    blockers = []
    for panel_id, genes in PANELS.items():
        if len(genes) != len(set(genes)):
            raise RuntimeError(f"Duplicate gene in {panel_id}")
        retained = [g for g in genes if g in ahba]
        missing = [g for g in genes if g not in ahba]
        if len(retained) < max(4, int(0.75 * len(genes))):
            blockers.append(f"Insufficient AHBA retention for {panel_id}: {len(retained)}/{len(genes)}")
        panel_obj[panel_id] = {
            "published_genes": genes,
            "published_n": len(genes),
            "retained_primary_ahba_genes": retained,
            "retained_primary_ahba_n": len(retained),
            "missing_primary_ahba_genes": missing,
        }
        for gene in genes:
            membership_rows.append({
                "panel_id": panel_id,
                "gene": gene,
                "retained_primary_ahba": gene in ahba,
            })

    payload = {
        "schema_version": 2,
        "analysis": "outcome-blind freeze of exact literature-listed language-related gene panels",
        "citation": CITATION,
        "source_definition": SOURCE_NOTE,
        "loads_neurosem_target": False,
        "loads_exploratory_pls_results": False,
        "loads_molecular_association_results": False,
        "loads_model_quantities": False,
        "panels": panel_obj,
        "ready_for_independent_language_gene_validation": not blockers,
        "blockers": blockers,
        "guardrails": [
            "Do not alter panel membership after inspecting NeuroSem associations.",
            "These are exact subsets explicitly listed in the peer-reviewed article, not a reconstruction of Dataset S5.",
            "Treat the structural-connectivity and dyslexia panels as separate literature-defined hypotheses.",
            "Use spatially constrained cortical nulls and size/co-expression-aware gene-set nulls in outcome testing.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out / "gene_panels.json").write_text(json.dumps({"citation": CITATION, "panels": PANELS}, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(membership_rows).to_csv(out / "gene_panel_membership.csv", index=False)
    (out / "references.md").write_text(
        "# Published language-gene panels v2\n\n"
        + CITATION + "\n\n"
        + SOURCE_NOTE + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "ready" if not blockers else "blocked",
        "panels": {k: {"published_n": v["published_n"], "retained_primary_ahba_n": v["retained_primary_ahba_n"]} for k, v in panel_obj.items()},
        "blockers": blockers,
    }, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
