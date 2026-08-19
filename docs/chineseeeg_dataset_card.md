# ChineseEEG dataset card

## Identity

- **Dataset:** ChineseEEG
- **Primary publication:** Mou X, He C, Tan L, et al. *ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding.* Scientific Data. 2024;11:550.
- **DOI:** 10.1038/s41597-024-03398-7
- **OpenNeuro accession:** ds004952
- **Published OpenNeuro snapshot cited by the paper:** v1.2.0
- **OpenNeuro DOI:** 10.18112/openneuro.ds004952.v1.2.0
- **Alternative host:** Science Data Bank / CHNNeuro, DOI 10.57760/sciencedb.CHNNeuro.00007
- **Author code:** https://github.com/ncclabsustech/Chinese_reading_task_eeg_processing

## Why NeuroSem uses it first

ChineseEEG currently offers the strongest discovery setting for the first NeuroSem hypothesis. It combines a large natural-language stimulus space, multiple participants, high-density EEG, eye tracking, precise event markers, raw and minimally processed data, and the exact text materials. Unlike small command or imagined-speech datasets, it provides enough linguistic diversity to estimate nontrivial representational geometry. Unlike EEG-only corpora without gaze information, it also gives us an explicit measurement of reading behavior that can enter nuisance models.

## Participants and task

- 10 participants.
- Silent reading of Chinese text from *The Little Prince* and *Garnett Dream*.
- The published stimulus inventory contains 115,233 Chinese characters, 2,985 unique.
- Text was divided into runs and presentation units of no more than 10 Chinese characters.
- Participants followed highlighted text while EEG and eye tracking were recorded.
- One known acquisition exception is documented for sub-07, GarnettDream run 18: markers were lost and the participant repeated the task using chapter 19.

## Acquisition

### EEG

- 128-channel EGI GSN-HydroCel-128 montage.
- Acquisition sampling rate: 1,000 Hz.
- Raw source data were collected as EGI `.mff` and distributed in BIDS-compatible BrainVision form (`.vhdr`, `.vmrk`, `.eeg`) as well as through dataset derivatives.

### Eye tracking

- Tobii Pro Glasses 3.
- Maximum / used sampling rate reported as 100 Hz.
- Each experimental run has associated eye-tracking data.

## Published preprocessing

The paper describes a deliberately minimal pipeline:

1. segment formal reading periods using event markers;
2. retain an additional 10 s around formal reading to reduce edge effects;
3. downsample EEG from 1,000 Hz to 256 Hz;
4. apply 50 Hz notch filtering;
5. create 0.5-30 Hz and 0.5-80 Hz filtered derivatives;
6. detect bad channels with PyPREP plus manual review, then interpolate by spherical splines;
7. run Infomax ICA with 20 components and fixed seed 97;
8. automatically label components with `mne-iclabel` followed by manual inspection;
9. remove obvious ocular/cardiac noise components;
10. re-reference to average reference.

Author software versions reported in the publication include Python 3.10, MNE 1.6.0, PyPREP 0.4.3, mne-iclabel 0.5.1, MNE-BIDS 0.14, pybv 0.7.5, and transformers 4.36.2.

## Distributed structure relevant to NeuroSem

The dataset follows EEG-BIDS. It includes:

- participant metadata;
- raw EEG / BIDS EEG files;
- event TSV files;
- channel/electrode metadata;
- eye-tracking data;
- two filtered EEG derivatives (0.5-30 and 0.5-80 Hz);
- minimally preprocessed EEG;
- ICA component information;
- original and segmented novel text;
- precomputed text embeddings.

For NeuroSem, the author-provided text embeddings are a **replication baseline only**. The primary model representations must be regenerated from pinned models and tokenizers so layer-wise and model-wise comparisons are reproducible.

## Initial NeuroSem unit of analysis

Do not start at the full-sentence level. The first audit should determine the most defensible alignment unit from the event files and segmented text. Candidate units are:

1. highlighted presentation unit;
2. character/token;
3. word, after Chinese word segmentation;
4. sentence / line segment.

The unit should be selected before examining semantic RSA results. We should prefer the finest unit with reliable temporal alignment and sufficient repetitions / observations for stable RDM estimation.

## Required nuisance structure

At minimum, construct or measure:

- character/token identity;
- word/character frequency;
- character length / token count;
- sentence or presentation-unit position;
- run and session;
- time within run;
- fixation duration and gaze position;
- stimulus duration / presentation timing;
- orthographic similarity;
- local context / surprisal;
- temporal lag / autocorrelation structure.

Chinese-specific segmentation choices must be treated as a sensitivity analysis rather than hidden preprocessing.

## First reproducibility target

Before NeuroSem hypothesis testing, reproduce at least one dataset-validation result using the author preprocessing logic. A practical target is the paper's sensor-level time-frequency validation on a documented text segment, or another result that can be reproduced without source reconstruction.

## Known risks

1. Naturalistic sequential text has strong temporal autocorrelation and position structure. Random trial shuffling is invalid as the only null.
2. Text units are not independent because they occur in narrative context.
3. Chinese tokenization has no unique ground truth. Character-, word-, and contextual-unit analyses may differ.
4. Eye movements carry linguistic information and are also a confound. They should enter nuisance/variance-partitioning analyses rather than being ignored.
5. Precomputed semantic embeddings from the dataset authors cannot serve as the only semantic target.
6. Manual steps in bad-channel and ICA review limit exact automated reproduction. We should first reproduce the published derivative pipeline, then define an analysis-grade deterministic alternative if necessary.

## Go/no-go contribution

ChineseEEG supports H1 if semantic/model geometry explains held-out neural geometry after nuisance control and dependence-preserving inference, with reproducible effects across participants. Raw model-brain correlation alone does not satisfy the milestone.
