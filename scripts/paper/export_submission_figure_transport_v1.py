#!/usr/bin/env python3
"""Export current canonical submission figure PNGs as bounded base64 text chunks.

Transport only. This script performs no plotting, model evaluation, neural analysis,
selection, or statistical inference. It is used to move already-built safe figure
assets into the document-authoring environment.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs" / "paper_figures_final"
OUT = ROOT / "outputs" / "paper_figures_final_transport" / "latest"
STEMS = [
    "figure1",
    "figure2",
    "figure3",
    "figure4",
    "extended_data_figure2",
    "extended_data_figure3",
    "extended_data_figure4",
]
CHUNK = 100_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    manifest = {"schema_version": 1, "status": "ok", "source_dir": str(SOURCE.relative_to(ROOT)), "assets": {}}
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*"):
        if old.is_file():
            old.unlink()
    for stem in STEMS:
        src = SOURCE / f"{stem}.png"
        if not src.is_file():
            raise FileNotFoundError(src)
        raw = src.read_bytes()
        enc = base64.b64encode(raw).decode("ascii")
        parts = [enc[i:i + CHUNK] for i in range(0, len(enc), CHUNK)]
        paths = []
        for i, part in enumerate(parts, 1):
            p = OUT / f"{stem}_png_base64_part{i:02d}.txt"
            p.write_text(part, encoding="ascii")
            paths.append(str(p.relative_to(ROOT)))
        manifest["assets"][stem] = {
            "source": str(src.relative_to(ROOT)),
            "source_sha256": sha256(src),
            "source_bytes": len(raw),
            "base64_chars": len(enc),
            "parts": paths,
        }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": str(OUT.relative_to(ROOT)), "asset_count": len(STEMS)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
