# TMNRED frozen E5 external-transfer protocol v1

Status: prospectively frozen after the model-blind TMNRED EEG representation analysis and before inspecting any TMNRED language-model alignment.

## Objective

Test whether the ChineseEEG-trained neural-guided multilingual E5 model transfers to an independent Chinese EEG dataset without TMNRED model tuning.

## Frozen EEG target

- Dataset: TMNRED, OpenNeuro ds005383, published snapshot v1.0.0.
- Frozen participant cohort: the 29 participants passing the pre-outcome TMNRED structural/QC freeze; sub-25 is excluded.
- EEG source: published artifact-rejected epoched `z.set` derivative.
- EEG representation: **all-sensor temporal mean amplitude (`row_mean_all`) only** for the primary transfer test.
- Time window: 0.0 to <2.0 s after sentence onset.
- sub-23 is deterministically resampled from 500 Hz to 200 Hz before feature extraction, as frozen previously.
- Neural RDM: feature-wise z-score across the participant/session retained sentence items, then correlation distance.
- Analysis remains within session/block. No cross-session sentence RDM is used for the primary test.

The TMNRED amplitude-SD and 8-bin representations are not eligible to define transfer success because their relative performance was observed only after the primary EEG representation result. They remain secondary EEG-representation sensitivities for later reporting, not model-selection targets.

## Frozen language models

Primary model family: `intfloat/multilingual-e5-large` at revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`.

Arms:

1. `lambda_0`: frozen ChineseEEG text-only adapter.
2. `lambda_0p10`: frozen ChineseEEG neural-guided adapter at the already selected neural-loss weight 0.10. This is the primary neural-vs-text contrast.
3. `base`: pinned unadapted multilingual E5, secondary context control.
4. `lambda_1`: frozen full neural-loss adapter, secondary dose/context control.

No model is trained, fine-tuned, recalibrated, or selected using TMNRED.

## Text representation

- Use the original Chinese sentence from the TMNRED source-material workbook for each session/block item.
- Prefix each sentence with `query: `, matching the frozen E5 evaluation convention.
- Pool the final hidden state using attention-mask mean pooling.
- L2-normalize sentence embeddings.
- Model RDM: cosine distance.

English translations are not part of the primary transfer test.

## Participant/session matching

For each participant and session:

1. use the participant's retained EEG items from `event.bepoch`;
2. subset the fixed model RDM to exactly those same sentence items;
3. compute neural-model Spearman RSA on the available pairwise edges;
4. compute the same four frozen nuisance RDMs on that item subset:
   - absolute trial-position difference;
   - Chinese character-count difference;
   - punctuation-count difference;
   - Chinese character-set Jaccard distance.

Primary RSA residualizes both neural and model RDM edge vectors against these nuisance RDMs before Spearman correlation. Raw RSA is secondary.

## Participant aggregation

Within each model arm, aggregate the eight session-level RSA values for each participant using a Fisher-z mean. The participant is the inferential unit.

## Primary endpoint and inference

Primary endpoint:

`delta = residual RSA(lambda_0p10) - residual RSA(lambda_0)`

computed for each of the 29 frozen participants.

Primary summary:

- mean participant delta;
- median participant delta;
- fraction of participants with positive delta;
- paired participant bootstrap 95% confidence interval for the mean delta;
- one-sided paired sign-flip permutation test for mean delta > 0, using 200,000 Monte Carlo sign configurations and fixed seed 20260825, with plus-one correction.

The directional test is prespecified because the transfer hypothesis is that neural-guided training improves external neural alignment relative to the text-only adapter.

## Secondary endpoints

- raw RSA `lambda_0p10 - lambda_0`;
- absolute residual and raw RSA for base, lambda_0, lambda_0p10, and lambda_1;
- residual and raw `lambda_1 - lambda_0` deltas;
- session-level results for descriptive heterogeneity only.

Secondary results cannot replace the primary endpoint if the primary endpoint is null.

## Guardrails

- No TMNRED representation, time-window, model, layer, pooling rule, loss weight, or nuisance set may be changed after seeing transfer results and still be called confirmatory.
- No selection on the TMNRED amplitude-SD or 8-bin reliability result is allowed for the primary transfer claim.
- A null result is retained and interpreted as a boundary on transfer.
- TMNRED is not used to train any model in this analysis.
