#!/usr/bin/env python3
"""Model-blind Garnett Dream presentation-row to text mapping probe.

This probe is intentionally outcome-blind. It reads only tracked text/metadata/code
files, the already-frozen Garnett event tables, and the already-materialized novel
text. It never opens EEG signal samples and never loads model embeddings/adapters.

The goal is to determine whether an exact deterministic mapping from frozen
(chapter, ROWS->ROWE index) items to stimulus text is already encoded in the
public dataset. No novel text is written to artifacts; only paths, hashes,
structural counts, match counts, and code-line metadata are exported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

TEXT_EXTS = {".txt", ".tsv", ".csv", ".json", ".md", ".yaml", ".yml", ".py", ".m", ".js"}
PATH_KEYWORDS = ("garnett", "dream", "novel", "stim", "reading", "present", "experiment", "row")
CODE_EXTS = {".py", ".m", ".js"}
CODE_KEYWORDS = ("Garnett", "Dream", "ROWS", "ROWE", "novel", "stim", "reading", "present")


def git_lines(root: Path, *args: str) -> list[str]:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return [x for x in cp.stdout.splitlines() if x.strip()]


def annex_get(root: Path, rel: str) -> dict:
    p = root / rel
    before = p.exists() and p.is_file() and p.stat().st_size > 0
    cp = None
    if not before:
        cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True, check=False)
    after = p.exists() and p.is_file() and p.stat().st_size > 0
    return {
        "materialized_before": before,
        "materialized_after": after,
        "annex_get_returncode": None if cp is None else cp.returncode,
        "annex_get_stderr_tail": "" if cp is None else cp.stderr[-500:],
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def norm_text(s: str) -> str:
    return re.sub(r"\s+", "", str(s or "").strip())


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def safe_text_summary(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = raw.splitlines()
    return {
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "n_lines": len(lines),
        "n_nonempty_lines": sum(bool(x.strip()) for x in lines),
        "n_characters": len(raw),
    }


def code_hits(path: Path) -> list[dict]:
    hits = []
    if path.suffix.lower() not in CODE_EXTS:
        return hits
    for lineno, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), start=1):
        found = [k for k in CODE_KEYWORDS if k.lower() in line.lower()]
        if found:
            hits.append({"line": lineno, "keywords": sorted(set(found)), "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest()})
    return hits


def value_profile(values: list[str]) -> dict:
    vals = [str(v or "").strip() for v in values]
    nonempty = [v for v in vals if v]
    lengths = [len(v) for v in nonempty]
    numeric = sum(bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", v)) for v in nonempty)
    return {
        "n": len(vals),
        "n_nonempty": len(nonempty),
        "fraction_nonempty": len(nonempty) / len(vals) if vals else 0.0,
        "n_unique_nonempty": len(set(nonempty)),
        "fraction_numeric_nonempty": numeric / len(nonempty) if nonempty else 0.0,
        "length_min": min(lengths) if lengths else None,
        "length_median": statistics.median(lengths) if lengths else None,
        "length_max": max(lengths) if lengths else None,
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

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    canonical_subject = "04"
    expected_counts = {int(k): int(v) for k, v in freeze.get("chapter_item_counts", {}).items()}
    if sorted(expected_counts) != list(range(1, 19)):
        raise SystemExit("Expected frozen chapters 1..18")

    tracked = git_lines(root, "ls-files")
    candidates = []
    for rel in tracked:
        p = Path(rel)
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        low = rel.lower()
        if not any(k in low for k in PATH_KEYWORDS):
            continue
        rec = {"path": rel, "suffix": p.suffix.lower(), **annex_get(root, rel)}
        full = root / rel
        if rec["materialized_after"]:
            rec.update(safe_text_summary(full))
            hits = code_hits(full)
            rec["n_code_keyword_hits"] = len(hits)
            rec["code_keyword_hits"] = hits
        candidates.append(rec)

    novel_paths = [r["path"] for r in candidates if "garnettdream" in r["path"].lower() and r["suffix"] == ".txt" and r.get("materialized_after")]
    if len(novel_paths) != 1:
        raise SystemExit(f"Expected exactly one materialized GarnettDream .txt, got {novel_paths}")
    novel_path = root / novel_paths[0]
    novel_raw = novel_path.read_text(encoding="utf-8-sig", errors="replace")
    novel_lines_norm = [norm_text(x) for x in novel_raw.splitlines() if norm_text(x)]
    novel_line_hashes = Counter(hashlib.sha256(x.encode("utf-8")).hexdigest() for x in novel_lines_norm)
    novel_norm = norm_text(novel_raw)

    with args.item_identity.open("r", encoding="utf-8-sig", newline="") as f:
        item_rows = list(csv.DictReader(f))
    by_chapter = defaultdict(list)
    for r in item_rows:
        if str(r["subject"]) == canonical_subject:
            by_chapter[int(r["chapter"])].append(r)

    event_results = []
    exact_line_match_total = 0
    substring_match_total = 0
    total_rows = 0
    all_values_look_like_text = True

    for chapter in range(1, 19):
        rows = sorted(by_chapter[chapter], key=lambda r: int(r["item_index"]))
        if len(rows) != expected_counts[chapter]:
            raise SystemExit(f"Canonical subject chapter {chapter} item mismatch")
        run = int(rows[0]["run"])
        # The frozen materialization and successful reliability analysis use the
        # preproc/filtered_0.5_30 event family. The prior probe accidentally read
        # derivatives/filtered_0.5_30, whose row indices are not the frozen ones.
        event_rel = f"derivatives/preproc/filtered_0.5_30/sub-{canonical_subject}/ses-GarnettDream/eeg/sub-{canonical_subject}_ses-GarnettDream_task-reading_run-{run:02d}_events.tsv"
        event_path = root / event_rel
        if not event_path.exists():
            raise SystemExit(f"Missing canonical frozen event table: {event_rel}")
        events = read_tsv(event_path)

        rows_values = []
        rowe_values = []
        exact_line = 0
        substring = 0
        for item in rows:
            si = int(item["rows_event_row"]) - 1
            ei = int(item["rowe_event_row"]) - 1
            if not (0 <= si < len(events) and 0 <= ei < len(events)):
                raise SystemExit(
                    f"Frozen event-row index outside canonical event table: chapter={chapter} run={run} "
                    f"item={item['item_index']} rows={si + 1} rowe={ei + 1} n_events={len(events)}"
                )
            sv = str(events[si].get("value", "") or "").strip()
            ev = str(events[ei].get("value", "") or "").strip()
            rows_values.append(sv)
            rowe_values.append(ev)
            nv = norm_text(sv)
            if nv:
                h = hashlib.sha256(nv.encode("utf-8")).hexdigest()
                if novel_line_hashes[h] > 0:
                    exact_line += 1
                if nv in novel_norm:
                    substring += 1

        vp = value_profile(rows_values)
        looks_text = bool(vp["fraction_nonempty"] >= 0.95 and vp["fraction_numeric_nonempty"] <= 0.05 and (vp["length_median"] or 0) >= 2)
        all_values_look_like_text = all_values_look_like_text and looks_text
        total_rows += len(rows)
        exact_line_match_total += exact_line
        substring_match_total += substring
        event_results.append({
            "chapter": chapter,
            "run": run,
            "n_items": len(rows),
            "event_source": event_rel,
            "rows_value_profile": vp,
            "rowe_value_profile": value_profile(rowe_values),
            "rows_values_look_text_bearing": looks_text,
            "rows_exact_novel_line_matches": exact_line,
            "rows_novel_substring_matches": substring,
        })

    exact_mapping_from_rows_value = bool(
        total_rows > 0
        and all_values_look_like_text
        and substring_match_total == total_rows
    )

    with (out / "candidate_file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "suffix", "materialized_before", "materialized_after", "size_bytes", "sha256", "n_lines", "n_nonempty_lines", "n_characters", "n_code_keyword_hits"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(candidates)

    summary = {
        "schema_version": 2,
        "dataset": "ChineseEEG Garnett Dream",
        "purpose": "model-blind exact presentation-row to text mapping probe before any Garnett model validation",
        "loads_eeg_samples": False,
        "computes_reliability_or_rsa": False,
        "computes_model_quantities": False,
        "exports_novel_text": False,
        "canonical_subject_for_event_structure": canonical_subject,
        "frozen_event_source_family": "derivatives/preproc/filtered_0.5_30",
        "expected_items_by_chapter": {str(k): v for k, v in sorted(expected_counts.items())},
        "candidate_files": candidates,
        "novel_file": {"path": novel_paths[0], **safe_text_summary(novel_path)},
        "event_value_probe": event_results,
        "aggregate": {
            "n_presentation_rows": total_rows,
            "rows_exact_novel_line_matches": exact_line_match_total,
            "rows_novel_substring_matches": substring_match_total,
            "all_rows_values_look_text_bearing": all_values_look_like_text,
            "exact_mapping_from_rows_value": exact_mapping_from_rows_value,
        },
        "freeze_gate": {
            "exact_row_text_mapping_identified": exact_mapping_from_rows_value,
            "ready_to_freeze_model_validation_text_mapping": exact_mapping_from_rows_value,
            "reason": (
                "Every canonical ROWS event carries a nonnumeric text-bearing value that occurs in the materialized Garnett novel; freeze ROWS value as the exact item text source."
                if exact_mapping_from_rows_value
                else "ROWS value is not yet sufficient for an exact complete mapping; inspect the safe candidate-file/code-hit inventory before defining any model analysis."
            ),
        },
        "guardrails": [
            "No Garnett EEG signal sample is opened.",
            "No Garnett reliability result is used to choose a text mapping.",
            "No model embedding, adapter, lambda, or RSA is loaded or computed.",
            "No novel text content is exported; only structural counts and hashes/match counts are stored.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "n_rows": total_rows, "exact_mapping_from_rows_value": exact_mapping_from_rows_value, "output_dir": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
