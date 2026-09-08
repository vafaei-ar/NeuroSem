#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.stats import chi2, norm

from scripts.analysis.nmi_remaining_regional_core_v1 import FUNCTIONAL_LANGUAGE, LEFT_SENSORIMOTOR, LEFT_VISUAL

MAIN_REGIONAL = Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest")
REMAINING = Path("outputs/nmi_remaining_regional_ideas_v1/latest")


def system_for_region(family: str, name: str) -> str:
    if family == "language" and name in FUNCTIONAL_LANGUAGE:
        return "language"
    if family == "dk68" and name in LEFT_SENSORIMOTOR:
        return "sensorimotor"
    if family == "dk68" and name in LEFT_VISUAL:
        return "visual"
    raise KeyError((family, name))


def synthesis_frame():
    import pandas as pd
    regional = pd.read_csv(REMAINING / "regional_participant_results.csv")
    rel = pd.read_csv(MAIN_REGIONAL / "region_summary.csv")[["region_key", "model_blind_reliability_mean"]]
    regional = regional.merge(rel, on="region_key", how="left", validate="many_to_one")
    if regional["model_blind_reliability_mean"].isna().any():
        raise RuntimeError("missing reliability in synthesis frame")
    regional["system"] = [system_for_region(f, n) for f, n in zip(regional["family"], regional["region_name"])]
    regional["reliability_z"] = (regional["model_blind_reliability_mean"] - regional["model_blind_reliability_mean"].mean()) / regional["model_blind_reliability_mean"].std(ddof=0)
    return regional


def two_way_cluster_fit(df, condition_col: str) -> tuple[dict, list[dict]]:
    import pandas as pd
    import statsmodels.formula.api as smf
    from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

    d = df.copy()
    d[condition_col] = d[condition_col].astype(str)
    formula = f"delta ~ reliability_z + C(subject) + C({condition_col}) * C(system)"
    fit = smf.ols(formula, data=d).fit()
    g_subject = pd.factorize(d["subject"])[0]
    g_region = pd.factorize(d["region_key"])[0]
    cov, _c0, _c1 = cov_cluster_2groups(fit, g_subject, g_region, use_correction=True)
    names = list(fit.params.index)
    beta = np.asarray(fit.params, float)
    idx = [i for i, n in enumerate(names) if f"C({condition_col})" in n and "C(system)" in n and ":" in n]
    if not idx:
        raise RuntimeError(f"no interaction terms found for {condition_col}")
    b = beta[idx]
    V = np.asarray(cov)[np.ix_(idx, idx)]
    wald = float(b @ np.linalg.pinv(V) @ b)
    p_wald = float(chi2.sf(wald, len(idx)))
    reduced = smf.ols(f"delta ~ reliability_z + C(subject) + C({condition_col}) + C(system)", data=d).fit()
    delta_r2 = float(fit.rsquared - reduced.rsquared)
    se = np.sqrt(np.clip(np.diag(cov), 0, np.inf))
    coef_rows = []
    for i, name in enumerate(names):
        z = float(beta[i] / se[i]) if se[i] > 0 else float("nan")
        coef_rows.append({
            "model": condition_col, "term": name, "estimate": float(beta[i]),
            "two_way_cluster_se": float(se[i]), "z": z,
            "two_sided_normal_p": float(2 * norm.sf(abs(z))) if np.isfinite(z) else float("nan"),
        })
    return {
        "formula": formula, "n_rows": int(len(d)),
        "n_subject_clusters": int(d["subject"].nunique()),
        "n_region_clusters": int(d["region_key"].nunique()),
        "interaction_df": len(idx), "interaction_wald_chi2": wald,
        "interaction_wald_p": p_wald,
        "incremental_ols_r2_interaction": delta_r2,
        "inference": "OLS fixed effects with Cameron-Gelbach-Miller two-way clustered covariance by participant and region",
    }, coef_rows


def hierarchical_synthesis() -> tuple[dict, list[dict]]:
    frame = synthesis_frame()
    dose = frame[frame["condition_family"] == "e5_dose"].copy()
    if dose["dose"].nunique() != 5:
        raise RuntimeError("expected five nonzero dose conditions")
    dose["dose_label"] = dose["dose"].map(lambda x: f"lambda_{float(x):g}")
    dose_summary, dose_coefs = two_way_cluster_fit(dose, "dose_label")

    model = frame[frame["condition_family"] == "model_family"].copy()
    grouped = model.groupby(
        ["model_key", "subject", "region_key", "family", "hemisphere", "region_name", "system", "reliability_z"],
        as_index=False,
    )["delta"].mean()
    if grouped["model_key"].nunique() != 6:
        raise RuntimeError("expected six model backbones")
    model_summary, model_coefs = two_way_cluster_fit(grouped, "model_key")

    raw = [dose_summary["interaction_wald_p"], model_summary["interaction_wald_p"]]
    order = np.argsort(raw)
    adj = [None, None]
    first = min(1.0, 2.0 * raw[int(order[0])])
    second = max(first, raw[int(order[1])])
    adj[int(order[0])] = float(first)
    adj[int(order[1])] = float(min(1.0, second))
    dose_summary["two_model_holm_p"] = adj[0]
    model_summary["two_model_holm_p"] = adj[1]
    return {
        "dose_by_system": dose_summary,
        "backbone_by_system": model_summary,
        "omnibus_multiplicity": "Holm correction across the two prespecified synthesis interaction tests",
        "model_seed_handling": "three prespecified seeds averaged within participant x region x backbone before synthesis regression",
        "status": "secondary synthesis; individual interaction coefficients are not promoted as new confirmatory discoveries",
    }, dose_coefs + model_coefs
