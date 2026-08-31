#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('outputs/nmi_reviewer_response_scientific_v1/latest')
ADAPTER_ROOT = Path('outputs/nmi_multiseed_e5_v1')
OUT = Path('outputs/nmi_reviewer_response_diagnostic_v1/latest/diagnostic.json')
SEEDS = [20260829, 20260830, 20260831]
DATASETS = ['zuco', 'smn4lang_fmri']
CONTRASTS = ['shuffled_minus_text', 'genuine_minus_shuffled']


def stamp(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def csv_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open('r', encoding='utf-8', newline='') as f:
        return sum(1 for _ in csv.DictReader(f))


def file_state(path: Path) -> dict:
    return {
        'exists': path.exists(),
        'is_file': path.is_file(),
        'size_bytes': path.stat().st_size if path.is_file() else None,
        'mtime_utc': stamp(path),
    }


def adapter_runs(seed: int, arm: str) -> list[dict]:
    root = ADAPTER_ROOT / f'seed_{seed}' / arm
    if not root.exists():
        return []
    rows = []
    for p in sorted(x for x in root.iterdir() if x.is_dir()):
        rows.append({
            'path': str(p),
            'mtime_utc': stamp(p),
            'has_adapter': (p / 'adapter').is_dir(),
            'has_summary': (p / 'summary.json').is_file(),
            'summary_mtime_utc': stamp(p / 'summary.json'),
        })
    return rows


def main() -> int:
    payload = {
        'schema_version': 1,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'reviewer_output_root': str(ROOT),
        'root_exists': ROOT.exists(),
        'root_mtime_utc': stamp(ROOT),
        'top_level_summary': file_state(ROOT / 'summary.json'),
        'hierarchical_bootstrap': file_state(Path('outputs/nmi_hierarchical_robustness_v1/latest/summary.json')),
        'model_space_characterization': file_state(Path('outputs/nmi_model_space_characterization_v1/latest/summary.json')),
        'seeds': [],
    }

    for seed in SEEDS:
        srow = {
            'seed': seed,
            'adapters': {
                arm: adapter_runs(seed, arm)
                for arm in ['text_only', 'neural', 'shuffled_neural']
            },
            'targets': {},
        }
        for dataset in DATASETS:
            drow = {}
            for contrast in CONTRASTS:
                root = ROOT / f'seed_{seed}' / dataset / contrast
                csv_name = 'subject_results.csv' if dataset == 'zuco' else 'participant_results.csv'
                story_name = 'story_results.csv'
                drow[contrast] = {
                    'dir_exists': root.exists(),
                    'dir_mtime_utc': stamp(root),
                    'summary': file_state(root / 'summary.json'),
                    'participant_csv': file_state(root / csv_name),
                    'participant_rows': csv_rows(root / csv_name),
                    'story_csv': file_state(root / story_name),
                    'story_rows': csv_rows(root / story_name),
                }
            srow['targets'][dataset] = drow
        payload['seeds'].append(srow)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
