#!/usr/bin/env python3
"""Compatibility wrapper for the presentation-only Figure 5 redesign.

Some frozen legacy summary JSON files predate the status=ok field. This wrapper treats a
missing status key as legacy-success while preserving rejection of any explicit non-ok status.
It changes no scientific value or plotting logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import build_nmi_figure5_redesign_v1 as b  # noqa: E402

_original_read_json = b.read_json


def _legacy_compatible_read_json(path: Path) -> dict:
    payload = _original_read_json(path)
    if "status" not in payload:
        payload = dict(payload)
        payload["status"] = "ok"
    return payload


b.read_json = _legacy_compatible_read_json

if __name__ == "__main__":
    raise SystemExit(b.main())
