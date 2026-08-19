# Candidate Neural-Language Datasets

This file tracks datasets that could support NeuroSem. The ranking is provisional and should be updated after access, licensing, stimulus structure, synchronization, and preprocessing are verified directly from source documentation.

| Dataset | Modality | Approx. subjects | Linguistic structure | Main role in NeuroSem | Current priority |
|---|---|---:|---|---|---|
| ChineseEEG / ChineseEEG-2 | EEG | 10 + 12 | Natural Chinese narrative across reading, reading aloud, and listening variants | Primary natural-language geometry; cross-modality tests | High |
| Chisco | EEG | 3 | Dense imagined-speech phrases/sentences across semantic categories | Dense within-subject semantic geometry | High |
| SIGNAL | EEG | 21 | Controlled sentences with semantic/grammatical manipulations | Controlled semantic falsification experiment | High |
| Russian-Spanish directional concepts | EEG/EMG | 22 | Six matched directional concepts, overt/covert, two languages | Clean cross-language validation | High for validation |
| ZuCo | EEG + eye tracking | multiple releases | English natural reading | Independent English replication | Medium-high |
| Kymata Soto | EEG/MEG | ~35 | Continuous language/conversation stimuli | Cross-modality replication | Medium |
| Pereira2018 | fMRI | small cohort | Hundreds of sentence stimuli | Independent modality validation | Medium |
| Fedorenko language ECoG resources | ECoG | small clinical cohorts | Word/sentence language tasks | Mechanistic invasive validation | Medium |
| VocalMind / related speech sEEG resources | sEEG | small clinical cohorts | Overt/mimed/imagined speech | Mechanistic validation | Medium |

## Selection principles

A useful dataset should provide as many of the following as possible:

1. trial- or stimulus-level correspondence between neural data and linguistic units;
2. enough semantic diversity to estimate a nontrivial representational geometry;
3. multiple participants for cross-subject validation;
4. available raw or minimally processed neural data;
5. exact stimulus text and timing information;
6. metadata needed to construct nuisance representations;
7. licensing that permits reproducible academic analysis;
8. complementary task, language, or recording modality relative to the primary dataset.

## Proposed initial dataset roles

### Primary discovery dataset

Use a natural-language EEG resource with rich stimuli and multiple participants. ChineseEEG / ChineseEEG-2 is the leading candidate pending direct technical audit.

### Controlled validation dataset

Use SIGNAL or a comparable controlled semantic-anomaly dataset to test whether apparent semantic alignment survives lexical, syntactic, difficulty, and timing controls.

### Cross-language validation

Use the Russian-Spanish directional-concept dataset. Its small vocabulary prevents broad semantic training, but its matched meanings and different surface forms provide a clean test of language-invariant relational geometry.

### Dense imagined-speech analysis

Use Chisco for high-trial-count within-subject analyses and semantic-category structure. The small number of participants limits population-level claims.

## Required audit before analysis

For every selected dataset, record:

- official citation and permanent identifier;
- license and access requirements;
- number of participants and exclusions;
- channels, sampling rate, reference, and montage;
- preprocessing already applied;
- event markers and synchronization quality;
- exact number and type of linguistic stimuli;
- repetitions per stimulus;
- language and task condition;
- subject/session structure;
- known artifacts or caveats;
- storage size and expected compute requirement.

Do not treat the values in the provisional table above as analysis metadata until verified from the primary dataset documentation.
