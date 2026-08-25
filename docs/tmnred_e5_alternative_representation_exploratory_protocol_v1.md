# TMNRED E5 alternative-representation exploratory protocol v1

Status: frozen after completion of the prospectively designated TMNRED `row_mean_all` transfer test and before inspecting any E5 transfer result for the alternative TMNRED representations below.

## Purpose

The confirmatory TMNRED transfer endpoint used the ChineseEEG-selected all-sensor temporal mean (`row_mean_all`) and was null. The earlier model-blind TMNRED EEG reliability analysis had already included two prespecified sensitivity representations, `row_std_all` and `relative_8bin_all`, and both were more reliable than `row_mean_all` in TMNRED. This follow-up asks whether the frozen ChineseEEG-trained model aligns differently with those already-defined TMNRED geometries.

This analysis is exploratory. It cannot replace or redefine the completed confirmatory TMNRED transfer result. Any positive alternative-representation result requires independent confirmation in a later dataset, preferably ZuCo.

## Frozen representations

Only the following two already-defined TMNRED sensitivity representations are evaluated:

1. `row_std_all`: per retained sentence epoch, standard deviation over the frozen 0.0-2.0 s post-onset interval for each of the 30 EEG channels, yielding one 30-dimensional vector per sentence.
2. `relative_8bin_all`: divide the same frozen 0.0-2.0 s interval into eight deterministic contiguous time bins; average amplitude within each channel x bin and concatenate all bins, yielding one 240-dimensional vector per sentence.

No new time window, spatial region, frequency band, phase measure, distance metric, nuisance model, language-model layer, pooling rule, or neural-loss lambda may be selected using TMNRED outcomes in this analysis.

## Cohort and preprocessing

Use the already frozen TMNRED cohort of 29 participants, excluding `sub-25`. Retain `sub-23` with the same deterministic 500 Hz to 200 Hz resampling used in the primary analysis. Use the same artifact-rejected `z.set` signal source, `bepoch` trial mapping, retained-item masks, and 0.0-2.0 s interval.

For each participant x session x representation, z-score EEG features across retained items and construct a correlation-distance neural RDM.

## Model arms

Use exactly the already frozen multilingual E5 model family and adapters:

- base model as a descriptive secondary reference;
- ChineseEEG-trained text-only lambda 0 comparator;
- ChineseEEG-trained neural-guided lambda 0.10 model as the primary exploratory contrast;
- ChineseEEG-trained lambda 1 model as a descriptive secondary control.

TMNRED remains completely excluded from model training and hyperparameter selection.

## RSA and nuisance control

For each participant x session, compare the neural RDM with each model RDM using Spearman correlation. The primary exploratory RSA is computed after separately residualizing the neural and model edge vectors against the same four frozen TMNRED nuisance RDMs:

- absolute trial-position difference;
- CJK character-count difference;
- punctuation-count difference;
- CJK character-set Jaccard distance.

Raw RSA is secondary.

## Aggregation and inference

Aggregate the eight within-session RSA values to one participant-level value per model arm and representation using Fisher-z averaging.

For each representation separately, the primary exploratory contrast is lambda 0.10 minus lambda 0 residual RSA across the 29 participants. Report:

- mean and median participant-level delta;
- fraction of participants with positive delta;
- paired participant bootstrap 95% CI for the mean delta;
- one-sided paired sign-flip Monte Carlo p-value using the same fixed permutation count and deterministic seed family as the completed primary TMNRED transfer analysis;
- corresponding raw-RSA contrast as secondary;
- lambda 1 minus lambda 0 residual contrast as descriptive secondary evidence.

Also summarize session-level heterogeneity for the lambda 0.10 minus lambda 0 residual contrast, including the mean participant delta in each of the eight sessions and the fraction of participants positive within each session. These session summaries are descriptive and are not separate confirmatory tests.

## Interpretation guardrails

- The completed `row_mean_all` TMNRED transfer result remains the confirmatory result regardless of this analysis.
- `row_std_all` and `relative_8bin_all` are exploratory follow-ups because their superior TMNRED EEG reliability was observed before this model-transfer analysis but after the primary representation had already been designated from ChineseEEG.
- A positive result here does not establish general transfer until reproduced in an independent dataset.
- A null result is retained and reported.
- No additional TMNRED representation search is permitted from these outcomes without explicitly labeling it as a new exploratory generation step requiring later independent confirmation.
