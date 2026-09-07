#!/usr/bin/env python3
"""Build the first machine-verifiable NeuroSem NMI v1.18 provenance ledger.

This is a read-only audit of already-completed derived outputs. It does not train or
score models, recompute neural outcomes, select analyses, or edit the manuscript.
The starting claim/source manifest is committed separately so unresolved lineage is
visible rather than silently inferred.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "NMI_V117_CLAIM_MANIFEST_V1.json"
OUT = ROOT / "outputs" / "nmi_v118_provenance_ledger_v1" / "latest"

CLAIM_FIELDS = [
    "claim_id", "manuscript_version", "manuscript_location", "claim_label",
    "reported_value", "units_or_scale", "inferential_role", "source_job_id",
    "source_job_status", "source_project_commit", "artifact_path", "artifact_sha256",
    "field_selector", "observed_value", "comparison_tolerance", "cohort_or_item_set",
    "model_or_adapter_identity", "provenance_class", "verification_status", "notes",
]
OUTPUT_FIELDS = [
    "output_id", "job_id", "job_status", "project_commit", "task", "artifact_path",
    "artifact_sha256", "scientific_role", "cohort_or_item_set", "model_or_adapter_identity",
    "manuscript_disposition", "superseded_by", "notes",
]
EXCEPTION_FIELDS = ["exception_id", "severity", "category", "source_or_claim", "message"]
SOURCE_FIELDS = [
    "source_id", "artifact_path", "expected_sha256", "observed_sha256", "hash_status",
    "job_id", "job_status", "project_commit", "task", "provenance_class", "disposition",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_structured(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    raise ValueError(f"Unsupported structured source: {path}")


def selector_tokens(selector: str) -> list[Any]:
    tokens: list[Any] = []
    for part in selector.split("."):
        m = re.fullmatch(r"([^\[]+)(.*)", part)
        if not m:
            raise KeyError(selector)
        tokens.append(m.group(1))
        tail = m.group(2)
        for idx in re.findall(r"\[(\d+)\]", tail):
            tokens.append(int(idx))
    return tokens


def select(obj: Any, selector: str) -> Any:
    cur = obj
    for token in selector_tokens(selector):
        if isinstance(token, int):
            cur = cur[token]
        else:
            cur = cur[token]
    return cur


def comparable(observed: Any, reported: Any, tolerance: float) -> tuple[bool, str]:
    if isinstance(reported, bool):
        return observed is reported, f"observed={observed!r}"
    if isinstance(reported, (int, float)) and not isinstance(reported, bool):
        try:
            obs = float(observed)
            rep = float(reported)
        except Exception:
            return False, f"non-numeric observed={observed!r}"
        if not (math.isfinite(obs) and math.isfinite(rep)):
            return False, f"non-finite comparison observed={obs}, reported={rep}"
        diff = abs(obs - rep)
        return diff <= float(tolerance), f"abs_diff={diff:.12g}"
    return str(observed) == str(reported), f"observed={observed!r}"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manuscript_version = manifest["manuscript_version"]

    exceptions: list[dict] = []
    source_rows: list[dict] = []
    source_cache: dict[str, Any] = {}
    source_state: dict[str, dict] = {}

    for source_id, src in manifest["sources"].items():
        path = ROOT / src["path"]
        observed_sha = ""
        hash_status = "missing"
        if path.exists() and path.is_file():
            observed_sha = sha256_file(path)
            hash_status = "verified" if observed_sha == src.get("sha256") else "mismatch"
            if path.suffix.lower() in {".json", ".csv"}:
                try:
                    source_cache[source_id] = load_structured(path)
                except Exception as exc:
                    exceptions.append({
                        "exception_id": f"SRC_PARSE_{source_id}", "severity": "blocking",
                        "category": "source_parse", "source_or_claim": source_id,
                        "message": f"Could not parse {src['path']}: {type(exc).__name__}: {exc}",
                    })
        else:
            exceptions.append({
                "exception_id": f"SRC_MISSING_{source_id}", "severity": "blocking",
                "category": "missing_artifact", "source_or_claim": source_id,
                "message": f"Required artifact is missing: {src['path']}",
            })
        if hash_status == "mismatch":
            exceptions.append({
                "exception_id": f"SRC_HASH_{source_id}", "severity": "blocking",
                "category": "hash_mismatch", "source_or_claim": source_id,
                "message": f"Expected {src.get('sha256')} but observed {observed_sha} for {src['path']}",
            })
        missing_meta = [k for k in ("job_id", "project_commit", "task") if not src.get(k)]
        if missing_meta:
            exceptions.append({
                "exception_id": f"SRC_META_{source_id}", "severity": "major",
                "category": "missing_job_lineage", "source_or_claim": source_id,
                "message": "Missing source job metadata fields: " + ", ".join(missing_meta),
            })
        source_state[source_id] = {"path": path, "hash_status": hash_status, "observed_sha": observed_sha, **src}
        source_rows.append({
            "source_id": source_id, "artifact_path": src["path"],
            "expected_sha256": src.get("sha256", ""), "observed_sha256": observed_sha,
            "hash_status": hash_status, "job_id": src.get("job_id") or "",
            "job_status": src.get("job_status") or "", "project_commit": src.get("project_commit") or "",
            "task": src.get("task") or "", "provenance_class": src.get("provenance_class") or "",
            "disposition": src.get("disposition") or "",
        })

    claim_rows: list[dict] = []
    for claim in manifest["claims"]:
        source_id = claim["source"]
        src = source_state.get(source_id)
        observed: Any = ""
        status = "missing"
        notes: list[str] = []
        if src is None:
            notes.append("source id absent from manifest")
        elif src["hash_status"] != "verified":
            status = "missing" if src["hash_status"] == "missing" else "unresolved"
            notes.append(f"source hash status={src['hash_status']}")
        elif source_id not in source_cache:
            status = "unresolved"
            notes.append("structured source was not parsed")
        else:
            try:
                observed = select(source_cache[source_id], claim["selector"])
                ok, detail = comparable(observed, claim["reported_value"], claim.get("tolerance", 0.0))
                status = "verified" if ok else "incorrect"
                notes.append(detail)
            except Exception as exc:
                status = "unresolved"
                notes.append(f"selector failed: {type(exc).__name__}: {exc}")
        if status != "verified":
            exceptions.append({
                "exception_id": f"CLAIM_{claim['claim_id']}",
                "severity": "blocking" if claim.get("inferential_role") == "primary" else "major",
                "category": f"claim_{status}", "source_or_claim": claim["claim_id"],
                "message": "; ".join(notes) or status,
            })
        claim_rows.append({
            "claim_id": claim["claim_id"], "manuscript_version": manuscript_version,
            "manuscript_location": claim.get("manuscript_location", ""), "claim_label": claim.get("claim_label", ""),
            "reported_value": claim.get("reported_value", ""), "units_or_scale": claim.get("units_or_scale", ""),
            "inferential_role": claim.get("inferential_role", ""), "source_job_id": src.get("job_id") or "" if src else "",
            "source_job_status": src.get("job_status") or "" if src else "", "source_project_commit": src.get("project_commit") or "" if src else "",
            "artifact_path": src.get("path") or "" if src else "", "artifact_sha256": src.get("observed_sha") or "" if src else "",
            "field_selector": claim.get("selector", ""), "observed_value": observed,
            "comparison_tolerance": claim.get("tolerance", 0), "cohort_or_item_set": claim.get("cohort_or_item_set", ""),
            "model_or_adapter_identity": claim.get("model_or_adapter_identity", ""),
            "provenance_class": src.get("provenance_class") or "" if src else "",
            "verification_status": status, "notes": "; ".join(notes),
        })

    claim_sources = {c["source"] for c in manifest["claims"]}
    output_rows: list[dict] = []
    for source_id, src in source_state.items():
        output_rows.append({
            "output_id": source_id, "job_id": src.get("job_id") or "", "job_status": src.get("job_status") or "",
            "project_commit": src.get("project_commit") or "", "task": src.get("task") or "",
            "artifact_path": src.get("path") or "", "artifact_sha256": src.get("observed_sha") or "",
            "scientific_role": "claim-bearing" if source_id in claim_sources else "required reverse-ledger source family",
            "cohort_or_item_set": "", "model_or_adapter_identity": "",
            "manuscript_disposition": src.get("disposition") or "", "superseded_by": "",
            "notes": "hash-pinned" if src.get("hash_status") == "verified" else f"hash_status={src.get('hash_status')}",
        })

    for source_id in manifest.get("required_source_families_without_atomic_claim_rows_yet", []):
        exceptions.append({
            "exception_id": f"COVERAGE_{source_id}", "severity": "major", "category": "claim_coverage_pending",
            "source_or_claim": source_id,
            "message": "Source family is in manuscript scope but atomic v1.17 claim rows have not yet been enumerated in the claim manifest.",
        })
    for i, message in enumerate(manifest.get("known_lineage_exceptions_to_test", []), start=1):
        exceptions.append({
            "exception_id": f"LINEAGE_{i:02d}", "severity": "major", "category": "lineage_reconciliation_pending",
            "source_or_claim": "cross-source", "message": message,
        })

    write_csv(OUT / "claim_to_source.csv", claim_rows, CLAIM_FIELDS)
    write_csv(OUT / "output_to_manuscript.csv", output_rows, OUTPUT_FIELDS)
    write_csv(OUT / "exceptions.csv", exceptions, EXCEPTION_FIELDS)
    write_csv(OUT / "source_manifest.csv", source_rows, SOURCE_FIELDS)

    status_counts: dict[str, int] = {}
    for row in claim_rows:
        status_counts[row["verification_status"]] = status_counts.get(row["verification_status"], 0) + 1
    severity_counts: dict[str, int] = {}
    for row in exceptions:
        severity_counts[row["severity"]] = severity_counts.get(row["severity"], 0) + 1
    summary = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "v1.18 bidirectional provenance ledger first pass",
        "manuscript_version_audited": manuscript_version,
        "claim_rows": len(claim_rows),
        "claim_status_counts": status_counts,
        "source_rows": len(source_rows),
        "verified_source_hashes": sum(r["hash_status"] == "verified" for r in source_rows),
        "exception_rows": len(exceptions),
        "exception_severity_counts": severity_counts,
        "shipping_gate_pass": bool(claim_rows) and all(r["verification_status"] == "verified" for r in claim_rows) and not exceptions,
        "guardrails": {
            "model_training_performed": False,
            "neural_analysis_performed": False,
            "model_evaluation_performed": False,
            "manuscript_edited": False,
            "unresolved_items_are_preserved": True,
        },
        "next_action": "Resolve exceptions, enumerate remaining manuscript claim families, rerun until the shipping gate criteria in docs/NMI_V118_PROVENANCE_LEDGER_SPEC.md are satisfied.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [
        "NeuroSem NMI v1.18 bidirectional provenance ledger - first pass",
        "",
        f"Claim rows: {len(claim_rows)}",
        "Claim status: " + ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items())),
        f"Source rows: {len(source_rows)}; verified source hashes: {summary['verified_source_hashes']}",
        f"Exceptions: {len(exceptions)} (" + ", ".join(f"{k}={v}" for k, v in sorted(severity_counts.items())) + ")",
        f"Shipping gate pass: {summary['shipping_gate_pass']}",
        "",
        "This is intentionally a first pass. Any missing job lineage, incomplete claim-family coverage,",
        "failed/recovery lineage, or source mismatch remains explicit in exceptions.csv.",
    ]
    (OUT / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
