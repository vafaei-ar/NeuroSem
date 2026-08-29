# NMI second-round revision v0.7

Date: 2026-08-28

This note records the manuscript-only changes made after the second simulated Nature Machine Intelligence review. No new outcome-bearing analysis was performed.

## Changes applied

1. Title narrowed from “provides” to “can provide” a transferable relational constraint.
2. Replaced most “external biological transfer” language with the narrower “external neural transfer”.
3. Added foundational brain–language-model literature to distinguish prior neural predictivity, shared geometry and brain-tuning from NeuroSem’s fresh external-neural-transfer criterion.
4. Made the exploratory lambda=0.10 carry-forward rationale explicit: lambda=0.10 produced a larger held-out neural shift than lambda=0.03 while retaining a small observed STS decrement, whereas lambda=0.30 incurred a substantially larger semantic cost. The manuscript states that this was an outcome-informed development trade-off, not confirmatory optimization.
5. Corrected SMN4Lang fMRI wording to match the frozen implementation: within each story, retained fMRI timepoints are represented by LanA multivoxel patterns and converted to a correlation-distance RDM across timepoints; participant-level results aggregate the frozen story-wise geometries.
6. Added the inferential-scope limitation that participant-level tests generalize across individuals conditional on each dataset’s fixed stimulus set and do not constitute a separate random-effects test over arbitrary linguistic stimuli.
7. Tightened independence language so that complementary external tests are described as changing different dimensions (participants, language/task context, modality), rather than implying every dimension changes in every test.
8. Preserved the explicit model-family limitation: fresh external transfer was tested only for the frozen multilingual-E5 candidate.
9. Kept MEG as a reliability boundary with no model evaluation and AHBA as secondary Extended Data material.
10. Added five foundational references: Schrimpf et al. 2021; Caucheteux & King 2022; Goldstein et al. 2022; Goldstein et al. 2024; Schwartz et al. 2019.

## Guardrails

No new lambda, model family, model layer, checkpoint, neural representation, ROI, lag, sensor, frequency, stimulus subset, semantic benchmark or target dataset was selected or evaluated for this revision.
