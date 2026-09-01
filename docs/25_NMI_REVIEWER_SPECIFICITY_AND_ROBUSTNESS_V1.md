# 25. NMI reviewer-driven neural-specificity and robustness protocol v1

**Status:** frozen before reviewer-driven specificity execution.

## Purpose

Address the central reviewer question raised after the completed primary NeuroSem evidence chain: does external neural transfer require the item-matched neural relational target, or can it be reproduced by a matched auxiliary relational objective whose neural target has been destroyed by item permutation?

This analysis is explicitly **reviewer-driven and post-confirmatory**. It does not alter the status of the original ChineseEEG -> ZuCo EEG -> SMN4Lang fMRI external evidence chain.

## Global guardrails

- Keep the original primary multilingual-E5 lambda=0.10 versus lambda=0 result unchanged.
- Do not use ZuCo or SMN4Lang outcomes to select seeds, lambda, checkpoint, layer, pooling rule, target permutation, participant subset, stimulus subset, or stopping rule.
- Report every prespecified seed and both external targets.
- Do not perform rescue tuning after any null or unfavorable result.
- Reuse the existing frozen ZuCo and SMN4Lang target pipelines without representation changes.
- Treat all new results as post-confirmatory specificity/sensitivity evidence.

## Neural-specificity control

### Model

Use the same multilingual-E5-large revision and LoRA/text-objective protocol as the established ChineseEEG-guided E5 analysis.

### Seeds

Use exactly the three already-prespecified post-confirmatory optimization seeds:

- 20260829
- 20260830
- 20260831

These seeds were previously used for genuine-neural E5 robustness and were not selected from the reviewer-specificity outcomes.

### Arms

For each seed compare three matched training conditions:

1. text-only lambda=0;
2. genuine ChineseEEG relational target, lambda=0.10;
3. shuffled-neural ChineseEEG relational target, lambda=0.10.

The shuffled-neural targets are the already-materialized `shuffled_neural_target.npy` arrays produced with the frozen ChineseEEG neural-target construction. They preserve the training budget and target dimensionality while destroying the linguistic-item correspondence encoded by the genuine neural target.

### External targets

Evaluate both fixed targets:

1. ZuCo 2.0 Task 1 Normal Reading EEG, 17-participant frozen pipeline;
2. SMN4Lang LanA language-network fMRI, 12-participant frozen pipeline.

No target-side model or representation selection is permitted.

### Primary reviewer estimand

For each seed and external target:

`genuine-neural external residual RSA - shuffled-neural external residual RSA`

Report participant-level values, mean, median, fraction positive, participant bootstrap interval, exact one-sided sign-flip P under the reviewer-motivated directional question, and the corresponding two-sided exact sign-flip sensitivity P.

### Secondary contextual estimand

For each seed and target also report:

`shuffled-neural external residual RSA - text-only external residual RSA`

This identifies whether a generic matched relational regularizer transfers even when item-neural correspondence is destroyed.

### Cross-seed summary

Cross-seed summaries are descriptive. Report all three seed-level means and sign stability for genuine-minus-shuffled and shuffled-minus-text-only. Do not treat three optimization seeds as a population-level random-effects sample of training procedures.

## Participant x stimulus sensitivity

Re-run the already-frozen post-confirmatory hierarchical robustness analysis for the original primary lambda=0.10 versus lambda=0 transfer contrast:

- ZuCo: participants x seven Normal Reading runs;
- SMN4Lang fMRI: participants x stories.

Use 10,000 two-factor bootstrap resamples under the existing deterministic seed and preserve the guardrail that this is a sensitivity over the analyzed stimulus units, not unrestricted inference over arbitrary language stimuli.

## Model-space perturbation characterization

Re-run the already-frozen model-space characterization for the original text-only versus genuine-neural multilingual-E5 contrast. Report embedding cosine similarity, RDM Pearson correlation, RDM Spearman correlation, linear CKA, and k-nearest-neighbour overlap using the existing frozen analysis script and inputs.

## Statistical sensitivity

For reviewer-facing reporting, add the corresponding exact two-sided sign-flip P values for the major participant-level external contrasts while retaining the originally prespecified one-sided tests as primary where applicable.

## Interpretation rules

- If genuine-neural exceeds shuffled-neural consistently across both targets, interpret this as evidence that external transfer depends on the item-matched neural relational organization beyond a generic matched relational regularizer.
- If genuine-neural exceeds shuffled-neural in only one target, describe specificity as target-selective.
- If genuine-neural and shuffled-neural are similar, narrow the mechanism claim to relational regularization associated with neural transfer rather than neural-specific relational content.
- If shuffled-neural exceeds genuine-neural, treat this as a material challenge to the neural-specificity interpretation and revise the manuscript accordingly.

No outcome in this reviewer-driven analysis can retroactively alter the prospective status of the original external tests.
