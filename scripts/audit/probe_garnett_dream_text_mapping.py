#!/usr/bin/env python3
"""Model-blind Garnett Dream text-source and row-mapping probe.

This probe materializes only tracked small text/metadata files under derivatives/novels,
never exports novel text, and compares structural row counts against the already-frozen
ROWS->ROWE item counts. It does not load EEG samples or compute any neural/model outcome.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".tsv", ".csv", ".json", ".md"}
CHAPTER_RE = re.compile(r"(?:ch(?:apter)?[-_ ]*|run[-_ ]*)(\d{1,2})", re.I)


def git_lines(root: Path, *args: str) -> list[str]:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return [x for x in cp.stdout.splitlines() if x.strip()]


def annex_get(root: Path, rel: str) -> dict:
    p = root / rel
    before = p.exists()
    cp = None
    if not before:
        cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True, check=False)
    after = p.exists()
    return {
        "path": rel,
        "materialized_before": before,
        "materialized_after": after,
        "returncode": None if cp is None else cp.returncode,
        "stderr_tail": "" if cp is None else cp.stderr[-800:],
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def summarize_text(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = raw.splitlines()
    nonempty = [x for x in lines if x.strip()]
    return {
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "n_lines": len(lines),
        "n_nonempty_lines": len(nonempty),
        "n_characters": len(raw),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--alignment-freeze", type=Path, default=Path("outputs/garnett_dream_alignment_freeze_probe/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_text_mapping_probe/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    freeze = json.loads(args.alignment_freeze.read_text(encoding="utf-8"))
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    chapter_counts = {}
    for subject in freeze.get("subject_runs", []):
        for run in subject.get("runs", []):
            if run.get("structurally_valid") and run.get("chapter") is not None:
                ch = int(run["chapter"])
                n = int(run["n_items"])
                chapter_counts.setdefault(ch, set()).add(n)
    inconsistent = {str(k): sorted(v) for k, v in chapter_counts.items() if len(v) != 1}
    expected = {int(k): next(iter(v)) for k, v in chapter_counts.items() if len(v) == 1}

    tracked = git_lines(root, "ls-files", "derivatives/novels")
    text_files = [p for p in tracked if Path(p).suffix.lower() in TEXT_SUFFIXES]

    rows = []
    for rel in text_files:
        rec = annex_get(root, rel)
        p = root / rel
        row = {"path": rel, **rec, "suffix": Path(rel).suffix.lower()}
        if p.exists() and p.is_file():
            row.update(summarize_text(p))
            m = CHAPTER_RE.search(rel)
            row["chapter_from_path"] = int(m.group(1)) if m else ""
            row["matches_expected_nonempty_lines"] = False
            if m:
                ch = int(m.group(1))
                if ch in expected:
                    row["matches_expected_nonempty_lines"] = row["n_nonempty_lines"] == expected[ch]
        rows.append(row)

    with (out / "text_file_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = sorted({k for r in rows for k in r.keys()})
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)

    exact_matches = [
        {"path": r["path"], "chapter": r.get("chapter_from_path"), "n_nonempty_lines": r.get("n_nonempty_lines")}
        for r in rows if r.get("matches_expected_nonempty_lines")
    ]
    garnett_named = [r["path"] for r in rows if "garnett" in r["path"].lower()]

    summary = {
        "schema_version": 1,
        "purpose": "model-blind Garnett Dream public text-source / presentation-row mapping probe",
        "loads_eeg_samples": False,
        "computes_model_quantities": False,
        "computes_reliability_or_rsa": False,
        "exports_novel_text": False,
        "alignment_freeze": str(args.alignment_freeze),
        "expected_items_by_chapter": {str(k): v for k, v in sorted(expected.items())},
        "inconsistent_structural_item_counts": inconsistent,
        "n_tracked_novel_text_metadata_files": len(text_files),
        "n_materialized_after": sum(bool(r.get("materialized_after")) for r in rows),
        "garnett_named_paths": garnett_named,
        "exact_linecount_matches": exact_matches,
        "freeze_gate": {
            "ready_for_eeg_materialization": bool(not inconsistent and len(rows) > 0 and all(r.get("materialized_after") for r in rows)),
            "ready_for_reliability": False,
            "reason": "This stage freezes/diagnoses public text structure only. EEG companions must next be materialized and the final row identity mapping frozen before reliability."
        },
        "notes": [
            "No novel text content is written to artifacts; only paths, hashes, sizes, and counts are exported.",
            "No EEG sample array is opened.",
            "No model embedding, reliability, RSA, or outcome-bearing statistic is computed."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if inconsistent:
        raise SystemExit(f"Inconsistent structural item counts across subjects: {inconsistent}")
    if any(not r.get("materialized_after") for r in rows):
        raise SystemExit("One or more tracked derivatives/novels text/metadata files could not be materialized")
    print(json.dumps({"status": "ok", "n_files": len(rows), "n_exact_matches": len(exact_matches), "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
