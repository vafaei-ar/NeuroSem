#!/usr/bin/env python3
"""Export the verified v1.19.3 submission figure PNGs as bounded base64 text chunks.

Transport only. This script does not compute, modify, select, or summarize scientific values.
It exists so read-only RunRelay artifact transport can reconstruct the exact PNG bytes used
for manuscript integration.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "outputs" / "paper_figures_final"
OUT = ROOT / "outputs" / "paper_figures_transport_v1193" / "latest"
FIGURES = [
    "figure1.png", "figure2.png", "figure3.png", "figure4.png",
    "extended_data_figure1.png", "extended_data_figure2.png",
    "extended_data_figure3.png", "extended_data_figure4.png",
]
CHUNK = 120_000


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "transport_only": True, "files": []}
    for name in FIGURES:
        p = SRC / name
        if not p.is_file():
            raise FileNotFoundError(p)
        raw = p.read_bytes()
        enc = base64.b64encode(raw).decode("ascii")
        parts = []
        for i in range(0, len(enc), CHUNK):
            part = OUT / f"{p.stem}_png_base64_part{i // CHUNK + 1:02d}.txt"
            part.write_text(enc[i:i+CHUNK], encoding="ascii")
            parts.append(str(part.relative_to(ROOT)))
        manifest["files"].append({
            "source": str(p.relative_to(ROOT)),
            "size_bytes": len(raw),
            "sha256": sha256(raw),
            "base64_parts": parts,
        })
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(OUT.relative_to(ROOT)), "files": len(FIGURES)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
