#!/usr/bin/env python3
from __future__ import annotations
import argparse,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from common import OUT
BUILDERS=[("Main Figure 1","build_figure1.py"),("Main Figure 2","build_figure2.py"),("Main Figure 3","build_figure3.py"),("Main Figure 4","build_figure4.py"),("Extended Data Figure 1","build_extended_data_figure1.py"),("Extended Data Figure 2","build_extended_data_figure2.py"),("Extended Data Figure 3","build_extended_data_figure3.py"),("Extended Data Figure 4","build_extended_data_figure4.py")]
def run(script): subprocess.run([sys.executable,str(HERE/script)],cwd=ROOT,check=True)
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--no-clean",action="store_true",help="do not clear outputs/paper_figures_final before building"); args=p.parse_args()
    if not args.no_clean and OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True,exist_ok=True)
    for i,(label,script) in enumerate(BUILDERS,1): print(f"[{i}/{len(BUILDERS)}] {label}",flush=True); run(script)
    print("[validation] final figure package",flush=True); run("validate_all_figures.py"); print(f"All 8 submission figures built successfully in {OUT.relative_to(ROOT)}.",flush=True); return 0
if __name__=="__main__": raise SystemExit(main())
