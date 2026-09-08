#!/usr/bin/env python3
"""Rebuild Figure 4 and emit small byte-preserving PNG transport chunks.

This is an artifact-transport wrapper around build_nmi_figure4_v1183. It does not
change scientific values or plotting logic. The PNG is base64 encoded and split
into fixed small text chunks solely so the exact generated artifact can be
retrieved through direct-text artifact transport when binary bundle retrieval is
unavailable.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import build_nmi_figure4_v1183 as figure4_builder

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/nmi_v1183_figure4/latest"
CHUNK_SIZE = 70000
N_CHUNKS = 10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rc = figure4_builder.main()
    if rc != 0:
        return rc

    png = OUT / "figure4.png"
    encoded = base64.b64encode(png.read_bytes()).decode("ascii")
    chunks = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]
    if len(chunks) > N_CHUNKS:
        raise RuntimeError(f"Figure 4 PNG needs {len(chunks)} chunks, expected at most {N_CHUNKS}")

    paths = []
    for i in range(N_CHUNKS):
        p = OUT / f"figure4_png_b64_{i:02d}.txt"
        p.write_text(chunks[i] if i < len(chunks) else "", encoding="ascii")
        paths.append(p)

    manifest = {
        "schema_version": 1,
        "status": "ok",
        "transport": "base64 fixed-size chunks",
        "chunk_size_chars": CHUNK_SIZE,
        "nonempty_chunks": len(chunks),
        "declared_chunks": N_CHUNKS,
        "decoded_png_sha256": sha256(png),
        "encoded_length_chars": len(encoded),
        "chunks": [
            {
                "path": str(p.relative_to(ROOT)),
                "size_chars": len(p.read_text(encoding="ascii")),
                "sha256": sha256(p),
            }
            for p in paths
        ],
    }
    (OUT / "figure4_png_chunks_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
