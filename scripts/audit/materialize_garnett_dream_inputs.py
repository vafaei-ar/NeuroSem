#!/usr/bin/env python3
"""Materialize frozen Garnett Dream BrainVision inputs without loading EEG samples.

Uses the previously frozen alignment summary. For each structurally valid subject-run,
materializes the selected filtered_0.5_30 BrainVision triplet, validates header/marker
companions, and freezes row identity as (chapter, within-run ROWS->ROWE pair index).
No EEG sample array, reliability, RSA, embedding, or model quantity is computed.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


def tracked(root: Path, rel: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", rel], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def annex_get(root: Path, rel: str) -> dict:
    p = root / rel
    rec = {"path": rel, "tracked": tracked(root, rel), "materialized_before": p.exists() and p.stat().st_size > 0 if p.exists() else False}
    if not rec["tracked"]:
        rec["status"] = "not_tracked"
        return rec
    if not rec["materialized_before"]:
        cp = subprocess.run(["git", "-C", str(root), "annex", "get", "--", rel], capture_output=True, text=True)
        rec["annex_get_returncode"] = cp.returncode
        rec["annex_get_stdout_tail"] = cp.stdout[-1000:]
        rec["annex_get_stderr_tail"] = cp.stderr[-1000:]
    rec["materialized_after"] = p.exists() and p.stat().st_size > 0 if p.exists() else False
    rec["size_bytes"] = p.stat().st_size if p.exists() else None
    rec["status"] = "materialized" if rec["materialized_after"] else "not_materializable"
    return rec


def read_events(path: Path):
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_ini(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith(";") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/chineseeeg"))
    ap.add_argument("--alignment-freeze", type=Path, default=Path("outputs/garnett_dream_alignment_freeze_probe/latest/summary.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/garnett_dream_input_materialization/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    freeze = json.loads(args.alignment_freeze.read_text(encoding="utf-8"))
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)

    if freeze.get("selected_event_source_family") != "derivatives/preproc/filtered_0.5_30":
        raise SystemExit("Unexpected frozen source family")

    inventory = []
    item_rows = []
    failures = []
    ready_runs = []
    chapter_counts = defaultdict(set)

    for subrec in freeze.get("subject_runs", []):
        sub = subrec["subject"]
        for rr in subrec.get("runs", []):
            if not rr.get("structurally_valid"):
                continue
            run = int(rr["run"]); chapter = int(rr["chapter"])
            event_rel = rr["path"]
            base = event_rel[:-len("_events.tsv")]
            triplet = [base + "_eeg.vhdr", base + "_eeg.vmrk", base + "_eeg.eeg"]
            recs = [annex_get(root, rel) for rel in triplet]
            for x in recs:
                inventory.append({"subject": sub, "run": run, "chapter": chapter, **x})
            if any(x.get("status") != "materialized" for x in recs):
                failures.append({"subject": sub, "run": run, "chapter": chapter, "reason": "brainvision_companion_unavailable"})
                continue

            vhdr = root / triplet[0]; vmrk = root / triplet[1]; eeg = root / triplet[2]
            h = read_ini(vhdr); m = read_ini(vmrk)
            if h.get("DataFile") != eeg.name or h.get("MarkerFile") != vmrk.name:
                failures.append({"subject": sub, "run": run, "chapter": chapter, "reason": "header_companion_reference_mismatch", "DataFile": h.get("DataFile"), "MarkerFile": h.get("MarkerFile")})
                continue
            if m.get("DataFile") not in {None, "", eeg.name}:
                failures.append({"subject": sub, "run": run, "chapter": chapter, "reason": "marker_data_reference_mismatch", "DataFile": m.get("DataFile")})
                continue

            events = read_events(root / event_rel)
            types = [str(r.get("trial_type", "")).strip() for r in events]
            pairs = []
            core = [(i, t) for i, t in enumerate(types) if t in {"ROWS", "ROWE"}]
            if len(core) % 2:
                failures.append({"subject": sub, "run": run, "chapter": chapter, "reason": "odd_rows_rowe_event_count"})
                continue
            ok = True
            for j in range(0, len(core), 2):
                if core[j][1] != "ROWS" or core[j+1][1] != "ROWE":
                    ok = False; break
                pairs.append((core[j][0], core[j+1][0]))
            if not ok:
                failures.append({"subject": sub, "run": run, "chapter": chapter, "reason": "nonalternating_rows_rowe"})
                continue

            for idx, (si, ei) in enumerate(pairs, start=1):
                item_rows.append({"subject": sub, "run": run, "chapter": chapter, "item_index": idx, "item_id": f"CH{chapter:02d}_ROW{idx:04d}", "rows_event_row": si + 1, "rowe_event_row": ei + 1})
            chapter_counts[chapter].add(len(pairs))
            ready_runs.append({"subject": sub, "run": run, "chapter": chapter, "n_items": len(pairs), "vhdr": triplet[0], "vmrk": triplet[1], "eeg": triplet[2]})

    inconsistent = {str(ch): sorted(vals) for ch, vals in sorted(chapter_counts.items()) if len(vals) != 1}
    if inconsistent:
        failures.append({"reason": "inconsistent_item_count_within_chapter", "chapters": inconsistent})

    fields = ["subject","run","chapter","path","tracked","materialized_before","materialized_after","size_bytes","status","annex_get_returncode","annex_get_stdout_tail","annex_get_stderr_tail"]
    with (out / "session_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(inventory)
    with (out / "item_identity.csv").open("w", encoding="utf-8", newline="") as f:
        flds = ["subject","run","chapter","item_index","item_id","rows_event_row","rowe_event_row"]
        w = csv.DictWriter(f, fieldnames=flds); w.writeheader(); w.writerows(item_rows)

    subjects = sorted({r["subject"] for r in ready_runs})
    chapter_support = Counter(r["chapter"] for r in ready_runs)
    summary = {
        "schema_version": 1,
        "dataset": "ChineseEEG Garnett Dream",
        "model_blind": True,
        "loads_eeg_samples": False,
        "computes_reliability_or_rsa": False,
        "computes_model_quantities": False,
        "analysis_source": "derivatives/preproc/filtered_0.5_30 BrainVision",
        "analysis_unit": "one highlighted presentation row, frozen as ordered ROWS->ROWE pair within chapter",
        "item_identity_rule": "CHxx + within-run ROWS->ROWE pair index; counts must agree across subjects for each chapter",
        "sub07_policy": "CH19 excluded; missing CH18 remains missing",
        "n_ready_runs": len(ready_runs),
        "n_ready_subjects": len(subjects),
        "ready_subjects": subjects,
        "chapter_support_runs": {str(k): int(v) for k,v in sorted(chapter_support.items())},
        "chapter_item_counts": {str(k): next(iter(v)) for k,v in sorted(chapter_counts.items()) if len(v)==1},
        "n_item_rows": len(item_rows),
        "failures": failures,
        "freeze_gate": {
            "ready_for_reliability": len(failures) == 0 and len(ready_runs) > 0,
            "reason": "All frozen BrainVision companions are materialized and row identities are structurally consistent" if len(failures)==0 else "Materialization or structural failures remain"
        },
        "notes": [
            "No EEG signal samples are opened in this stage.",
            "No participant is excluded based on EEG values or model outcomes.",
            "Novel text content is not required for EEG-only reliability; semantic text mapping is deferred until model validation."
        ]
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"Garnett input materialization had {len(failures)} failure(s)")
    print(json.dumps({"status":"ok","n_ready_runs":len(ready_runs),"n_ready_subjects":len(subjects),"n_item_rows":len(item_rows)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
