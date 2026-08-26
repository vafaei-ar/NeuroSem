#!/usr/bin/env python3
"""Model-blind structural probe for ChineseEEG Garnett Dream.

This script inventories only paths and small metadata/text tables. It does not load
EEG signal samples and does not compute reliability, RSA, model embeddings, or any
outcome-bearing quantity.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_SUFFIXES = {".json", ".tsv", ".csv", ".txt", ".md"}
EEG_SUFFIXES = {".eeg", ".vhdr", ".vmrk", ".set", ".fdt", ".edf", ".bdf", ".fif", ".cnt"}
ENTITY_RE = {
    "subject": re.compile(r"(?:^|[/_])sub-([^_/]+)", re.I),
    "run": re.compile(r"(?:^|[/_])run-([0-9]+)", re.I),
    "task": re.compile(r"(?:^|[/_])task-([^_/\.]+)", re.I),
}


def entity(path: str, key: str) -> str | None:
    m = ENTITY_RE[key].search(path)
    return m.group(1) if m else None


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            r = csv.DictReader(f, delimiter=delim)
            return list(r.fieldnames or []), list(r)
    except Exception:
        return [], []


def small_unique(rows: list[dict[str, str]], field: str, limit: int = 12) -> list[dict[str, Any]]:
    c = Counter(str(r.get(field, "")).strip() for r in rows)
    c.pop("", None)
    return [{"value": k, "n": v} for k, v in c.most_common(limit)]


def git_text(root: Path, *args: str) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=20)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_structure_probe/latest"))
    args = ap.parse_args()

    root = args.data_root.expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"ChineseEEG root does not exist: {root}")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    all_paths = sorted(p for p in root.rglob("*") if "/.git/" not in str(p))
    files = [p for p in all_paths if os.path.lexists(p)]

    candidates: set[Path] = set()
    task_names_from_json: set[str] = set()

    # Filename/path discovery first.
    for p in files:
        low = str(p.relative_to(root)).lower()
        if "garnett" in low or "dream" in low:
            candidates.add(p)

    # Metadata discovery protects against task names that are not obvious in paths.
    for p in files:
        if p.suffix.lower() != ".json" or not p.name.endswith("_eeg.json"):
            continue
        try:
            payload = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        task = str(payload.get("TaskName", "")).strip()
        if task and ("garnett" in task.lower() or "dream" in task.lower()):
            task_names_from_json.add(task)
            candidates.add(p)
            stem_prefix = p.name.replace("_eeg.json", "")
            for sibling in p.parent.glob(stem_prefix + "*"):
                candidates.add(sibling)

    # If task entities are discovered, include all files carrying those task labels.
    task_entities = {entity(str(p.relative_to(root)), "task") for p in candidates}
    task_entities = {x for x in task_entities if x}
    for p in files:
        rel = str(p.relative_to(root))
        t = entity(rel, "task")
        if t and any(t.lower() == x.lower() for x in task_entities):
            candidates.add(p)

    inventory: list[dict[str, Any]] = []
    event_summaries: list[dict[str, Any]] = []
    subjects: set[str] = set()
    runs_by_subject: defaultdict[str, set[int]] = defaultdict(set)

    for p in sorted(candidates):
        rel = str(p.relative_to(root))
        suf = p.suffix.lower()
        sub = entity(rel, "subject")
        run_s = entity(rel, "run")
        task = entity(rel, "task")
        if sub:
            subjects.add(sub)
        if sub and run_s:
            runs_by_subject[sub].add(int(run_s))

        materialized = bool(p.exists())
        size = None
        if materialized and p.is_file():
            try:
                size = p.stat().st_size
            except OSError:
                size = None
        inventory.append({
            "path": rel,
            "subject": sub or "",
            "run": int(run_s) if run_s else "",
            "task": task or "",
            "suffix": suf,
            "is_eeg_signal_file": suf in EEG_SUFFIXES,
            "is_small_metadata": suf in TEXT_SUFFIXES,
            "materialized": materialized,
            "size_bytes": size if size is not None else "",
            "is_symlink": p.is_symlink(),
        })

        if materialized and p.is_file() and p.name.endswith("_events.tsv"):
            fields, rows = read_table(p)
            rec: dict[str, Any] = {
                "path": rel,
                "subject": sub,
                "run": int(run_s) if run_s else None,
                "task": task,
                "n_rows": len(rows),
                "columns": fields,
            }
            for field in ["trial_type", "value", "stimulus", "stim_file", "word", "text", "sentence"]:
                if field in fields:
                    rec[field] = small_unique(rows, field)
            event_summaries.append(rec)

    # Explicitly surface the published sub-07 run-18 exception if present in the tree.
    sub07_r18 = [r for r in inventory if str(r["subject"]).lstrip("0") == "7" and r["run"] == 18]

    per_subject = []
    for sub in sorted(subjects):
        rr = sorted(runs_by_subject.get(sub, set()))
        per_subject.append({"subject": sub, "runs": rr, "n_runs": len(rr)})

    summary = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(root),
        "dataset_git_commit": git_text(root, "rev-parse", "HEAD"),
        "dataset_git_describe": git_text(root, "describe", "--tags", "--always", "--dirty"),
        "purpose": "model-blind Garnett Dream structure/materialization probe before any neural outcome analysis",
        "loads_eeg_samples": False,
        "computes_model_quantities": False,
        "computes_reliability_or_rsa": False,
        "task_names_from_eeg_json": sorted(task_names_from_json),
        "task_entities_from_paths": sorted(task_entities),
        "n_candidate_files": len(inventory),
        "n_candidate_eeg_signal_files": sum(bool(r["is_eeg_signal_file"]) for r in inventory),
        "n_materialized_candidate_eeg_signal_files": sum(bool(r["is_eeg_signal_file"] and r["materialized"]) for r in inventory),
        "n_event_files_summarized": len(event_summaries),
        "subjects": sorted(subjects),
        "n_subjects": len(subjects),
        "runs_by_subject": per_subject,
        "sub07_run18_files_present": len(sub07_r18),
        "sub07_run18_note": "Published acquisition exception: markers were lost and task was repeated using chapter 19; resolve structurally before outcome analysis.",
        "freeze_gate": {
            "ready_for_signal_materialization_design": bool(len(subjects) > 0 and len(task_entities) > 0),
            "ready_for_reliability": False,
            "reason": "This probe only inventories structure. Exact analysis unit, event/text alignment, materialization list, and structural QC must be frozen next.",
        },
    }

    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "subject", "run", "task", "suffix", "is_eeg_signal_file", "is_small_metadata", "materialized", "size_bytes", "is_symlink"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(inventory)
    (out / "events_summary.json").write_text(json.dumps(event_summaries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "n_subjects": len(subjects),
        "task_entities": sorted(task_entities),
        "n_candidate_files": len(inventory),
        "n_event_files_summarized": len(event_summaries),
        "output_dir": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
