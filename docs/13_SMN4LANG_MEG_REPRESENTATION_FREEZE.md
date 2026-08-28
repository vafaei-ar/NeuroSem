# SMN4Lang MEG representation freeze

Status: **frozen before any MEG reliability or model outcome**

Date: 2026-08-28

## Purpose

The SMN4Lang MEG analysis is the final prospective external outcome-bearing analysis for the current manuscript. It asks whether the transferable language-related neural geometry already supported by independent EEG and fMRI can also be detected in MEG from the same 12 SMN4Lang participants and 60 spoken Mandarin stories.

This document freezes the MEG representation and reliability gate before any MEG reliability value or model comparison is computed.

## Evidence available at freeze

The deterministic representative released preprocessed FIF was materialized from the public OpenNeuro S3 mirror and verified against its git-annex MD5. It contains 306 MEG sensors: 204 planar gradiometers and 102 magnetometers. Sampling rate is 1000 Hz. Released preprocessing is 1-40 Hz. The representative contains no bad MEG channels, has device-to-head transform metadata, and was inspected with `preload=False`. No MEG reliability or model outcome has been computed.

## Primary participant-comparable representation

The primary representation is intentionally sensor-order/position robust and uses the full released MEG bandwidth and all retained MEG sensors.

For every participant and story/run:

1. Use the released preprocessed 1-40 Hz MEG FIF without additional frequency filtering.
2. Exclude samples covered by released annotations whose description begins with `bad`, using the released artifact annotation only.
3. Divide the full valid run duration into 32 equal normalized-time bins. The bins are defined by relative run progress, not by linguistic or model information.
4. Within each bin, compute one root-mean-square field magnitude over all retained magnetometer samples and one root-mean-square field magnitude over all retained planar-gradiometer samples. Do not select individual sensors.
5. This yields 32 magnetometer values plus 32 gradiometer values, a fixed 64-dimensional run vector.
6. Within each channel type separately, z-score the 32 bin values across time bins. This removes arbitrary absolute scale between channel types and participants while retaining within-story temporal shape.
7. Concatenate the two standardized 32-bin vectors in fixed order: magnetometers, then planar gradiometers.
8. Compute the 60 x 60 story RDM within each participant using correlation distance between the 64-dimensional story vectors.

No alternative number of bins, sensor subset, frequency band, source reconstruction, latency window, or feature family will be searched after outcomes are observed.

## Why this representation is frozen

Individual sensor amplitudes are not directly homologous across participants because head position relative to the device differs, even when the acquisition system and channel naming are shared. A channel-type global RMS summary is invariant to sensor ordering and does not require source localization, sensor matching, anatomical ROI selection, or fMRI-informed choices. Separating magnetometers and planar gradiometers respects their different physical units and sensitivity profiles. Normalized-time binning provides a fixed-dimensional story representation without selecting event latencies or frequency bands.

The 32-bin choice is fixed prospectively as a broad low-dimensional summary: it preserves coarse temporal evolution across several-minute stories while avoiding a high-dimensional time-point representation. It will not be tuned.

## Structural readiness check before reliability

Before loading the full MEG cohort for reliability, a model-blind cross-participant format probe must verify:

- exactly 12 participants are represented;
- the same 60 task-RDR run identities are available for every participant;
- each participant has at least one verified representative preprocessed FIF that can be materialized from the public mirror;
- representative files use the expected MEG channel types and compatible sampling/preprocessing metadata;
- no model quantities are loaded.

A failure of these structural conditions stops the MEG analysis until the structural issue is resolved without reference to neural-model outcomes.

## Reliability gate

After structural readiness passes, compute participant-level leave-one-participant-out reliability of the frozen story RDM.

For participant `i`:

1. Vectorize the upper triangle of that participant's 60 x 60 RDM.
2. Compute the edgewise mean RDM vector over the other 11 participants.
3. Compute Spearman correlation between participant `i` and the leave-one-out group mean.

The inferential unit is the participant (`n=12`). Report mean, median, all participant values, the number positive, a participant bootstrap 95% confidence interval for the mean, and an exact one-sided sign-flip test of the mean against zero.

The reliability gate passes only if all structural criteria pass, the mean leave-one-out reliability is positive, the 95% participant-bootstrap confidence interval lies entirely above zero, and the exact one-sided sign-flip p-value is <0.05.

If the reliability gate fails, stop before any E5 model evaluation. Do not rescue the result by changing bins, bands, sensors, source space, latency windows, preprocessing, or representation family.

## Conditional model test after a passed gate

Only after the frozen MEG reliability gate passes, run one confirmatory E5 contrast:

- model: `intfloat/multilingual-e5-large`;
- pinned revision: `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`;
- neural-guided condition: lambda 0.10;
- text-only condition: lambda 0;
- no SMN4Lang training or tuning;
- no model, layer, checkpoint, prompt, pooling, lambda, sensor, frequency, latency, or source-space search;
- participant is the inferential unit.

A reliable MEG geometry with null or negative lambda 0.10 minus lambda 0 transfer is a boundary result and will not be rescued by post-hoc analysis changes.
