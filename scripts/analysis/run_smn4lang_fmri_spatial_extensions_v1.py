#!/usr/bin/env python3
"""Frozen post-confirmatory SMN4Lang fMRI spatial extension suite v1.

Consumes only completed participant-level regional transfer outputs. It implements
analyses whose definitions do not depend on results produced by the new dose/model
extension runs: full-cortex reliability adjustment, hemispheric specificity,
association-cortex controls, and within-language temporal-vs-frontal organization.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROTOCOL = "docs/28_NMI_FMRI_SPATIAL_EXTENSIONS_V1.md"
INPUT_DIR = Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest")
OUTPUT_DIR = Path("outputs/smn4lang_fmri_spatial_extensions_v1/latest")
BOOTSTRAP_SEED = 20260906
N_BOOT = 10_000

DK_LANGUAGE = (
    "parsopercularis",
    "parstriangularis",
    "superiortemporal",
    "middletemporal",
    "inferiorparietal",
    "supramarginal",
)
OTHER_ASSOCIATION = (
    "superiorfrontal",
    "rostralmiddlefrontal",
    "caudalmiddlefrontal",
    "superiorparietal",
    "precuneus",
    "posteriorcingulate",
)
PRIMARY_SENSORIMOTOR = ("precentral", "postcentral", "paracentral")
PRIMARY_VISUAL = ("pericalcarine", "cuneus", "lingual", "lateraloccipital")
PRIMARY_CORTEX = PRIMARY_SENSORIMOTOR + PRIMARY_VISUAL
FUNCTIONAL_FRONTAL = ("IFG", "IFGorb", "MFG")
FUNCTIONAL_TEMPORAL = ("AntTemp", "PostTemp")
FUNCTIONAL_PARIETAL = ("AngG",)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exact_two_sided_signflip_p(values: np.ndarray) -> float:
    x = np.asarray(values, dtype=float)
    obs = abs(float(np.mean(x)))
    total = 1 << len(x)
    ge = 0
    for bits in range(total):
        signs = np.ones(len(x), dtype=float)
        for j in range(len(x)):
            if (bits >> j) & 1:
                signs[j] = -1.0
        if abs(float(np.mean(x * signs))) >= obs - 1e-15:
            ge += 1
    return ge / total


def exact_maxstat_p(matrix: np.ndarray) -> np.ndarray:
    x = np.asarray(matrix, dtype=float)
    obs = np.abs(np.mean(x, axis=0))
    total = 1 << x.shape[0]
    null_max = np.empty(total, dtype=float)
    for bits in range(total):
        signs = np.ones(x.shape[0], dtype=float)
        for j in range(x.shape[0]):
            if (bits >> j) & 1:
                signs[j] = -1.0
        null_max[bits] = float(np.max(np.abs(np.mean(x * signs[:, None], axis=0))))
    return np.asarray([np.mean(null_max >= v - 1e-15) for v in obs], dtype=float)


def bootstrap_ci(values: np.ndarray, salt: int = 0) -> tuple[float, float]:
    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED + salt)
    idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(values: np.ndarray, salt: int = 0) -> dict:
    x = np.asarray(values, dtype=float)
    lo, hi = bootstrap_ci(x, salt=salt)
    return {
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "n_positive": int(np.sum(x > 0)),
        "n_total": int(len(x)),
        "bootstrap_ci_low": lo,
        "bootstrap_ci_high": hi,
        "exact_two_sided_signflip_p": exact_two_sided_signflip_p(x),
    }


def main() -> int:
    participant_path = INPUT_DIR / "participant_results.csv"
    region_path = INPUT_DIR / "region_summary.csv"
    if not participant_path.exists() or not region_path.exists():
        raise FileNotFoundError("completed frozen regional transfer outputs are required")

    participant_rows = read_csv(participant_path)
    region_rows = read_csv(region_path)
    subjects = sorted({r["subject"] for r in participant_rows})
    if len(subjects) != 12:
        raise RuntimeError(f"expected 12 participants, found {len(subjects)}")

    delta = {
        (r["family"], r["hemisphere"], r["region_name"], r["subject"]): float(r["delta_0p10_minus_0"])
        for r in participant_rows
    }
    reliability = {
        (r["family"], r["hemisphere"], r["region_name"]): float(r["model_blind_reliability_mean"])
        for r in region_rows
    }

    def group_vector(family: str, hemi: str, names: tuple[str, ...]) -> np.ndarray:
        out = []
        for sub in subjects:
            vals = []
            for name in names:
                key = (family, hemi, name, sub)
                if key not in delta:
                    raise RuntimeError(f"missing participant delta for {key}")
                vals.append(delta[key])
            out.append(float(np.mean(vals)))
        return np.asarray(out, dtype=float)

    left_lang = group_vector("dk68", "L", DK_LANGUAGE)
    right_lang = group_vector("dk68", "R", DK_LANGUAGE)
    other_assoc = group_vector("dk68", "L", OTHER_ASSOCIATION)
    primary = group_vector("dk68", "L", PRIMARY_CORTEX)
    functional_frontal = group_vector("language", "L", FUNCTIONAL_FRONTAL)
    functional_temporal = group_vector("language", "L", FUNCTIONAL_TEMPORAL)
    functional_parietal = group_vector("language", "L", FUNCTIONAL_PARIETAL)

    hemisphere_contrast = left_lang - right_lang
    language_minus_other = left_lang - other_assoc
    other_minus_primary = other_assoc - primary
    temporal_minus_frontal = functional_temporal - functional_frontal

    left_dk_names = sorted({
        r["region_name"] for r in participant_rows
        if r["family"] == "dk68" and r["hemisphere"] == "L"
    })
    if len(left_dk_names) != 34:
        raise RuntimeError(f"expected 34 left DK parcels, found {len(left_dk_names)}")
    lang_set = set(DK_LANGUAGE)
    rel = np.asarray([reliability[("dk68", "L", n)] for n in left_dk_names], dtype=float)
    if float(np.std(rel)) == 0.0:
        raise RuntimeError("left-DK reliability has zero variance")
    rel_z = (rel - np.mean(rel)) / np.std(rel)
    language_member = np.asarray([1.0 if n in lang_set else 0.0 for n in left_dk_names], dtype=float)
    X = np.column_stack([np.ones(len(left_dk_names)), rel_z, language_member])
    full_cortex_beta = []
    participant_reliability_corr = []
    for sub in subjects:
        y = np.asarray([delta[("dk68", "L", n, sub)] for n in left_dk_names], dtype=float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        full_cortex_beta.append(float(beta[2]))
        participant_reliability_corr.append(float(np.corrcoef(rel, y)[0, 1]))
    full_cortex_beta = np.asarray(full_cortex_beta, dtype=float)
    participant_reliability_corr = np.asarray(participant_reliability_corr, dtype=float)

    focal_names = [
        "full_cortex_reliability_adjusted_language_coefficient",
        "left_minus_right_dk_language",
        "dk_language_minus_other_association",
        "other_association_minus_primary_cortex",
        "functional_temporal_minus_frontal_language",
    ]
    focal_vectors = [
        full_cortex_beta,
        hemisphere_contrast,
        language_minus_other,
        other_minus_primary,
        temporal_minus_frontal,
    ]
    focal_matrix = np.column_stack(focal_vectors)
    fwer = exact_maxstat_p(focal_matrix)

    focal_summary = {}
    for i, (name, values) in enumerate(zip(focal_names, focal_vectors)):
        focal_summary[name] = {**summarize(values, salt=i), "familywise_maxstat_p": float(fwer[i])}

    participant_out = []
    for i, sub in enumerate(subjects):
        participant_out.append({
            "subject": sub,
            "left_dk_language_mean_delta": left_lang[i],
            "right_dk_language_mean_delta": right_lang[i],
            "left_other_association_mean_delta": other_assoc[i],
            "left_primary_cortex_mean_delta": primary[i],
            "functional_frontal_mean_delta": functional_frontal[i],
            "functional_temporal_mean_delta": functional_temporal[i],
            "functional_parietal_mean_delta": functional_parietal[i],
            "full_cortex_reliability_adjusted_language_coefficient": full_cortex_beta[i],
            "left_minus_right_dk_language": hemisphere_contrast[i],
            "dk_language_minus_other_association": language_minus_other[i],
            "other_association_minus_primary_cortex": other_minus_primary[i],
            "functional_temporal_minus_frontal_language": temporal_minus_frontal[i],
            "left_dk_delta_vs_reliability_pearson_r": participant_reliability_corr[i],
        })

    region_rows_out = []
    region_mean_delta = {}
    for name in left_dk_names:
        vals = np.asarray([delta[("dk68", "L", name, sub)] for sub in subjects], dtype=float)
        region_mean_delta[name] = float(np.mean(vals))
        if name in DK_LANGUAGE:
            group = "dk_language_associated"
        elif name in OTHER_ASSOCIATION:
            group = "other_association"
        elif name in PRIMARY_CORTEX:
            group = "primary_cortex"
        else:
            group = "other_left_dk"
        region_rows_out.append({
            "hemisphere": "L",
            "region_name": name,
            "analysis_group": group,
            "mean_delta": float(np.mean(vals)),
            "model_blind_reliability_mean": reliability[("dk68", "L", name)],
        })

    region_mean_y = np.asarray([region_mean_delta[n] for n in left_dk_names], dtype=float)
    region_reliability_r = float(np.corrcoef(rel, region_mean_y)[0, 1])

    summary = {
        "schema_version": 1,
        "analysis": "SMN4Lang fMRI frozen spatial extension suite",
        "protocol": PROTOCOL,
        "status": "ok",
        "post_confirmatory": True,
        "input_sha256": {
            str(participant_path): sha256(participant_path),
            str(region_path): sha256(region_path),
        },
        "n_subjects": len(subjects),
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "multiplicity_family": focal_names,
        "frozen_groups": {
            "dk_language_associated": list(DK_LANGUAGE),
            "other_association": list(OTHER_ASSOCIATION),
            "primary_sensorimotor": list(PRIMARY_SENSORIMOTOR),
            "primary_visual": list(PRIMARY_VISUAL),
            "functional_frontal": list(FUNCTIONAL_FRONTAL),
            "functional_temporal": list(FUNCTIONAL_TEMPORAL),
            "functional_parietal_descriptive": list(FUNCTIONAL_PARIETAL),
        },
        "system_mean_deltas": {
            "left_dk_language": float(np.mean(left_lang)),
            "right_dk_language": float(np.mean(right_lang)),
            "left_other_association": float(np.mean(other_assoc)),
            "left_primary_cortex": float(np.mean(primary)),
            "functional_frontal": float(np.mean(functional_frontal)),
            "functional_temporal": float(np.mean(functional_temporal)),
            "functional_parietal": float(np.mean(functional_parietal)),
        },
        "focal_tests": focal_summary,
        "reliability_descriptives": {
            "region_mean_delta_vs_reliability_pearson_r": region_reliability_r,
            "participant_correlation_mean": float(np.mean(participant_reliability_corr)),
        },
        "guardrails": {
            "definitions_frozen_before_execution": True,
            "no_new_model_training": True,
            "no_new_fmri_preprocessing": True,
            "no_region_selection_from_suite_outcomes": True,
            "participant_is_inferential_unit": True,
            "five_focal_tests_share_one_exact_maxstat_family": True,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_DIR / "participant_spatial_extensions.csv", participant_out)
    write_csv(OUTPUT_DIR / "left_dk_region_summary.csv", region_rows_out)
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.2), constrained_layout=True)
    ax = axes[0, 0]
    group_data = [left_lang, other_assoc, primary]
    group_labels = ["Language", "Other association", "Primary"]
    for i, vals in enumerate(group_data):
        ax.scatter(np.full(len(vals), i), vals * 1e3, s=14, alpha=0.75)
    ax.plot(np.arange(3), [np.mean(v) * 1e3 for v in group_data], marker="D", linewidth=1.2)
    ax.set_xticks(np.arange(3), group_labels)
    ax.set_ylabel("Delta RSA x 10^-3")
    ax.set_title("Association hierarchy")

    ax = axes[0, 1]
    for i, sub in enumerate(subjects):
        ax.plot([0, 1], [left_lang[i] * 1e3, right_lang[i] * 1e3], marker="o", linewidth=0.7, alpha=0.65)
    ax.set_xticks([0, 1], ["Left", "Right"])
    ax.set_ylabel("DK language mean delta x 10^-3")
    ax.set_title("Hemispheric specificity")

    ax = axes[1, 0]
    is_lang = np.asarray([n in lang_set for n in left_dk_names])
    ax.scatter(rel[~is_lang], region_mean_y[~is_lang] * 1e3, s=22, label="Other DK")
    ax.scatter(rel[is_lang], region_mean_y[is_lang] * 1e3, s=30, marker="D", label="Language-associated")
    ax.set_xlabel("Model-blind reliability")
    ax.set_ylabel("Mean delta RSA x 10^-3")
    ax.set_title("Whole-cortex reliability relationship")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1, 1]
    for i, sub in enumerate(subjects):
        ax.plot([0, 1], [functional_frontal[i] * 1e3, functional_temporal[i] * 1e3], marker="o", linewidth=0.7, alpha=0.65)
    ax.set_xticks([0, 1], ["Frontal", "Temporal"])
    ax.set_ylabel("Functional language delta x 10^-3")
    ax.set_title("Within-language organization")

    fig.suptitle("SMN4Lang fMRI spatial extension suite", fontsize=11)
    fig.savefig(OUTPUT_DIR / "figure_spatial_extensions.png", dpi=600)
    fig.savefig(OUTPUT_DIR / "figure_spatial_extensions.pdf")
    plt.close(fig)

    report = [
        "SMN4Lang fMRI spatial extension suite v1",
        "Status: ok",
        "Post-confirmatory: yes",
        f"Participants: {len(subjects)}",
        "",
        f"Left DK language mean delta: {np.mean(left_lang):.9g}",
        f"Right DK language mean delta: {np.mean(right_lang):.9g}",
        f"Other association mean delta: {np.mean(other_assoc):.9g}",
        f"Primary cortex mean delta: {np.mean(primary):.9g}",
        f"Functional frontal mean delta: {np.mean(functional_frontal):.9g}",
        f"Functional temporal mean delta: {np.mean(functional_temporal):.9g}",
        "",
    ]
    for name in focal_names:
        s = focal_summary[name]
        report.append(
            f"{name}: mean={s['mean']:.9g}; positive={s['n_positive']}/{s['n_total']}; "
            f"95% CI=[{s['bootstrap_ci_low']:.9g}, {s['bootstrap_ci_high']:.9g}]; "
            f"P={s['exact_two_sided_signflip_p']:.9g}; FWER P={s['familywise_maxstat_p']:.9g}"
        )
    report.extend([
        "",
        f"Regional mean delta vs reliability Pearson r: {region_reliability_r:.9g}",
    ])
    (OUTPUT_DIR / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
