#!/usr/bin/env python3
"""Model-blind documentation probe for TMNRED.

Reads only small, already-materialized metadata/documentation files from the
pinned OpenNeuro checkout. It does not materialize or load EEG signal payloads,
model embeddings, or neural-model alignment results.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_text(path: Path, limit: int = 20000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:limit]


def read_tsv_header_and_rows(path: Path, max_rows: int = 12) -> dict:
    if not path.exists() or not path.is_file():
        return {"exists": False}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {
        "exists": True,
        "columns": list(rows[0].keys()) if rows else [],
        "n_rows": len(rows),
        "sample_rows": rows[:max_rows],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data/raw/tmnred")
    ap.add_argument("--output-dir", default="outputs/tmnred_docs_probe/latest")
    args = ap.parse_args()

    root = Path(args.data_root)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        raise SystemExit(f"TMNRED root not found: {root}")

    payload: dict = {
        "schema_version": 1,
        "dataset": "TMNRED",
        "model_blind": True,
        "signal_loaded": False,
        "readme": read_text(root / "README"),
        "dataset_description": {},
        "participants": read_tsv_header_and_rows(root / "participants.tsv", max_rows=8),
        "representative_sidecars": [],
        "representative_event_schema": [],
        "stimulus_metadata_paths": [],
        "derivative_paths_sample": [],
        "notes": [
            "No EEG signal payloads are loaded or materialized by this probe.",
            "The purpose is to resolve acquisition, task, stimulus, and derivative semantics before freezing signal-level analysis.",
        ],
    }

    desc = root / "dataset_description.json"
    if desc.exists():
        payload["dataset_description"] = json.loads(desc.read_text(encoding="utf-8"))

    # Representative BIDS JSON sidecars and event tables, already materialized
    # by the OpenNeuro metadata checkout.
    for path in sorted(root.glob("sub-*/ses-*/eeg/*_eeg.json"))[:6]:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # diagnostic only
            obj = {"_read_error": repr(exc)}
        payload["representative_sidecars"].append({
            "path": path.relative_to(root).as_posix(),
            "content": obj,
        })

    for path in sorted(root.glob("sub-*/ses-*/eeg/*_events.tsv"))[:6]:
        rec = read_tsv_header_and_rows(path, max_rows=12)
        rec["path"] = path.relative_to(root).as_posix()
        payload["representative_event_schema"].append(rec)

    # Identify public stimulus metadata and derivative documentation paths, but
    # do not open binary or annexed signal files.
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        lower = rel.lower()
        if any(token in lower for token in ("stim", "material", "semantic", "sentence")) and path.suffix.lower() in {".csv", ".tsv", ".json", ".xlsx"}:
            payload["stimulus_metadata_paths"].append(rel)
        if rel.startswith("derivatives/") and len(payload["derivative_paths_sample"]) < 160:
            payload["derivative_paths_sample"].append(rel)

    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(outdir / "summary.json"),
        "representative_sidecars": len(payload["representative_sidecars"]),
        "representative_event_files": len(payload["representative_event_schema"]),
        "stimulus_metadata_paths": len(payload["stimulus_metadata_paths"]),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
