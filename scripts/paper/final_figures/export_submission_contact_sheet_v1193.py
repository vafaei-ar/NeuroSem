#!/usr/bin/env python3
"""Create a compact presentation-only WebP contact sheet of the eight verified figures."""
from __future__ import annotations
import base64, hashlib, json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "outputs" / "paper_figures_final"
OUT = ROOT / "outputs" / "paper_figures_contact_v1193" / "latest"
NAMES = ["figure1","figure2","figure3","figure4","extended_data_figure1","extended_data_figure2","extended_data_figure3","extended_data_figure4"]
CELL_W, CELL_H = 1100, 778
COLS, ROWS = 2, 4

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (COLS*CELL_W, ROWS*CELL_H), "white")
    boxes = {}
    for i, name in enumerate(NAMES):
        p = SRC / f"{name}.png"
        if not p.is_file():
            raise FileNotFoundError(p)
        im = Image.open(p).convert("RGB")
        im.thumbnail((CELL_W, CELL_H), Image.Resampling.LANCZOS)
        cell_x, cell_y = (i % COLS)*CELL_W, (i // COLS)*CELL_H
        x = cell_x + (CELL_W-im.width)//2
        y = cell_y + (CELL_H-im.height)//2
        canvas.paste(im, (x,y))
        boxes[name] = {"cell":[cell_x,cell_y,CELL_W,CELL_H], "paste":[x,y,im.width,im.height]}
    webp = OUT / "submission_figures_contact.webp"
    canvas.save(webp, "WEBP", quality=55, method=6)
    raw = webp.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    (OUT / "submission_figures_contact_webp_base64.txt").write_text(encoded, encoding="ascii")
    digest = hashlib.sha256(raw).hexdigest()
    manifest = {"schema_version":1,"presentation_only":True,"webp_sha256":digest,"webp_bytes":len(raw),"cell_w":CELL_W,"cell_h":CELL_H,"cols":COLS,"rows":ROWS,"boxes":boxes,"source_names":NAMES}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","bytes":len(raw),"sha256":digest},indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
