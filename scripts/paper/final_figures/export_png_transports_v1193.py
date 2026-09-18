#!/usr/bin/env python3
"""Export canonical final NeuroSem figure PNGs as bounded base64 text chunks.

Transport only. Source PNG bytes are encoded exactly; no resizing, recompression,
scientific computation, or figure modification is performed.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "outputs/paper_figures_final"
OUT = ROOT / "outputs/paper_figures_transport_v1193/latest"
CHUNK = 120_000
STEMS = [
    "figure1", "figure2", "figure3", "figure4",
    "extended_data_figure1", "extended_data_figure2",
    "extended_data_figure3", "extended_data_figure4",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*"):
        if old.is_file():
            old.unlink()
    manifest = {
        "schema_version": 1,
        "status": "ok",
        "scientific_values_changed": False,
        "encoding": "base64; concatenate parts in numeric order to recover exact PNG bytes",
        "items": {},
    }
    for stem in STEMS:
        src = SOURCE / f"{stem}.png"
        if not src.is_file():
            raise FileNotFoundError(src)
        raw = src.read_bytes()
        payload = base64.b64encode(raw).decode("ascii")
        chunks = [payload[i:i+CHUNK] for i in range(0, len(payload), CHUNK)]
        parts = []
        for i, chunk in enumerate(chunks, 1):
            p = OUT / f"{stem}_png_base64_part{i:02d}.txt"
            p.write_text(chunk, encoding="ascii")
            parts.append(str(p.relative_to(ROOT)))
        manifest["items"][stem] = {
            "source": str(src.relative_to(ROOT)),
            "source_sha256": sha256(src),
            "source_bytes": len(raw),
            "parts": parts,
            "part_count": len(parts),
        }
    mp = OUT / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
