# 19. Post-confirmatory bidirectional fMRI-to-EEG transfer: frozen primary test

**Status:** frozen before external EEG evaluation.

## Question

Does the multilingual-E5 representational perturbation selected using only held-out SMN4Lang fMRI source stories transfer to the independent ZuCo 2.0 normal-reading EEG target?

## Evidential status

This is a post-confirmatory secondary generalization experiment. It does not alter the status of the primary ChineseEEG-derived external-transfer chain.

## Frozen source candidate

The source-only calibration result is `outputs/nmi_bidirectional_fmri_calibration_v1/latest/summary.json`.

Required checks before ZuCo is read:

- `external_eeg_read` is `false`;
- `source_gate_pass` is `true`;
- selected lambda is exactly `0.01` under the prespecified one-standard-error rule;
- matched control is lambda `0.0` from the same calibration run and seed.

No alternative lambda, checkpoint, model, layer, pooling rule, or source story subset may be selected after ZuCo evaluation.

## Primary target

ZuCo 2.0 Task 1 normal reading, using the already frozen 17-participant cohort, seven runs, temporal-mean EEG representation, nuisance RDMs, participant aggregation, bootstrap interval, and exact sign-flip convention from the existing external-transfer pipeline.

## Primary estimand

For each participant:

`fMRI-guided selected-lambda residual RSA - matched lambda-0 residual RSA`

Report mean, median, fraction positive, participant bootstrap 95% interval, and exact directional sign-flip inference.

## Stopping rule

This job evaluates ZuCo only. ChineseEEG run-07 remains a secondary target and is not read in this primary test. It will be considered only after the primary ZuCo result is inspected.
