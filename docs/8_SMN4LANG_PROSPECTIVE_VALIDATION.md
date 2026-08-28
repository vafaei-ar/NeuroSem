# SMN4Lang prospective cross-modal validation

**Status:** candidate selected before any SMN4Lang NeuroSem neural-model outcome

## Why this dataset

SMN4Lang (OpenNeuro `ds004078`; Wang et al., Scientific Data 2022; DOI `10.1038/s41597-022-01708-5`) is the preferred next external dataset because it can test a qualitatively new claim rather than adding another EEG replication.

The public descriptor reports:

- 12 native-Mandarin adults;
- the same participants measured with both fMRI and MEG;
- 60 naturalistic spoken Chinese stories, approximately six hours total;
- the same story set used in both modalities;
- word- and character-level onset/offset timing aligned to the audio;
- manually checked story transcripts and sentence segmentation;
- preprocessed fMRI in CIFTI surface and MNI volume spaces;
- preprocessed sensor-level MEG;
- fMRI TR = 0.710 s;
- 306-channel MEG sampled at 1000 Hz before preprocessing.

This dataset is therefore a potential test of whether semantic geometry learned from Chinese reading EEG generalizes across language task, laboratory, participants, acquisition system, and measurement modality to spatially resolved fMRI and, conditionally, MEG.

## Publication-level question

Primary conceptual question:

> Does the established NeuroSem semantic geometry, learned from Chinese reading EEG, generalize to independently measured cortical semantic geometry during naturalistic Chinese language comprehension in fMRI?

Conditional secondary question, attempted only if the fMRI arm is structurally feasible and scientifically informative:

> Is the same representational relationship detectable in MEG from the same people hearing the same stories, providing a bridge across EEG, MEG, and fMRI?

The purpose is not to search for another positive dataset. A clean null is retained and should end further external-dataset searching unless a separate, prospectively justified publication question emerges.

## Prospective sequence

1. **Metadata-only structural audit.** Inventory the exact OpenNeuro snapshot, participants, fMRI/MEG story runs, public transcripts, timing files, sentence boundaries, preprocessed derivatives, and approximate materialization costs. Do not load neural signals or any NeuroSem model.
2. **Freeze one fMRI semantic unit and one spatial representation.** The choice must be justified from acquisition/timing structure before any model comparison. Candidate constructions include sentence-level or fixed-duration HRF-aware windows; no window search is allowed after outcomes are exposed.
3. **Freeze nuisance structure.** At minimum control temporal separation and simple lexical/length structure that can be defined from public annotations without model outcomes. Additional motion/low-frequency controls may be included if dictated by the released preprocessing and fixed before reliability/model analysis.
4. **fMRI-only reliability gate.** Establish participant-level leave-one-participant-out neural-geometry reliability using all frozen participants and the frozen semantic/spatial representation. No embedding model is loaded.
5. **Single frozen model contrast.** Only if the fMRI reliability gate passes, evaluate the already established ChineseEEG-trained multilingual-E5 `lambda=0.10` neural-guided adapter against the matched `lambda=0` text-only adapter. No SMN4Lang tuning, layer search, lambda search, checkpoint search, ROI search, or semantic-unit search.
6. **Conditional MEG arm.** Consider MEG only after the fMRI analysis is complete and only with a separately frozen model-blind temporal representation and reliability gate. Do not use fMRI model outcomes to choose MEG latency, frequency band, sensor subset, or representation.

## Spatial-analysis guardrail

Do not select cortical regions based on the `lambda=0.10` versus `lambda=0` contrast.

Acceptable primary choices are either:

- a prespecified broad cortical surface representation; or
- an independently defined language/network mask from an external atlas or a model-blind neural reliability criterion frozen before model evaluation.

If spatial localization is reported after the primary test, it is secondary and must use appropriate multiple-comparison and spatial-autocorrelation control.

## Model guardrails

- Reuse the exact pinned multilingual-E5 model revision and completed ChineseEEG-trained adapters already used in TMNRED, ZuCo, Garnett Dream, Nature directional EEG, and DERCo.
- The sole confirmatory contrast is `lambda=0.10 - lambda=0`.
- Do not use the BERT/GPT2/Word2Vec features distributed with SMN4Lang to choose an ROI, temporal unit, HRF lag, E5 layer, or other analysis option.
- Do not train on SMN4Lang.
- Participant is the inferential unit.
- Preserve positive, null, or negative outcomes.

## Stop rules

Stop SMN4Lang before model evaluation if any of the following holds:

- exact story/text/timing identity cannot be recovered across participants;
- the released fMRI derivative cannot support a participant-comparable semantic item definition without substantial arbitrary deconvolution choices;
- the frozen fMRI neural representation fails its prospective reliability gate;
- materialization requirements are disproportionate to the scientific value.

After a completed frozen SMN4Lang fMRI test, do not search additional public datasets simply because the model contrast is null.

## Alternative datasets already screened

- **MOUS:** exceptionally large (204 Dutch participants with fMRI and MEG), but controlled sentence/scrambled-word trials and different MEG/fMRI stimulus subsets make it less directly aligned with the current naturalistic Chinese semantic-geometry question.
- **CRSF / ds004301:** 11 Mandarin participants and 672 repeated concepts provide excellent concept-level reliability, but each concept is paired with related pictures and the task is explicit concept thinking rather than naturalistic language comprehension.
- **Huth natural-language fMRI / Narratives:** scientifically strong naturalistic-language resources, but English auditory stimuli change language and modality simultaneously. They remain backups, not parallel confirmatory datasets.

The publication priority is therefore one rigorous SMN4Lang fMRI analysis, not broad dataset accumulation.
