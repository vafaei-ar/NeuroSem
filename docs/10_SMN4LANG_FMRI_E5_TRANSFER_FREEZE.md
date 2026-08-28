# SMN4Lang fMRI multilingual-E5 transfer freeze

**Status:** prospectively frozen after the model-blind fMRI reliability gate passed and before any SMN4Lang model-brain outcome is computed.

## Confirmatory question

Does the already trained ChineseEEG neural-guided multilingual-E5 adapter (`lambda=0.10`) align better with reliable SMN4Lang fMRI language-network geometry than the matched ChineseEEG text-only adapter (`lambda=0`)?

This is the single confirmatory SMN4Lang model contrast specified in `docs/8_SMN4LANG_PROSPECTIVE_VALIDATION.md`.

## Frozen model arms

Only two model arms are evaluated:

- `lambda=0`: ChineseEEG text-only adapter.
- `lambda=0.10`: ChineseEEG neural-guided adapter selected before SMN4Lang.

Both use the pinned `intfloat/multilingual-e5-large` revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`, the established `query: ` prefix, masked-mean pooling of the last hidden state, and L2-normalized embeddings.

No base-model arm, `lambda=1`, layer search, checkpoint search, lambda search, prompt search, or SMN4Lang tuning is allowed in this confirmatory analysis.

## Frozen linguistic-to-TR mapping

The neural reliability analysis established a TR-level representation. The model representation therefore uses the same fMRI temporal items.

For each story:

1. Read the released word-level `start`, `end`, and `word` arrays.
2. Process tokens in their released order.
3. At every word onset, construct the causal text available at that time as the within-sentence prefix ending at that token. This prevents future words from contributing to an earlier fMRI item.
4. Reset the prefix after sentence-final punctuation (`。`, `！`, `？`, `!`, `?`).
5. Encode every causal prefix independently with each frozen E5 adapter.
6. Place each embedding at its released word-onset TR using `floor(start / 0.71)`.
7. Sum simultaneous word events within a TR and convolve each embedding dimension with the same fixed canonical HRF used by the fMRI reliability analysis.
8. Sample the resulting model state at the same retained fMRI TRs.

No lag, window width, sentence length, pooling rule, or HRF parameter is selected from SMN4Lang model outcomes.

## Frozen TR inclusion rule

The reliability analysis retains TRs from the story audio onset to the end of the scan. For the model comparison, additionally require strictly positive model-blind HRF-convolved word-onset density. This removes only pre-linguistic zero-drive TRs for which no semantic model vector exists. The rule is identical for both adapters and uses no model outcome.

## Frozen neural representation

Reuse the reliability-stage neural definition without modification:

- all 12 participants;
- all 60 stories;
- preprocessed MNI fMRI derivatives;
- independently released LanA probabilistic language atlas;
- LanA threshold `>= 0.20`;
- exact native atlas/fMRI grid match;
- voxelwise z-scoring across retained TRs;
- correlation-distance RDM across LanA-mask multivoxel patterns.

The verified LanA atlas member is `SPM/LanA_n806.nii`, with SHA256 `3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babcaa3`.

## Frozen nuisance control

For every story, residualize both the neural RDM and each model RDM against the same three model-blind pairwise nuisance RDMs used in reliability:

1. absolute temporal separation in seconds;
2. absolute difference in canonical-HRF-convolved word-onset density;
3. absolute difference in canonical-HRF-convolved acoustic RMS envelope.

The primary model-brain statistic within each participant/story is Spearman correlation between the nuisance-residualized neural and model RDM vectors.

## Frozen aggregation and inference

For each participant and model arm:

1. compute residual RSA independently in all 60 stories;
2. aggregate the 60 correlations by an unweighted Fisher-z mean and transform back to correlation scale.

The sole confirmatory effect is participant-level:

`delta = RSA(lambda=0.10) - RSA(lambda=0)`.

Report:

- mean and median participant delta;
- number and fraction of positive participant deltas;
- 10,000-resample participant bootstrap 95% CI for the mean delta;
- exact one-sided participant sign-flip p-value for mean delta greater than zero.

Participant, not story or TR, is the inferential unit.

## Guardrails

- The completed fMRI reliability summary must report `reliability_gate_pass: true` before model loading.
- Do not train or adapt any model on SMN4Lang.
- Do not change the LanA mask, threshold, HRF, temporal item, nuisance set, participant set, story set, E5 layer, prompt prefix, pooling rule, or adapter after viewing the contrast.
- Do not use SMN4Lang-distributed BERT, GPT2, Word2Vec, or other model features for selection.
- Do not run ROI or localization searches based on `lambda=0.10 - lambda=0`.
- Preserve positive, null, or negative outcomes.
- A completed null result does not justify searching additional public datasets.

## Outputs

Only safe derived aggregate outputs are exported:

- `summary.json`
- `participant_results.csv`
- `story_results.csv`
