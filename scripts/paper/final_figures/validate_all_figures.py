#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from common import OUT, PIPELINE, ROOT, sha256

STEMS=["figure1","figure2","figure3","figure4","extended_data_figure1","extended_data_figure2","extended_data_figure3","extended_data_figure4"]
EXTS=["png","pdf","svg"]
BUILDERS=[HERE/f"build_figure{i}.py" for i in range(1,5)]+[HERE/f"build_extended_data_figure{i}.py" for i in range(1,5)]
FORBIDDEN_IMPORT_PREFIXES=("build_nmi_figure","nmi_mockup_style","nmi_visualizations_v4")


def validate_builder_is_canonical(path:Path)->None:
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    imported=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): imported.extend(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module: imported.append(node.module)
    bad=[name for name in imported if name.startswith(FORBIDDEN_IMPORT_PREFIXES)]
    if bad: raise RuntimeError(f"{path}: imports deprecated visualization module(s): {bad}")


def main()->int:
    for builder in BUILDERS: validate_builder_is_canonical(builder)
    missing=[]
    for stem in STEMS:
        for ext in EXTS:
            p=OUT/f"{stem}.{ext}"
            if not p.is_file() or p.stat().st_size==0: missing.append(str(p))
        mp=OUT/f"{stem}_manifest.json"
        if not mp.is_file(): missing.append(str(mp)); continue
        payload=json.loads(mp.read_text(encoding='utf-8'))
        if payload.get('status')!='ok': raise RuntimeError(f"{mp}: status is not ok")
        if payload.get('scientific_values_changed') is not False: raise RuntimeError(f"{mp}: scientific_values_changed must be false")
        if payload.get('pipeline')!=PIPELINE: raise RuntimeError(f"{mp}: wrong pipeline identifier")
        if not payload.get('inputs'): raise RuntimeError(f"{mp}: no frozen inputs recorded")
    if missing: raise FileNotFoundError('Missing final figure asset(s): '+', '.join(missing))
    stale=OUT/'source_manifest.json'
    if stale.exists(): raise RuntimeError('Unexpected shared source_manifest.json remains in final output directory')
    assets={}
    for stem in STEMS:
        assets[stem]={ext:{'path':str((OUT/f'{stem}.{ext}').relative_to(ROOT)),'sha256':sha256(OUT/f'{stem}.{ext}'),'bytes':(OUT/f'{stem}.{ext}').stat().st_size} for ext in EXTS}
    summary={'schema_version':2,'pipeline':PIPELINE,'status':'ok','figure_count':8,'main_figures':4,'extended_data_figures':4,'supplementary_figures':0,'scientific_values_changed':False,'assets':assets,'figure_manifests':{stem:f'{stem}_manifest.json' for stem in STEMS},'canonical_code_dir':str(HERE.relative_to(ROOT))}
    out=OUT/'submission_figure_manifest.json'; out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':'ok','pipeline':PIPELINE,'figure_count':8,'output_dir':str(OUT),'manifest':str(out)},indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
