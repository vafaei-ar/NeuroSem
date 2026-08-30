#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import numpy as np

SEEDS = [20260829, 20260830, 20260831]
BASE_CONFIG = Path('configs/e5_neural_tuning_v1.json')
EXISTING_ROOT = Path('outputs/nmi_multiseed_e5_v1')
OUT = Path('outputs/nmi_reviewer_response_scientific_v1/latest')


def run(cmd: list[str]) -> None:
    print('+', ' '.join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def latest_adapter(root: Path) -> Path:
    candidates = sorted([p / 'adapter' for p in root.iterdir() if p.is_dir() and (p / 'adapter').is_dir()]) if root.exists() else []
    if not candidates:
        raise RuntimeError(f'no adapter under {root}')
    return candidates[-1]


def read_csv(path: Path) -> list[dict]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def exact_two_sided_signflip(values: list[float]) -> float:
    x = np.asarray(values, dtype=float)
    n = len(x)
    obs = abs(float(np.mean(x)))
    count = 0
    total = 1 << n
    for mask in range(total):
        signs = np.ones(n, dtype=float)
        for i in range(n):
            if mask & (1 << i):
                signs[i] = -1.0
        if abs(float(np.mean(x * signs))) >= obs - 1e-15:
            count += 1
    return float(count / total)


def pair_delta_file(dataset: str, out_dir: Path) -> tuple[Path, str]:
    if dataset == 'zuco':
        return out_dir / 'subject_results.csv', 'delta_0p10_minus_0'
    return out_dir / 'participant_results.csv', 'delta_0p10_minus_0'


def summarize_pair(dataset: str, out_dir: Path) -> dict:
    csv_path, key = pair_delta_file(dataset, out_dir)
    rows = read_csv(csv_path)
    vals = [float(r[key]) for r in rows]
    summary = json.loads((out_dir / 'summary.json').read_text(encoding='utf-8'))
    if dataset == 'zuco':
        primary = summary['primary_result']
        mean_delta = float(primary['mean_delta'])
        one_sided = float(primary['exact_one_sided_signflip_p'])
        ci = primary['bootstrap_95_ci_mean_delta']
    else:
        mean_delta = float(summary['primary_mean_delta'])
        one_sided = float(summary['primary_exact_one_sided_signflip_p'])
        ci = summary['primary_bootstrap_95_ci_mean_delta']
    return {
        'n_participants': len(vals),
        'mean_delta': mean_delta,
        'median_delta': float(np.median(vals)),
        'n_positive': int(np.sum(np.asarray(vals) > 0)),
        'bootstrap_95_ci_mean_delta': [float(ci[0]), float(ci[1])],
        'exact_one_sided_signflip_p': one_sided,
        'exact_two_sided_signflip_p': exact_two_sided_signflip(vals),
        'participant_deltas': vals,
    }


def ensure_shuffled(seed: int, seed_root: Path) -> Path:
    shuffled_root = seed_root / 'shuffled_neural'
    existing = sorted([p for p in shuffled_root.iterdir() if p.is_dir() and (p / 'adapter').is_dir()]) if shuffled_root.exists() else []
    if existing:
        chosen = existing[-1]
        saved = json.loads((chosen / 'summary.json').read_text(encoding='utf-8'))
        cfg = saved.get('config', {})
        if int(cfg.get('seed', -1)) != seed or abs(float(cfg.get('neural_loss_weight', -1)) - 0.10) > 1e-12:
            raise RuntimeError(f'unexpected pre-existing shuffled control under {chosen}')
        print(f'Reusing frozen shuffled control: {chosen}', flush=True)
        return chosen / 'adapter'

    cfg0 = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))
    cfg = dict(cfg0)
    cfg['seed'] = seed
    cfg['neural_loss_weight'] = 0.10
    cfg['reviewer_driven_specificity_control'] = True
    cfg['protocol'] = 'docs/25_NMI_REVIEWER_SPECIFICITY_AND_ROBUSTNESS_V1.md'
    cfg_path = seed_root / 'reviewer_specificity_config.json'
    cfg_path.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
    run([
        '.venv/bin/python', 'scripts/tuning/train_e5_neurosem_lora.py',
        '--arm', 'shuffled_neural', '--config', str(cfg_path),
        '--output-dir', str(seed_root), '--device', 'auto'
    ])
    return latest_adapter(shuffled_root)


def original_two_sided_sensitivity() -> dict:
    specs = {
        'zuco_primary': (Path('outputs/zuco2_nr_e5_transfer_v1/latest/subject_results.csv'), 'delta_0p10_minus_0'),
        'smn4lang_fmri_primary': (Path('outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv'), 'delta_0p10_minus_0'),
    }
    out = {}
    for name, (path, key) in specs.items():
        rows = read_csv(path)
        vals = [float(r[key]) for r in rows]
        out[name] = {
            'n_participants': len(vals),
            'mean_delta': float(np.mean(vals)),
            'exact_two_sided_signflip_p': exact_two_sided_signflip(vals),
        }
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    seed_results = []

    for idx, seed in enumerate(SEEDS, start=1):
        print(f'=== reviewer neural-specificity seed {idx}/{len(SEEDS)}: {seed} ===', flush=True)
        seed_root = EXISTING_ROOT / f'seed_{seed}'
        text_adapter = latest_adapter(seed_root / 'text_only')
        genuine_root = seed_root / 'neural'
        genuine_adapter = latest_adapter(genuine_root)
        shuffled_adapter = ensure_shuffled(seed, seed_root)

        row = {
            'seed': seed,
            'text_adapter': str(text_adapter.resolve()),
            'genuine_adapter': str(genuine_adapter.resolve()),
            'shuffled_adapter': str(shuffled_adapter.resolve()),
            'targets': {},
        }

        for dataset in ['zuco', 'smn4lang_fmri']:
            target_root = OUT / f'seed_{seed}' / dataset
            shuffled_vs_text = target_root / 'shuffled_minus_text'
            genuine_vs_shuffled = target_root / 'genuine_minus_shuffled'

            run([
                '.venv/bin/python', 'scripts/robustness/evaluate_external_with_adapters_v1.py',
                '--dataset', dataset, '--text-adapter', str(text_adapter),
                '--neural-root', str(seed_root / 'shuffled_neural'), '--output-dir', str(shuffled_vs_text)
            ])
            run([
                '.venv/bin/python', 'scripts/robustness/evaluate_external_with_adapters_v1.py',
                '--dataset', dataset, '--text-adapter', str(shuffled_adapter),
                '--neural-root', str(genuine_root), '--output-dir', str(genuine_vs_shuffled)
            ])

            row['targets'][dataset] = {
                'genuine_minus_shuffled': summarize_pair(dataset, genuine_vs_shuffled),
                'shuffled_minus_text': summarize_pair(dataset, shuffled_vs_text),
            }
        seed_results.append(row)

    # Re-run already frozen reviewer-requested sensitivity analyses.
    run(['.venv/bin/python', 'scripts/robustness/nmi_hierarchical_bootstrap_v1.py'])
    run(['.venv/bin/python', 'scripts/robustness/nmi_model_space_characterization_v1.py'])

    cross_seed = {}
    for dataset in ['zuco', 'smn4lang_fmri']:
        gms = [r['targets'][dataset]['genuine_minus_shuffled']['mean_delta'] for r in seed_results]
        smt = [r['targets'][dataset]['shuffled_minus_text']['mean_delta'] for r in seed_results]
        cross_seed[dataset] = {
            'genuine_minus_shuffled_seed_means': gms,
            'genuine_minus_shuffled_all_seed_means_positive': bool(all(v > 0 for v in gms)),
            'genuine_minus_shuffled_mean_of_seed_means': float(np.mean(gms)),
            'shuffled_minus_text_seed_means': smt,
            'shuffled_minus_text_all_seed_means_positive': bool(all(v > 0 for v in smt)),
            'shuffled_minus_text_mean_of_seed_means': float(np.mean(smt)),
        }

    payload = {
        'schema_version': 1,
        'analysis_stage': 'reviewer-driven post-confirmatory specificity and robustness',
        'protocol': 'docs/25_NMI_REVIEWER_SPECIFICITY_AND_ROBUSTNESS_V1.md',
        'seeds': SEEDS,
        'specificity_control': {
            'control': 'already-materialized shuffled ChineseEEG neural target; lambda=0.10; matched E5/LoRA/text objective and training budget',
            'seed_results': seed_results,
            'cross_seed_summary': cross_seed,
        },
        'original_primary_two_sided_sensitivity': original_two_sided_sensitivity(),
        'hierarchical_bootstrap_output': 'outputs/nmi_hierarchical_robustness_v1/latest/summary.json',
        'model_space_characterization_output': 'outputs/nmi_model_space_characterization_v1/latest/summary.json',
        'guardrails': [
            'Reviewer-driven and post-confirmatory; does not alter the original prospective evidence hierarchy.',
            'No ZuCo or SMN4Lang target outcome is used for model, lambda, checkpoint, representation, participant, or stimulus selection.',
            'All three prespecified added seeds and both external targets are retained.',
            'No model-specific or target-specific rescue tuning is permitted after outcome inspection.',
        ],
    }
    (OUT / 'summary.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
