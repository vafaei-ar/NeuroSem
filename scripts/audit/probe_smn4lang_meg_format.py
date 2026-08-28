#!/usr/bin/env python3
"""Compatibility entry point for the model-blind SMN4Lang MEG probe.

The first execution established that the metadata checkout has no configured
annex content remote for the representative MEG FIF. The named RunRelay task
is intentionally preserved, but the probe now delegates to the narrower
materialization-route diagnostic before any payload download or signal access.
"""
from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    target = Path(__file__).with_name("probe_smn4lang_meg_materialization_route.py")
    runpy.run_path(str(target), run_name="__main__")
