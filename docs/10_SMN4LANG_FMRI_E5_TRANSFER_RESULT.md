# SMN4Lang fMRI E5 transfer: frozen result and decision

**Status:** completed confirmatory analysis
**Completed:** 2026-08-28
**RunRelay job:** `NEUROSEM-SMN4LANG-FMRI-E5-TRANSFER-0001`
**NeuroSem commit:** `abfbac4d54269d96c52ac0cd61776cc2a0c2f892`

## Scientific question

Does neural guidance learned from Chinese natural-reading EEG produce a language-model representation that generalizes to independently measured cortical language geometry during naturalistic auditory comprehension?

This is a cross-dataset, cross-participant, cross-task, and cross-measurement-modality test. The model was trained only on ChineseEEG. SMN4Lang was never used for training or model selection.

## Why SMN4Lang

SMN4Lang / OpenNeuro `ds004078` contains 12 native-Mandarin participants listening to 60 naturalistic Chinese stories with fMRI and MEG. The fMRI arm was selected prospectively as the primary cross-modal validation because it tests whether the learned neural relational target survives a qualitative change in measurement modality and language task.

The analysis sequence was deliberately outcome-protected:

1. metadata and timebase audits;
2. independent LanA language-network mask freeze;
3. model-blind fMRI neural-geometry reliability gate;
4. only after that gate passed, one frozen model contrast.

## Frozen neural representation

Primary fMRI neural geometry:

- 12 participants;
- 60 stories;
- 720 participant-story runs;
- TR = 0.710 s;
- independent LanA probabilistic language-network mask thresholded at 0.20;
- 25,137 retained voxels;
- featurewise z-scoring across retained TRs;
- correlation-distance RDM across LanA multivoxel patterns;
- nuisance control for absolute temporal separation, canonical-HRF-convolved word-onset density, and canonical-HRF-convolved acoustic RMS envelope.

The model-blind reliability analysis passed strongly before any E5 model was loaded:

- mean participant reliability `r = 0.65327`;
- median `0.64760`;
- 12/12 participants positive;
- bootstrap 95% CI `[0.63945, 0.66843]`;
- exact one-sided sign-flip `p = 0.00024414`.

## Frozen semantic mapping

The semantic drive was fixed before model comparison:

- model: `intfloat/multilingual-e5-large`;
- pinned revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`;
- input prefix `query: `;
- semantic state: causal within-sentence prefix embedding available at each released word onset;
- sentence state reset at sentence-final punctuation;
- word event mapped to TR by `floor(word_start / 0.71)`;
- same fixed canonical HRF as the reliability analysis;
- model RDM: cosine distance;
- retain the same stimulus-period TR family with positive HRF word-onset density;
- no lag, HRF, semantic-unit, model, layer, lambda, checkpoint, or ROI search.

## Confirmatory contrast

The only confirmatory contrast was:

> ChineseEEG-trained multilingual-E5 `lambda=0.10` neural-guided adapter minus the matched ChineseEEG-trained `lambda=0` text-only adapter.

Both models saw identical SMN4Lang text and timing. No SMN4Lang training occurred.

Participant was the inferential unit. Within each story, nuisance-residualized neural and model RDMs were compared by Spearman correlation. Story-wise correlations were aggregated within participant by unweighted Fisher-z mean and transformed back with `tanh`.

## Result

Mean participant residual RSA:

- `lambda=0`: **0.12092396**;
- `lambda=0.10`: **0.12177646**.

Primary neural-guided advantage:

- mean delta: **+0.00085250**;
- median delta: **+0.00086365**;
- positive participants: **12/12**;
- fraction positive: **1.00**;
- participant bootstrap 95% CI: **[+0.00078966, +0.00091398]**;
- exact one-sided sign-flip: **p = 0.00024414**.

Participant deltas ranged from approximately **+0.000646 to +0.001020**. Thus, the effect is small in absolute RSA units but exceptionally consistent across participants.

Story-level effects are heterogeneous and include negative cells. This does not alter the confirmatory conclusion because participant, not story, was prospectively designated as the inferential unit.

## Guardrails verified

The completed analysis records that:

- the fMRI reliability gate was verified before model loading;
- no SMN4Lang training occurred;
- only `lambda=0` and `lambda=0.10` were loaded;
- no layer search occurred;
- no lambda search occurred;
- no checkpoint search occurred;
- no ROI search occurred;
- no lag or HRF search occurred;
- no semantic-unit search occurred.

## Scientific interpretation

This result is the strongest external validation of the NeuroSem modeling claim because it is not merely another EEG replication. Neural guidance learned from Chinese natural-reading EEG produces a small but reproducible representational change that better matches independent language-network fMRI geometry during auditory narrative comprehension.

The important claim is therefore not that neural guidance produces a large generic semantic gain. It is that a relational target derived from human neural data can be learned by a language model and can generalize prospectively across participants, datasets, tasks, and measurement modalities.

The modest absolute effect size should be stated explicitly. The value of the result comes from its experimental independence, frozen design, directional consistency, and cross-modal generalization rather than from a large increase in RSA magnitude.

## Decision

The primary SMN4Lang fMRI validation is complete and positive.

Do not:

- tune SMN4Lang;
- search lambdas, layers, checkpoints, ROIs, lags, HRFs, or semantic units;
- search another fMRI dataset to obtain a larger effect;
- redefine the result based on story-level heterogeneity.

For manuscript purposes, SMN4Lang fMRI should be treated as the capstone prospective cross-modal validation. ZuCo provides complementary cross-language EEG validation. TMNRED, Garnett Dream, and the directional-word dataset should be retained as boundary conditions showing that the model-transfer effect is selective rather than universal.

A SMN4Lang MEG analysis is optional and secondary. If pursued, it must begin with a separately frozen model-blind reliability analysis and cannot use the fMRI model outcome to choose temporal windows, bands, sensors, or representations.
