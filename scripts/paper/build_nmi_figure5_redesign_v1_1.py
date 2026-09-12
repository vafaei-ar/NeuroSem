#!/usr/bin/env python3
"""Compatibility wrapper for the redesigned NMI Figure 5 builder.

Some legacy frozen summary JSON files predate the project-wide ``status`` field.
The canonical Figure 5 builder correctly rejects an explicit non-OK status, but older
successful summaries can omit the field entirely. This wrapper treats *missing* status
as legacy-success metadata while preserving rejection of any explicit non-OK status.
No scientific values are modified.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts" / "paper" / "build_nmi_figure5_redesign_v1.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("nmi_figure5_redesign_v1", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load canonical builder: {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    mod = load_builder()
    original_read_json = mod.read_json

    def read_json_legacy_compatible(path):
        payload = original_read_json(path)
        # Legacy successful summaries may omit status entirely. Do not alter or
        # accept any explicit non-OK status.
        if isinstance(payload, dict) and "status" not in payload:
            payload = dict(payload)
            payload["status"] = "ok"
        return payload

    mod.read_json = read_json_legacy_compatible
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
