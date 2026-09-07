#!/usr/bin/env python3
"""Prefetch the exact frozen MPNet revision, then materialize the fixed surrogate targets.

Implementation-only wrapper for the alternative-signal control. The scientific target
is defined in materialize_nmi_alternative_signal_mpnet_v1.py. This wrapper reads the
already-frozen immutable model revision directly from the completed model-family panel,
downloads only that exact revision if needed, then executes the unchanged materializer.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_RESOLVED_MODELS = REPO_ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/resolved_models.json"
MATERIALIZER = REPO_ROOT / "scripts/robustness/materialize_nmi_alternative_signal_mpnet_v1.py"
MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def frozen_panel_revision() -> tuple[str, str]:
    payload = json.loads(PANEL_RESOLVED_MODELS.read_text(encoding="utf-8"))
    rec = payload.get("multilingual_mpnet") if isinstance(payload, dict) else None
    if not isinstance(rec, dict):
        raise RuntimeError("Prior model-family revision freeze lacks multilingual_mpnet")
    model_id = str(rec.get("model_id") or "")
    revision = str(rec.get("revision") or "")
    if model_id != MODEL_ID or len(revision) < 20:
        raise RuntimeError(f"Unexpected frozen MPNet identity: model_id={model_id!r}, revision={revision!r}")
    return model_id, revision


def main() -> int:
    model_id, revision = frozen_panel_revision()
    print(f"Prefetching exact frozen model: {model_id}@{revision}", flush=True)
    snapshot_download(
        repo_id=model_id,
        revision=revision,
        repo_type="model",
        local_files_only=False,
    )
    subprocess.run([sys.executable, str(MATERIALIZER)], cwd=REPO_ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
