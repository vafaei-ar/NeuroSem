# Nature-facing analysis gap review

**Updated:** 2026-08-28

## Decision summary

The current NeuroSem evidence is sufficient to support the main scientific claim without adding another external dataset or reopening model/representation search. The manuscript already contains: a reproducible development neural geometry; sealed neural-guided learning; positive cross-language EEG transfer in ZuCo; positive prospective cross-modal fMRI transfer in SMN4Lang; multiple null/inconclusive boundary conditions; and a generic-semantic non-advantage that constrains interpretation.

No additional analysis is required to rescue the paper.

There is, however, one prospectively justified analysis that could materially strengthen a Nature-level multimodal claim: the conditional SMN4Lang MEG arm already specified in `docs/8_SMN4LANG_PROSPECTIVE_VALIDATION.md` before the fMRI NeuroSem model outcome.

## Highest-value optional analysis: SMN4Lang MEG

### Why it is scientifically valuable

SMN4Lang measured the same 12 participants hearing the same 60 stories with both fMRI and MEG. A successful frozen MEG analysis would connect:

- Chinese natural-reading EEG used to derive/train the neural constraint;
- independent sensor-level MEG from the same SMN4Lang participants and stories as the fMRI validation;
- independent language-network fMRI in those participants.

This would provide an EEG -> MEG -> fMRI multimodal bridge rather than another dataset replication.

### Why it is not post-hoc rescue

The MEG arm was written into the prospective SMN4Lang protocol before the fMRI model result. The protocol stated that MEG would be considered only after the fMRI arm was structurally feasible and scientifically informative, and required a separately frozen model-blind temporal representation and reliability gate.

The positive fMRI result therefore satisfies the prospectively documented condition for considering MEG.

### Required sequence

1. **Model-blind MEG structural/timebase audit.** Verify all 12 participants x 60 stories, preprocessed sensor data, timing identity, sample rate, bad-channel handling, and participant-comparable timebase. Do not load NeuroSem models.
2. **Freeze one MEG representation before model outcomes.** Choose a single temporal/sensor construction from acquisition and reliability considerations only. Do not use the fMRI model contrast to select latency, frequency band, sensor subset, temporal pooling, source reconstruction, or dimensionality reduction.
3. **MEG-only reliability gate.** Participant-level leave-one-participant-out neural-geometry reliability across the frozen stories/representation.
4. **Single frozen model test only if reliability passes.** Compare the established ChineseEEG-trained multilingual-E5 lambda=0.10 neural-guided adapter against the matched lambda=0 text-only adapter. No SMN4Lang training or model/layer/lambda/checkpoint search.
5. **Participant-level inference.** Preserve the participant as the inferential unit and report the same paired delta, bootstrap interval, and exact sign-flip framework where applicable.
6. **Stop after the frozen result.** Positive, null, or negative outcomes are retained. Do not rescue a null MEG result with latency/frequency/sensor searches.

### Publication value of possible outcomes

- **Reliable MEG + positive frozen transfer:** major strengthening. The main paper can claim that the learned neural constraint generalizes across independent brains and across all three major non-invasive measurement families represented here: EEG, MEG, and fMRI.
- **Reliable MEG + null/negative frozen transfer:** scientifically useful boundary. Keep SMN4Lang fMRI as the capstone and use MEG to show that transfer depends on measurement/task geometry rather than being universal.
- **MEG reliability failure:** stop before model evaluation. Report only as a feasibility/reliability limitation, not as evidence against the model.

## Analyses not recommended

### Additional public neural datasets

Do not add Huth, Narratives, MOUS, CRSF, or another EEG dataset simply to increase the count of positive tests. The prospective SMN4Lang protocol explicitly prioritized one rigorous cross-modal validation over broad dataset accumulation.

### Additional lambda/model/layer/checkpoint searches

Do not reopen lambda, architecture, pooling, layer, checkpoint, prompt, or embedding-model search using ZuCo or SMN4Lang outcomes. The strongest claim depends on carrying an already established frozen model into external neural data.

### Post-hoc fMRI ROI or HRF optimization

Do not search alternative language ROIs, atlas thresholds, HRF lags, temporal windows, or semantic units after observing the positive SMN4Lang result. The independently defined LanA analysis should remain the primary cross-modal result.

### Result-driven negative controls

Do not add arbitrary shuffled models, alternative adapters, or newly invented control families solely because the primary result is positive. Controls that were already part of model development can be shown where relevant, but new outcome-driven controls should be labelled exploratory and are not needed for the primary claim.

### Cross-dataset pooled meta-analysis of raw RSA deltas

Do not pool raw RSA deltas across EEG and fMRI as though they share a common measurement scale. A qualitative/generalization matrix and dataset-specific paired effects are more defensible.

## High-value work that is not a new scientific test

These should proceed regardless of whether MEG is attempted:

1. Build the four main figures specified in `paper/NATURE_SUBMISSION_PACKAGE.md` and `paper/FIGURE_TABLE_PLAN.md`.
2. Produce a compact independence table showing, for each validation dataset, independence of participants, language, text, task, acquisition site, modality, and target-dataset tuning.
3. Produce a provenance table linking every primary numerical claim to the exact RunRelay job, NeuroSem commit, and Drive artifact.
4. Show participant-level paired effects for ZuCo and SMN4Lang, not only group means/p-values.
5. Show SMN4Lang story-level effects descriptively in Extended Data while retaining participant as the inferential unit.
6. Keep effect-size language explicit: the SMN4Lang fMRI gain is small in absolute RSA units but highly directionally consistent.
7. Keep all major null/inconclusive transfer datasets visible to support the selective-generalization interpretation.

## Current scientific stopping rule

Without MEG, the core manuscript is already complete enough to write and submit. If MEG is pursued, it should be the final outcome-bearing external neural analysis for this paper. No additional dataset/model search should follow its result.
