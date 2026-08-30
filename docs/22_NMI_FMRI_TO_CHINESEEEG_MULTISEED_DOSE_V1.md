# NMI post-confirmatory fMRI-to-ChineseEEG multi-seed dose robustness v1

## Status and purpose

This analysis is frozen after observing the single-seed ChineseEEG run-07 dose-response. It is therefore post-confirmatory robustness, not fresh confirmation. Its purpose is to test whether the directional fMRI-to-ChineseEEG dose-response is reproducible across independent optimization trajectories of multilingual E5.

## Fixed model and source

- Model: `intfloat/multilingual-e5-large`
- Revision: `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`
- Source geometry: previously frozen SMN4Lang fMRI relational target and the same fixed 20-story training / 12-story validation partition.
- Training architecture, LoRA configuration, text objective, fMRI relational objective, pooling, HRF construction, nuisance model, optimizer, learning rate, weight decay, epoch schedule, batch sizes and memory implementation are unchanged from `run_nmi_bidirectional_fmri_source_calibration_v1.py`.

## Frozen seeds and lambda grid

Additional optimization seeds are exactly:

- 20260829
- 20260830
- 20260831

For every seed, train and retain all six prespecified lambda arms:

`0, 0.01, 0.03, 0.10, 0.30, 1.0`

No lambda may be added, removed, retuned or selected using ChineseEEG outcomes.

## Target evaluation

Evaluate every retained arm on the already-frozen ChineseEEG run-07 representation and nuisance-adjusted RSA pipeline used in the preceding dose-response analysis. No target-side representation, participant, item, layer, checkpoint or nuisance search is permitted.

The existing development seed 20260823 may be included in the final descriptive aggregate only by reading its already-frozen dose-response outputs. The three new seeds are the primary added robustness trajectories.

## Primary robustness estimands

For each seed and each positive lambda versus lambda=0, report participant-level delta RSA, mean and median delta, number/fraction positive, participant-bootstrap 95% CI and exact paired sign-flip p-value.

For each seed, estimate the participant-level ordered slope of delta RSA against log10(lambda) over positive lambdas.

Across the three new seeds, report:

1. mean of seed-level mean delta at each lambda;
2. number of seeds with positive mean delta at each lambda;
3. mean of seed-level participant slope means;
4. number of seeds with positive slope mean;
5. the full seed-by-participant-by-lambda table without outcome-based exclusions.

A descriptive pooled analysis across seed-participant observations may be reported, but it must not be presented as if optimization seeds and human participants were exchangeable independent biological replicates.

## Interpretation guardrails

- This analysis cannot convert ChineseEEG run-07 into a fresh independent confirmation because its outcomes have already been observed.
- A reproducible positive trend across seeds supports optimization-seed robustness of the post-confirmatory ChineseEEG directional pattern.
- A heterogeneous or null trend is a boundary result and must be reported without rescue tuning.
- The previously frozen lambda=0.01 ZuCo reverse-transfer test remains the primary reverse-direction test.
- No new lambda search or ChineseEEG-informed model selection is permitted after this run.
