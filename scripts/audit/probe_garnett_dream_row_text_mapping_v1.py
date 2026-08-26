#!/usr/bin/env python3
"""Model-blind Garnett Dream row-text mapping probe, broad presentation-source pass.

The first completed pass established that frozen ROWS event values are a
single numeric marker rather than item text. This revision preserves that
model-blind check and broadens source discovery to all tracked small
code/config/documentation files regardless of path name. It never opens EEG
samples, loads model quantities, or exports novel/source text.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

SCAN_EXTS = {".py", ".m", ".js", ".ts", ".r", ".json", ".yaml", ".yml", ".md", ".txt", ".csv", ".tsv"}
KEYWORDS = ("GarnettDream", "Garnett Dream", "LittlePrince", "Little Prince", "ROWS", "ROWE", "highlight", "stimulus", "stimuli", "presentation", "psychopy", "pylink")
MAX_BYTES = 5_000_000


def git_lines(root: Path, *args: str) -> list[str]:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return [x for x in cp.stdout.splitlines() if x.strip()]


def annex_get(root: Path, rel: str) -> bool:
    p = root / rel
    if p.exists() and p.is_file() and p.stat().st_size > 0:
        return True
    cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True, check=False)
    return cp.returncode == 0 and p.exists() and p.is_file() and p.stat().st_size > 0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def value_profile(values: list[str]) -> dict:
    vals = [str(v or "").strip() for v in values]
    nonempty = [v for v in vals if v]
    numeric = sum(bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", v)) for v in nonempty)
    return {
        "n": len(vals),
        "n_nonempty": len(nonempty),
        "n_unique_nonempty": len(set(nonempty)),
        "fraction_numeric_nonempty": numeric / len(nonempty) if nonempty else 0.0,
        "unique_lengths": sorted(set(map(len, nonempty)))[:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--input-freeze", type=Path, default=Path("outputs/garnett_dream_input_materialization/latest/summary.json"))
    ap.add_argument("--item-identity", type=Path, default=Path("outputs/garnett_dream_input_materialization/latest/item_identity.csv"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_row_text_mapping_probe_v1/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    freeze = json.loads(args.input_freeze.read_text(encoding="utf-8"))
    if not freeze.get("freeze_gate", {}).get("ready_for_reliability"):
        raise SystemExit("Garnett input freeze is not structurally ready")
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)

    canonical_subject = "04"
    with args.item_identity.open("r", encoding="utf-8-sig", newline="") as f:
        item_rows = list(csv.DictReader(f))
    by_chapter = defaultdict(list)
    for r in item_rows:
        if str(r["subject"]) == canonical_subject:
            by_chapter[int(r["chapter"])].append(r)

    chapter_profiles = []
    all_rows_values = []
    for chapter in range(1, 19):
        rows = sorted(by_chapter[chapter], key=lambda r: int(r["item_index"]))
        run = int(rows[0]["run"])
        event_rel = f"derivatives/preproc/filtered_0.5_30/sub-{canonical_subject}/ses-GarnettDream/eeg/sub-{canonical_subject}_ses-GarnettDream_task-reading_run-{run:02d}_events.tsv"
        events = read_tsv(root / event_rel)
        vals = []
        for item in rows:
            si = int(item["rows_event_row"]) - 1
            if not 0 <= si < len(events):
                raise SystemExit(f"Frozen ROWS event index out of bounds: chapter={chapter}, item={item['item_index']}, index={si}, n_events={len(events)}")
            if str(events[si].get("trial_type", "")).strip() != "ROWS":
                raise SystemExit(f"Frozen ROWS identity mismatch: chapter={chapter}, item={item['item_index']}")
            vals.append(str(events[si].get("value", "") or "").strip())
        all_rows_values.extend(vals)
        chapter_profiles.append({"chapter": chapter, "run": run, "profile": value_profile(vals)})

    vp_all = value_profile(all_rows_values)
    rows_value_is_numeric_marker = bool(vp_all["n_nonempty"] == vp_all["n"] and vp_all["fraction_numeric_nonempty"] == 1.0 and vp_all["n_unique_nonempty"] <= 2)

    tracked = git_lines(root, "ls-files")
    hits = []
    scanned = 0
    materialization_failures = 0
    scan_exts_lower = {x.lower() for x in SCAN_EXTS}
    for rel in tracked:
        suffix = Path(rel).suffix.lower()
        if suffix not in scan_exts_lower:
            continue
        if not annex_get(root, rel):
            materialization_failures += 1
            continue
        p = root / rel
        size = p.stat().st_size
        if size > MAX_BYTES:
            continue
        scanned += 1
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
        line_hits = []
        for lineno, line in enumerate(raw.splitlines(), start=1):
            matched = sorted({k for k in KEYWORDS if k.lower() in line.lower()})
            if matched:
                line_hits.append({"line": lineno, "keywords": matched, "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest()})
        if line_hits:
            hits.append({"path": rel, "suffix": suffix, "size_bytes": size, "sha256": sha256(p), "n_keyword_lines": len(line_hits), "keyword_lines": line_hits})

    likely = [r for r in hits if any(any(k in {"GarnettDream", "Garnett Dream", "ROWS", "ROWE", "highlight", "presentation", "psychopy", "pylink"} for k in h["keywords"]) for h in r["keyword_lines"])]

    with (out / "candidate_file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "suffix", "size_bytes", "sha256", "n_keyword_lines"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        w.writerows([{k:r[k] for k in fields} for r in hits])

    summary = {
        "schema_version": 2,
        "dataset": "ChineseEEG Garnett Dream",
        "purpose": "model-blind exact row-text mapping probe before Garnett model validation",
        "loads_eeg_samples": False,
        "computes_reliability_or_rsa": False,
        "computes_model_quantities": False,
        "exports_novel_text_or_code_lines": False,
        "canonical_subject_for_event_structure": canonical_subject,
        "rows_value_profile_all_chapters": vp_all,
        "rows_value_is_numeric_marker_not_text": rows_value_is_numeric_marker,
        "chapter_value_profiles": chapter_profiles,
        "n_tracked_files": len(tracked),
        "n_small_text_code_files_scanned": scanned,
        "n_files_with_keyword_hits": len(hits),
        "n_likely_presentation_files": len(likely),
        "likely_presentation_files": likely,
        "materialization_failures_count": materialization_failures,
        "freeze_gate": {
            "exact_row_text_mapping_identified": False,
            "presentation_source_candidates_found": bool(likely),
            "ready_to_freeze_model_validation_text_mapping": False,
            "reason": "ROWS values are numeric markers, not text. Inspect safe presentation-source candidates for deterministic stimulus construction before any model analysis." if likely else "ROWS values are numeric markers and no tracked presentation-construction source was found; do not invent a text mapping from outcomes.",
        },
        "guardrails": [
            "No EEG signal sample is opened.",
            "No Garnett reliability result is used to choose a mapping.",
            "No model embedding, adapter, lambda, or RSA is loaded or computed.",
            "No novel or code-line text is exported; only structural profiles, paths, hashes, line numbers, and keyword names are stored.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status":"ok","rows_value_is_numeric_marker":rows_value_is_numeric_marker,"n_scanned":scanned,"n_likely":len(likely),"output_dir":str(out)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
