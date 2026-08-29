#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', choices=['zuco', 'smn4lang_fmri'], required=True)
    ap.add_argument('--text-adapter', type=Path, required=True)
    ap.add_argument('--neural-root', type=Path, required=True, help='Directory containing timestamped neural training runs with adapter subdirectories.')
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()

    if args.dataset == 'zuco':
        import scripts.tuning.evaluate_zuco2_nr_e5_transfer_v1 as mod
        mod.TEXT_ONLY_ADAPTER = args.text_adapter.resolve()
        mod.LAMBDA_010_ROOT = args.neural_root.resolve()
        sys.argv = [mod.__file__, '--output-dir', str(args.output_dir), '--device', 'auto']
        mod.main()
    else:
        import scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 as mod
        mod.TEXT_ONLY_ADAPTER = args.text_adapter.resolve()
        mod.LAMBDA_010_ROOT = args.neural_root.resolve()
        sys.argv = [mod.__file__, '--output-dir', str(args.output_dir), '--device', 'auto']
        raise SystemExit(mod.main())


if __name__ == '__main__':
    main()
