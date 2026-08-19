# Candidate Neural-Language Datasets

This file tracks datasets that could support NeuroSem. Values below were checked against primary dataset publications on 2026-08-19. Analysis code should still verify downloaded file inventories, event structures, and licenses before use.

## Current ranking

| Dataset | Modality | Participants | Linguistic structure | Main NeuroSem role | Priority |
|---|---|---:|---|---|---|
| ChineseEEG | 128-channel EEG + eye tracking | 10 | Natural Chinese text from two novels; silent reading | Primary discovery dataset for natural-language neural geometry | **1** |
| ChineseEEG-2 | 128-channel EEG + audio | 12 total: 4 reading aloud, 8 passive listening | Same Chinese corpus family as ChineseEEG; token/sentence-aligned naturalistic language | Cross-modal replication and semantic-geometry transfer | **2** |
| SIGNAL | 64-channel EEG | 21 | 600 Russian sentences: congruent, semantic incongruent, grammatical incongruent, combined | Controlled semantic falsification / nuisance-control dataset | **3** |
| Directional-word dataset | 38-channel EEG; EMG subset | 22: 12 Russian, 10 Spanish | Six semantically matched direction concepts; overt and covert articulation | Clean cross-language relational-geometry validation | **4** |
| ZuCo | 128-channel EEG + eye tracking | 12 in original release | 1,107 English natural sentences, 21,629 words | Independent English natural-reading replication | **5** |
| Kymata Soto | simultaneous EEG + MEG | 35: 15 Russian, 20 English | ~7 min natural conversation, repeated 4x Russian / 8x English; word and phoneme timestamps | Cross-language and cross-modality speech replication | **6** |
| Chisco | EEG | 3 | 6,681 Chinese everyday sentences across 39 semantic categories; dense imagined speech | Dense within-subject semantic geometry | **7** |
| VocalMind | sEEG | clinical cohort | Vocalized, mimed, and imagined speech; word and sentence tasks | Invasive mechanistic validation | **8** |
| Pereira2018 / other fMRI language resources | fMRI | small cohorts | Sentence/concept stimuli | Independent recording-modality validation | Later |
| Fedorenko / other ECoG language resources | ECoG | small clinical cohorts | Word/sentence language tasks | Independent invasive validation | Later |

## Primary decision

### Discovery: ChineseEEG

ChineseEEG is the current primary discovery dataset. Its main advantages for NeuroSem are semantic richness, naturalistic language, multiple participants, high-density EEG, simultaneous eye tracking, and availability of both raw/preprocessed EEG and model-derived semantic representations. The eye-tracking stream is especially valuable because it provides word-level temporal anchoring and nuisance variables that can help separate semantic structure from fixation and reading-position effects.

Primary publication: Mou X, He C, Tan L, et al. *ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding.* Scientific Data. 2024;11:550. DOI: 10.1038/s41597-024-03398-7.

### Cross-modal replication: ChineseEEG-2

ChineseEEG-2 extends the same general corpus into reading-aloud and passive-listening conditions. It contains four reading-aloud participants with about 10.8 hours of EEG in total and eight passive-listening participants with about 21.6 hours in total. Raw EEG, text, audio, preprocessed EEG, and derived text/audio embeddings are distributed in a BIDS-oriented structure.

Important limitation: reading-aloud and passive-listening data come from different participant groups. Cross-modal tests are therefore population-level / representational transfer tests, not within-person modality comparisons.

Primary publication: *An EEG Dataset for Multimodal Semantic Alignment and Neural Decoding during Reading and Listening.* Scientific Data. 2026;13:148. DOI: 10.1038/s41597-025-06466-8.

### Controlled validation: SIGNAL

SIGNAL contains 600 Russian sentences formed as 150 matched groups with four conditions: congruent, semantically incongruent, grammatically incongruent, and semantic-plus-grammatical incongruent. EEG was collected from 21 native Russian speakers with 64 channels. The publication supplies lexical-semantic stimulus controls, target-word epochs, behavioral validation, EEG validation, and an LLM probing baseline.

This dataset is particularly valuable for testing whether NeuroSem detects semantic information specifically rather than generic surprisal, grammatical anomaly, sentence position, or target-word properties.

Primary publication: Komissarenko A, Voloshina E, Cheveleva A, et al. *SIGNAL: Dataset for Semantic and Inferred Grammar Neurological Analysis of Language.* Scientific Data. 2025;12:1687. DOI: 10.1038/s41597-025-05966-x.

### Cross-language validation: directional-word dataset

This dataset was published on 2026-08-17. It includes 22 healthy participants, 12 native Russian speakers and 10 native Spanish speakers, performing overt and covert articulation of six spatial-direction concepts. EEG was acquired from 38 electrodes at 500 Hz. The authors explicitly selected words for semantic equivalence rather than phonetic similarity.

This is scientifically useful for NeuroSem because the relational hypothesis can be tested across different surface forms. However, six shared concepts are far too few for broad semantic training, so this dataset should remain a validation dataset.

Critical caveat: four Russian participants used a modified marker protocol. Their trial segmentation differs from the standard protocol, so the first cross-language analysis should either exclude them or treat protocol as an explicit sensitivity stratum.

Primary publication: Kostulin DV, Shaposhnikov PD, Ekizyan AKh, et al. *EEG-based brain-computer interface (BCI) dataset for directional word recognition.* Scientific Data. 2026;13:1195. DOI: 10.1038/s41597-026-07809-9.

### Independent English replication: ZuCo

The original ZuCo release contains simultaneous EEG and eye-tracking data from 12 native English speakers reading 1,107 natural sentences containing 21,629 words. EEG was recorded with 128 channels at 500 Hz. Eye tracking provides fixation-derived word boundaries, making ZuCo useful for an independent English word-level replication and for explicit fixation-related nuisance modeling.

Primary publication: Hollenstein N, Rotsztejn J, Troendle M, et al. *ZuCo, a simultaneous EEG and eye-tracking resource for natural sentence reading.* Scientific Data. 2018;5:180291. DOI: 10.1038/sdata.2018.291.

### Natural speech replication: Kymata Soto

Kymata Soto contains simultaneous EEG and MEG from 15 native Russian and 20 native English speakers listening to approximately seven minutes of conversational speech. Each participant heard the same language-specific conversation repeatedly, four repetitions in Russian and eight in English. Word- and phoneme-level timestamp annotations are provided, and the dataset is BIDS-organized and CC-BY.

Its main value is not direct translation-level bilingual matching. The English and Russian groups hear different native-language material. It is therefore better suited to testing whether the same geometry-analysis framework generalizes across languages and EEG/MEG than to a strict translation-equivalence test.

Primary publication: Yang CT, Parish O, Klimovich-Gray A, et al. *Kymata Soto Language Dataset: an electro-magnetoencephalographic dataset for natural speech processing.* Scientific Data. 2026;13:254. DOI: 10.1038/s41597-026-06579-8.

### Dense imagined speech: Chisco

Chisco contains 6,681 Chinese everyday sentences assembled from social media and dialogue/story resources and grouped into 39 semantic categories. Only three participants contributed the neural recordings, so population inference is weak. The density of material makes it valuable for within-subject geometry and representation-learning experiments, not as the primary evidence for cross-subject generality.

Primary publication: *Chisco: An EEG-based BCI dataset for decoding of imagined speech.* Scientific Data. 2024. DOI: 10.1038/s41597-024-04114-1.

### Invasive validation: VocalMind

VocalMind provides original and processed stereotactic EEG across vocalized, mimed, and imagined speech, with word and sentence tasks. It is useful later as an invasive high-SNR test of whether semantic-relational effects observed with scalp EEG survive a different neural recording technology.

Primary publication: He T, Wei M, Wang R, et al. *VocalMind: A Stereotactic EEG Dataset for Vocalized, Mimed, and Imagined Speech in Tonal Language.* Scientific Data. 2025;12:657. DOI: 10.1038/s41597-025-04741-2.

## Selection principles

A useful dataset should provide as many of the following as possible:

1. stimulus-level correspondence between neural data and linguistic units;
2. enough semantic diversity to estimate a nontrivial representational geometry;
3. multiple participants for cross-subject validation;
4. raw or minimally processed neural data;
5. exact stimulus text and timing information;
6. metadata needed to construct nuisance representations;
7. licensing that permits reproducible academic analysis;
8. complementary task, language, or recording modality relative to the discovery dataset.

## Recommended sequence

1. **ChineseEEG**: primary go/no-go discovery analysis.
2. **SIGNAL**: controlled semantic-versus-grammar falsification analysis.
3. **ChineseEEG-2**: cross-modal replication using the same general corpus family.
4. **Directional Russian-Spanish dataset**: language-invariant concept-geometry test.
5. **ZuCo**: independent English natural-reading replication.
6. Add Kymata Soto, Chisco, or an invasive dataset only when they answer a specific unresolved question.

This sequence is deliberate. Loading every dataset at the start would increase engineering burden without strengthening the first inference. The first paper needs a small number of complementary datasets with distinct inferential roles, not a collection of unrelated benchmarks.

## Download-level audit still required

Before analysis of each selected dataset, verify from the actual distributed files:

- license file and redistribution restrictions;
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
