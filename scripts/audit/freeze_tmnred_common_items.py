#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from scipy.io import loadmat


def load_bepoch(set_path: Path):
    d = loadmat(set_path, simplify_cells=True)
    src = d.get('EEG') if isinstance(d.get('EEG'), dict) else d
    b = src.get('bepoch')
    if b is None:
        raise RuntimeError(f'bepoch missing: {set_path}')
    if hasattr(b, 'tolist'):
        b = b.tolist()
    if not isinstance(b, list):
        b = [b]
    return [int(x) for x in b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-root', default='data/raw/tmnred')
    ap.add_argument('--materialization-summary', default='outputs/tmnred_representation_input_materialization/latest/summary.json')
    ap.add_argument('--output-dir', default='outputs/tmnred_common_item_freeze/latest')
    ap.add_argument('--min-common-items', type=int, default=20)
    args = ap.parse_args()

    root = Path(args.data_root)
    summary = json.loads(Path(args.materialization_summary).read_text())
    subjects = summary['ready_subjects_all_8_sessions']
    outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    sessions = [f'ses-{i}' for i in range(1,9)]
    per_session = {}
    failures = []

    for session in sessions:
        retained = {}
        for subject in subjects:
            p = root / f'derivatives/preproc/{subject}/{session}/{subject}-{session}z.set'
            try:
                vals = load_bepoch(p)
                if len(vals) != len(set(vals)):
                    raise RuntimeError('duplicate bepoch values')
                retained[subject] = sorted(vals)
            except Exception as exc:
                failures.append({'subject': subject, 'session': session, 'error': f'{type(exc).__name__}:{exc}'})
        if failures:
            continue
        common = sorted(set.intersection(*[set(v) for v in retained.values()]))
        union = sorted(set.union(*[set(v) for v in retained.values()]))
        per_session[session] = {
            'n_subjects': len(subjects),
            'n_common_items': len(common),
            'common_bepoch': common,
            'n_union_items': len(union),
            'min_retained_per_subject': min(len(v) for v in retained.values()),
            'max_retained_per_subject': max(len(v) for v in retained.values()),
        }
        if len(common) < args.min_common_items:
            failures.append({'session': session, 'error': f'common item intersection below {args.min_common_items}: {len(common)}'})

    payload = {
        'schema_version': 1,
        'dataset': 'TMNRED',
        'model_blind': True,
        'ready_subjects': subjects,
        'n_ready_subjects': len(subjects),
        'item_identity': 'EEGLAB bepoch, already validated against BIDS event row ordering',
        'primary_design': 'within-session RDMs on exact common retained item intersection across the frozen 29-subject cohort',
        'min_common_items_required': args.min_common_items,
        'sessions': per_session,
        'failures': failures,
        'notes': [
            'No EEG values, representation reliability, language-model embeddings, or neural-model RSA are computed.',
            'This freezes item availability before any representation outcome is inspected.',
            'The same common item set within each session will be used for every primary representation candidate.'
        ]
    }
    (outdir/'summary.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    if failures:
        raise SystemExit(f'TMNRED common-item freeze failed with {len(failures)} issue(s)')
    print(json.dumps({'status':'ok','n_subjects':len(subjects),'common_items':{k:v['n_common_items'] for k,v in per_session.items()}}, indent=2))

if __name__ == '__main__':
    main()
