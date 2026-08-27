#!/usr/bin/env python3
"""Compatibility launcher for the frozen published-language-panel validation.

This launcher changes only the serialization shape of the already-frozen panel
JSON when panel entries are direct gene lists. It does not alter gene membership,
analysis parameters, seeds, nulls, statistics, or thresholds.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    argv = sys.argv[1:]
    try:
        i = argv.index("--panel-json")
    except ValueError as exc:
        raise SystemExit("--panel-json is required") from exc
    if i + 1 >= len(argv):
        raise SystemExit("--panel-json requires a path")

    src = Path(argv[i + 1])
    obj = json.loads(src.read_text(encoding="utf-8"))
    panels = obj.get("panels", obj)
    changed = False
    fixed = dict(obj)
    fixed_panels = dict(panels)
    for pid, value in panels.items():
        if isinstance(value, list):
            fixed_panels[pid] = {"genes": value}
            changed = True
    if not changed:
        cmd = [sys.executable, "scripts/analysis/run_ahba_published_language_panel_validation_v1.py", *argv]
        return subprocess.run(cmd, check=False).returncode

    fixed["panels"] = fixed_panels
    with tempfile.TemporaryDirectory(prefix="neurosem_panel_compat_") as td:
        tmp = Path(td) / "gene_panels.compat.json"
        tmp.write_text(json.dumps(fixed, indent=2) + "\n", encoding="utf-8")
        patched = list(argv)
        patched[i + 1] = str(tmp)
        cmd = [sys.executable, "scripts/analysis/run_ahba_published_language_panel_validation_v1.py", *patched]
        return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
