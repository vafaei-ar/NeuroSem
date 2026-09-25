#!/usr/bin/env python3
"""Static/preflight validation for the frozen matched-MPNet protocol."""
from __future__ import annotations
import hashlib, json, py_compile
from pathlib import Path

CONFIG=Path("configs/nmi_matched_mpnet_surrogate_v1.json")
PROTOCOL=Path("docs/NMI_MATCHED_MPNET_SURROGATE_V1.md")
CAL=Path("outputs/nmi_matched_mpnet_calibration_v1/latest/summary.json")
GRID=Path("scripts/robustness/run_nmi_matched_mpnet_grid_v1.py")
EXT=Path("scripts/robustness/run_nmi_matched_mpnet_external_v1.py")
OUT=Path("outputs/nmi_matched_mpnet_protocol_preflight_v1/latest")

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""): h.update(ch)
    return h.hexdigest()

def main()->int:
    OUT.mkdir(parents=True,exist_ok=True)
    for p in [CONFIG,PROTOCOL,CAL,GRID,EXT]:
        if not p.is_file(): raise FileNotFoundError(p)
    py_compile.compile(str(GRID),doraise=True)
    py_compile.compile(str(EXT),doraise=True)
    cfg=json.loads(CONFIG.read_text(encoding="utf-8"))
    cal=json.loads(CAL.read_text(encoding="utf-8"))
    if sha256(CAL)!=cfg["calibration_summary_sha256"]: raise RuntimeError("calibration hash mismatch")
    if abs(float(cal["mean_delta"])-float(cfg["genuine_mean_delta"]))>1e-15: raise RuntimeError("mean delta mismatch")
    if cfg["external_outcomes_permitted_during_selection"] is not False: raise RuntimeError("selection guardrail invalid")
    if len(cfg["dose_grid"])!=8 or len(cfg["seeds"])!=3: raise RuntimeError("unexpected grid/seed cardinality")
    if not (cfg["tolerance_low"] < cfg["genuine_mean_delta"] <= cfg["tolerance_high"]): raise RuntimeError("genuine reference outside tolerance band")
    payload={
        "schema_version":1,"status":"ok",
        "config_sha256":sha256(CONFIG),
        "protocol_sha256":sha256(PROTOCOL),
        "calibration_summary_sha256":sha256(CAL),
        "grid_script_sha256":sha256(GRID),
        "external_script_sha256":sha256(EXT),
        "dose_grid":cfg["dose_grid"],"seeds":cfg["seeds"],
        "tolerance_band":[cfg["tolerance_low"],cfg["tolerance_high"]],
        "guardrails":{"external_outcomes_permitted_during_selection":False}
    }
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    (OUT/"report.txt").write_text("Matched-MPNet protocol preflight: OK\n"+json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
