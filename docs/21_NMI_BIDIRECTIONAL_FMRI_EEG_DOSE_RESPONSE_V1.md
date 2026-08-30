# NMI post-confirmatory fMRI-to-EEG dose-response characterization v1

## Status

This is an exploratory/post-confirmatory characterization performed after the frozen lambda=0.01 fMRI-to-ZuCo result was observed. It does not replace, upgrade, or redefine that primary reverse-direction test.

## Scientific question

Given that held-out SMN4Lang source alignment increased with the strength of the fMRI relational constraint, does EEG transfer show an ordered dose-response across the already-trained fMRI-guided E5 adapters?

## Frozen candidates

Use only the six adapters already produced by the source-only calibration job, with no retraining and no new lambda values:

- lambda=0
- lambda=0.01
- lambda=0.03
- lambda=0.10
- lambda=0.30
- lambda=1.0

All use the same multilingual-E5 model revision, LoRA specification, source stories, optimization schedule and source geometry as the completed source calibration.

## Targets

1. ZuCo 2.0 Task 1 normal-reading EEG, using the frozen 17-participant all-retained-channel temporal-mean representation and the existing nuisance-adjusted RSA pipeline.
2. ChineseEEG sealed run-07, using the frozen 10-participant row-mean EEG representation and nuisance-adjusted RSA pipeline. This is secondary because ChineseEEG contributed to the broader development history.

No target-side representation, participant, item, model, layer, checkpoint or lambda selection is permitted.

## Estimands

For each positive lambda and each target, compute participant-level delta RSA relative to lambda=0, then report:

- mean and median delta;
- number and fraction of positive participants;
- participant-bootstrap 95% percentile CI with 10,000 resamples;
- exact paired sign-flip one-sided and two-sided p values;
- Holm-adjusted one-sided p values across the five positive-lambda contrasts within each target.

## Ordered trend

For each participant, regress delta RSA across the five positive lambdas on log10(lambda), using lambdas 0.01, 0.03, 0.10, 0.30 and 1.0. Summarize the participant slopes by mean, median, bootstrap 95% CI, fraction positive and exact sign-flip inference. Also report the descriptive Spearman association between log10(lambda) and the five target-level mean deltas.

The ordered-trend analysis asks whether stronger fMRI relational supervision is associated with systematically stronger EEG transfer. It is not a basis for selecting a new lambda.

## Interpretation guardrails

- The lambda=0.01 ZuCo result remains the primary frozen reverse-transfer result.
- All additional lambda results are exploratory/post-confirmatory.
- Do not choose or promote a new optimal lambda from EEG outcomes.
- A larger or more significant effect at another lambda is evidence about dose-response shape, not a rescued confirmatory result.
- Report every lambda regardless of sign or significance.
- Do not add new lambda values after seeing these results.
