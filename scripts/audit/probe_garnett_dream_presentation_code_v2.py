#!/usr/bin/env python3
"""Model-blind Garnett Dream presentation-construction code/metadata probe.

This second-stage probe follows the completed v1 row-text probe. It scans all
tracked small code/config/documentation files for presentation-construction
keywords regardless of path name, because v1's path-keyword filter can miss
relevant experiment scripts. It does not open EEG samples, load model
quantities, or export novel text/code lines. Only file paths, hashes, line
numbers, and matched keyword names are written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

SCAN_EXTS = {".py", ".m", ".js", ".ts", ".r", ".R", ".json", ".yaml", ".yml", ".md", ".txt", ".csv", ".tsv"}
KEYWORDS = (
    "GarnettDream", "Garnett Dream", "LittlePrince", "Little Prince",
    "ROWS", "ROWE", "trial_type", "highlight", "row", "reading",
    "stimulus", "stimuli", "presentation", "psychopy", "pylink",
)
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--v1-summary", type=Path, default=Path("outputs/garnett_dream_row_text_mapping_probe_v1/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_presentation_code_probe_v2/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    v1 = json.loads(args.v1_summary.read_text(encoding="utf-8"))
    if v1.get("aggregate", {}).get("exact_mapping_from_rows_value"):
        raise SystemExit("v1 already identified an exact ROWS-value mapping; v2 is unnecessary")

    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    tracked = git_lines(root, "ls-files")
    hits = []
    scanned = 0
    materialization_failures = []

    for rel in tracked:
        suffix = Path(rel).suffix
        if suffix not in SCAN_EXTS and suffix.lower() not in {x.lower() for x in SCAN_EXTS}:
            continue
        p = root / rel
        if not annex_get(root, rel):
            materialization_failures.append(rel)
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > MAX_BYTES:
            continue
        scanned += 1
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
        file_hits = []
        for lineno, line in enumerate(raw.splitlines(), start=1):
            matched = sorted({k for k in KEYWORDS if k.lower() in line.lower()})
            if matched:
                file_hits.append({
                    "line": lineno,
                    "keywords": matched,
                    "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                })
        if file_hits:
            hits.append({
                "path": rel,
                "suffix": suffix,
                "size_bytes": size,
                "sha256": sha256(p),
                "n_keyword_lines": len(file_hits),
                "keyword_lines": file_hits,
            })

    with (out / "hit_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "suffix", "size_bytes", "sha256", "n_keyword_lines"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        w.writerows([{k:r[k] for k in fields} for r in hits])

    likely = [r for r in hits if any(any(k in {"GarnettDream", "Garnett Dream", "ROWS", "ROWE", "highlight", "presentation", "psychopy", "pylink"} for k in h["keywords"]) for h in r["keyword_lines"])]
    summary = {
        "schema_version": 1,
        "dataset": "ChineseEEG Garnett Dream",
        "purpose": "model-blind presentation-construction code/metadata discovery after v1 showed ROWS value is numeric, not text",
        "loads_eeg_samples": False,
        "computes_reliability_or_rsa": False,
        "computes_model_quantities": False,
        "exports_novel_text_or_code_lines": False,
        "v1_aggregate": v1.get("aggregate", {}),
        "n_tracked_files": len(tracked),
        "n_small_text_code_files_scanned": scanned,
        "n_files_with_keyword_hits": len(hits),
        "n_likely_presentation_files": len(likely),
        "likely_presentation_files": likely,
        "materialization_failures_count": len(materialization_failures),
        "freeze_gate": {
            "presentation_source_candidates_found": bool(likely),
            "ready_for_model_validation_text_mapping": False,
            "reason": "Inspect the safe line-number/keyword evidence from likely presentation files before defining a deterministic text mapping." if likely else "No tracked presentation-construction source was found; do not invent a text mapping from outcomes.",
        },
        "guardrails": [
            "No EEG sample array is opened.",
            "No Garnett reliability result is used to choose a mapping.",
            "No language-model embedding, adapter, lambda, or RSA is loaded or computed.",
            "No novel text or source-code line content is exported; only hashes, paths, line numbers, and keyword names are stored.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status":"ok","n_scanned":scanned,"n_hit_files":len(hits),"n_likely":len(likely),"output_dir":str(out)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
