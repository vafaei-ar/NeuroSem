#!/usr/bin/env python3
"""Compatibility entrypoint for the strict ChineseEEG representation benchmark.

Keeps the scientific benchmark unchanged while providing NumPy 2.x compatibility
for the legacy ``np.trapz`` calls used by the benchmark implementation.
"""

from __future__ import annotations

import numpy as np

# NumPy 2.x removed np.trapz in favor of np.trapezoid. The benchmark only uses
# this function for numerical integration of periodogram power. Restore the old
# alias locally for this process when needed, without changing numerical intent.
if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid  # type: ignore[attr-defined]

from run_chineseeeg_eeg_representation_overnight import main


if __name__ == "__main__":
    raise SystemExit(main())
