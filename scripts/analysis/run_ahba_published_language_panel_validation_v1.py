#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

def main():
    argv=sys.argv[1:]
    i=argv.index('--panel-json')
    src=Path(argv[i+1])
    obj=json.loads(src.read_text(encoding='utf-8'))
    panels=obj.get('panels',obj)
    fixed=dict(obj); fixed_panels=dict(panels)
    changed=False
    for pid,value in panels.items():
        if isinstance(value,list):
            fixed_panels[pid]={'genes':list(value)}; changed=True
    if changed:
        fixed['panels']=fixed_panels
        with tempfile.TemporaryDirectory(prefix='neurosem_panel_compat_') as td:
            p=Path(td)/'gene_panels.compat.json'
            p.write_text(json.dumps(fixed,indent=2)+'\n',encoding='utf-8')
            argv=list(argv); argv[i+1]=str(p)
            return subprocess.run([sys.executable,'scripts/analysis/run_ahba_published_language_panel_validation_v1_core.py',*argv],check=False).returncode
    return subprocess.run([sys.executable,'scripts/analysis/run_ahba_published_language_panel_validation_v1_core.py',*argv],check=False).returncode

if __name__=='__main__': raise SystemExit(main())
