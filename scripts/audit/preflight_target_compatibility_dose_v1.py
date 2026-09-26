#!/usr/bin/env python3
from __future__ import annotations
import json, py_compile, traceback
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT=ROOT/"outputs/target_compatibility_dose_preflight_v1/latest"
TARGET=ROOT/"scripts/robustness/run_target_compatibility_dose_v1.py"

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    checks={}
    try:
        py_compile.compile(str(TARGET),doraise=True)
        checks["py_compile"]="ok"
    except Exception:
        checks["py_compile"]="failed"
        checks["py_compile_traceback"]=traceback.format_exc()
    try:
        import scripts.robustness.run_target_compatibility_dose_v1 as mod
        checks["import"]="ok"
        for name,p in {
            "forward_participant":mod.FORWARD/"participant_dose_results.csv",
            "forward_summary":mod.FORWARD/"dose_summary.csv",
            **{f"adapter_{d}":p for d,p in mod.ADAPTERS.items()},
        }.items():
            checks[name]={"path":str(p.relative_to(ROOT)),"exists":p.exists(),"is_dir":p.is_dir(),"is_file":p.is_file()}
    except Exception:
        checks["import"]="failed"
        checks["import_traceback"]=traceback.format_exc()
    status="ok" if checks.get("py_compile")=="ok" and checks.get("import")=="ok" else "failed"
    payload={"status":status,"checks":checks}
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    (OUT/"report.txt").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
