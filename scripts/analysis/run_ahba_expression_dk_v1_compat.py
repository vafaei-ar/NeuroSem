#!/usr/bin/env python3
"""Compatibility wrapper for frozen AHBA expression preparation.

Restores only legacy pandas call signatures required by abagen 0.1.3 under
current pandas, then executes the frozen preparation script unchanged.
"""
from __future__ import annotations

import runpy
from pathlib import Path

import pandas as pd


def _install_set_axis_compat() -> bool:
    """Allow legacy ``set_axis(..., inplace=False)`` calls from abagen 0.1.3."""
    original_df = pd.DataFrame.set_axis
    original_series = pd.Series.set_axis

    def _df_set_axis(self, labels, axis=0, inplace=None, copy=None):
        if inplace not in (None, False):
            raise TypeError("Compatibility wrapper only supports inplace=False")
        kwargs = {"axis": axis}
        if copy is not None:
            kwargs["copy"] = copy
        return original_df(self, labels, **kwargs)

    def _series_set_axis(self, labels, axis=0, inplace=None, copy=None):
        if inplace not in (None, False):
            raise TypeError("Compatibility wrapper only supports inplace=False")
        kwargs = {"axis": axis}
        if copy is not None:
            kwargs["copy"] = copy
        return original_series(self, labels, **kwargs)

    pd.DataFrame.set_axis = _df_set_axis
    pd.Series.set_axis = _series_set_axis
    return True


def main() -> None:
    _install_set_axis_compat()
    target = Path(__file__).with_name("prepare_ahba_expression_dk_v1.py")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
