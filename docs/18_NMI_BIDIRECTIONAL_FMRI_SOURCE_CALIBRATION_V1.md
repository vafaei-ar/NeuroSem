# NMI bidirectional fMRI-source E5 calibration v1

**Status:** frozen post-confirmatory source-only calibration protocol. No EEG target may be read by this stage.

## Question

Can the frozen SMN4Lang fMRI relational geometry induce a stable multilingual-E5 perturbation using source-only training and validation, before any EEG evaluation?

## Fixed source

- Dataset: SMN4Lang / OpenNeuro ds004078.
- Neural representation: the already-frozen LanA-mask within-story timepoint geometry and nuisance model.
- Source targets: `outputs/nmi_bidirectional_fmri_source_v1/latest/targets/story_XX.npz` produced by the model-blind source-freeze stage.
- Source split: 48 train stories and 12 validation stories from the committed SHA256 split.
- Calibration-training subset: exactly 20 of the 48 train stories, selected before model training by SHA256 ordering of `fmri-source-calibration-story-XX`: `[56,15,48,55,27,3,23,6,21,58,36,40,12,30,9,35,20,5,49,28]`.
- The remaining 28 source-train stories are not used for lambda selection and are not substituted after outcomes are known.

## Model and optimization

- Model: `intfloat/multilingual-e5-large`.
- Revision: `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`.
- Input prefix: `query: `.
- Pooling: attention-mask mean of final hidden state, L2 normalized.
- LoRA: q/v, rank 8, alpha 16, dropout 0.05.
- Optimizer: AdamW, learning rate 2e-4, weight decay 0.01.
- Fixed epochs: 5.
- Calibration seed: 20260823.
- One story-level optimizer step per calibration-training story per epoch schedule. Each of the 20 stories is used exactly once across the five epochs, four stories per epoch. No early stopping.
- Text objective: symmetric dropout-view InfoNCE, temperature 0.05, on a deterministic set of at most 32 causal prefixes from the current story.
- Neural objective: `1 - corr(z(d_model_residual), target_group_fMRI)` where `d_model_residual` is the cosine-distance RDM among the frozen retained fMRI timepoints after the same three nuisance RDMs are linearly residualized. Model states are constructed by placing causal sentence-prefix E5 embeddings at released word onsets and applying the same canonical HRF used in the frozen fMRI analysis.

## Lambda calibration

Evaluate exactly `{0, .01, .03, .10, .30, 1.0}` at the calibration seed. No other lambda is permitted.

For each lambda, train for the fixed five-epoch schedule and compute the mean held-out source-validation correlation over the 12 frozen validation stories.

Candidate rule:

1. Among positive lambdas only, identify the largest mean source-validation correlation.
2. Compute the standard error over the 12 validation-story correlations for that best positive lambda.
3. Choose the **smallest positive lambda** whose mean is within one standard error of that best positive mean.
4. Proceed to external EEG testing only if the selected positive lambda has a higher mean source-validation correlation than lambda 0. Otherwise stop and report source-learning failure. Do not inspect EEG.

This source-only rule is developmental and post-confirmatory. It is not evidence of external transfer.

## Next stage if the source gate passes

Freeze the selected lambda, then train matched text-only and fMRI-guided E5 arms at seeds `20260829`, `20260830`, and `20260831` under the same source schedule. Only after all six adapters are frozen may the external evaluator read ZuCo EEG. ChineseEEG run-07 remains secondary.

## Guardrails

- No ZuCo or ChineseEEG access in calibration.
- No change to model revision, pooling, layer, LoRA, ROI, HRF, nuisance model, story split, source target, lambda grid, seed, epoch count, or candidate rule after outcomes are observed.
- No rescue search after a source-gate failure.
