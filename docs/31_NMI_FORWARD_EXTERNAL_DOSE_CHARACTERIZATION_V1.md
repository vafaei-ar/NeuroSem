# NeuroSem forward external dose characterization v1

**Status:** post-confirmatory characterization, frozen before any new ZuCo or SMN4Lang external-dose outcomes are inspected.

## Purpose

Characterize how the strength of the already-trained ChineseEEG-derived relational objective affects external transfer to the previously frozen ZuCo EEG and SMN4Lang fMRI targets. This analysis does not replace or revise the prospective lambda=0.10 tests. It asks a distinct post-confirmatory machine-learning question: whether external relational transfer varies with objective strength under the fixed multilingual-E5 training recipe.

## Evidence hierarchy

The original ChineseEEG-to-ZuCo and ChineseEEG-to-SMN4Lang lambda=0.10 contrasts remain the primary prospective transfer tests. This dose characterization is subsequent and descriptive/inferential only within the explicitly frozen dose family below. No result from this analysis may be promoted to prospective confirmation or used to redefine the primary dose.

## Verified arm provenance

The pre-outcome structural audit `K7M4V2R9` verified that all six model arms and their summaries/adapters exist and that the primary ZuCo and SMN4Lang evaluation code still matches the exact executed primary versions.

Use exactly the prespecified ChineseEEG-source grid:

`lambda = [0.00, 0.01, 0.03, 0.10, 0.30, 1.00]`

Provenance is fixed as follows:

- `lambda=0.00`: original frozen E5 text-only anchor, `outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter`.
- `lambda=0.01`: Pareto-grid intermediate arm, `outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural/20260823_192219/adapter`.
- `lambda=0.03`: Pareto-grid intermediate arm, `outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural/20260823_192323/adapter`.
- `lambda=0.10`: Pareto-grid intermediate arm, `outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural/20260823_192425/adapter`.
- `lambda=0.30`: Pareto-grid intermediate arm, `outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural/20260823_192528/adapter`.
- `lambda=1.00`: original frozen genuine-neural E5 anchor, `outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter`, reused by the original Pareto grid rather than retrained for that grid.

All six arms use `intfloat/multilingual-e5-large` revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`, seed `20260823`, 5 epochs, batch size 32, learning rate 2e-4, weight decay 0.01, and the same representation/training recipe; only the neural-loss weight differs.

Do not train, retrain, replace, add, delete, interpolate, or select dose arms after external outcomes are inspected.

## Outcome-status asymmetry fixed before evaluation

At the time of this freeze, the following quantities have already been observed and are not fresh outcomes:

- ChineseEEG run-07 dose-response values across all six doses;
- the eight-task external STS mean and task-level scores across all six doses;
- the original prospective ZuCo and SMN4Lang lambda=0.10 versus lambda=0 results.

The following outcomes have **not** been inspected across the full six-dose forward grid and are the new characterization targets:

- ZuCo EEG external transfer for lambda=0.01, 0.03, 0.30 and 1.00 relative to lambda=0;
- SMN4Lang fMRI external transfer for lambda=0.01, 0.03, 0.30 and 1.00 relative to lambda=0.

Any neural-transfer-versus-STS plot therefore combines a newly evaluated external-transfer axis with an already-observed STS axis. This asymmetry must be stated in any manuscript figure or caption. The STS axis cannot be used retrospectively to choose or privilege a dose.

## Frozen ZuCo evaluation

Reuse the exact primary ZuCo pipeline and inputs without modification:

- 17 frozen participants and all 7 NR runs;
- the same frozen item mapping and temporal-mean EEG representation;
- the same four nuisance RDMs;
- cosine-distance model RDMs;
- within-run nuisance residualization;
- within-run Spearman RSA;
- participant aggregation by Fisher-z mean across the seven runs;
- participant as inferential unit.

For every non-zero dose, report participant-level `delta(lambda) = RSA(lambda) - RSA(lambda=0)` using the same participant set.

For each dose report:

- mean and median participant delta;
- number/fraction of positive participant deltas;
- 10,000-resample participant bootstrap 95% CI for mean delta, using the same bootstrap implementation as the primary analysis;
- exact two-sided participant sign-flip p-value for the mean delta, with one-sided direction shown only as a secondary sensitivity if already provided by the shared helper;
- arm-wise group mean RSA descriptively.

No participant, run, item, nuisance, representation, model, or dose selection may use dose outcomes.

## Frozen SMN4Lang fMRI evaluation

Reuse the exact primary SMN4Lang pipeline and inputs without modification:

- 12 participants and all 60 stories;
- LanA mask threshold 0.20 and the same retained fMRI TR family;
- the same causal within-sentence semantic state;
- same word-to-TR mapping and canonical HRF;
- same temporal-separation, HRF word-density and HRF acoustic-RMS nuisance family;
- cosine-distance model RDMs;
- story-wise nuisance-residualized Spearman RSA;
- participant aggregation by unweighted Fisher-z mean across stories;
- participant as inferential unit.

For every non-zero dose, report participant-level `delta(lambda) = RSA(lambda) - RSA(lambda=0)` using the same participant and story sets.

For each dose report:

- mean and median participant delta;
- number/fraction of positive participant deltas;
- 10,000-resample participant bootstrap 95% CI for mean delta, using the same bootstrap implementation as the primary analysis;
- exact two-sided participant sign-flip p-value for the mean delta, with one-sided direction shown only as a secondary sensitivity if already provided by the shared helper;
- arm-wise group mean RSA descriptively.

No story, participant, TR, mask, nuisance, HRF, semantic unit, model, checkpoint, or dose selection may use dose outcomes.

## Prespecified presentation

Always show all six doses, including lambda=0, for both external targets.

Primary characterization displays:

1. external ZuCo delta-RSA versus lambda;
2. external SMN4Lang delta-RSA versus lambda;
3. if the already-observed matched STS values are used, external neural-transfer delta versus STS change for the same six arms, with the caption explicitly stating the outcome-status asymmetry above.

Do not report an "optimal" lambda, a best-dose inferential claim, or target-specific dose selection. Do not infer monotonicity unless the complete displayed curve visibly supports that descriptive statement; no monotonicity test is added.

## Interpretation rules

- A rising curve supports the descriptive claim that stronger relational weighting is associated with larger external transfer under this fixed E5 recipe.
- A flat, saturating, irregular or reversing curve is retained and interpreted as evidence that stronger source weighting does not guarantee larger external transfer.
- The lambda=0.10 prospective tests retain their original evidential status regardless of the characterization curve.
- Even if lambda=1.00 produces the largest effect, it must not replace lambda=0.10 as the prospective headline result.
- The existing STS dose series is an already-observed development/benchmark characterization, not a fresh external confirmation axis.
- No new lambda values, alternative checkpoints, model families, target datasets, behavioral endpoints, or rescue analyses are permitted from the dose results.

## Stop rule

After this single six-dose evaluation on ZuCo and SMN4Lang, stop the forward-dose characterization. Do not add lambda=3, intermediate values, alternative seeds, new targets, or additional optimization trajectories based on the observed curve.

## Planned safe outputs

Export only safe derived outputs:

- `summary.json` with provenance, frozen grid, outcome-status notes and aggregate statistics;
- `zuco_subject_dose_results.csv`;
- `smn4lang_participant_dose_results.csv`;
- `dose_summary.csv`.

No raw restricted neural data or credentials are exported.
