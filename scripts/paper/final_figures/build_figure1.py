#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAPER_SCRIPTS = ROOT / "scripts" / "paper"
if str(PAPER_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPTS))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import build_nmi_figure1_mockup_v3 as impl
from common import OUT


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "source_manifest.json"
    if tmp.exists():
        tmp.unlink()
    impl.OUT = OUT
    impl.main()
    if not tmp.exists():
        raise RuntimeError("Figure 1 builder did not emit its source manifest")
    tmp.replace(OUT / "figure1_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
