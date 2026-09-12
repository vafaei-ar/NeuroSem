#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=[
 'scripts/paper/build_nmi_figure1_mockup_v3.py',
 'scripts/paper/build_nmi_figure2_mockup_v3.py',
 'scripts/paper/build_nmi_figure3_mockup_v3.py',
 'scripts/paper/build_nmi_figure4_mockup_v3.py',
]
for i,s in enumerate(SCRIPTS,1):
    print(f'[{i}/{len(SCRIPTS)}] {s}',flush=True)
    subprocess.run([sys.executable,str(ROOT/s)],cwd=ROOT,check=True)
print('All mockup-v3 figures built successfully.')
