#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

SEEDS = [20260829, 20260830, 20260831]
ROOT = Path('outputs/nmi_reviewer_response_scientific_v1/latest')
OUT = Path('outputs/nmi_reviewer_response_consolidated_v1/latest')


def read_csv(path: Path) -> list[dict]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def exact_two_sided_signflip(values: list[float]) -> float:
    x = np.asarray(values, dtype=float)
    obs = abs(float(np.mean(x)))
    total = 1 << len(x)
    count = 0
    for mask in range(total):
        signs = np.ones(len(x), dtype=float)
        for i in range(len(x)):
            if mask & (1 << i):
                signs[i] = -1.0
        if abs(float(np.mean(x * signs))) >= obs - 1e-15:
            count += 1
    return float(count / total)


def summarize(dataset: str, comparison_dir: Path) -> dict:
    csv_name = 'subject_results.csv' if dataset == 'zuco' else 'participant_results.csv'
    rows = read_csv(comparison_dir / csv_name)
    vals = [float(r['delta_0p10_minus_0']) for r in rows]
    arr = np.asarray(vals, dtype=float)
    return {
        'n_participants': len(vals),
        'mean_delta': float(np.mean(arr)),
        'median_delta': float(np.median(arr)),
        'n_positive': int(np.sum(arr > 0)),
        'exact_two_sided_signflip_p': exact_two_sided_signflip(vals),
        'source_summary': json.loads((comparison_dir / 'summary.json').read_text(encoding='utf-8')),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    seed_results = []
    for seed in SEEDS:
        row = {'seed': seed, 'targets': {}}
        for dataset in ['zuco', 'smn4lang_fmri']:
            base = ROOT / f'seed_{seed}' / dataset
            row['targets'][dataset] = {
                'shuffled_minus_text': summarize(dataset, base / 'shuffled_minus_text'),
                'genuine_minus_shuffled': summarize(dataset, base / 'genuine_minus_shuffled'),
            }
        seed_results.append(row)

    cross_seed = {}
    for dataset in ['zuco', 'smn4lang_fmri']:
        gms = [r['targets'][dataset]['genuine_minus_shuffled']['mean_delta'] for r in seed_results]
        smt = [r['targets'][dataset]['shuffled_minus_text']['mean_delta'] for r in seed_results]
        cross_seed[dataset] = {
            'genuine_minus_shuffled_seed_means': gms,
            'genuine_minus_shuffled_mean_of_seed_means': float(np.mean(gms)),
            'genuine_minus_shuffled_all_seed_means_positive': bool(all(v > 0 for v in gms)),
            'shuffled_minus_text_seed_means': smt,
            'shuffled_minus_text_mean_of_seed_means': float(np.mean(smt)),
            'shuffled_minus_text_all_seed_means_positive': bool(all(v > 0 for v in smt)),
        }

    hb_path = Path('outputs/nmi_hierarchical_robustness_v1/latest/summary.json')
    ms_path = Path('outputs/nmi_model_space_characterization_v1/latest/summary.json')
    payload = {
        'schema_version': 1,
        'analysis_stage': 'reviewer-driven post-confirmatory consolidation of completed outputs',
        'specificity_control': {
            'seeds': SEEDS,
            'seed_results': seed_results,
            'cross_seed_summary': cross_seed,
        },
        'hierarchical_bootstrap': json.loads(hb_path.read_text(encoding='utf-8')),
        'model_space_characterization': json.loads(ms_path.read_text(encoding='utf-8')),
        'provenance_note': (
            'Specificity evaluations for all three seeds and both external targets were completed by the '
            'scientific child process associated with cancelled RunRelay job Q4R8M2K7. The hierarchical '
            'bootstrap was also completed. The model-space characterization is the previously completed '
            'frozen post-confirmatory result and was not rerun here. This consolidation performs no training, '
            'model evaluation, target selection, or new scientific search.'
        ),
    }
    path = OUT / 'summary.json'
    path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
