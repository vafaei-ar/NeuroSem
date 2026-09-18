#!/usr/bin/env python3
"""Create a presentation-only JPEG contact sheet of the eight verified submission figures."""
from __future__ import annotations
import base64, hashlib, json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"outputs"/"paper_figures_final"
OUT=ROOT/"outputs"/"paper_figures_contact_v1193"/"latest"
NAMES=["figure1","figure2","figure3","figure4","extended_data_figure1","extended_data_figure2","extended_data_figure3","extended_data_figure4"]
CELL_W=1300
CELL_H=920
COLS=2
ROWS=4

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    canvas=Image.new("RGB",(COLS*CELL_W,ROWS*CELL_H),"white")
    boxes={}
    for i,name in enumerate(NAMES):
        p=SRC/f"{name}.png"
        if not p.is_file(): raise FileNotFoundError(p)
        im=Image.open(p).convert("RGB")
        im.thumbnail((CELL_W,CELL_H),Image.Resampling.LANCZOS)
        x=(i%COLS)*CELL_W+(CELL_W-im.width)//2
        y=(i//COLS)*CELL_H+(CELL_H-im.height)//2
        canvas.paste(im,(x,y))
        boxes[name]={"cell":[(i%COLS)*CELL_W,(i//COLS)*CELL_H,CELL_W,CELL_H],"paste":[x,y,im.width,im.height]}
    jpg=OUT/"submission_figures_contact.jpg"
    canvas.save(jpg,"JPEG",quality=92,optimize=True,progressive=True,dpi=(200,200))
    raw=jpg.read_bytes()
    b64=base64.b64encode(raw).decode("ascii")
    (OUT/"submission_figures_contact_jpg_base64.txt").write_text(b64,encoding="ascii")
    manifest={"schema_version":1,"presentation_only":True,"jpeg_sha256":hashlib.sha256(raw).hexdigest(),"jpeg_bytes":len(raw),"cell_w":CELL_W,"cell_h":CELL_H,"cols":COLS,"rows":ROWS,"boxes":boxes,"source_names":NAMES}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","bytes":len(raw),"sha256":manifest["jpeg_sha256"]},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
