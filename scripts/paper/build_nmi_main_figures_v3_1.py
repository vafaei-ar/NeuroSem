#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


def load_v3():
    path = Path(__file__).with_name("build_nmi_main_figures_v3.py")
    spec = importlib.util.spec_from_file_location("neurosem_nmi_figures_v3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shallow_discover_csv(module, root: Path, required: set[str], prefer: str | None = None) -> Path:
    # Figure assembly must never recursively crawl the full outputs tree. Some
    # historical output directories contain large nested caches and adapters.
    # Frozen aggregate result tables used by the manuscript are written at the
    # first or second level below each analysis' latest/ directory.
    candidates = list(root.glob("*/latest/*.csv"))
    candidates.extend(root.glob("*/latest/*/*.csv"))
    matches = []
    for p in candidates:
        try:
            if required.issubset(module.headers(p)):
                score = int(prefer is not None and prefer.lower() in str(p).lower())
                matches.append((score, p.stat().st_mtime, p))
        except Exception:
            continue
    if not matches:
        raise FileNotFoundError(
            f"No shallow frozen CSV under {root} with columns {sorted(required)}"
        )
    matches.sort(key=lambda z: (z[0], z[1]), reverse=True)
    chosen = matches[0][2]
    print(f"figure-source: {chosen}", flush=True)
    return chosen


def main() -> int:
    module = load_v3()
    module.discover_csv = lambda root, required, prefer=None: shallow_discover_csv(
        module, root, required, prefer
    )
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
