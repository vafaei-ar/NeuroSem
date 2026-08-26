#!/usr/bin/env python3
"""Model-blind Garnett Dream event/text/materialization freeze probe.

This is a structural-only probe. It never loads EEG samples and never computes
reliability, RSA, embeddings, or any model quantity. It explicitly restricts to
ses-GarnettDream; the earlier broad structure probe could over-include Little
Prince because both sessions use task-reading.
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

EEG_EXTS = {".eeg", ".vhdr", ".vmrk", ".set", ".fdt", ".edf", ".bdf", ".fif", ".cnt"}
SMALL_TEXT_EXTS = {".tsv", ".csv", ".json", ".txt", ".md"}
SUB_RE = re.compile(r"(?:^|[/_])sub-([^_/]+)", re.I)
RUN_RE = re.compile(r"(?:^|[/_])run-([0-9]+)", re.I)
CH_RE = re.compile(r"^CH([0-9]+)$", re.I)


def ent(rx: re.Pattern[str], text: str) -> str | None:
    m = rx.search(text)
    return m.group(1) if m else None


def git_text(root: Path, *args: str) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=20)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            r = csv.DictReader(f, delimiter="\t")
            return list(r.fieldnames or []), list(r)
    except Exception:
        return [], []


def is_materialized(path: Path) -> bool:
    if not os.path.lexists(path):
        return False
    if path.is_symlink():
        try:
            return path.exists() and path.stat().st_size > 0
        except OSError:
            return False
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def source_family(rel: str) -> str:
    parts = Path(rel).parts
    if not parts:
        return "unknown"
    if parts[0] != "derivatives":
        return "raw"
    return "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts)


def event_structure(path: Path) -> dict[str, Any]:
    fields, rows = read_tsv(path)
    types = [str(r.get("trial_type", "")).strip() for r in rows]
    counts = Counter(types)
    chapter_markers = sorted({int(m.group(1)) for t in types if (m := CH_RE.match(t))})
    core = [(i, t) for i, t in enumerate(types) if t in {"ROWS", "ROWE"}]
    n_pairs = 0
    pair_ok = len(core) % 2 == 0
    if pair_ok:
        for j in range(0, len(core), 2):
            if core[j][1] != "ROWS" or core[j + 1][1] != "ROWE":
                pair_ok = False
                break
            n_pairs += 1
    return {
        "columns": fields,
        "n_rows": len(rows),
        "n_rows_start": counts.get("ROWS", 0),
        "n_rows_end": counts.get("ROWE", 0),
        "n_structural_pairs": n_pairs if pair_ok else 0,
        "rows_rowe_strict_alternation": bool(pair_ok),
        "chapter_markers": chapter_markers,
        "other_trial_type_counts": {k: v for k, v in sorted(counts.items()) if k not in {"ROWS", "ROWE"}},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_alignment_freeze_probe/latest"))
    args = ap.parse_args()
    root = args.data_root.expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"ChineseEEG root does not exist: {root}")
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    all_files = sorted(p for p in root.rglob("*") if os.path.lexists(p) and "/.git/" not in str(p))
    garnett_files = [p for p in all_files if "ses-garnettdream" in str(p.relative_to(root)).lower()]
    events = [p for p in garnett_files if p.name.endswith("_events.tsv") and is_materialized(p)]
    event_records = []
    for p in events:
        rel = str(p.relative_to(root)); sub = ent(SUB_RE, rel) or ""; run_s = ent(RUN_RE, rel)
        if not sub or not run_s: continue
        event_records.append({"path": rel, "subject": sub, "run": int(run_s), "source_family": source_family(rel), **event_structure(p)})
    family_coverage = Counter(r["source_family"] for r in event_records)
    preferred = "derivatives/preproc/filtered_0.5_30"
    selected_family = preferred if family_coverage.get(preferred, 0) else (family_coverage.most_common(1)[0][0] if family_coverage else None)
    selected = [r for r in event_records if r["source_family"] == selected_family]
    selected_by_sr = {}; duplicate_selected = []
    for r in sorted(selected, key=lambda x: x["path"]):
        k = (r["subject"], r["run"])
        if k in selected_by_sr: duplicate_selected.append({"subject": k[0], "run": k[1], "paths": [selected_by_sr[k]["path"], r["path"]]})
        else: selected_by_sr[k] = r
    subject_runs = defaultdict(list); valid_chapters_by_subject = defaultdict(list); exclusions = []
    for (sub, run), r in sorted(selected_by_sr.items()):
        chapters = r["chapter_markers"]; chapter = chapters[0] if len(chapters) == 1 else None
        structurally_valid = bool(r["rows_rowe_strict_alternation"] and r["n_rows_start"] > 0 and r["n_rows_start"] == r["n_rows_end"] and chapter is not None)
        reason = "" if structurally_valid else "invalid ROWS/ROWE pairing or non-unique/missing CHxx chapter marker"
        if chapter == 19:
            structurally_valid = False; reason = "CH19 is unique replacement material for sub-07 and is not interchangeable with CH18"
        if structurally_valid: valid_chapters_by_subject[sub].append(int(chapter))
        else: exclusions.append({"subject": sub, "run": run, "chapter": chapter, "reason": reason, "path": r["path"]})
        subject_runs[sub].append({"run": run, "chapter": chapter, "n_items": r["n_structural_pairs"], "structurally_valid": structurally_valid, "reason": reason, "path": r["path"]})
    subjects = sorted(subject_runs); chapter_support = Counter()
    for sub in subjects: chapter_support.update(set(valid_chapters_by_subject[sub]))
    chapters_80 = sorted(ch for ch, n in chapter_support.items() if n >= max(1, (len(subjects) * 8 + 9) // 10))
    chapters_all = sorted(ch for ch, n in chapter_support.items() if n == len(subjects))
    materialization_rows = []
    for p in garnett_files:
        rel = str(p.relative_to(root))
        if selected_family and source_family(rel) != selected_family: continue
        if p.suffix.lower() not in EEG_EXTS and not p.name.endswith("_events.tsv") and not p.name.endswith("_channels.tsv") and not p.name.endswith("_eeg.json"): continue
        sub = ent(SUB_RE, rel) or ""; run_s = ent(RUN_RE, rel)
        materialization_rows.append({"path": rel, "subject": sub, "run": int(run_s) if run_s else "", "suffix": p.suffix.lower(), "materialized": is_materialized(p), "is_signal_file": p.suffix.lower() in EEG_EXTS})
    text_candidates = []
    for p in all_files:
        if p.suffix.lower() not in SMALL_TEXT_EXTS: continue
        rel = str(p.relative_to(root)); low = rel.lower()
        if any(k in low for k in ["garnett", "dream", "novel", "stim", "text", "segment"]):
            size = None
            try: size = p.stat().st_size if p.exists() and p.is_file() else None
            except OSError: pass
            text_candidates.append({"path": rel, "suffix": p.suffix.lower(), "materialized": is_materialized(p), "size_bytes": size})
    summary = {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(), "dataset_root": str(root),
        "dataset_git_commit": git_text(root, "rev-parse", "HEAD"), "dataset_git_describe": git_text(root, "describe", "--tags", "--always", "--dirty"),
        "purpose": "model-blind Garnett Dream event/text/materialization freeze probe",
        "correction_to_prior_probe": "This probe restricts explicitly to ses-GarnettDream. The prior structure probe could over-include LittlePrince because both sessions use task-reading.",
        "loads_eeg_samples": False, "computes_model_quantities": False, "computes_reliability_or_rsa": False,
        "analysis_unit_candidate": "one highlighted presentation row, delimited by a strict ROWS -> ROWE event pair",
        "selected_event_source_family": selected_family,
        "selected_event_source_rule": "prefer derivatives/preproc/filtered_0.5_30 when present; otherwise maximal model-blind subject-run coverage",
        "n_subjects": len(subjects), "subjects": subjects, "n_selected_subject_runs": len(selected_by_sr), "duplicate_selected_subject_runs": duplicate_selected,
        "subject_runs": [{"subject": s, "runs": subject_runs[s]} for s in subjects],
        "chapter_support": {str(k): int(v) for k, v in sorted(chapter_support.items())}, "chapters_supported_by_all_subjects": chapters_all,
        "chapters_supported_by_at_least_80pct_subjects": chapters_80, "structural_exclusions": exclusions,
        "sub07_policy": "Do not treat CH19 as a replacement for CH18. Use only structurally matching chapter identities across participants; missing CH18 for sub-07 remains missing.",
        "text_candidate_count": len(text_candidates),
        "freeze_gate": {"ready_for_materialization": bool(selected_family and subjects and not duplicate_selected), "ready_for_reliability": False, "reason": "Next freeze must identify the exact public text file/row mapping and materialize the selected EEG companions before outcome-bearing EEG reliability."},
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "event_structure.json").write_text(json.dumps(event_records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "text_candidates.json").write_text(json.dumps(text_candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "materialization_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "subject", "run", "suffix", "materialized", "is_signal_file"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(materialization_rows)
    print(json.dumps({"status": "ok", "selected_event_source_family": selected_family, "n_subjects": len(subjects), "n_selected_subject_runs": len(selected_by_sr), "chapters_all": chapters_all, "chapters_80pct": chapters_80, "n_structural_exclusions": len(exclusions), "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
