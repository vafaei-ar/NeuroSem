#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr, spearmanr

from scripts.analysis.run_zuco2_nr_primary_representation_reliability import EXPECTED, load_material_rows
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import TEXT_ONLY_ADAPTER, LAMBDA_010_ROOT, latest_completed_adapter, load_adapter, encode_texts

K = 10


def centered_linear_cka(x: np.ndarray, y: np.ndarray) -> float:
    x = x - x.mean(axis=0, keepdims=True)
    y = y - y.mean(axis=0, keepdims=True)
    xty = x.T @ y
    num = float(np.sum(xty * xty))
    den = float(np.linalg.norm(x.T @ x, ord='fro') * np.linalg.norm(y.T @ y, ord='fro'))
    return num / den if den > 0 else float('nan')


def knn_overlap(a: np.ndarray, b: np.ndarray, k: int) -> tuple[float, list[float]]:
    da = squareform(pdist(a, metric='cosine'))
    db = squareform(pdist(b, metric='cosine'))
    overlaps = []
    for i in range(a.shape[0]):
        na = set(np.argsort(da[i])[1:k+1].tolist())
        nb = set(np.argsort(db[i])[1:k+1].tolist())
        overlaps.append(len(na & nb) / len(na | nb))
    return float(np.mean(overlaps)), overlaps


def main():
    import torch

    out = Path('outputs/nmi_model_space_characterization_v1/latest')
    out.mkdir(parents=True, exist_ok=True)
    mapping = json.loads(Path('outputs/zuco2_nr_format_probe/latest/summary.json').read_text(encoding='utf-8'))
    maps = {r['run']: r for r in mapping['wordcount_mapping_diagnostics']}
    texts = []
    for run in range(1, 8):
        rows = load_material_rows(Path('data/raw/zuco2_probe/task_materials') / f'nr_{run}.csv')
        selected = maps[f'NR{run}']['selected_material_rows_1based']
        run_texts = [str(rows[i-1][2]).strip() for i in selected]
        if len(run_texts) != EXPECTED[run]:
            raise RuntimeError(f'NR{run}: frozen text count mismatch')
        texts.extend(run_texts)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    adapter_010 = latest_completed_adapter(LAMBDA_010_ROOT)
    tok0, m0 = load_adapter(TEXT_ONLY_ADAPTER, device)
    e0 = encode_texts(m0, tok0, texts, device)
    del m0
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    tok1, m1 = load_adapter(adapter_010, device)
    e1 = encode_texts(m1, tok1, texts, device)
    del m1
    if torch.cuda.is_available(): torch.cuda.empty_cache()

    if e0.shape != e1.shape or e0.shape[0] != len(texts):
        raise RuntimeError('embedding shape mismatch')
    item_cos = np.sum(e0 * e1, axis=1) / np.clip(np.linalg.norm(e0, axis=1) * np.linalg.norm(e1, axis=1), 1e-12, None)
    d0 = pdist(e0, metric='cosine')
    d1 = pdist(e1, metric='cosine')
    p = float(pearsonr(d0, d1).statistic)
    s = float(spearmanr(d0, d1).statistic)
    cka = float(centered_linear_cka(e0, e1))
    knn_mean, knn_items = knn_overlap(e0, e1, K)

    payload = {
        'schema_version': 1,
        'analysis_stage': 'post-confirmatory descriptive model-space characterization',
        'protocol': 'docs/nmi_postconfirmatory_robustness_protocol_v1.md',
        'stimulus_set': 'frozen ZuCo 2.0 Task 1 normal-reading texts',
        'n_items': len(texts),
        'lambda_0_adapter': str(Path(TEXT_ONLY_ADAPTER).resolve()),
        'lambda_0p10_adapter': str(Path(adapter_010).resolve()),
        'metrics': {
            'corresponding_item_cosine_similarity_mean': float(np.mean(item_cos)),
            'corresponding_item_cosine_similarity_median': float(np.median(item_cos)),
            'pairwise_cosine_distance_pearson': p,
            'pairwise_cosine_distance_spearman': s,
            'linear_centered_cka': cka,
            'knn_k': K,
            'mean_knn_jaccard_overlap': knn_mean,
        },
        'guardrail': 'No neural outcome is used and no high-change item categories are inspected or selected.'
    }
    (out / 'summary.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    with (out / 'item_metrics.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['item_index', 'corresponding_cosine_similarity', 'knn_jaccard_overlap'])
        w.writeheader()
        for i, (c, j) in enumerate(zip(item_cos, knn_items)):
            w.writerow({'item_index': i, 'corresponding_cosine_similarity': float(c), 'knn_jaccard_overlap': float(j)})
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
