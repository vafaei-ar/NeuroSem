#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np

from scripts.analysis.nmi_remaining_regional_core_v1 import (
    CACHE, FUNCTIONAL_FRONTAL, FUNCTIONAL_LANGUAGE, FUNCTIONAL_TEMPORAL,
    POOLED_CONTROL, SEEDS, STORIES, SUBJECTS, atomic_progress,
    build_selected_neural_cache, e5_model_residual,
)
from scripts.analysis.run_smn4lang_fmri_reliability import TR, canonical_hrf, fisher_mean
from scripts.tuning.evaluate_smn4lang_fmri_e5_transfer_v1 import safe_spearman
from scripts.tuning.evaluate_tmnred_e5_transfer_v1 import load_adapter

REVIEWER_ROOT = Path("outputs/nmi_multiseed_e5_v1")
BOOTSTRAP_SEED = 20260936
N_BOOT = 10_000


def latest_adapter(root: Path) -> Path:
    candidates = [p / "adapter" for p in root.iterdir() if p.is_dir() and (p / "adapter").is_dir()] if root.exists() else []
    if not candidates:
        raise FileNotFoundError(f"no adapter under {root}")
    return sorted(candidates)[-1]


def exact_two_sided_signflip_p(values: np.ndarray) -> float:
    x = np.asarray(values, float)
    obs = abs(float(x.mean()))
    ge = 0
    total = 1 << len(x)
    for bits in range(total):
        signs = np.ones(len(x), float)
        for j in range(len(x)):
            if (bits >> j) & 1:
                signs[j] = -1.0
        if abs(float(np.mean(x * signs))) >= obs - 1e-15:
            ge += 1
    return ge / total


def exact_maxstat_p(matrix: np.ndarray) -> np.ndarray:
    x = np.asarray(matrix, float)
    obs = np.abs(x.mean(axis=0))
    null = np.empty(1 << x.shape[0], float)
    for bits in range(1 << x.shape[0]):
        signs = np.ones(x.shape[0], float)
        for j in range(x.shape[0]):
            if (bits >> j) & 1:
                signs[j] = -1.0
        null[bits] = float(np.max(np.abs(np.mean(x * signs[:, None], axis=0))))
    return np.asarray([np.mean(null >= v - 1e-15) for v in obs], float)


def bootstrap_ci(values: np.ndarray, salt: int) -> tuple[float, float]:
    x = np.asarray(values, float)
    rng = np.random.default_rng(BOOTSTRAP_SEED + salt)
    idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def evaluate_adapter(adapter: Path, meta: list[dict], contexts: dict[int, dict], device: str) -> np.ndarray:
    import torch
    hrf = canonical_hrf(TR)
    vals = np.empty((len(SUBJECTS), len(meta), len(STORIES)), float)
    tok, model = load_adapter(adapter, device)
    for ti, story in enumerate(STORIES):
        mr = e5_model_residual(model, tok, contexts[story], device, hrf)
        with np.load(CACHE / f"story_{story:02d}.npz") as cache:
            for si, _sub in enumerate(SUBJECTS):
                for ri in range(len(meta)):
                    vals[si, ri, ti] = safe_spearman(cache[f"s{si:02d}_r{ri:02d}"], mr)
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    out = np.empty((len(SUBJECTS), len(meta)), float)
    for si in range(len(SUBJECTS)):
        for ri in range(len(meta)):
            out[si, ri] = fisher_mean(vals[si, ri, :])
    return out


def shuffled_regional_control() -> tuple[dict, list[dict], list[dict]]:
    meta, contexts = build_selected_neural_cache(Path("data/raw/smn4lang").resolve())
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("GPU required for regional shuffled-target control")
    name_to_idx = {r["region_name"]: i for i, r in enumerate(meta)}
    lang_idx = np.asarray([name_to_idx[n] for n in FUNCTIONAL_LANGUAGE], int)
    control_idx = np.asarray([name_to_idx[n] for n in POOLED_CONTROL], int)
    front_idx = np.asarray([name_to_idx[n] for n in FUNCTIONAL_FRONTAL], int)
    temp_idx = np.asarray([name_to_idx[n] for n in FUNCTIONAL_TEMPORAL], int)

    participant_rows, seed_rows, vectors = [], [], []
    completed_arms = 0
    for seed in SEEDS:
        root = REVIEWER_ROOT / f"seed_{seed}"
        adapters = {
            "text": latest_adapter(root / "text_only"),
            "genuine": latest_adapter(root / "neural"),
            "shuffled": latest_adapter(root / "shuffled_neural"),
        }
        arm = {}
        for name, path in adapters.items():
            arm[name] = evaluate_adapter(path, meta, contexts, "cuda")
            completed_arms += 1
            atomic_progress(
                2 + completed_arms,
                12,
                "regional-shuffled-control",
                f"completed seed {seed} arm {name}",
            )
        gen_delta = arm["genuine"] - arm["text"]
        shuf_delta = arm["shuffled"] - arm["text"]
        gen_spec = gen_delta[:, lang_idx].mean(axis=1) - gen_delta[:, control_idx].mean(axis=1)
        shuf_spec = shuf_delta[:, lang_idx].mean(axis=1) - shuf_delta[:, control_idx].mean(axis=1)
        diff = gen_spec - shuf_spec
        tf_gen = gen_delta[:, temp_idx].mean(axis=1) - gen_delta[:, front_idx].mean(axis=1)
        tf_shuf = shuf_delta[:, temp_idx].mean(axis=1) - shuf_delta[:, front_idx].mean(axis=1)
        vectors.append((gen_spec, shuf_spec, diff))
        seed_rows.append({
            "seed": seed,
            "genuine_specificity_mean": float(gen_spec.mean()),
            "shuffled_specificity_mean": float(shuf_spec.mean()),
            "genuine_minus_shuffled_specificity_mean": float(diff.mean()),
            "genuine_minus_shuffled_n_positive": int(np.sum(diff > 0)),
            "genuine_temporal_minus_frontal_mean": float(tf_gen.mean()),
            "shuffled_temporal_minus_frontal_mean": float(tf_shuf.mean()),
        })
        for si, sub in enumerate(SUBJECTS):
            participant_rows.append({
                "seed": seed,
                "subject": sub,
                "genuine_specificity": float(gen_spec[si]),
                "shuffled_specificity": float(shuf_spec[si]),
                "genuine_minus_shuffled_specificity": float(diff[si]),
                "genuine_temporal_minus_frontal": float(tf_gen[si]),
                "shuffled_temporal_minus_frontal": float(tf_shuf[si]),
            })

    avg_gen = np.mean(np.stack([x[0] for x in vectors]), axis=0)
    avg_shuf = np.mean(np.stack([x[1] for x in vectors]), axis=0)
    avg_diff = np.mean(np.stack([x[2] for x in vectors]), axis=0)
    fwer = exact_maxstat_p(np.column_stack([avg_diff, avg_shuf]))
    dlo, dhi = bootstrap_ci(avg_diff, 1)
    slo, shi = bootstrap_ci(avg_shuf, 2)
    return {
        "primary_genuine_minus_shuffled_language_specificity": {
            "mean": float(avg_diff.mean()), "n_positive": int(np.sum(avg_diff > 0)),
            "bootstrap_ci_low": dlo, "bootstrap_ci_high": dhi,
            "exact_two_sided_signflip_p": exact_two_sided_signflip_p(avg_diff),
            "two_test_familywise_maxstat_p": float(fwer[0]),
        },
        "secondary_shuffled_minus_text_language_specificity": {
            "mean": float(avg_shuf.mean()), "n_positive": int(np.sum(avg_shuf > 0)),
            "bootstrap_ci_low": slo, "bootstrap_ci_high": shi,
            "exact_two_sided_signflip_p": exact_two_sided_signflip_p(avg_shuf),
            "two_test_familywise_maxstat_p": float(fwer[1]),
        },
        "descriptive_genuine_specificity_mean": float(avg_gen.mean()),
        "seed_summary": seed_rows,
        "seeds": list(SEEDS),
    }, participant_rows, seed_rows
