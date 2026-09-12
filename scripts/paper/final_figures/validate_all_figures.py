#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from common import OUT, sha256
STEMS=["figure1","figure2","figure3","figure4","extended_data_figure1","extended_data_figure2","extended_data_figure3","extended_data_figure4"]
EXTS=["png","pdf","svg"]

def main()->int:
    missing=[]
    for stem in STEMS:
        for ext in EXTS:
            p=OUT/f"{stem}.{ext}"
            if not p.is_file() or p.stat().st_size==0: missing.append(str(p))
        mp=OUT/f"{stem}_manifest.json"
        if not mp.is_file(): missing.append(str(mp)); continue
        payload=json.loads(mp.read_text(encoding="utf-8"))
        if payload.get("status")!="ok": raise RuntimeError(f"{mp}: status is not ok")
        if payload.get("scientific_values_changed") is not False: raise RuntimeError(f"{mp}: scientific_values_changed must be false")
    if missing: raise FileNotFoundError("Missing final figure asset(s): "+", ".join(missing))
    stale=OUT/"source_manifest.json"
    if stale.exists(): raise RuntimeError("Unexpected shared source_manifest.json remains in final output directory")
    assets={}
    for stem in STEMS:
        assets[stem]={ext:{"path":str((OUT/f"{stem}.{ext}").relative_to(OUT.parent.parent)),"sha256":sha256(OUT/f"{stem}.{ext}"),"bytes":(OUT/f"{stem}.{ext}").stat().st_size} for ext in EXTS}
    summary={"schema_version":1,"status":"ok","figure_count":8,"main_figures":4,"extended_data_figures":4,"supplementary_figures":0,"scientific_values_changed":False,"assets":assets,"figure_manifests":{stem:f"{stem}_manifest.json" for stem in STEMS}}
    out=OUT/"submission_figure_manifest.json"; out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","figure_count":8,"output_dir":str(OUT),"manifest":str(out)},indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
