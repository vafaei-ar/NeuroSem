from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "paper_figures_final"
PIPELINE = "neurosem_submission_figures_v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def legacy_status_ok(payload: dict) -> bool:
    return payload.get("status", "ok") == "ok"


def write_manifest(name: str, builder: Path, inputs: list[Path], outputs: list[Path], extra: dict | None = None) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "pipeline": PIPELINE,
        "status": "ok",
        "scientific_values_changed": False,
        "builder": str(builder.resolve().relative_to(ROOT)),
        "builder_sha256": sha256(builder),
        "inputs": {str(p.resolve().relative_to(ROOT)): sha256(p) for p in inputs},
        "outputs": {str(p.resolve().relative_to(ROOT)): sha256(p) for p in outputs},
    }
    if extra:
        payload.update(extra)
    path = OUT / f"{name}_manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def save_three(fig, stem: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for ext, kwargs in (("png", {"dpi": 300}), ("pdf", {}), ("svg", {})):
        path = OUT / f"{stem}.{ext}"
        fig.savefig(path, bbox_inches=None, **kwargs)
        paths.append(path)
    return paths
