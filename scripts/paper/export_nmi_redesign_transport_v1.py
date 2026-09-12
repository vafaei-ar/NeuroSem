#!/usr/bin/env python3
"""Create safe text transports for already-built redesigned NeuroSem figures.

Presentation/transport only. This performs no scientific computation. SVGs for Figures 1-4
are gzip+base64 encoded exactly. Figure 5 and Extended Data Figure 1 are downsampled only
for DOCX placement to 2200 px width, then PNG bytes are base64 encoded into bounded chunks.
The original publication PNGs remain unchanged and their hashes are recorded.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/nmi_redesign_transport_v1/latest"
CHUNK = 120_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="ascii")


def encode_svg(stem: str, path: Path, manifest: dict) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = path.read_bytes()
    payload = base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")
    out = OUT / f"{stem}_svg_gzip_base64.txt"
    write_text(out, payload)
    manifest[stem] = {
        "source": str(path.relative_to(ROOT)),
        "source_sha256": sha256(path),
        "transport": str(out.relative_to(ROOT)),
        "transport_sha256": sha256(out),
        "encoding": "gzip+base64",
    }


def docx_png(stem: str, path: Path, manifest: dict) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob(f"{stem}_docx_png_base64_part*.txt"):
        old.unlink()
    with Image.open(path) as im:
        im.load()
        if im.width > 2200:
            height = round(im.height * 2200 / im.width)
            im = im.resize((2200, height), Image.Resampling.LANCZOS)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        out_png = OUT / f"{stem}_docx.png"
        im.save(out_png, format="PNG", optimize=True, dpi=(300, 300))
    payload = base64.b64encode(out_png.read_bytes()).decode("ascii")
    chunks = [payload[i:i+CHUNK] for i in range(0, len(payload), CHUNK)]
    paths = []
    for i, chunk in enumerate(chunks, 1):
        p = OUT / f"{stem}_docx_png_base64_part{i:02d}.txt"
        write_text(p, chunk)
        paths.append(p)
    manifest[stem] = {
        "source": str(path.relative_to(ROOT)),
        "source_sha256": sha256(path),
        "docx_png": str(out_png.relative_to(ROOT)),
        "docx_png_sha256": sha256(out_png),
        "docx_png_size": out_png.stat().st_size,
        "docx_png_dimensions": list(Image.open(out_png).size),
        "encoding": "base64 concatenated in part order",
        "parts": [str(p.relative_to(ROOT)) for p in paths],
        "part_sha256": [sha256(p) for p in paths],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "status": "ok",
        "purpose": "byte-preserving figure transport and DOCX-placement derivatives",
        "scientific_values_changed": False,
        "items": {},
    }
    for n in range(1, 5):
        encode_svg(
            f"figure{n}",
            ROOT / f"outputs/nmi_figure{n}_redesign_v1/latest/figure{n}.svg",
            manifest["items"],
        )
    docx_png(
        "figure5",
        ROOT / "outputs/nmi_figure5_redesign_v1/latest/figure5.png",
        manifest["items"],
    )
    docx_png(
        "extended_data_figure1",
        ROOT / "outputs/nmi_figure5_redesign_v1/latest/extended_data_figure1.png",
        manifest["items"],
    )
    mp = OUT / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
