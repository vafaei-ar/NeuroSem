#!/usr/bin/env python3
"""Reconstruct the historical ChineseEEG run-07 derived-output lineage.

Read-only provenance audit. It scans safe derived NeuroSem outputs and records only
aggregate cohort-count metadata, timestamps, paths, and hashes. It does not read raw
EEG arrays, score models, rerun analyses, or export participant identifiers.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

OUT = Path("outputs/nmi_v118_run07_history_audit_v1/latest")
OUTPUTS = Path("outputs")
CURRENT_DEV = Path("paper/figure_data/chineseeeg_development_v1.json")
TS_RE = re.compile(r"(20\d{6})[_-]?(\d{6})")
RUN_RE = re.compile(r"run[-_ ]?0?7|run07", re.I)
COUNT_KEYS = {
    "n_subjects", "n_participants", "n_valid_subjects", "subject_count",
    "participant_count", "n_subjects_evaluated", "n_frozen_subjects",
    "n_retained_subjects", "n_included_subjects",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def timestamp_from_path(path: Path) -> str:
    hits = TS_RE.findall(str(path))
    if not hits:
        return ""
    d, t = hits[-1]
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}"


def aggregate_counts(x: Any, prefix: str = "") -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{prefix}.{k}" if prefix else k
            if k in COUNT_KEYS and isinstance(v, (int, float)) and float(v).is_integer():
                out.append((p, int(v)))
            lk = k.lower()
            if isinstance(v, list) and ("subject" in lk or "participant" in lk):
                # Record only aggregate length, never identifiers.
                out.append((p + ".len", len(v)))
            out.extend(aggregate_counts(v, p))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if isinstance(v, (dict, list)):
                out.extend(aggregate_counts(v, f"{prefix}[{i}]"))
    return out


def looks_run07(path: Path, text: str) -> bool:
    rel = str(path).lower()
    if "chineseeeg" not in rel and "chinese" not in rel:
        # Content can still establish ChineseEEG lineage.
        if "chineseeeg" not in text.lower() and "chinese eeg" not in text.lower():
            return False
    return bool(RUN_RE.search(rel) or RUN_RE.search(text))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []

    # Summary/manifest JSONs are the canonical machine-readable historical evidence.
    candidates = []
    if OUTPUTS.exists():
        for p in OUTPUTS.rglob("*.json"):
            if p.name in {"summary.json", "source_manifest.json", "manifest.json", "recovery_manifest.json"}:
                candidates.append(p)

    for path in sorted(candidates):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if not looks_run07(path, text):
            continue
        try:
            data = json.loads(text)
        except Exception as e:
            parse_errors.append({"path": str(path), "error": f"{type(e).__name__}: {e}"})
            continue
        counts = aggregate_counts(data)
        unique_counts = sorted({v for _, v in counts if 0 <= v <= 100})
        rows.append({
            "timestamp_from_path": timestamp_from_path(path),
            "artifact_path": str(path),
            "sha256": sha256(path),
            "cohort_count_candidates": ";".join(str(v) for v in unique_counts),
            "count_fields": ";".join(f"{k}={v}" for k, v in counts),
        })

    rows.sort(key=lambda r: (r["timestamp_from_path"] or "9999", r["artifact_path"]))
    distinct_counts = sorted({int(x) for r in rows for x in r["cohort_count_candidates"].split(";") if x})
    count9 = sum("9" in r["cohort_count_candidates"].split(";") for r in rows)
    count10 = sum("10" in r["cohort_count_candidates"].split(";") for r in rows)

    current = {}
    if CURRENT_DEV.is_file():
        d = json.loads(CURRENT_DEV.read_text(encoding="utf-8"))
        current = {
            "path": str(CURRENT_DEV),
            "sha256": sha256(CURRENT_DEV),
            "status": d.get("status"),
            "reliability_n_subjects": (d.get("reliability") or {}).get("n_subjects"),
            "reserved_run07_note": (d.get("provenance") or {}).get("reserved_run07"),
        }

    # A chronology is considered reconstructed only if the machine-readable history
    # contains both 10- and 9-participant run-07 states and at least two timestamps.
    timestamps = sorted({r["timestamp_from_path"] for r in rows if r["timestamp_from_path"]})
    lineage_closed = 9 in distinct_counts and 10 in distinct_counts and len(timestamps) >= 2

    with (OUT / "history.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["timestamp_from_path", "artifact_path", "sha256", "cohort_count_candidates", "count_fields"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    summary = {
        "schema_version": 1,
        "status": "ok",
        "analysis_stage": "run-07 historical provenance reconstruction",
        "n_run07_json_artifacts": len(rows),
        "n_parse_errors": len(parse_errors),
        "timestamps": timestamps,
        "distinct_cohort_count_candidates": distinct_counts,
        "artifacts_with_count_9": count9,
        "artifacts_with_count_10": count10,
        "lineage_closed": lineage_closed,
        "closure_rule": "machine-readable run-07 history contains both 10- and 9-participant states and at least two timestamped states",
        "current_development_summary": current,
        "parse_errors": parse_errors,
        "guardrails": {
            "raw_eeg_read": False,
            "model_scoring_performed": False,
            "neural_analysis_performed": False,
            "participant_identifiers_exported": False,
            "manuscript_editing_performed": False,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "NeuroSem ChineseEEG run-07 historical provenance audit",
        f"Run-07 JSON artifacts: {len(rows)}",
        f"Distinct cohort-count candidates: {distinct_counts}",
        f"Timestamped states: {len(timestamps)}",
        f"Artifacts containing n=10: {count10}",
        f"Artifacts containing n=9: {count9}",
        f"Lineage closed under audit rule: {lineage_closed}",
    ]
    if not lineage_closed:
        lines.append("Status: unresolved; do not infer missing cohort transitions from memory or manuscript prose.")
    else:
        lines.append("Status: machine-readable 10-to-9 cohort transition is present; inspect history.csv before marking manuscript lineage resolved.")
    (OUT / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "n_artifacts": len(rows), "lineage_closed": lineage_closed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
