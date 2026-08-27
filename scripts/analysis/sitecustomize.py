"""Narrow runtime compatibility for the AHBA language-panel validator.

This file is imported automatically by Python's site initialization when scripts
in this directory are executed. It is intentionally inert for every script except
run_ahba_published_language_panel_validation_v1.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_TARGET = "run_ahba_published_language_panel_validation_v1.py"
_PANEL_IDS = {
    "wong_2024_language_connectivity_6",
    "wong_2024_language_dyslexia_14",
}

if Path(sys.argv[0]).name == _TARGET:
    _original_loads = json.loads

    def _loads_compat(s, *args, **kwargs):
        obj = _original_loads(s, *args, **kwargs)
        if isinstance(obj, dict) and isinstance(obj.get("panels"), dict):
            panels = obj["panels"]
            if _PANEL_IDS.issubset(panels) and all(
                isinstance(panels[pid], list) for pid in _PANEL_IDS
            ):
                obj = dict(obj)
                obj["panels"] = dict(panels)
                for pid in _PANEL_IDS:
                    obj["panels"][pid] = {
                        "retained_primary_ahba_genes": list(panels[pid])
                    }
        return obj

    json.loads = _loads_compat
