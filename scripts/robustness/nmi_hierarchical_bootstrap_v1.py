#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

SEED = 20260829
N_BOOT = 10_000


def read_csv(path: Path):
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def matrix_from_rows(rows, subject_key, stimulus_key, delta_key):
    subjects = sorted({r[subject_key] for r in rows})
    stimuli = sorted({r[stimulus_key] for r in rows}, key=lambda x: int(str(x).replace('NR', '')))
    si = {s: i for i, s in enumerate(subjects)}
    ti = {t: i for i, t in enumerate(stimuli)}
    mat = np.full((len(subjects), len(stimuli)), np.nan, dtype=float)
    for r in rows:
        mat[si[r[subject_key]], ti[r[stimulus_key]]] = float(r[delta_key])
    if not np.isfinite(mat).all():
        raise RuntimeError('incomplete participant x stimulus matrix')
    return subjects, stimuli, mat


def two_factor_bootstrap(mat, rng):
    n_sub, n_stim = mat.shape
    vals = np.empty(N_BOOT, dtype=float)
    for b in range(N_BOOT):
        s = rng.integers(0, n_sub, size=n_sub)
        t = rng.integers(0, n_stim, size=n_stim)
        vals[b] = float(mat[np.ix_(s, t)].mean())
    return vals


def summarize(name, subjects, stimuli, mat, rng):
    boot = two_factor_bootstrap(mat, rng)
    return {
        'dataset': name,
        'n_participants': len(subjects),
        'n_stimulus_units': len(stimuli),
        'observed_cell_mean_delta': float(mat.mean()),
        'participant_mean_deltas': [float(x) for x in mat.mean(axis=1)],
        'stimulus_mean_deltas': [float(x) for x in mat.mean(axis=0)],
        'two_factor_bootstrap': {
            'seed': SEED,
            'n_resamples': N_BOOT,
            'percentile_95ci': [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            'fraction_bootstrap_means_gt_0': float(np.mean(boot > 0)),
        },
        'interpretation_guardrail': 'Post-confirmatory sensitivity over participants and analyzed stimulus units; not unrestricted stimulus-population inference.'
    }


def main():
    out = Path('outputs/nmi_hierarchical_robustness_v1/latest')
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    zuco_rows = read_csv(Path('outputs/zuco2_nr_e5_transfer_v1/latest/session_results.csv'))
    z_sub, z_stim, z_mat = matrix_from_rows(zuco_rows, 'subject', 'run', 'delta_0p10_minus_0')

    fmri_rows = read_csv(Path('outputs/smn4lang_fmri_e5_transfer_v1/latest/story_results.csv'))
    f_sub, f_stim, f_mat = matrix_from_rows(fmri_rows, 'subject', 'story', 'delta_0p10_minus_0')

    payload = {
        'schema_version': 1,
        'analysis_stage': 'post-confirmatory participant-by-stimulus hierarchical robustness',
        'protocol': 'docs/nmi_postconfirmatory_robustness_protocol_v1.md',
        'zuco': summarize('ZuCo 2.0 Task 1 normal reading', z_sub, z_stim, z_mat, rng),
        'smn4lang_fmri': summarize('SMN4Lang fMRI', f_sub, f_stim, f_mat, rng),
    }
    (out / 'summary.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
