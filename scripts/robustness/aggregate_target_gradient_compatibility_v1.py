#!/usr/bin/env python3
"""Aggregate the five frozen target-gradient compatibility outputs."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TARGETS=["zuco","smn4lang_fmri","derco","tmnred","garnett_dream"]
OUT=ROOT/"outputs/target_gradient_compatibility_v1/latest"

def read_csv(p):
    with p.open("r",encoding="utf-8",newline="") as f: return list(csv.DictReader(f))

def write_csv(p,rows):
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries=[]; all_part=[]; source_hashes=set(); param_hashes=set()
    for t in TARGETS:
        d=ROOT/"outputs/target_gradient_compatibility_v1"/t/"latest"
        s=json.loads((d/"summary.json").read_text(encoding="utf-8"))
        if s.get("status")!="ok" or s.get("target")!=t: raise RuntimeError(f"{t}: incomplete")
        r=s["result"]
        summaries.append({
            "target":t,
            "historical_target_class":s["historical_target_class"],
            "n_participants":r["n_participants"],
            "mean_gradient_cosine":r["mean_gradient_cosine"],
            "median_gradient_cosine":r["median_gradient_cosine"],
            "n_positive":r["n_positive"],
            "fraction_positive":r["fraction_positive"],
            "bootstrap_95ci_low":r["participant_bootstrap_95ci_mean"][0],
            "bootstrap_95ci_high":r["participant_bootstrap_95ci_mean"][1],
        })
        source_hashes.add(s["source_gradient"]["sha256_float32"])
        param_hashes.add(s["parameter_manifest"]["sha256"])
        for row in read_csv(d/"participant_cosines.csv"):
            all_part.append({"target":t,"historical_target_class":s["historical_target_class"],**row})
    if len(source_hashes)!=1: raise RuntimeError(f"source gradient hash mismatch: {source_hashes}")
    if len(param_hashes)!=1: raise RuntimeError(f"parameter manifest hash mismatch: {param_hashes}")
    write_csv(OUT/"target_summary.csv",summaries)
    write_csv(OUT/"participant_cosines_all_targets.csv",all_part)
    payload={
        "schema_version":1,"status":"ok",
        "analysis_stage":"post-confirmatory target-gradient compatibility aggregate",
        "protocol":"docs/TARGET_COMPATIBILITY_MECHANISM_V1.md",
        "source_gradient_sha256_float32":next(iter(source_hashes)),
        "parameter_manifest_sha256":next(iter(param_hashes)),
        "targets":summaries,
        "guardrail":"Historical target classes were fixed before gradient outcomes; this five-target aggregate is descriptive mechanism evidence, not prospective prediction."
    }
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    (OUT/"report.txt").write_text("Target-gradient compatibility aggregate complete.\n",encoding="utf-8")
    print(json.dumps({"status":"ok","n_targets":5,"out":str(OUT)},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
