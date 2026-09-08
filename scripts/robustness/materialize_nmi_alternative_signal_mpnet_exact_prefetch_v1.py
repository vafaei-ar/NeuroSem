#!/usr/bin/env python3
"""Prefetch the exact frozen MPNet revision, then materialize the fixed surrogate targets.

Implementation-only launcher for the alternative-signal control. It reads the already-
frozen immutable model revision from the completed model-family panel, downloads only
that exact revision if needed, then executes the participant-specific nuisance
materializer fixed before any surrogate transfer outcome was observed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_RESOLVED_MODELS = REPO_ROOT / "outputs/nmi_bidirectional_model_family_panel_v1/latest/resolved_models.json"
MATERIALIZER = REPO_ROOT / "scripts/robustness/materialize_nmi_alternative_signal_mpnet_v2.py"
MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
PREFLIGHT = REPO_ROOT / "outputs/nmi_alternative_signal_mpnet_targets_v1/latest/preflight.txt"
MAX_DIAGNOSTIC_CHARS = 12000


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


def note(text: str) -> None:
    PREFLIGHT.parent.mkdir(parents=True, exist_ok=True)
    with PREFLIGHT.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def diagnostic_tail(text: str | None) -> str:
    value = (text or "").strip()
    if len(value) > MAX_DIAGNOSTIC_CHARS:
        value = value[-MAX_DIAGNOSTIC_CHARS:]
    return value


def main() -> int:
    PREFLIGHT.parent.mkdir(parents=True, exist_ok=True)
    PREFLIGHT.write_text("MPNet alternative-signal preflight\n", encoding="utf-8")
    model_id, revision = frozen_panel_revision()
    note(f"model_id={model_id}")
    note(f"revision={revision}")
    note("materializer=subject_specific_nuisance_v2")
    print(f"Prefetching exact frozen model: {model_id}@{revision}", flush=True)
    try:
        snapshot_download(
            repo_id=model_id,
            revision=revision,
            repo_type="model",
            local_files_only=False,
        )
        note("snapshot_download=ok")
    except Exception as exc:
        note(f"snapshot_download=failed:{type(exc).__name__}:{exc}")
        raise

    proc = subprocess.run(
        [sys.executable, str(MATERIALIZER)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    note(f"materializer_returncode={proc.returncode}")
    stdout_tail = diagnostic_tail(proc.stdout)
    stderr_tail = diagnostic_tail(proc.stderr)
    if stdout_tail:
        note("materializer_stdout_tail_begin")
        note(stdout_tail)
        note("materializer_stdout_tail_end")
    if stderr_tail:
        note("materializer_stderr_tail_begin")
        note(stderr_tail)
        note("materializer_stderr_tail_end")
    if proc.returncode != 0:
        raise RuntimeError(f"Materializer failed with exit code {proc.returncode}; see declared preflight artifact")
    note("materializer=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
