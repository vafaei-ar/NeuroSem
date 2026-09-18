#!/usr/bin/env python3
"""Compact transport for v1.19.3 manuscript assembly.

Vector figures are gzip+base64 encoded from canonical SVG bytes. Surface figures
(Figure 4 and Extended Data Figure 3) are base64 encoded from exact canonical PNG
bytes in bounded chunks. Transport only; no scientific computation or rendering.
"""
from __future__ import annotations
import base64, gzip, hashlib, json
from pathlib import Path
from io import BytesIO
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"outputs/paper_figures_final"
OUT=ROOT/"outputs/paper_figures_transport_v1193_compact/latest"
CHUNK=120_000
WEBP_CHUNK=20_000
DOCX_WEBP_WIDTH=1200
VECTOR=["figure1","figure2","figure3","extended_data_figure2","extended_data_figure4"]
RASTER=["figure4","extended_data_figure3"]

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob("*"):
        if p.is_file(): p.unlink()
    m={"schema_version":1,"status":"ok","scientific_values_changed":False,"items":{}}
    for stem in VECTOR:
        src=SRC/f"{stem}.svg"
        if not src.is_file(): raise FileNotFoundError(src)
        payload=base64.b64encode(gzip.compress(src.read_bytes(),compresslevel=9,mtime=0)).decode("ascii")
        out=OUT/f"{stem}_svg_gzip_base64.txt"; out.write_text(payload,encoding="ascii")
        m["items"][stem]={"source":str(src.relative_to(ROOT)),"source_sha256":sha256(src),"transport":str(out.relative_to(ROOT)),"encoding":"gzip+base64"}
    for stem in RASTER:
        src=SRC/f"{stem}.png"
        if not src.is_file(): raise FileNotFoundError(src)
        payload=base64.b64encode(src.read_bytes()).decode("ascii")
        chunks=[payload[i:i+CHUNK] for i in range(0,len(payload),CHUNK)]
        parts=[]
        for i,ch in enumerate(chunks,1):
            p=OUT/f"{stem}_png_base64_part{i:02d}.txt"; p.write_text(ch,encoding="ascii"); parts.append(str(p.relative_to(ROOT)))
        with Image.open(src) as im:
            im=im.convert("RGB")
            h=round(im.height*DOCX_WEBP_WIDTH/im.width)
            im=im.resize((DOCX_WEBP_WIDTH,h),Image.Resampling.LANCZOS)
            buf=BytesIO(); im.save(buf,format="WEBP",quality=90,method=6)
            webp_raw=buf.getvalue()
        webp_b64=base64.b64encode(webp_raw).decode("ascii")
        webp_chunks=[webp_b64[i:i+WEBP_CHUNK] for i in range(0,len(webp_b64),WEBP_CHUNK)]
        webp_parts=[]
        for i,ch in enumerate(webp_chunks,1):
            p=OUT/f"{stem}_docx_webp_base64_part{i:02d}.txt"; p.write_text(ch,encoding="ascii"); webp_parts.append(str(p.relative_to(ROOT)))
        m["items"][stem]={"source":str(src.relative_to(ROOT)),"source_sha256":sha256(src),"encoding":"base64 concatenated in part order","parts":parts,
                          "docx_webp":{"width_px":DOCX_WEBP_WIDTH,"quality":90,"bytes":len(webp_raw),"encoding":"base64 concatenated in part order","parts":webp_parts}}
    mp=OUT/"manifest.json"; mp.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(m,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
