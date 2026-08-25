# Candidate Neural-Language Datasets

**Last updated:** 2026-08-25

This file tracks datasets that support or may support NeuroSem. Dataset roles have been updated after the ChineseEEG, TMNRED, Nature directional, and ZuCo 2.0 work completed through 2026-08-25.

For the current paper-facing interpretation, read [`docs/2_DATASETS_AND_TASKS.md`](docs/2_DATASETS_AND_TASKS.md) first. The key methodological change is that datasets are now ranked by **task comparability and inferential role**, not only by size or semantic appeal.

## Current core evidence hierarchy

| Dataset / subset | Modality | Participants | Participant task | Current NeuroSem role | Priority |
|---|---|---:|---|---|---|
| ChineseEEG: Little Prince | 128-channel EEG + eye tracking | 10 | Silent natural Chinese reading | Discovery, representation selection, neural/model development | **1** |
| ChineseEEG: Garnett Dream | 128-channel EEG + eye tracking | same ChineseEEG cohort family | Silent natural Chinese reading of a different novel | Same-acquisition, different-text replication | **2** |
| TMNRED | EEG | 30 available; 29 frozen for current analysis | Chinese sentence reading | Independent Chinese-reading EEG replication and external model-transfer test | **3** |
| ZuCo 2.0 Task 1 NR | EEG + eye tracking | 18 in current public inventory | English normal reading | Independent English-reading and cross-language replication | **4** |
| Directional-word dataset | 38-channel EEG; EMG subset | 22 | Overt/covert articulation of six directions | Secondary out-of-task / inner-speech generalization | **5** |
| ChineseEEG-2 | 128-channel EEG + audio | 12 total | Reading aloud or passive listening | Future cross-modal extension | Later |
| SIGNAL | 64-channel EEG | 21 | Controlled sentence congruency/anomaly task | Future semantic-specificity falsification | Later |
| Kymata Soto | EEG + MEG | 35 | Natural speech listening | Future speech/cross-modality replication | Later |
| Chisco | EEG | 3 | Imagined speech | Dense within-subject geometry | Later |
| VocalMind | sEEG | clinical cohort | Vocalized, mimed, imagined speech | Invasive mechanistic validation | Later |
| Pereira2018 / other fMRI language resources | fMRI | small cohorts | Sentence/concept processing | Independent recording-modality validation | Later |
| Fedorenko / other ECoG resources | ECoG | clinical cohorts | Word/sentence language tasks | Independent invasive validation | Later |

## Primary discovery: ChineseEEG Little Prince

ChineseEEG is the primary discovery resource. The project has so far used the *Little Prince* runs for the main neural-reliability, BERT correspondence, BERT tuning, E5 replication, and sealed run-07 analyses.

Advantages:

- naturalistic Chinese language;
- high-density EEG;
- simultaneous eye tracking;
- repeated narrative runs;
- enough structure for cross-subject and held-out-run analysis;
- nuisance variables related to reading position and timing.

Primary publication: Mou X, He C, Tan L, et al. *ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding.* Scientific Data. 2024;11:550. DOI: 10.1038/s41597-024-03398-7.

## High-priority internal replication: ChineseEEG Garnett Dream

ChineseEEG contains a second novel, *Garnett Dream*, in addition to *The Little Prince*. This provides an important replication opportunity that was underused in the initial work.

Scientific role:

- hold acquisition family relatively stable;
- change the linguistic material substantially;
- test whether the selected neural geometry and neural/model correspondence depend on one narrative;
- provide a different-text replication before broad cross-dataset claims.

The intended analysis should freeze the Little Prince representation, nuisance, and RSA decisions before examining Garnett Dream results.

## Independent Chinese-reading replication: TMNRED

TMNRED is now a core external dataset rather than merely a candidate.

The model-blind workflow established a frozen cohort of 29 participants across eight sessions, with 50 high-coverage sentence items retained in every session under the prospective >=80% participant-coverage rule.

Completed roles:

- independent EEG-only reliability of the ChineseEEG-selected temporal-mean representation;
- sensitivity reliability for amplitude SD and an 8-bin temporal representation;
- frozen ChineseEEG-trained E5 transfer test;
- exploratory transfer tests to the two sensitivity EEG representations.

Key interpretation: the EEG geometry itself replicates modestly in independent Chinese reading, but the ChineseEEG-trained neural-guided E5 advantage does not transfer detectably.

## Independent English-reading replication: ZuCo 2.0 Task 1 Normal Reading

ZuCo is now the key cross-language reading dataset.

The current target is ZuCo 2.0 Task 1 Normal Reading because the public inventory supports 18 participants with seven normal-reading EEG runs each, stronger for the intended cross-subject reliability analysis than the original ZuCo 1.0 cohort.

Current structural findings from the representative-file probe:

- continuous EEG rather than pre-epoched sentence trials;
- representative file: 105 channels, 500 Hz;
- 50 sentence units in NR1;
- 100 core sentence-boundary events = 50 ordered start/end pairs;
- 42 pairs use `10 -> 11`;
- 8 pairs use `12 -> 13`;
- trigger `15` is auxiliary after question-associated sentences;
- `90` and `20` act as run-level markers.

This gives a prospective sentence-extraction rule: sentence identity = run + sentence order, with sentence windows delimited by the two allowed event-pair types.

No EEG reliability or model-transfer result should be claimed until full-cohort materialization/QC completes.

Relevant publication family: Hollenstein N, Rotsztejn J, Troendle M, et al. *ZuCo, a simultaneous EEG and eye-tracking resource for natural sentence reading.* Scientific Data. 2018;5:180291. DOI: 10.1038/sdata.2018.291.

## Directional Russian-Spanish EEG dataset: out-of-task validation

This dataset contains 22 healthy participants, 12 Russian and 10 Spanish speakers, performing overt and covert articulation of six spatial-direction concepts. EEG was acquired from 38 electrodes at 500 Hz.

Primary publication: Kostulin DV, Shaposhnikov PD, Ekizyan AKh, et al. *EEG-based brain-computer interface (BCI) dataset for directional word recognition.* Scientific Data. 2026;13:1195. DOI: 10.1038/s41597-026-07809-9.

### Updated interpretation

Earlier project notes described this as a clean cross-language validation dataset. That framing is now too strong.

The primary NeuroSem condition is covert/inner speech. This is **not task-equivalent** to the reading paradigms in ChineseEEG, TMNRED, or ZuCo. Covert articulation can involve internal generation, phonological rehearsal, and speech-motor planning in addition to semantics.

Therefore this dataset should be used as:

- a secondary out-of-task generalization test;
- a mechanistic concept-geometry test;
- evidence about robustness to a major task shift.

A null result here should not be treated as a direct falsification of reading-related semantic geometry.

Critical caveat retained from the original dataset audit: four Russian participants used a modified marker protocol and should be excluded from the first strict cross-language comparison or treated as a protocol sensitivity stratum.

## ChineseEEG-2: future cross-modal extension

ChineseEEG-2 extends the corpus family into reading-aloud and passive-listening conditions. It contains four reading-aloud participants and eight passive-listening participants.

Important limitation: the modalities are recorded in different participant groups, so this supports population-level representational transfer rather than within-person modality comparison.

Primary publication: *An EEG Dataset for Multimodal Semantic Alignment and Neural Decoding during Reading and Listening.* Scientific Data. 2026;13:148. DOI: 10.1038/s41597-025-06466-8.

## SIGNAL: future controlled specificity test

SIGNAL contains 600 Russian sentences organized into congruent, semantically incongruent, grammatically incongruent, and combined conditions.

Its strongest role is a falsification/specificity test: whether NeuroSem effects track semantic structure rather than generic anomaly, syntax, surprisal, sentence position, or target-word properties.

Primary publication: Komissarenko A, Voloshina E, Cheveleva A, et al. *SIGNAL: Dataset for Semantic and Inferred Grammar Neurological Analysis of Language.* Scientific Data. 2025;12:1687. DOI: 10.1038/s41597-025-05966-x.

## Kymata Soto

Kymata Soto contains simultaneous EEG and MEG from Russian- and English-speaking groups listening to natural conversational speech.

Its main value is future cross-language and cross-modality speech replication, not strict translation-level bilingual matching because the language groups hear different native-language material.

Primary publication: Yang CT, Parish O, Klimovich-Gray A, et al. *Kymata Soto Language Dataset: an electro-magnetoencephalographic dataset for natural speech processing.* Scientific Data. 2026;13:254. DOI: 10.1038/s41597-026-06579-8.

## Chisco

Chisco contains 6,681 Chinese everyday sentences across 39 semantic categories with only three participants.

Its density makes it useful for within-subject geometry or representation-learning experiments, but the small neural cohort makes it weak for population-level generalization.

Primary publication: *Chisco: An EEG-based BCI dataset for decoding of imagined speech.* Scientific Data. 2024. DOI: 10.1038/s41597-024-04114-1.

## VocalMind

VocalMind provides stereotactic EEG for vocalized, mimed, and imagined speech, including word and sentence tasks.

It remains a possible later invasive/high-SNR validation if the project reaches a question that specifically requires a different neural recording technology.

Primary publication: He T, Wei M, Wang R, et al. *VocalMind: A Stereotactic EEG Dataset for Vocalized, Mimed, and Imagined Speech in Tonal Language.* Scientific Data. 2025;12:657. DOI: 10.1038/s41597-025-04741-2.

## Selection principles

A dataset should be added only when it answers a specific unresolved question. Priority criteria are:

1. task comparability to the hypothesis being tested;
2. stimulus-level neural-language correspondence;
3. enough semantic diversity for a nontrivial geometry;
4. multiple participants for cross-subject validation;
5. raw or minimally processed neural data;
6. exact stimulus text and timing information;
7. nuisance metadata;
8. licensing and reproducibility;
9. complementary language, task, or modality only when that complement has a clear inferential purpose.

## Current recommended sequence

1. ChineseEEG Little Prince: completed discovery/development evidence.
2. ChineseEEG Garnett Dream: different-text replication.
3. TMNRED: completed independent Chinese-reading EEG replication; model transfer null.
4. ZuCo 2.0 Task 1 NR: current independent English-reading replication.
5. Nature directional: retain as secondary out-of-task evidence.
6. Add SIGNAL, ChineseEEG-2, Kymata Soto, Chisco, or invasive datasets only if the results above leave a specific unresolved question.

The first paper needs a coherent evidence chain, not a large collection of unrelated neural-language datasets.

## Download-level audit requirement

Before analysis of any newly selected dataset, verify from the distributed files:

- license and redistribution restrictions;
- checksums / complete file inventory;
- subject exclusions;
- channel names and montage;
- exact event-marker semantics;
- stimulus identifiers and text normalization;
- repetitions per stimulus;
- session/block structure;
- missing or corrupt files;
- preprocessing provenance;
- storage and compute requirements.
