# NeuroSem: preliminary project brief for discussion with Abbas

## Core idea

We are testing whether semantic relationships measured in human brain activity contain reproducible structure that is not fully captured by standard language-model representations. The long-term goal is to determine whether this residual neural semantic geometry can provide useful auxiliary supervision for language models.

The central scientific question is:

> Can residual human neural semantic geometry contribute information beyond ordinary linguistic and experimental structure, and can that information eventually improve language-model representations?

## Current dataset and analysis

Primary discovery resource: ChineseEEG natural-reading dataset.

Current neural representation:
- whole-row mean EEG activity across 128 channels;
- featurewise z-scoring across rows within subject;
- correlation-distance representational dissimilarity matrix (RDM).

Current semantic representation:
- `google-bert/bert-base-chinese`;
- pinned revision `8d2a91f91cc38c96bb8b4556ba70c392f8d5ee55`;
- primary target: mean-pooled final hidden layer over non-special tokens.

Nuisance controls include row position, duration, character count, chapter, character-set overlap, and punctuation-related structure. Inference uses dependence-preserving within-chapter circular shifts rather than iid row shuffling.

## What we established before semantic testing

The initially tested flattened sensor-time representation had weak cross-subject reliability. A simpler whole-row mean representation was substantially more reproducible and was selected based on neural reliability before semantic testing.

For the selected row-mean representation:
- raw leave-one-subject-out cross-subject reliability: approximately 0.220;
- after controlling basic positional, duration, character-count, and chapter nuisances: approximately 0.121;
- residual reliability was clearly above a circular-shift null (`p` approximately 0.001).

This established that the neural target itself contains reproducible cross-subject structure beyond simple nuisance geometry.

## Held-out semantic replication across six runs

Primary BERT final-layer partial-Spearman effects:

| Run | Mean residual neural-semantic effect | Run permutation p-value |
| --- | ---: | ---: |
| 01 | 0.0057 | 0.051 |
| 02 | 0.0034 | 0.083 |
| 03 | 0.0145 | 0.00060 |
| 04 | 0.0045 | 0.110 |
| 05 | 0.0174 | 0.040 |
| 06 | 0.0056 | 0.083 |

Cross-run aggregate across runs 01-06:
- positive primary effect in 6/6 runs;
- mean run effect = 0.0085;
- exact one-sided run-level sign-flip `p = 0.015625`;
- common-subject aggregate positive in 8/9 subjects;
- exact subject-level sign-flip `p = 0.0391`;
- every leave-one-run-out aggregate remains positive.

Thus the result is not driven by one unusually strong run.

## Important nuance

The prespecified last-four-layer BERT sensitivity representation is also now positive at the cross-run level:
- positive in 5/6 runs;
- run-level exact sign-flip `p = 0.046875`.

Therefore, we should no longer describe the result as uniquely specific to the final BERT layer. The stronger claim is that multiple nearby BERT representational summaries show a small but reproducible residual correspondence with EEG geometry, with the final layer remaining the prespecified primary target.

## Current interpretation

The effect is small in magnitude but unusually consistent across held-out narrative runs. The strongest defensible conclusion at this stage is:

> ChineseEEG contains a reproducible residual neural geometry that shows small but consistent correspondence with BERT representational geometry after nuisance control across six independent narrative runs.

This provides preliminary within-dataset support for the first NeuroSem hypothesis, but it does not yet establish that the aligned structure is uniquely semantic, model-general, or useful for model training.

## Next planned steps

1. Keep run-07 sealed as an additional holdout for later model validation.
2. Compare a prespecified panel of major model families on already analyzed runs rather than testing arbitrary checkpoints until one performs best.
3. Planned model families include the current Chinese BERT baseline, XLM-R, multilingual-E5, BGE-M3, and Qwen embedding models.
4. Evaluate whether model-family effects replicate across runs and whether the same neural geometry is shared across models.
5. Strengthen semantic specificity controls against lexical, orthographic, positional, and other non-semantic language structure.
6. Replicate in an independent neural-language dataset if the cross-model signal remains stable.
7. Only then move to parameter-efficient neural-guided tuning using LoRA/adapters.

## Proposed tuning question

The tuning phase should not simply maximize brain-model correlation. The decisive test should be:

> Does auxiliary supervision from residual neural geometry improve held-out semantic generalization beyond matched text-only supervision?

A strong design would compare:
- neural-residual relational supervision;
- matched text-only semantic supervision;
- shuffled-neural supervision;
- no-tuning baseline;
- evaluation on held-out stimuli, subjects, and ideally an independent dataset.

## Why this may be interesting

A positive result would suggest that human neural semantic organization provides a biologically grounded training signal that is not redundant with ordinary language-only supervision. A negative tuning result would still be informative because it would distinguish representational correspondence from useful transferable supervision.

## Status for discussion

This is an early-stage project with a reproducible preliminary signal and a defined validation path. The project is now mature enough for scientific discussion about model comparison, control analyses, tuning strategy, and publication framing, while retaining at least one additional held-out run for later validation.
