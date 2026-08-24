# Nature directional-word EEG external validation plan v1

Status: frozen before inspection of the distributed EEG files.

## Purpose

Use the Scientific Data 2026 directional-word EEG dataset as a genuinely independent neural validation dataset for NeuroSem.

Primary publication:
Kostulin DV, Shaposhnikov PD, Ekizyan AKh, et al. EEG-based brain-computer interface (BCI) dataset for directional word recognition. Scientific Data. 2026;13:1195. DOI: 10.1038/s41597-026-07809-9.

Data DOI: 10.5281/zenodo.20374418.

This dataset is not used for model training or lambda selection. It is reserved for external neural validation.

## Why this dataset matters

ChineseEEG established that NeuroSem can steer a model toward residual neural geometry within one natural-reading dataset. The directional-word dataset gives a harder test because it differs in participants, laboratory, task, electrode montage, language, and stimulus format.

The dataset contains 22 participants:
- 12 native Russian speakers;
- 10 native Spanish speakers;
- overt and covert articulation;
- six shared spatial-direction concepts: up, down, left, right, forward, backward;
- 38-channel EEG at 500 Hz.

The six concepts are semantically matched across Russian and Spanish but differ in surface form and phonology. This makes the dataset useful for asking whether NeuroSem captures concept-level neural geometry that generalizes across languages.

## Primary question

Does the prespecified low-dose E5 NeuroSem model selected from the exploratory ChineseEEG Pareto analysis show better alignment with independent covert-speech EEG concept geometry than the matched text-only E5 model?

Primary model contrast:
- E5 lambda = 0.10 versus E5 lambda = 0.00 text-only.

The lambda = 0.10 candidate is frozen before this external EEG dataset is inspected. It was selected because it showed a measurable neural-alignment increase in ChineseEEG with only a small external STS cost. The Nature dataset is therefore a fresh neural target for this candidate.

Secondary model comparisons:
- lambda = 1.00 versus lambda = 0.00;
- frozen untuned E5 base where technically available.

No new lambda values will be added based on the Nature-data results.

## Primary condition and population

Primary condition: covert / inner articulation.

Reason: overt speech has larger articulatory and EMG contamination. Overt speech is retained as a secondary sensitivity comparison, not the primary endpoint.

Primary participants: standard-marker-protocol participants only.

The publication identifies four Russian participants with a modified marker protocol: sub1, sub3, sub5, and sub10. They are excluded from the primary analysis and retained for a separate sensitivity analysis if the distributed files support unambiguous harmonization.

Expected primary sample before file audit:
- 8 Russian standard-protocol participants;
- 10 Spanish participants;
- total 18 participants.

## Important confounds

The dataset has several known design features that must not be ignored:
- self-initiated right-hand keypress can contaminate approximately the first 0-200 ms after the marker;
- overt articulation can contain strong speech-muscle activity;
- covert articulation can still include weak subvocal EMG;
- Russian and Spanish words differ in phonology and syllable count;
- stimulus order was predominantly fixed;
- only six shared concepts are available, so the representational geometry contains only 15 unique concept pairs.

Because of the small semantic inventory, this dataset is a validation/control dataset, not a training dataset.

## Stage 0: data audit before any model comparison

The first execution stage is strictly structural and quality-control oriented.

It will:
- download the pinned Zenodo record;
- verify the published MD5 checksum;
- inventory raw and preprocessed files;
- verify participant counts and language folders;
- inspect MNE Epochs metadata without computing semantic RSA;
- inspect event-file dimensions and label structure;
- identify standard versus modified marker-protocol participants;
- record sampling rate, channels, epoch duration, event IDs, and trial counts;
- write safe derived audit summaries only.

The audit must not:
- load any NeuroSem model adapter;
- compute model embeddings;
- compute neural-model RSA;
- inspect whether lambda = 0.10 performs better or worse than any control.

This preserves the Nature dataset as a fresh external neural test while we verify the actual distributed structure.

## Stage 1: freeze exact neural representation after audit

After the structural audit, and before any model embedding is compared with EEG, freeze:
- exact trial-to-concept label mapping;
- exact post-marker time window, with the primary analysis excluding the early keypress-contaminated interval when supported by the event structure;
- exact EEG feature representation;
- trial aggregation rule within participant and concept;
- nuisance variables and sensitivity analyses;
- exact inference procedure.

Candidate neural representations may be compared only by neural reliability, never by correspondence with model embeddings. Any feature selection must therefore use EEG-only reproducibility criteria.

## Intended external-validation logic

For each language and participant:
1. estimate one neural representation per shared concept from covert-speech trials;
2. construct the six-concept neural representational dissimilarity matrix;
3. construct the corresponding six-concept model RDM using the exact Russian or Spanish stimulus words;
4. compare neural and model RDMs using a rank-based relational statistic;
5. compare lambda = 0.10 against lambda = 0.00 at the participant level;
6. aggregate the model contrast across participants with an exact or dependence-preserving subject-level test appropriate to the audited structure.

Cross-language consistency is central: a useful result should not depend only on one language group.

## Interpretation rules

A positive result would mean that a low-dose NeuroSem model chosen without using this dataset aligns better with independent neural concept geometry than matched text-only tuning. This would support cross-dataset and cross-language neural generalization.

A null result would mean the ChineseEEG steering effect does not clearly generalize to this very different six-concept inner-speech setting.

A negative result would argue against broad neural-geometry transfer for the current objective.

None of these outcomes, by itself, establishes improved general semantic behavior. The Nature dataset is an external neural validation, not a replacement for semantic benchmarks.

## No post-hoc rescue

Do not:
- search extra lambda values on this dataset;
- choose a time window because it favors lambda = 0.10;
- choose an EEG feature because it improves neural-model alignment;
- drop participants based on model-alignment results;
- report overt speech as primary if covert speech is unfavorable.

Any follow-up choices motivated by these results must be labeled exploratory and tested on another fresh target.
