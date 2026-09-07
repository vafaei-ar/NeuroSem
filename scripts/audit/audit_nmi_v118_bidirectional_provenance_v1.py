#!/usr/bin/env python3
"""Second-pass machine-verifiable NeuroSem NMI v1.18 provenance ledger.

Read-only audit of already-completed safe derived outputs. This pass overlays the
v1.17 claim inventory with recovered RunRelay lineage and atomic coverage for the
previously unenumerated dose/model-space/reverse/spatial result families. It does
not train or score models, recompute neural outcomes, select analyses, or edit the
manuscript.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

BASE = Path("docs/NMI_V117_CLAIM_MANIFEST_V1.json")
OVERLAY = Path("docs/NMI_V118_PROVENANCE_OVERLAY_V2.json")
OUT = Path("outputs/nmi_v118_provenance_ledger_v1/latest")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else ["status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        if rows:
            w.writerows(rows)


def split_selector(selector: str) -> list[str]:
    parts, buf, depth = [], [], 0
    for ch in selector:
        if ch == "." and depth == 0:
            parts.append("".join(buf)); buf = []
        else:
            if ch == "[": depth += 1
            elif ch == "]": depth -= 1
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    if depth != 0:
        raise KeyError(f"unbalanced selector: {selector}")
    return parts


def parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if (len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'"):
        return s[1:-1]
    if s.lower() == "true": return True
    if s.lower() == "false": return False
    if s.lower() == "null": return None
    try:
        if re.fullmatch(r"[-+]?\d+", s): return int(s)
        return float(s)
    except ValueError:
        return s


def equivalent(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)
    return str(a) == str(b)


def apply_bracket(value: Any, spec: str) -> Any:
    if re.fullmatch(r"\d+", spec):
        return value[int(spec)]
    if not isinstance(value, list):
        raise KeyError(f"filter applied to non-list: [{spec}]")
    conds = []
    for item in spec.split(","):
        if "=" not in item:
            raise KeyError(f"bad filter condition: {item}")
        k, v = item.split("=", 1)
        conds.append((k.strip(), parse_scalar(v)))
    hits = []
    for rec in value:
        if not isinstance(rec, dict):
            continue
        ok = True
        for k, expected in conds:
            if k not in rec or not equivalent(rec[k], expected):
                ok = False; break
        if ok:
            hits.append(rec)
    if len(hits) != 1:
        raise KeyError(f"filter [{spec}] matched {len(hits)} rows")
    return hits[0]


def select(payload: Any, selector: str) -> Any:
    cur = payload
    for part in split_selector(selector):
        m = re.match(r"^([^\[]+)", part)
        if m:
            key = m.group(1)
            if not isinstance(cur, dict) or key not in cur:
                raise KeyError(f"missing key {key} in {selector}")
            cur = cur[key]
        for spec in re.findall(r"\[([^\]]+)\]", part):
            cur = apply_bracket(cur, spec)
    return cur


def compare_value(reported: Any, observed: Any, tolerance: Any) -> tuple[str, str]:
    if isinstance(reported, bool) or isinstance(observed, bool):
        ok = reported is observed
        return ("verified" if ok else "incorrect", "" if ok else f"reported={reported!r}; observed={observed!r}")
    if isinstance(reported, (int, float)) and isinstance(observed, (int, float)):
        r, o = float(reported), float(observed)
        tol = float(tolerance or 0)
        diff = abs(r - o)
        ok = math.isfinite(r) and math.isfinite(o) and diff <= tol + 1e-15
        return ("verified" if ok else "incorrect", f"abs_diff={diff:.15g}; tolerance={tol:.15g}")
    ok = str(reported) == str(observed)
    return ("verified" if ok else "incorrect", "" if ok else f"reported={reported!r}; observed={observed!r}")


def scan_run07_history() -> dict[str, Any]:
    roots = [Path("outputs/chineseeeg_run07_holdout_rsa"), Path("outputs/chineseeeg_run07_holdout_embeddings")]
    entries = []
    count_keys = {"n_subjects", "n_participants", "n_valid_subjects", "subject_count", "n_subjects_evaluated"}

    def find_counts(x: Any, prefix: str = "") -> list[tuple[str, Any]]:
        out = []
        if isinstance(x, dict):
            for k, v in x.items():
                p = f"{prefix}.{k}" if prefix else k
                if k in count_keys and isinstance(v, (int, float)):
                    out.append((p, v))
                out.extend(find_counts(v, p))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                out.extend(find_counts(v, f"{prefix}[{i}]"))
        return out

    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("summary.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entries.append({
                    "path": str(path),
                    "sha256": sha256(path),
                    "subject_count_candidates": find_counts(data),
                })
            except Exception as e:
                entries.append({"path": str(path), "error": f"{type(e).__name__}: {e}"})
    return {"roots": [str(r) for r in roots], "n_summary_files": len(entries), "entries": entries}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = json.loads(BASE.read_text(encoding="utf-8"))
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    sources = {k: dict(v) for k, v in base["sources"].items()}
    for key, patch in overlay.get("source_overrides", {}).items():
        if key not in sources:
            raise RuntimeError(f"overlay override references absent source: {key}")
        sources[key].update(patch)
    for key, rec in overlay.get("source_additions", {}).items():
        if key in sources:
            raise RuntimeError(f"overlay addition duplicates source: {key}")
        sources[key] = dict(rec)

    added_claims = []
    for claim_file in overlay.get("claim_files", []):
        payload = json.loads(Path(claim_file).read_text(encoding="utf-8"))
        added_claims.extend(payload.get("claims", []))
    claims = list(base.get("claims", [])) + added_claims
    ids = [c["claim_id"] for c in claims]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        raise RuntimeError(f"duplicate claim ids: {dup}")

    exceptions: list[dict[str, Any]] = []
    source_rows = []
    payloads: dict[str, Any] = {}
    for key, src in sources.items():
        p = Path(src["path"])
        exists = p.is_file()
        observed_hash = sha256(p) if exists else ""
        expected_hash = src.get("sha256") or ""
        hash_ok = bool(exists and expected_hash and observed_hash == expected_hash)
        if exists:
            try:
                payloads[key] = json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                payloads[key] = None
                exceptions.append({"exception_type":"source_parse_error","severity":"blocking","source":key,"claim_id":"","detail":f"{type(e).__name__}: {e}"})
        else:
            payloads[key] = None
        missing_meta = [f for f in ("job_id", "job_status", "project_commit", "task") if not src.get(f)]
        if missing_meta:
            exceptions.append({"exception_type":"missing_job_lineage","severity":"blocking","source":key,"claim_id":"","detail":"missing " + ",".join(missing_meta)})
        if not exists:
            exceptions.append({"exception_type":"missing_source_artifact","severity":"blocking","source":key,"claim_id":"","detail":str(p)})
        elif not hash_ok:
            exceptions.append({"exception_type":"source_hash_mismatch","severity":"blocking","source":key,"claim_id":"","detail":f"expected={expected_hash}; observed={observed_hash}"})
        source_rows.append({
            "source_key": key,
            "artifact_path": str(p),
            "expected_sha256": expected_hash,
            "observed_sha256": observed_hash,
            "hash_verified": hash_ok,
            "job_id": src.get("job_id") or "",
            "job_status": src.get("job_status") or "",
            "project_commit": src.get("project_commit") or "",
            "task": src.get("task") or "",
            "provenance_class": src.get("provenance_class") or "",
            "manuscript_disposition": src.get("disposition") or "",
            "lineage_note": src.get("lineage_note") or "",
        })

    claim_rows = []
    claims_by_source = Counter()
    for claim in claims:
        src_key = claim["source"]
        claims_by_source[src_key] += 1
        src = sources.get(src_key)
        status, detail, observed = "missing", "", ""
        if src is None:
            detail = "source key absent from manifest"
        else:
            srow = next(r for r in source_rows if r["source_key"] == src_key)
            if not srow["hash_verified"]:
                status = "unresolved"
                detail = "source artifact missing or hash not verified"
            elif payloads.get(src_key) is None:
                status = "unresolved"
                detail = "source payload unavailable"
            else:
                try:
                    observed = select(payloads[src_key], claim["selector"])
                    status, detail = compare_value(claim["reported_value"], observed, claim.get("tolerance", 0))
                except Exception as e:
                    status = "unresolved"
                    detail = f"selector_error={type(e).__name__}: {e}"
        if status != "verified":
            exceptions.append({"exception_type":f"claim_{status}","severity":"blocking","source":src_key,"claim_id":claim["claim_id"],"detail":detail})
        claim_rows.append({
            "claim_id": claim["claim_id"],
            "manuscript_version": base.get("manuscript_version", "v1.17"),
            "manuscript_location": claim.get("manuscript_location", ""),
            "claim_label": claim.get("claim_label", ""),
            "reported_value": claim.get("reported_value", ""),
            "units_or_scale": claim.get("units_or_scale", ""),
            "inferential_role": claim.get("inferential_role", ""),
            "source_key": src_key,
            "source_job_id": (src or {}).get("job_id") or "",
            "source_job_status": (src or {}).get("job_status") or "",
            "source_project_commit": (src or {}).get("project_commit") or "",
            "artifact_path": (src or {}).get("path") or "",
            "artifact_sha256": (src or {}).get("sha256") or "",
            "field_selector": claim.get("selector", ""),
            "observed_value": observed,
            "comparison_tolerance": claim.get("tolerance", 0),
            "cohort_or_item_set": claim.get("cohort_or_item_set", ""),
            "model_or_adapter_identity": claim.get("model_or_adapter_identity", ""),
            "provenance_class": (src or {}).get("provenance_class") or "",
            "verification_status": status,
            "notes": detail,
        })

    required = overlay.get("required_source_families", [])
    disposition_only = set(overlay.get("disposition_only_sources", []))
    for key in required:
        if claims_by_source[key] == 0 and key not in disposition_only:
            exceptions.append({"exception_type":"claim_coverage_pending","severity":"blocking","source":key,"claim_id":"","detail":"required manuscript source family has no atomic claim rows"})

    for rec in overlay.get("lineage_reconciliations", []):
        if rec.get("status") != "resolved":
            exceptions.append({"exception_type":"lineage_unresolved","severity":"blocking","source":"","claim_id":rec.get("lineage_id", ""),"detail":rec.get("description", "") + ": " + rec.get("resolution", "")})

    for rec in overlay.get("expected_manuscript_corrections", []):
        if not str(rec.get("status", "")).startswith("completed"):
            exceptions.append({"exception_type":"manuscript_or_shipping_correction_pending","severity":"blocking","source":"","claim_id":rec.get("correction_id", ""),"detail":f"{rec.get('location','')}: {rec.get('required_v118','')}"})

    output_rows = []
    for r in source_rows:
        output_rows.append({
            "output_id": r["source_key"],
            "job_id": r["job_id"],
            "job_status": r["job_status"],
            "project_commit": r["project_commit"],
            "task": r["task"],
            "artifact_path": r["artifact_path"],
            "artifact_sha256": r["expected_sha256"],
            "scientific_role": r["provenance_class"],
            "cohort_or_item_set": "",
            "model_or_adapter_identity": "",
            "manuscript_disposition": r["manuscript_disposition"],
            "superseded_by": "",
            "notes": r["lineage_note"],
        })

    run07_scan = scan_run07_history()
    status_counts = Counter(r["verification_status"] for r in claim_rows)
    source_hash_ok = sum(bool(r["hash_verified"]) for r in source_rows)
    unresolved_lineages = [x for x in overlay.get("lineage_reconciliations", []) if x.get("status") != "resolved"]
    pending_corrections = [x for x in overlay.get("expected_manuscript_corrections", []) if not str(x.get("status", "")).startswith("completed")]
    coverage_exceptions = [e for e in exceptions if e["exception_type"] == "claim_coverage_pending"]
    blocking = [e for e in exceptions if e.get("severity") == "blocking"]

    summary = {
        "schema_version": 2,
        "status": "ok",
        "analysis_stage": "second-pass bidirectional provenance ledger expansion",
        "manuscript_version_audited": base.get("manuscript_version", "v1.17"),
        "base_manifest": str(BASE),
        "overlay": str(OVERLAY),
        "claim_rows": len(claim_rows),
        "claim_status_counts": dict(status_counts),
        "source_rows": len(source_rows),
        "verified_source_hashes": source_hash_ok,
        "coverage_complete_for_declared_source_families": not coverage_exceptions,
        "lineage_reconciliations": overlay.get("lineage_reconciliations", []),
        "unresolved_lineage_count": len(unresolved_lineages),
        "pending_manuscript_or_shipping_corrections": pending_corrections,
        "run07_history_scan": run07_scan,
        "exception_rows": len(exceptions),
        "blocking_exception_rows": len(blocking),
        "shipping_gate_pass": len(blocking) == 0,
        "guardrails": {
            "model_training_performed": False,
            "model_evaluation_performed": False,
            "neural_analysis_performed": False,
            "manuscript_editing_performed": False,
            "source_hashes_checked": True,
            "filtered_list_selectors_supported": True,
        },
        "next_action": "Resolve remaining run-07 history and manuscript/shipping corrections; then rebuild v1.18 and rerun a final document-linked shipping ledger." if blocking else "Ledger gate passed; regenerate the final artifact bundle from this state."
    }

    claim_fields = ["claim_id","manuscript_version","manuscript_location","claim_label","reported_value","units_or_scale","inferential_role","source_key","source_job_id","source_job_status","source_project_commit","artifact_path","artifact_sha256","field_selector","observed_value","comparison_tolerance","cohort_or_item_set","model_or_adapter_identity","provenance_class","verification_status","notes"]
    output_fields = ["output_id","job_id","job_status","project_commit","task","artifact_path","artifact_sha256","scientific_role","cohort_or_item_set","model_or_adapter_identity","manuscript_disposition","superseded_by","notes"]
    source_fields = ["source_key","artifact_path","expected_sha256","observed_sha256","hash_verified","job_id","job_status","project_commit","task","provenance_class","manuscript_disposition","lineage_note"]
    exc_fields = ["exception_type","severity","source","claim_id","detail"]
    write_csv(OUT / "claim_to_source.csv", claim_rows, claim_fields)
    write_csv(OUT / "output_to_manuscript.csv", output_rows, output_fields)
    write_csv(OUT / "source_manifest.csv", source_rows, source_fields)
    write_csv(OUT / "exceptions.csv", exceptions, exc_fields)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = [
        "NeuroSem NMI v1.18 bidirectional provenance ledger - second pass",
        "Status: ok",
        f"Claims: {len(claim_rows)} ({dict(status_counts)})",
        f"Sources: {len(source_rows)}; exact source hashes verified: {source_hash_ok}/{len(source_rows)}",
        f"Declared source-family coverage complete: {not coverage_exceptions}",
        f"Unresolved lineages: {len(unresolved_lineages)}",
        f"Pending manuscript/shipping corrections: {len(pending_corrections)}",
        f"Exceptions: {len(exceptions)}; blocking: {len(blocking)}",
        f"Shipping gate pass: {summary['shipping_gate_pass']}",
        f"Run-07 historical summaries discovered: {run07_scan['n_summary_files']}",
        "",
        "The audit intentionally preserves v1.17 discrepancies rather than widening tolerances or rewriting reported values. A final pass must be linked to the edited v1.18 manuscript and fresh artifact bundle."
    ]
    (OUT / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status":"ok","claim_rows":len(claim_rows),"verified":status_counts.get("verified",0),"exceptions":len(exceptions),"shipping_gate_pass":summary["shipping_gate_pass"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
