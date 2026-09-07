#!/usr/bin/env python3
"""Final document-linked NMI v1.18 provenance and shipping audit.

This is a read-only verification pass over already-completed safe derived scientific
outputs plus the compact authoring-environment DOCX manifest. It performs no model
training/evaluation, neural analysis, inferential analysis or manuscript editing.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.audit_nmi_v118_bidirectional_provenance_v1 import compare_value, select  # noqa: E402

BASE = ROOT / "docs/NMI_V117_CLAIM_MANIFEST_V1.json"
V2 = ROOT / "docs/NMI_V118_PROVENANCE_OVERLAY_V2.json"
V3 = ROOT / "docs/NMI_V118_FINAL_OVERLAY_V3.json"
DOC_MANIFEST = ROOT / "docs/NMI_V118_DOCUMENT_MANIFEST_V1.json"
BUNDLE_MANIFEST = ROOT / "outputs/nmi_v118_submission_bundle_v1/latest/bundle_manifest.json"
PUBLICATION_MANIFEST = ROOT / "outputs/nmi_main_figures_v3/latest/source_manifest.json"
FIG1_MANIFEST = ROOT / "outputs/nmi_v118_figure1_provenance_v1/latest/source_manifest.json"
OUT = ROOT / "outputs/nmi_v118_final_shipping_audit_v1/latest"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else ["status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        if rows:
            w.writerows(rows)


def merged_state() -> tuple[dict[str, dict], list[dict], list[dict], list[dict]]:
    base = load(BASE); v2 = load(V2); v3 = load(V3)
    sources = {k: dict(v) for k, v in base["sources"].items()}
    for key, patch in v2.get("source_overrides", {}).items():
        sources[key].update(patch)
    for key, rec in v2.get("source_additions", {}).items():
        sources[key] = dict(rec)
    for key, rec in v3.get("source_additions", {}).items():
        sources[key] = dict(rec)

    claims = [dict(c) for c in base.get("claims", [])]
    for claim_file in v2.get("claim_files", []):
        claims.extend(dict(c) for c in load(ROOT / claim_file).get("claims", []))
    by_id = {c["claim_id"]: c for c in claims}
    for cid, patch in v3.get("claim_overrides", {}).items():
        if cid not in by_id:
            raise RuntimeError(f"Unknown v1.18 claim override: {cid}")
        by_id[cid].update(patch)
    claims = list(by_id.values())

    lineages = [dict(x) for x in v2.get("lineage_reconciliations", [])]
    lineage_by = {x["lineage_id"]: x for x in lineages}
    for lid, patch in v3.get("lineage_overrides", {}).items():
        if lid not in lineage_by:
            raise RuntimeError(f"Unknown lineage override: {lid}")
        lineage_by[lid].update(patch)

    corrections = [dict(x) for x in v2.get("expected_manuscript_corrections", [])]
    correction_by = {x["correction_id"]: x for x in corrections}
    for cid, patch in v3.get("manuscript_correction_overrides", {}).items():
        if cid not in correction_by:
            raise RuntimeError(f"Unknown correction override: {cid}")
        correction_by[cid].update(patch)
    return sources, claims, list(lineage_by.values()), list(correction_by.values())


def check_document_manifest(exceptions: list[dict]) -> bool:
    if not DOC_MANIFEST.is_file():
        exceptions.append({"exception_type":"document_manifest_missing","severity":"blocking","source":"","claim_id":"","detail":str(DOC_MANIFEST)})
        return False
    d = load(DOC_MANIFEST)
    ok = True
    if d.get("manuscript_version") != "v1.18" or len(d.get("documents", [])) != 4:
        ok = False
    for rec in d.get("documents", []):
        if not re.fullmatch(r"[0-9a-f]{64}", str(rec.get("sha256", ""))): ok = False
        if int(rec.get("pages_rendered_and_inspected", 0)) <= 0: ok = False
        if rec.get("zip_integrity") != "passed": ok = False
    for value in d.get("required_v118_corrections", {}).values():
        if value is not True: ok = False
    for value in d.get("negative_text_checks", {}).values():
        if value is not True: ok = False
    vqa = d.get("visual_qa", {})
    if not all(vqa.get(k) is True for k in ("all_final_pages_inspected", "no_clipping_or_overlap_detected", "figure1_docx_render_checked_after_svg_raster_wrapper_fix", "supplement_expanded_table6_checked_at_full_page")):
        ok = False
    if not ok:
        exceptions.append({"exception_type":"document_manifest_failed","severity":"blocking","source":"","claim_id":"","detail":"v1.18 document hash/structural/correction/visual-QA manifest did not satisfy all required checks"})
    return ok


def check_publication_figure1(exceptions: list[dict]) -> bool:
    if not PUBLICATION_MANIFEST.is_file() or not FIG1_MANIFEST.is_file():
        exceptions.append({"exception_type":"publication_figure1_missing","severity":"blocking","source":"","claim_id":"","detail":"publication or Figure 1 provenance manifest missing"})
        return False
    pub = load(PUBLICATION_MANIFEST)
    fig1_sha = sha256(FIG1_MANIFEST)
    ok = pub.get("status") == "ok" and pub.get("figure1_provenance_source_manifest_sha256") == fig1_sha
    outputs = pub.get("outputs", {})
    for ext in ("pdf", "svg", "png"):
        canonical = ROOT / f"outputs/nmi_main_figures_v3/latest/figure1.{ext}"
        provenance = ROOT / f"outputs/nmi_v118_figure1_provenance_v1/latest/figure1.{ext}"
        if not canonical.is_file() or not provenance.is_file() or sha256(canonical) != sha256(provenance):
            ok = False
    if not ok:
        exceptions.append({"exception_type":"publication_figure1_not_provenance_linked","severity":"blocking","source":"","claim_id":"","detail":"canonical Figure 1 is not byte-linked to the pinned provenance Figure 1 outputs"})
    return ok


def check_bundle(sources: dict[str, dict], exceptions: list[dict]) -> bool:
    if not BUNDLE_MANIFEST.is_file():
        exceptions.append({"exception_type":"fresh_bundle_missing","severity":"blocking","source":"","claim_id":"CORR_FRESH_BUNDLE","detail":str(BUNDLE_MANIFEST)})
        return False
    b = load(BUNDLE_MANIFEST)
    zip_path = ROOT / str(b.get("bundle", ""))
    listed = {rec.get("path") for rec in b.get("files", [])}
    required = {rec["path"] for rec in sources.values()}
    required.update({
        str(DOC_MANIFEST.relative_to(ROOT)),
        str(V3.relative_to(ROOT)),
        "outputs/publication_figures_tables_v2/latest/reproducibility_manifest.json",
        "outputs/nmi_main_figures_v3/latest/source_manifest.json",
        "outputs/nmi_v118_run07_history_audit_v1/latest/history.csv",
        "outputs/nmi_mpnet_model_space_comparison_v1/latest/seed_comparison_metrics.csv",
    })
    ok = (
        b.get("status") == "ok"
        and zip_path.is_file()
        and re.fullmatch(r"[0-9a-f]{64}", str(b.get("bundle_sha256", ""))) is not None
        and sha256(zip_path) == b.get("bundle_sha256")
        and required.issubset(listed)
        and b.get("guardrails", {}).get("september_provenance_and_postconfirmatory_outputs_included") is True
        and b.get("guardrails", {}).get("raw_neural_data_included") is False
        and b.get("guardrails", {}).get("document_hash_manifest_included") is True
    )
    if not ok:
        missing = sorted(required - listed)
        exceptions.append({"exception_type":"fresh_bundle_failed","severity":"blocking","source":"","claim_id":"CORR_FRESH_BUNDLE","detail":"bundle integrity/coverage failed; missing=" + ",".join(missing)})
    return ok


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sources, claims, lineages, corrections = merged_state()
    exceptions: list[dict[str, Any]] = []

    source_rows = []
    payloads = {}
    for key, src in sources.items():
        path = ROOT / src["path"]
        exists = path.is_file()
        observed = sha256(path) if exists else ""
        expected = src.get("sha256") or ""
        hash_ok = bool(exists and expected and observed == expected)
        if not exists:
            exceptions.append({"exception_type":"missing_source_artifact","severity":"blocking","source":key,"claim_id":"","detail":src["path"]})
        elif not hash_ok:
            exceptions.append({"exception_type":"source_hash_mismatch","severity":"blocking","source":key,"claim_id":"","detail":f"expected={expected}; observed={observed}"})
        try:
            payloads[key] = load(path) if exists else None
        except Exception as e:
            payloads[key] = None
            exceptions.append({"exception_type":"source_parse_error","severity":"blocking","source":key,"claim_id":"","detail":f"{type(e).__name__}: {e}"})
        missing_meta = [f for f in ("job_id", "job_status", "project_commit", "task") if not src.get(f)]
        if missing_meta:
            exceptions.append({"exception_type":"missing_job_lineage","severity":"blocking","source":key,"claim_id":"","detail":"missing " + ",".join(missing_meta)})
        source_rows.append({
            "source_key": key, "artifact_path": src["path"], "expected_sha256": expected,
            "observed_sha256": observed, "hash_verified": hash_ok, "job_id": src.get("job_id", ""),
            "job_status": src.get("job_status", ""), "project_commit": src.get("project_commit", ""),
            "task": src.get("task", ""), "provenance_class": src.get("provenance_class", ""),
        })

    claim_rows = []
    for claim in claims:
        src_key = claim["source"]; src = sources.get(src_key)
        status, detail, observed = "unresolved", "", ""
        srow = next((r for r in source_rows if r["source_key"] == src_key), None)
        if src is None or srow is None:
            detail = "source key absent"
        elif not srow["hash_verified"] or payloads.get(src_key) is None:
            detail = "source hash/payload unavailable"
        else:
            try:
                observed = select(payloads[src_key], claim["selector"])
                status, detail = compare_value(claim["reported_value"], observed, claim.get("tolerance", 0))
            except Exception as e:
                detail = f"selector_error={type(e).__name__}: {e}"
        if status != "verified":
            exceptions.append({"exception_type":f"claim_{status}","severity":"blocking","source":src_key,"claim_id":claim["claim_id"],"detail":detail})
        claim_rows.append({
            "claim_id": claim["claim_id"], "manuscript_version": "v1.18",
            "manuscript_location": claim.get("manuscript_location", ""), "claim_label": claim.get("claim_label", ""),
            "reported_value": claim.get("reported_value", ""), "observed_value": observed,
            "comparison_tolerance": claim.get("tolerance", 0), "source_key": src_key,
            "artifact_path": (src or {}).get("path", ""), "artifact_sha256": (src or {}).get("sha256", ""),
            "field_selector": claim.get("selector", ""), "verification_status": status, "notes": detail,
        })

    for rec in lineages:
        if rec.get("status") != "resolved":
            exceptions.append({"exception_type":"lineage_unresolved","severity":"blocking","source":"","claim_id":rec.get("lineage_id", ""),"detail":rec.get("description", "")})

    document_ok = check_document_manifest(exceptions)
    figure1_ok = check_publication_figure1(exceptions)
    bundle_ok = check_bundle(sources, exceptions)

    correction_rows = []
    for rec in corrections:
        cid = rec["correction_id"]
        status = rec.get("status", "")
        if cid == "CORR_FRESH_BUNDLE":
            complete = bundle_ok
            runtime_status = "completed_runtime_bundle" if complete else status
        else:
            complete = str(status).startswith("completed")
            runtime_status = status
        if not complete:
            exceptions.append({"exception_type":"manuscript_or_shipping_correction_pending","severity":"blocking","source":"","claim_id":cid,"detail":f"{rec.get('location','')}: status={runtime_status}"})
        correction_rows.append({"correction_id":cid,"status":runtime_status,"complete":complete})

    status_counts = Counter(r["verification_status"] for r in claim_rows)
    all_claims = len(claim_rows) == 129 and status_counts.get("verified", 0) == 129
    all_sources = all(bool(r["hash_verified"]) for r in source_rows)
    all_lineages = all(x.get("status") == "resolved" for x in lineages)
    all_corrections = all(bool(x["complete"]) for x in correction_rows)
    blocking = [e for e in exceptions if e.get("severity") == "blocking"]
    shipping_gate = bool(all_claims and all_sources and all_lineages and all_corrections and document_ok and figure1_ok and bundle_ok and not blocking)

    summary = {
        "schema_version": 1,
        "status": "ok" if shipping_gate else "blocked",
        "manuscript_version_audited": "v1.18",
        "claim_rows": len(claim_rows),
        "claim_status_counts": dict(status_counts),
        "source_rows": len(source_rows),
        "verified_source_hashes": sum(bool(r["hash_verified"]) for r in source_rows),
        "lineage_rows": len(lineages),
        "unresolved_lineage_count": sum(x.get("status") != "resolved" for x in lineages),
        "document_manifest_ok": document_ok,
        "publication_figure1_provenance_linked": figure1_ok,
        "fresh_bundle_ok": bundle_ok,
        "corrections": correction_rows,
        "blocking_exception_rows": len(blocking),
        "shipping_gate_pass": shipping_gate,
        "guardrails": {
            "model_training_performed": False,
            "model_evaluation_performed": False,
            "neural_analysis_performed": False,
            "manuscript_editing_performed": False,
            "docx_bytes_committed_to_public_repo": False,
        },
    }
    write_csv(OUT / "claim_to_source.csv", claim_rows)
    write_csv(OUT / "source_manifest.csv", source_rows)
    write_csv(OUT / "exceptions.csv", exceptions, ["exception_type","severity","source","claim_id","detail"])
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.txt").write_text(
        "NeuroSem NMI v1.18 final shipping audit\n"
        f"Status: {summary['status']}\n"
        f"Claims: {len(claim_rows)} ({dict(status_counts)})\n"
        f"Sources: {len(source_rows)}; exact source hashes verified: {summary['verified_source_hashes']}/{len(source_rows)}\n"
        f"Unresolved lineages: {summary['unresolved_lineage_count']}\n"
        f"Document manifest: {'PASS' if document_ok else 'FAIL'}\n"
        f"Canonical Figure 1 provenance link: {'PASS' if figure1_ok else 'FAIL'}\n"
        f"Fresh September bundle: {'PASS' if bundle_ok else 'FAIL'}\n"
        f"Blocking exceptions: {len(blocking)}\n"
        f"Shipping gate pass: {shipping_gate}\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0 if shipping_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
