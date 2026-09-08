#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from scripts.analysis.nmi_remaining_regional_core_v1 import FUNCTIONAL_FRONTAL, FUNCTIONAL_TEMPORAL, STORIES, SUBJECTS, read_csv

MAIN_REGIONAL = Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest")
PREFLIGHT_DIR = Path("outputs/smn4lang_regional_atlas_preflight_v1/latest")
BOOTSTRAP_SEED = 20260936
N_BOOT = 10_000
N_SPATIAL_SURROGATES = 10_000
DK_LANGUAGE = (
    "parsopercularis", "parstriangularis", "superiortemporal",
    "middletemporal", "inferiorparietal", "supramarginal",
)


def left_dk_design(region_summary_rows: list[dict]) -> tuple[list[str], np.ndarray, np.ndarray]:
    rows = [r for r in region_summary_rows if r["family"] == "dk68" and r["hemisphere"] == "L"]
    rows.sort(key=lambda r: r["region_name"])
    if len(rows) != 34:
        raise RuntimeError(f"expected 34 left DK parcels, got {len(rows)}")
    names = [r["region_name"] for r in rows]
    rel = np.asarray([float(r["model_blind_reliability_mean"]) for r in rows], float)
    if rel.std() == 0:
        raise RuntimeError("left-DK reliability has zero variance")
    rel_z = (rel - rel.mean()) / rel.std()
    lang = np.asarray([1.0 if n in set(DK_LANGUAGE) else 0.0 for n in names], float)
    X = np.column_stack([np.ones(34), rel_z, lang])
    return names, rel, X


def story_robustness() -> tuple[dict, list[dict]]:
    rows = read_csv(MAIN_REGIONAL / "story_results.csv")
    region_rows = read_csv(MAIN_REGIONAL / "region_summary.csv")
    subjects = list(SUBJECTS)
    stories = list(STORIES)
    left_names, _rel, X = left_dk_design(region_rows)
    xlang = np.linalg.pinv(X)[2]

    keys = [("dk68", "L", n) for n in left_names]
    keys += [("language", "L", n) for n in FUNCTIONAL_FRONTAL + FUNCTIONAL_TEMPORAL]
    key_index = {k: i for i, k in enumerate(keys)}
    s_index = {s: i for i, s in enumerate(subjects)}
    t_index = {int(t): i for i, t in enumerate(stories)}
    z0 = np.full((len(subjects), len(stories), len(keys)), np.nan, float)
    z1 = np.full_like(z0, np.nan)
    for r in rows:
        k = (r["family"], r["hemisphere"], r["region_name"])
        if k not in key_index:
            continue
        si = s_index[r["subject"]]
        ti = t_index[int(r["story"])]
        ri = key_index[k]
        a0 = np.clip(float(r["lambda_0_residual_rsa"]), -0.999999, 0.999999)
        a1 = np.clip(float(r["lambda_0p10_residual_rsa"]), -0.999999, 0.999999)
        z0[si, ti, ri] = np.arctanh(a0)
        z1[si, ti, ri] = np.arctanh(a1)
    if not np.isfinite(z0).all() or not np.isfinite(z1).all():
        raise RuntimeError("incomplete story-level matrix for frozen regions")

    dk_idx = np.asarray([key_index[("dk68", "L", n)] for n in left_names], int)
    front_idx = np.asarray([key_index[("language", "L", n)] for n in FUNCTIONAL_FRONTAL], int)
    temp_idx = np.asarray([key_index[("language", "L", n)] for n in FUNCTIONAL_TEMPORAL], int)

    def effects(story_idx: np.ndarray, participant_idx: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        if participant_idx is None:
            participant_idx = np.arange(len(subjects), dtype=int)
        a0 = np.tanh(z0[participant_idx][:, story_idx, :].mean(axis=1))
        a1 = np.tanh(z1[participant_idx][:, story_idx, :].mean(axis=1))
        d = a1 - a0
        beta = d[:, dk_idx] @ xlang
        tf = d[:, temp_idx].mean(axis=1) - d[:, front_idx].mean(axis=1)
        return beta, tf

    all_idx = np.arange(len(stories), dtype=int)
    beta_part, tf_part = effects(all_idx)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    boot_beta = np.empty(N_BOOT, float)
    boot_tf = np.empty(N_BOOT, float)
    for b in range(N_BOOT):
        pidx = rng.integers(0, len(subjects), size=len(subjects))
        tidx = rng.integers(0, len(stories), size=len(stories))
        bb, tt = effects(tidx, pidx)
        boot_beta[b] = float(bb.mean())
        boot_tf[b] = float(tt.mean())

    loo_rows = []
    for ti, story in enumerate(stories):
        bb, tt = effects(np.delete(all_idx, ti))
        loo_rows.append({
            "story_omitted": story,
            "reliability_adjusted_language_mean": float(bb.mean()),
            "temporal_minus_frontal_mean": float(tt.mean()),
        })

    return {
        "reliability_adjusted_language": {
            "participant_mean": float(beta_part.mean()),
            "n_positive_participants": int(np.sum(beta_part > 0)),
            "twofactor_bootstrap_ci_low": float(np.percentile(boot_beta, 2.5)),
            "twofactor_bootstrap_ci_high": float(np.percentile(boot_beta, 97.5)),
            "twofactor_bootstrap_fraction_gt_0": float(np.mean(boot_beta > 0)),
            "leave_one_story_out_min": float(min(r["reliability_adjusted_language_mean"] for r in loo_rows)),
            "leave_one_story_out_max": float(max(r["reliability_adjusted_language_mean"] for r in loo_rows)),
            "leave_one_story_out_positive": int(sum(r["reliability_adjusted_language_mean"] > 0 for r in loo_rows)),
            "leave_one_story_out_total": len(loo_rows),
        },
        "temporal_minus_frontal": {
            "participant_mean": float(tf_part.mean()),
            "n_positive_participants": int(np.sum(tf_part > 0)),
            "twofactor_bootstrap_ci_low": float(np.percentile(boot_tf, 2.5)),
            "twofactor_bootstrap_ci_high": float(np.percentile(boot_tf, 97.5)),
            "twofactor_bootstrap_fraction_gt_0": float(np.mean(boot_tf > 0)),
            "leave_one_story_out_min": float(min(r["temporal_minus_frontal_mean"] for r in loo_rows)),
            "leave_one_story_out_max": float(max(r["temporal_minus_frontal_mean"] for r in loo_rows)),
            "leave_one_story_out_positive": int(sum(r["temporal_minus_frontal_mean"] > 0 for r in loo_rows)),
            "leave_one_story_out_total": len(loo_rows),
        },
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }, loo_rows


def fit_exponential_range(dist: np.ndarray, residual: np.ndarray) -> tuple[float, list[dict]]:
    iu = np.triu_indices(len(residual), 1)
    d = dist[iu]
    g = 0.5 * (residual[iu[0]] - residual[iu[1]]) ** 2
    order = np.argsort(d)
    d, g = d[order], g[order]
    chunks = np.array_split(np.arange(len(d)), 6)
    bd = np.asarray([d[c].mean() for c in chunks], float)
    bg = np.asarray([g[c].mean() for c in chunks], float)
    dpos = d[d > 0]
    candidates = np.geomspace(max(float(dpos.min()), 1.0), max(float(d.max()) * 2.0, 2.0), 64)
    best = None
    for r in candidates:
        a = 1.0 - np.exp(-bd / r)
        sill = float(np.dot(a, bg) / max(np.dot(a, a), 1e-15))
        pred = sill * a
        sse = float(np.sum((bg - pred) ** 2))
        if best is None or sse < best[0]:
            best = (sse, float(r), pred)
    if best is None:
        raise RuntimeError("failed to fit spatial range")
    bins = [{
        "distance_mm": float(bd[i]),
        "empirical_semivariance": float(bg[i]),
        "fitted_semivariance": float(best[2][i]),
    } for i in range(len(bd))]
    return float(best[1]), bins


def spatial_surrogate_test() -> tuple[dict, list[float]]:
    region_rows = read_csv(MAIN_REGIONAL / "region_summary.csv")
    left_names, _rel, X = left_dk_design(region_rows)
    y_by = {r["region_name"]: float(r["delta_mean"]) for r in region_rows if r["family"] == "dk68" and r["hemisphere"] == "L"}
    y = np.asarray([y_by[n] for n in left_names], float)
    baseline = X[:, :2]
    fitted = baseline @ np.linalg.lstsq(baseline, y, rcond=None)[0]
    residual = y - fitted
    full_pinv = np.linalg.pinv(X)
    observed_beta = float(full_pinv[2] @ y)

    with (PREFLIGHT_DIR / "dk68_parcels.csv").open("r", encoding="utf-8", newline="") as f:
        cent_rows = list(csv.DictReader(f))
    cent_by = {r["parcel_name"]: r for r in cent_rows if r["hemisphere"] == "L"}
    xyz = np.asarray([[
        float(cent_by[n]["resampled_centroid_x_mm"]),
        float(cent_by[n]["resampled_centroid_y_mm"]),
        float(cent_by[n]["resampled_centroid_z_mm"]),
    ] for n in left_names], float)
    dist = np.linalg.norm(xyz[:, None, :] - xyz[None, :, :], axis=2)
    range_mm, bins = fit_exponential_range(dist, residual)
    cov = np.exp(-dist / range_mm) + np.eye(len(y)) * 1e-8
    L = np.linalg.cholesky(cov)
    sorted_resid = np.sort(residual)
    rng = np.random.default_rng(20261037)
    null_beta = np.empty(N_SPATIAL_SURROGATES, float)
    for i in range(N_SPATIAL_SURROGATES):
        field = L @ rng.standard_normal(len(y))
        ranks = np.argsort(np.argsort(field))
        ys = fitted + sorted_resid[ranks]
        null_beta[i] = float(full_pinv[2] @ ys)
    p_two = float((1 + np.sum(np.abs(null_beta) >= abs(observed_beta) - 1e-15)) / (N_SPATIAL_SURROGATES + 1))
    return {
        "method": "centroid-distance variogram-matched spatial surrogate null",
        "n_left_dk_parcels": 34,
        "n_surrogates": N_SPATIAL_SURROGATES,
        "seed": 20261037,
        "observed_reliability_adjusted_language_beta": observed_beta,
        "fitted_exponential_range_mm": range_mm,
        "two_sided_spatial_surrogate_p": p_two,
        "null_beta_mean": float(null_beta.mean()),
        "null_beta_sd": float(null_beta.std(ddof=1)),
        "variogram_bins": bins,
        "note": "not a surface-sphere spin test",
    }, null_beta.tolist()
