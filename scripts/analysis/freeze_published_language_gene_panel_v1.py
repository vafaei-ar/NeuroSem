#!/usr/bin/env python3
"""Freeze an external human language-cortex gene panel before NeuroSem testing.

Primary external source: Wong et al., PNAS 2024, Dataset S5. The paper defines
56 genes with region-specific laminar expression differences between frontal and
temporal language cortex plus upregulation in layer II/III and/or layer V/VI
excitatory corticocortical projection neurons.

This task is outcome-blind: it does not open NeuroSem semantic targets,
whole-transcriptome discovery results, molecular association results, or model
quantities. It only retrieves the published supplementary table, validates the
56-gene definition, and checks overlap with the frozen AHBA gene universe.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

import pandas as pd

SOURCE_URLS = [
    "https://www.pnas.org/doi/suppl/10.1073/pnas.2401687121/suppl_file/pnas.2401687121.sd05.xlsx",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11348331/bin/pnas.2401687121.sd05.xlsx?download=1",
    "https://pmc.ncbi.nlm.nih.gov/articles/instance/11348331/bin/pnas.2401687121.sd05.xlsx?download=1",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11348331/bin/pnas.2401687121.sd05.xlsx",
]
ANCHORS = {"PTPRK", "SOSTDC1", "NELL1", "NELL2", "SLIT1", "SLIT2", "RYR3", "SNCA", "LMO3", "LMO4", "CDH10"}
XLSX_MAGIC = b"PK\x03\x04"


def download_first(urls: list[str]) -> tuple[str, bytes]:
    errors = []
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 NeuroSem/1.0 scientific reproducibility",
                    "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                content_type = str(r.headers.get("Content-Type", ""))
                final_url = str(r.geturl())
            if len(data) < 1000:
                raise RuntimeError(f"response too small: {len(data)} bytes")
            if not data.startswith(XLSX_MAGIC):
                prefix = data[:80].decode("utf-8", errors="replace").replace("\n", " ")
                raise RuntimeError(
                    f"response is not XLSX ZIP bytes; content_type={content_type!r}; final_url={final_url!r}; prefix={prefix!r}"
                )
            return final_url, data
        except Exception as e:
            errors.append(f"{url}: {type(e).__name__}: {e}")
    raise RuntimeError("Could not retrieve Dataset S5 as XLSX: " + " | ".join(errors))


def norm_gene(x) -> str:
    s = str(x).strip().upper()
    return s if re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{1,30}", s) else ""


def extract_panel(xlsx: bytes) -> tuple[list[str], dict]:
    book = pd.read_excel(io.BytesIO(xlsx), sheet_name=None, engine="openpyxl")
    candidates = []
    for sheet_name, df in book.items():
        for gene_col in df.columns:
            genes = df[gene_col].map(norm_gene)
            anchor_hits = len(set(genes[genes.ne("")]) & ANCHORS)
            if anchor_hits < 3:
                continue
            pcols = [c for c in df.columns if any(k in str(c).lower() for k in ["fdr", "adj", "adjust", "q value", "q-value"])]
            unique = sorted(set(genes[genes.ne("")]))
            if len(unique) == 56 and ANCHORS.issubset(set(unique)):
                candidates.append((unique, {"sheet": sheet_name, "gene_column": str(gene_col), "filter": "sheet contains exactly 56 unique gene symbols"}))
            for pc in pcols:
                pv = pd.to_numeric(df[pc], errors="coerce")
                sel = sorted(set(genes[(genes.ne("")) & pv.lt(0.01)]))
                if len(sel) == 56 and ANCHORS.issubset(set(sel)):
                    candidates.append((sel, {"sheet": sheet_name, "gene_column": str(gene_col), "p_column": str(pc), "filter": "adjusted layer*lobe interaction p < 0.01"}))
    uniq = {tuple(g): meta for g, meta in candidates}
    if len(uniq) != 1:
        raise RuntimeError(f"Expected one unambiguous 56-gene extraction, found {len(uniq)} candidates")
    genes_tuple, meta = next(iter(uniq.items()))
    return list(genes_tuple), meta


def load_ahba_genes(root: Path) -> set[str]:
    paths = [
        root / "primary_leftright" / "gene_symbols.json",
        root / "primary_leftright" / "genes.json",
    ]
    for p in paths:
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
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/published_language_gene_panel_v1/latest"))
    args = ap.parse_args()

    url, raw = download_first(SOURCE_URLS)
    sha = hashlib.sha256(raw).hexdigest()
    genes, extraction = extract_panel(raw)
    if len(genes) != 56:
        raise RuntimeError(f"Expected exactly 56 published genes, got {len(genes)}")
    if not ANCHORS.issubset(set(genes)):
        raise RuntimeError("Published-panel anchor-gene validation failed")

    ahba = load_ahba_genes(args.expression_root)
    retained = [g for g in genes if g in ahba]
    missing = [g for g in genes if g not in ahba]
    blockers = []
    if len(retained) < 40:
        blockers.append(f"Fewer than 40/56 published language genes retained in primary AHBA universe: {len(retained)}")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    panel = {
        "panel_id": "wong_2024_language_laminar_56",
        "citation": "Wong MMK et al. Proc Natl Acad Sci USA. 2024;121(34):e2401687121. doi:10.1073/pnas.2401687121",
        "published_n": 56,
        "published_genes": genes,
        "retained_primary_ahba_genes": retained,
        "missing_primary_ahba_genes": missing,
        "source_url": url,
        "source_sha256": sha,
        "extraction": extraction,
    }
    (out / "gene_panel.json").write_text(json.dumps(panel, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame({"gene": genes, "retained_primary_ahba": [g in ahba for g in genes]}).to_csv(out / "gene_panel_membership.csv", index=False)
    refs = (
        "# Published language-gene panel v1\n\n"
        "Primary source: Wong MMK, Sha Z, Luetje L, Kong X-Z, et al. The neocortical infrastructure for language involves region-specific patterns of laminar gene expression. PNAS. 2024;121(34):e2401687121. doi:10.1073/pnas.2401687121.\n\n"
        "Frozen definition: the 56 genes in Dataset S5 satisfying FDR < 0.01 for layer-by-lobe interaction and upregulation in layer II/III and/or layer V/VI excitatory corticocortical projection neurons, as defined by the paper.\n"
    )
    (out / "references.md").write_text(refs, encoding="utf-8")
    summary = {
        "schema_version": 1,
        "analysis": "outcome-blind external human language-cortex gene-panel freeze v1",
        "loads_neurosem_target": False,
        "loads_exploratory_pls_results": False,
        "loads_molecular_association_results": False,
        "loads_model_quantities": False,
        "published_panel": "wong_2024_language_laminar_56",
        "published_n": 56,
        "retained_primary_ahba_n": len(retained),
        "missing_primary_ahba_n": len(missing),
        "missing_primary_ahba_genes": missing,
        "source_url": url,
        "source_sha256": sha,
        "extraction": extraction,
        "ready_for_independent_language_gene_validation": not blockers,
        "blockers": blockers,
        "guardrails": [
            "Do not change panel membership after inspecting NeuroSem associations.",
            "Treat this as independent external validation, not confirmation of the earlier GABA/serotonin hypothesis.",
            "Use both a spatially constrained cortical null and a gene-set/co-expression-aware null in the association test.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ready" if not blockers else "blocked", "published_n": 56, "retained_primary_ahba_n": len(retained), "blockers": blockers}, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
