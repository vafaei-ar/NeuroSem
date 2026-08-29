# NMI post-confirmatory robustness protocol v1

Status: frozen before execution; explicitly post-confirmatory.

## Purpose

This protocol addresses reviewer-facing robustness questions after the primary ZuCo and SMN4Lang fMRI outcomes are already known. None of the analyses below can provide new prospective confirmation. They are intended only to assess robustness and improve interpretation of the already-fixed lambda=0.10 versus lambda=0 contrast.

## Guardrails

- Do not change lambda, model family, model revision, LoRA architecture, training data, pooling, layer, optimizer, learning rate, batch size, epoch count, neural target, participant set, stimulus set, nuisance model, ROI, HRF, lag, EEG representation, or inferential unit.
- Do not select or discard seeds after outcomes are observed.
- Do not add further seeds if the frozen set is unfavorable.
- Do not search for linguistic categories, layers, neighborhoods, dimensions, ROIs, sensors, frequencies, or time windows that maximize an effect.
- Preserve all seed-level and robustness outputs regardless of direction.
- SMN4Lang MEG remains closed and is not touched.

## Analysis A: optimization-seed robustness

Run exactly three additional multilingual-E5 training seeds: `20260829`, `20260830`, and `20260831`.

For each seed, train exactly two matched arms using the frozen E5 recipe:

- lambda=0 text-only;
- lambda=0.10 genuine-neural.

All other settings are inherited unchanged from `configs/e5_neural_tuning_v1.json` and `scripts/tuning/train_e5_neurosem_lora.py`: train runs 01-05, descriptive run-06 validation, five fixed epochs, no early stopping, symmetric dropout-view InfoNCE text objective, LoRA query/value rank 8 alpha 16 dropout 0.05, learning rate 2e-4, weight decay 0.01, and the pinned multilingual-E5 revision.

Evaluate every completed seed, with no seed selection, on the already frozen external tests:

1. ZuCo 2.0 Task 1 normal-reading EEG using the exact existing transfer implementation and fixed participants/runs/nuisance controls;
2. SMN4Lang fMRI using the exact existing transfer implementation and fixed participants/stories/LanA mask/HRF/nuisance controls.

Primary robustness summaries are descriptive across seeds: seed-level mean participant delta, fraction of participants positive, and whether the sign of the mean delta matches the original fixed-seed result. No seed is promoted to a new confirmatory result.

## Analysis B: model-space perturbation characterization

Using the already frozen original lambda=0 and lambda=0.10 E5 adapters, characterize their geometry on the fixed ZuCo stimulus set without using neural outcomes.

Prespecified metrics:

- mean and median corresponding-item cosine similarity between lambda=0 and lambda=0.10 embeddings;
- Pearson and Spearman correlation between the two full pairwise cosine-distance vectors;
- linear centered kernel alignment (CKA) between the two embedding matrices;
- mean Jaccard overlap of the 10-nearest-neighbor sets under cosine distance.

This analysis is descriptive only. Do not inspect high-change items to create semantic or linguistic categories.

## Analysis C: participant-by-stimulus hierarchical robustness

Use only already generated locked transfer tables. Do not recompute model or neural representations.

- ZuCo: use the complete 17-participant x 7-run delta matrix from `outputs/zuco2_nr_e5_transfer_v1/latest/session_results.csv`.
- SMN4Lang fMRI: use the complete 12-participant x 60-story delta matrix from `outputs/smn4lang_fmri_e5_transfer_v1/latest/story_results.csv`.

For each dataset, perform exactly 10,000 two-factor bootstrap resamples. On each resample, sample participants with replacement and stimulus units (runs for ZuCo, stories for SMN4Lang) with replacement, then average the selected cell-level lambda=0.10 minus lambda=0 deltas. Report the observed cell mean, percentile 95% bootstrap interval, and fraction of bootstrap means greater than zero.

This is a sensitivity analysis for uncertainty over both individuals and the analyzed stimulus units. It does not turn the fixed set of stimuli into a claim of unrestricted language-population generalization.

## Interpretation

These analyses are post-confirmatory robustness checks. Favorable results may strengthen confidence that the original effect is not specific to one optimization trajectory or a small subset of stimulus units and may clarify the magnitude of the model-space perturbation. Unfavorable results must be reported and used to narrow the manuscript claim. No additional outcome-driven analysis family will be opened from these results.