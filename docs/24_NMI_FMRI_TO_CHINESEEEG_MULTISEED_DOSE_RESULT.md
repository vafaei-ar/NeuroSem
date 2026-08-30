# NMI fMRI-to-ChineseEEG multi-seed dose robustness: completed results

**Status:** completed post-confirmatory optimization-seed robustness analysis

**RunRelay job:** `C4M7R2K9` (`Replicate ChineseEEG dose across seeds`)

**Exact NeuroSem execution commit:** `0510c528432a49fd2244cabe0e3b3a05cafe0ec1`

**Runtime:** 01:02:35, exit 0, 8 declared artifacts

**Canonical Drive job folder:** https://drive.google.com/drive/folders/13Hp2bq-ELQua-SyvqAp6FjUAA_a2FsbH

**Protocol:** `docs/22_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_V1.md`

## Purpose and evidential status

This analysis was frozen only after the single-seed fMRI-to-ChineseEEG dose-response had been observed. It is therefore post-confirmatory robustness, not a fresh confirmation. The goal was to determine whether the directional ChineseEEG dose pattern survives independent multilingual-E5 optimization trajectories without changing the source, target, lambda grid, representation, training schedule or target-side analysis.

## Frozen model and design

- model: `intfloat/multilingual-e5-large`;
- revision: `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`;
- new seeds: `20260829`, `20260830`, `20260831`;
- lambda grid: `0, .01, .03, .10, .30, 1.0`;
- source: frozen SMN4Lang fMRI relational target and fixed 20-story training / 12-story validation design;
- target: unchanged ChineseEEG run-07 nuisance-adjusted RSA pipeline;
- no target-side model, representation, participant, item, layer, checkpoint or nuisance search;
- no lambda added or removed after ChineseEEG outcomes were known.

## Source-only validation behavior

For all three new seeds, held-out SMN4Lang source-validation alignment increased with stronger neural weight. The lambda=1 arm had the highest source validation alignment in each seed. This source-side monotonicity did not automatically imply a monotonic ChineseEEG target effect.

## ChineseEEG target effects by lambda and seed

Values are neural-guided arm minus the same-seed lambda=0 control on ChineseEEG run-07.

| Lambda | Seed 20260829 mean delta | Seed 20260830 mean delta | Seed 20260831 mean delta | Mean of seed means | New seeds positive |
|---:|---:|---:|---:|---:|---:|
| .01 | +7.7333e-06 | -7.7381e-07 | -1.1175e-07 | +2.2826e-06 | 1/3 |
| .03 | -1.0850e-05 | -2.3397e-06 | +1.0860e-06 | -4.0345e-06 | 1/3 |
| .10 | -1.6465e-05 | -1.1079e-05 | +6.9867e-06 | -6.8526e-06 | 1/3 |
| .30 | -2.9392e-06 | -1.7046e-05 | +1.4907e-05 | -1.6927e-06 | 1/3 |
| 1.0 | **+7.7478e-05** | **+6.2966e-05** | **+5.4571e-05** | **+6.5005e-05** | **3/3** |

The lower and intermediate doses are clearly optimization-seed heterogeneous. Only lambda=1.0 produced a positive seed-level mean in all three added trajectories.

## Lambda=1.0 participant-level results

Even at lambda=1.0, uncertainty remains substantial because ChineseEEG run-07 contains only 10 participants.

- seed 20260829: mean delta **+7.7478e-05**, 7/10 positive, bootstrap 95% CI **[-1.2345e-04,+2.7605e-04]**, exact one-sided p **.2451**;
- seed 20260830: mean delta **+6.2966e-05**, 7/10 positive, bootstrap 95% CI **[-1.1551e-04,+2.3667e-04]**, exact one-sided p **.2568**;
- seed 20260831: mean delta **+5.4571e-05**, direction positive at the seed mean level; the complete participant-level values are retained in the safe artifact table.

Thus, the high-dose sign is reproducible across optimization trajectories but is not independently significant within individual 10-participant seed evaluations.

## Ordered dose slopes

For each seed, participant-level delta RSA was regressed descriptively against `log10(lambda)` over the five positive lambda values. All three new seed-level mean slopes were positive:

| Seed | Mean participant slope | Positive participant slopes | 95% bootstrap CI | Exact one-sided p |
|---:|---:|---:|---:|---:|
| 20260829 | +2.9800e-05 | 7/10 | [-6.3445e-05,+1.2101e-04] | .2803 |
| 20260830 | +2.2842e-05 | 7/10 | [-6.0306e-05,+1.0268e-04] | .2988 |
| 20260831 | +2.4768e-05 | 7/10 | [-7.7279e-05,+1.2350e-04] | .3242 |

Across new seeds, the mean of these seed-level slope means was **+2.5804e-05**, and all 3/3 seed-level mean slopes were positive. However, every participant-bootstrap interval crossed zero and every per-seed exact test was non-significant.

## Interpretation

The correct interpretation is narrower than the single-seed dose-response initially suggested:

> The fMRI-to-ChineseEEG dose-response is not robustly monotonic across optimization seeds at low and intermediate neural weights. A high-dose lambda=1.0 effect is directionally consistent across all three added E5 trajectories, and all three trajectory-level dose slopes are positive, but participant-level uncertainty remains substantial. Therefore ChineseEEG provides suggestive high-dose/ordered-trend consistency rather than a separately established dose-response.

Do not promote lambda=1.0 to a new confirmatory optimum. The original source-selected lambda=.01 ZuCo reverse-transfer test remains the primary frozen reverse-direction result. The ChineseEEG multi-seed result is a post-confirmatory robustness characterization and should remain secondary.

## Artifact provenance

Canonical safe artifacts from `C4M7R2K9` include:

- `outputs/nmi_fmri_to_chineseeeg_multiseed_dose_v1/latest/summary.json`;
- `outputs/nmi_fmri_to_chineseeeg_multiseed_dose_v1/latest/seed_subject_lambda_results.csv`;
- per-seed calibration summaries;
- per-seed ChineseEEG participant-level dose tables.

All three prespecified added seeds and all six fixed lambda arms were retained. No rescue search followed the result.
