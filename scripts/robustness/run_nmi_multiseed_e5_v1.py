#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SEEDS = [20260829, 20260830, 20260831]
BASE_CONFIG = Path('configs/e5_neural_tuning_v1.json')
ROOT = Path('outputs/nmi_multiseed_e5_v1')


def run(cmd):
    print('+', ' '.join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def latest_adapter(root: Path) -> Path:
    candidates = sorted([p / 'adapter' for p in root.iterdir() if p.is_dir() and (p / 'adapter').is_dir()]) if root.exists() else []
    if not candidates:
        raise RuntimeError(f'no adapter under {root}')
    return candidates[-1]


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    cfg0 = json.loads(BASE_CONFIG.read_text(encoding='utf-8'))
    all_rows = []
    for idx, seed in enumerate(SEEDS, start=1):
        print(f'=== post-confirmatory seed {idx}/{len(SEEDS)}: {seed} ===', flush=True)
        seed_root = ROOT / f'seed_{seed}'
        seed_root.mkdir(parents=True, exist_ok=True)
        cfg = dict(cfg0)
        cfg['seed'] = seed
        cfg['postconfirmatory_robustness'] = True
        cfg_path = seed_root / 'config.json'
        cfg_path.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')

        run(['.venv/bin/python', 'scripts/tuning/train_e5_neurosem_lora.py', '--arm', 'text_only', '--config', cfg_path, '--output-dir', seed_root, '--device', 'auto'])
        run(['.venv/bin/python', 'scripts/tuning/train_e5_neurosem_lora.py', '--arm', 'neural', '--config', cfg_path, '--output-dir', seed_root, '--device', 'auto', '--neural-loss-weight', '0.10'])

        text_adapter = latest_adapter(seed_root / 'text_only')
        neural_root = seed_root / 'neural'

        zuco_out = seed_root / 'zuco'
        fmri_out = seed_root / 'smn4lang_fmri'
        run(['.venv/bin/python', 'scripts/robustness/evaluate_external_with_adapters_v1.py', '--dataset', 'zuco', '--text-adapter', text_adapter, '--neural-root', neural_root, '--output-dir', zuco_out])
        run(['.venv/bin/python', 'scripts/robustness/evaluate_external_with_adapters_v1.py', '--dataset', 'smn4lang_fmri', '--text-adapter', text_adapter, '--neural-root', neural_root, '--output-dir', fmri_out])

        z = json.loads((zuco_out / 'summary.json').read_text(encoding='utf-8'))['primary_result']
        f = json.loads((fmri_out / 'summary.json').read_text(encoding='utf-8'))
        f_primary = f.get('primary_result', f)
        f_mean = f_primary.get('mean_delta', f_primary.get('mean_participant_delta'))
        f_frac = f_primary.get('fraction_subjects_positive', f_primary.get('fraction_participants_positive'))
        all_rows.append({
            'seed': seed,
            'zuco_mean_delta': float(z['mean_delta']),
            'zuco_fraction_positive': float(z['fraction_subjects_positive']),
            'smn4lang_fmri_mean_delta': float(f_mean),
            'smn4lang_fmri_fraction_positive': float(f_frac),
        })

    payload = {
        'schema_version': 1,
        'analysis_stage': 'post-confirmatory optimization-seed robustness',
        'protocol': 'docs/nmi_postconfirmatory_robustness_protocol_v1.md',
        'seeds': SEEDS,
        'n_additional_seeds': len(SEEDS),
        'results': all_rows,
        'summary': {
            'zuco_all_seed_mean_deltas_positive': bool(all(r['zuco_mean_delta'] > 0 for r in all_rows)),
            'smn4lang_fmri_all_seed_mean_deltas_positive': bool(all(r['smn4lang_fmri_mean_delta'] > 0 for r in all_rows)),
            'zuco_mean_of_seed_mean_deltas': float(sum(r['zuco_mean_delta'] for r in all_rows) / len(all_rows)),
            'smn4lang_fmri_mean_of_seed_mean_deltas': float(sum(r['smn4lang_fmri_mean_delta'] for r in all_rows) / len(all_rows)),
        },
        'guardrail': 'All prespecified seeds are reported. These are post-confirmatory robustness analyses, not new prospective confirmation.'
    }
    latest = ROOT / 'latest'
    latest.mkdir(parents=True, exist_ok=True)
    (latest / 'summary.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
