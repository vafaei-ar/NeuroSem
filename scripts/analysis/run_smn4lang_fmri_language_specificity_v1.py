#!/usr/bin/env python3
"""Post-confirmatory SMN4Lang fMRI language-specificity analysis v1.

Consumes only completed regional transfer outputs and implements the frozen protocol
in docs/27_NMI_FMRI_LANGUAGE_SPECIFICITY_V1.md. No model fitting, neural preprocessing,
ROI search, dose selection, or target-side optimization is performed here.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROTOCOL = "docs/27_NMI_FMRI_LANGUAGE_SPECIFICITY_V1.md"
INPUT_DIR = Path("outputs/smn4lang_regional_fmri_e5_transfer_v1/latest")
OUTPUT_DIR = Path("outputs/smn4lang_fmri_language_specificity_v1/latest")
BOOTSTRAP_SEED = 20260905
N_BOOT = 10_000

FUNCTIONAL_LANGUAGE = ("IFG", "IFGorb", "MFG", "AntTemp", "PostTemp", "AngG")
LEFT_SENSORIMOTOR = ("precentral", "postcentral", "paracentral")
LEFT_VISUAL = ("pericalcarine", "cuneus", "lingual", "lateraloccipital")
DK_LANGUAGE = (
    "parsopercularis",
    "parstriangularis",
    "superiortemporal",
    "middletemporal",
    "inferiorparietal",
    "supramarginal",
)


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
    obs = abs(float(x.mean()))
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


def bootstrap_ci(values: np.ndarray) -> tuple[float, float]:
    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(values: np.ndarray) -> dict:
    x = np.asarray(values, dtype=float)
    lo, hi = bootstrap_ci(x)
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

    # Index participant deltas and regional model-blind reliability.
    delta: dict[tuple[str, str, str, str], float] = {}
    for r in participant_rows:
        key = (r["family"], r["hemisphere"], r["region_name"], r["subject"])
        delta[key] = float(r["delta_0p10_minus_0"])

    reliability: dict[tuple[str, str, str], float] = {}
    for r in region_rows:
        reliability[(r["family"], r["hemisphere"], r["region_name"])] = float(
            r["model_blind_reliability_mean"]
        )

    def group_vector(family: str, hemi: str, names: tuple[str, ...]) -> np.ndarray:
        out = []
        for sub in subjects:
            vals = []
            for name in names:
                k = (family, hemi, name, sub)
                if k not in delta:
                    raise RuntimeError(f"missing participant delta for {k}")
                vals.append(delta[k])
            out.append(float(np.mean(vals)))
        return np.asarray(out, dtype=float)

    functional = group_vector("language", "L", FUNCTIONAL_LANGUAGE)
    motor = group_vector("dk68", "L", LEFT_SENSORIMOTOR)
    visual = group_vector("dk68", "L", LEFT_VISUAL)
    dk_lang = group_vector("dk68", "L", DK_LANGUAGE)

    primary_motor = functional - motor
    primary_visual = functional - visual
    primary_matrix = np.column_stack([primary_motor, primary_visual])
    primary_fwer = exact_maxstat_p(primary_matrix)

    # Reliability-only one-to-one matching: six language parcels to six of seven fixed controls.
    controls = tuple(sorted(LEFT_SENSORIMOTOR + LEFT_VISUAL))
    lang_rels = [reliability[("language", "L", name)] for name in FUNCTIONAL_LANGUAGE]
    control_rels = {name: reliability[("dk68", "L", name)] for name in controls}
    best = None
    best_key = None
    for subset in itertools.combinations(controls, len(FUNCTIONAL_LANGUAGE)):
        for perm in itertools.permutations(subset):
            cost = float(sum(abs(a - control_rels[b]) for a, b in zip(lang_rels, perm)))
            key = (round(cost, 15), tuple(perm))
            if best_key is None or key < best_key:
                best_key = key
                best = perm
    if best is None:
        raise RuntimeError("reliability matching failed")
    matched_controls = tuple(best)
    matched_vec = group_vector("dk68", "L", matched_controls)
    matched_contrast = functional - matched_vec

    # Same-atlas anatomical replication.
    dk_vs_motor = dk_lang - motor
    dk_vs_visual = dk_lang - visual

    # Reliability-adjusted same-atlas contrast across the frozen 13 left-DK parcels.
    pooled_controls = LEFT_SENSORIMOTOR + LEFT_VISUAL
    all_names = DK_LANGUAGE + pooled_controls
    rel_x = np.asarray([reliability[("dk68", "L", name)] for name in all_names], dtype=float)
    X = np.column_stack([np.ones(len(rel_x)), rel_x])
    adjusted = []
    for sub in subjects:
        y = np.asarray([delta[("dk68", "L", name, sub)] for name in all_names], dtype=float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        adjusted.append(float(np.mean(resid[: len(DK_LANGUAGE)]) - np.mean(resid[len(DK_LANGUAGE) :])))
    adjusted = np.asarray(adjusted, dtype=float)

    contrast_vectors = {
        "functional_language_minus_left_sensorimotor": primary_motor,
        "functional_language_minus_left_visual": primary_visual,
        "functional_language_minus_reliability_matched_control": matched_contrast,
        "dk_language_minus_left_sensorimotor": dk_vs_motor,
        "dk_language_minus_left_visual": dk_vs_visual,
        "dk_language_minus_pooled_controls_reliability_adjusted": adjusted,
    }

    participant_out = []
    for i, sub in enumerate(subjects):
        participant_out.append({
            "subject": sub,
            "functional_language_mean_delta": functional[i],
            "left_sensorimotor_mean_delta": motor[i],
            "left_visual_mean_delta": visual[i],
            "dk_language_mean_delta": dk_lang[i],
            "reliability_matched_control_mean_delta": matched_vec[i],
            **{name: vals[i] for name, vals in contrast_vectors.items()},
        })

    region_group_rows = []
    for name in FUNCTIONAL_LANGUAGE:
        region_group_rows.append({
            "analysis_group": "functional_language",
            "family": "language",
            "hemisphere": "L",
            "region_name": name,
            "model_blind_reliability_mean": reliability[("language", "L", name)],
        })
    for group, names in [
        ("left_sensorimotor", LEFT_SENSORIMOTOR),
        ("left_visual", LEFT_VISUAL),
        ("dk_language_associated", DK_LANGUAGE),
    ]:
        for name in names:
            region_group_rows.append({
                "analysis_group": group,
                "family": "dk68",
                "hemisphere": "L",
                "region_name": name,
                "model_blind_reliability_mean": reliability[("dk68", "L", name)],
            })
    for lang, control in zip(FUNCTIONAL_LANGUAGE, matched_controls):
        region_group_rows.append({
            "analysis_group": "reliability_match_pair",
            "family": "language_to_dk68",
            "hemisphere": "L",
            "region_name": f"{lang} -> {control}",
            "model_blind_reliability_mean": (
                f"{reliability[(\"language\", \"L\", lang)]:.12g} -> "
                f"{reliability[(\"dk68\", \"L\", control)]:.12g}"
            ),
        })

    summary = {
        "schema_version": 1,
        "analysis": "SMN4Lang fMRI post-confirmatory language-specificity analysis",
        "protocol": PROTOCOL,
        "status": "ok",
        "input_sha256": {
            str(participant_path): sha256(participant_path),
            str(region_path): sha256(region_path),
        },
        "n_subjects": len(subjects),
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "frozen_groups": {
            "functional_language": list(FUNCTIONAL_LANGUAGE),
            "left_sensorimotor": list(LEFT_SENSORIMOTOR),
            "left_visual": list(LEFT_VISUAL),
            "dk_language_associated": list(DK_LANGUAGE),
        },
        "reliability_matching": {
            "candidate_controls": list(controls),
            "matched_controls_in_functional_language_order": list(matched_controls),
            "total_absolute_reliability_difference": float(best_key[0]),
            "used_transfer_outcomes_for_matching": False,
        },
        "primary": {
            "functional_language_minus_left_sensorimotor": {
                **summarize(primary_motor),
                "familywise_maxstat_p": float(primary_fwer[0]),
            },
            "functional_language_minus_left_visual": {
                **summarize(primary_visual),
                "familywise_maxstat_p": float(primary_fwer[1]),
            },
        },
        "sensitivities": {
            "functional_language_minus_reliability_matched_control": summarize(matched_contrast),
            "dk_language_minus_left_sensorimotor": summarize(dk_vs_motor),
            "dk_language_minus_left_visual": summarize(dk_vs_visual),
            "dk_language_minus_pooled_controls_reliability_adjusted": summarize(adjusted),
        },
        "system_mean_deltas": {
            "functional_language": float(functional.mean()),
            "dk_language_associated": float(dk_lang.mean()),
            "left_sensorimotor": float(motor.mean()),
            "left_visual": float(visual.mean()),
            "reliability_matched_control": float(matched_vec.mean()),
        },
        "guardrails": {
            "post_confirmatory": True,
            "no_new_model_training": True,
            "no_new_fmri_preprocessing": True,
            "no_region_selection_from_transfer_outcomes": True,
            "all_frozen_control_regions_retained": True,
            "participant_is_inferential_unit": True,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_DIR / "participant_contrasts.csv", participant_out)
    write_csv(OUTPUT_DIR / "region_groups_and_reliability.csv", region_group_rows)
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # Presentation-only summary figure from the frozen outputs.
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.35), constrained_layout=True)
    x = np.arange(len(subjects))
    for vals, label in [(primary_motor, "Language - motor"), (primary_visual, "Language - visual")]:
        axes[0].plot(x, vals * 1e3, marker="o", linewidth=1, label=label)
    axes[0].axhline(0, linewidth=0.8)
    axes[0].set_title("Functional language contrasts")
    axes[0].set_ylabel("Participant contrast (delta RSA x 10^-3)")
    axes[0].set_xlabel("Participant")
    axes[0].legend(frameon=False, fontsize=8)

    labels = ["Functional\nlanguage", "DK language\nassociated", "Sensorimotor", "Visual"]
    means = np.asarray([functional.mean(), dk_lang.mean(), motor.mean(), visual.mean()]) * 1e3
    axes[1].bar(np.arange(4), means)
    axes[1].set_xticks(np.arange(4), labels, rotation=20, ha="right")
    axes[1].set_ylabel("Mean delta RSA x 10^-3")
    axes[1].set_title("Frozen regional systems")

    sens_names = ["Matched\ncontrol", "DK-motor", "DK-visual", "Reliability-\nadjusted"]
    sens_vals = [matched_contrast, dk_vs_motor, dk_vs_visual, adjusted]
    sens_means = np.asarray([v.mean() for v in sens_vals]) * 1e3
    sens_err = []
    for v in sens_vals:
        lo, hi = bootstrap_ci(v)
        sens_err.append([(v.mean() - lo) * 1e3, (hi - v.mean()) * 1e3])
    yerr = np.asarray(sens_err).T
    axes[2].errorbar(np.arange(4), sens_means, yerr=yerr, fmt="o", capsize=3)
    axes[2].axhline(0, linewidth=0.8)
    axes[2].set_xticks(np.arange(4), sens_names, rotation=20, ha="right")
    axes[2].set_ylabel("Language advantage (delta RSA x 10^-3)")
    axes[2].set_title("Specificity sensitivities")

    fig.suptitle("SMN4Lang fMRI post-confirmatory language-specificity analysis", fontsize=11)
    fig.savefig(OUTPUT_DIR / "figure_language_specificity.png", dpi=600)
    fig.savefig(OUTPUT_DIR / "figure_language_specificity.pdf")
    plt.close(fig)

    report_lines = [
        "SMN4Lang fMRI language-specificity analysis v1",
        "Status: ok",
        "Post-confirmatory: yes",
        f"Participants: {len(subjects)}",
        "",
    ]
    for name, obj in summary["primary"].items():
        report_lines.append(
            f"PRIMARY {name}: mean={obj['mean']:.9g}; 95% CI=[{obj['bootstrap_ci_low']:.9g}, {obj['bootstrap_ci_high']:.9g}]; "
            f"positive={obj['n_positive']}/{obj['n_total']}; exact P={obj['exact_two_sided_signflip_p']:.9g}; "
            f"FWER P={obj['familywise_maxstat_p']:.9g}"
        )
    report_lines.append("")
    for name, obj in summary["sensitivities"].items():
        report_lines.append(
            f"SENSITIVITY {name}: mean={obj['mean']:.9g}; 95% CI=[{obj['bootstrap_ci_low']:.9g}, {obj['bootstrap_ci_high']:.9g}]; "
            f"positive={obj['n_positive']}/{obj['n_total']}; exact P={obj['exact_two_sided_signflip_p']:.9g}"
        )
    (OUTPUT_DIR / "report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": "ok", "output_dir": str(OUTPUT_DIR), "n_subjects": len(subjects)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
