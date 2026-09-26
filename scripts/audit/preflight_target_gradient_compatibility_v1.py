#!/usr/bin/env python3
"""Static/no-outcome preflight for target-gradient compatibility v1."""
from __future__ import annotations
import json
import py_compile
import sys
import traceback
from pathlib import Path

import numpy as np
from scipy.signal import fftconvolve

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
OUT=ROOT/"outputs/target_gradient_compatibility_preflight_v1/latest"
COMMON=ROOT/"scripts/robustness/target_gradient_common_v1.py"
RUNNER=ROOT/"scripts/robustness/run_target_gradient_compatibility_v1.py"


def conv_equivalence():
    import torch
    import torch.nn.functional as F
    rng=np.random.default_rng(20260926)
    events=rng.normal(size=(13,5)).astype(np.float32)
    h=rng.normal(size=4).astype(np.float32)
    x=torch.as_tensor(events).T.unsqueeze(0)
    kernel=torch.as_tensor(h).flip(0).view(1,1,-1).expand(5,1,-1)
    got=F.conv1d(x,kernel,padding=len(h)-1,groups=5)[0,:,:13].T.detach().numpy()
    want=fftconvolve(events,h[:,None],mode="full",axes=0)[:13]
    return float(np.max(np.abs(got-want)))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    checks={}
    for p in [COMMON,RUNNER]:
        try:
            py_compile.compile(str(p),doraise=True)
            checks[f"compile:{p.name}"]="ok"
        except Exception:
            checks[f"compile:{p.name}"]="failed"
            checks[f"traceback:{p.name}"]=traceback.format_exc()
    try:
        import scripts.robustness.target_gradient_common_v1 as common
        import scripts.robustness.run_target_gradient_compatibility_v1 as runner
        checks["import"]="ok"
        checks["reference_adapter_exists"]=common.TEXT_ADAPTER.is_dir()
        checks["source_runs"]={}
        for run in common.SOURCE_RUNS:
            rec=common.load_target_run(common.SOURCE_TARGET_ROOT,run)
            checks["source_runs"][str(run)]={
                "dir":str(rec["dir"].relative_to(ROOT)),
                "n_texts":len(rec["texts"]),
                "n_target_edges":int(np.asarray(rec["neural"]).size),
            }
        checks["targets"]=sorted(runner.TARGET_CLASS)
    except Exception:
        checks["import"]="failed"
        checks["import_traceback"]=traceback.format_exc()
    try:
        err=conv_equivalence()
        checks["torch_hrf_conv_max_abs_error"]=err
        checks["torch_hrf_conv_equivalent"]=bool(err<2e-5)
    except Exception:
        checks["torch_hrf_conv_equivalent"]=False
        checks["torch_hrf_conv_traceback"]=traceback.format_exc()
    required=[v for k,v in checks.items() if k.startswith("compile:")]
    ok=checks.get("import")=="ok" and all(v=="ok" for v in required) and checks.get("reference_adapter_exists") is True and checks.get("torch_hrf_conv_equivalent") is True
    payload={"schema_version":1,"status":"ok" if ok else "failed","checks":checks,
             "scientific_outcomes_computed":False}
    (OUT/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    (OUT/"report.txt").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
