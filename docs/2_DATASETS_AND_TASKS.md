# 2. Datasets and Tasks

**Last updated:** 2026-08-25

This document explains what each dataset contributes to NeuroSem, what participants were actually doing, and which scientific claim each dataset can test. This distinction is necessary because a null result from a different behavioral task is not equivalent to a null result from an independent replication of the same task.

## Dataset map

| Dataset | Participant task | Language | Recording | Current NeuroSem role | Status |
|---|---|---|---|---|---|
| ChineseEEG: Little Prince | Silent natural reading | Chinese | 128-channel EEG + eye tracking | Primary discovery and model-development dataset | Core analyses complete |
| ChineseEEG: Garnett Dream | Silent natural reading | Chinese | 128-channel EEG + eye tracking | Same-acquisition, different-text replication | Planned next core replication |
| TMNRED | Reading Chinese sentences | Chinese | EEG | Independent Chinese-reading replication | EEG reliability and E5 transfer complete |
| ZuCo 2.0 Task 1 NR | Normal reading of English sentences | English | EEG + eye tracking | Independent English-reading and cross-language replication | Structural/event audit complete; full-cohort QC next |
| Nature directional-word dataset | Overt/covert articulation of six directional concepts | Russian + Spanish | EEG; EMG subset | Out-of-task mechanistic/generalization test | Analyzed; not task-equivalent to reading |
| ChineseEEG-2 | Reading aloud / passive listening | Chinese | EEG + audio | Future cross-modal extension | Not yet part of the primary evidence chain |
| SIGNAL | Controlled sentence congruency/anomaly paradigm | Russian | EEG | Future semantic-specificity falsification dataset | Not yet analyzed |

## 2.1 ChineseEEG: Little Prince

### What participants did

Participants silently read Chinese text from *The Little Prince* while EEG and eye tracking were recorded.

### Why it is the discovery dataset

It provides:

- naturalistic language rather than isolated words;
- high-density EEG;
- multiple narrative runs;
- eye-tracking information for reading-related nuisance control;
- enough repeated structure to support cross-subject and held-out-run analysis.

### Current role

Little Prince has been used for:

- EEG representation selection;
- neural reliability analysis;
- BERT residual neural-semantic RSA;
- BERT neural-guided LoRA tuning;
- sealed run-07 neural holdout evaluation;
- multilingual-E5 architecture replication;
- neural-loss dose-response/Pareto exploration.

It should be described as **development/discovery**, not as an external validation dataset.

## 2.2 ChineseEEG: Garnett Dream

### What participants did

The same ChineseEEG dataset also contains silent reading of *Garnett Dream* under the same general acquisition family.

### Why it now matters

We initially focused on Little Prince. That left a major internal replication opportunity underused.

Garnett Dream is scientifically valuable because it changes the linguistic material while keeping many acquisition characteristics stable. It therefore tests whether the neural geometry and model-alignment effects depend on one particular narrative.

### Prospective role

Use Garnett Dream as a **different-text replication**, with analysis decisions frozen from the Little Prince work as much as possible.

It should be completed before making broad claims about cross-dataset generality.

## 2.3 TMNRED

### What participants did

Participants read Chinese sentences while EEG was recorded.

### Current frozen cohort

The model-blind materialization/QC process produced a frozen cohort of 29 participants across eight sessions. `sub-25` was excluded by the prospective data-quality rule; `sub-23` was retained with deterministic resampling where required.

The final item rule retained sentence items supported by at least 80% of participants within a session. Under that rule, all 50 sentence items were retained in every session.

### Why it is important

TMNRED is an independent Chinese reading dataset. Unlike the Nature directional dataset, the behavioral task remains reading/comprehension.

It therefore provides a stronger test of whether a reading-related EEG geometry replicates outside ChineseEEG.

### Analyses completed

- EEG-only representation reliability for the frozen temporal-mean primary representation.
- Sensitivity reliability for amplitude SD and an 8-bin temporal representation.
- Frozen ChineseEEG-to-TMNRED multilingual-E5 transfer test.
- Exploratory transfer tests using the SD and 8-bin TMNRED targets.

## 2.4 ZuCo 2.0 Task 1 Normal Reading

### What participants did

Participants normally read English sentences while EEG and eye tracking were recorded.

### Why it is the key next external dataset

ZuCo tests two things at once:

1. independent natural reading;
2. cross-language generalization from Chinese to English.

This makes it more informative for the main NeuroSem reading hypothesis than an imagined-speech or motor-language task.

### Current structural findings

The current target is ZuCo 2.0 Task 1 Normal Reading, with 18 participants and seven normal-reading runs per participant in the public inventory.

The representative EEG file is continuous, not epoched. The public probe established:

- 105 channels in the representative file;
- 500 Hz sampling;
- deterministic event latencies;
- 50 sentence units in NR1;
- 100 core sentence-boundary events = 50 ordered start/end pairs;
- 42 sentence pairs use trigger `10 -> 11`;
- 8 sentence pairs use trigger `12 -> 13`;
- trigger `15` is auxiliary after question-associated sentences;
- `90` and `20` behave as run-level start/end markers.

Thus sentence identity can be defined prospectively as run + sentence order, using event-pair boundaries.

### Next step

Full-cohort model-blind materialization/QC across all 18 participants x 7 runs, verifying that the same event rule holds before any EEG reliability result is examined.

## 2.5 Nature directional-word EEG dataset

### What participants did

Participants produced six directional concepts in overt and covert/inner-speech conditions. The NeuroSem primary analysis uses the covert/inner-speech condition.

### Why it is not directly comparable to reading

This task differs fundamentally from ChineseEEG, TMNRED, and ZuCo. It involves internally generating/articulating a small set of directional concepts rather than visually reading connected language.

That changes the likely mixture of neural processes. Covert articulation can include phonological rehearsal, speech-motor planning, internal generation, and task-specific control processes.

### Correct role

Treat this dataset as:

- an out-of-task generalization test;
- a mechanistic test of concept geometry;
- a secondary validation of whether any learned relational structure survives a substantial task shift.

Do **not** treat it as a task-matched external replication of reading-related EEG geometry.

## 2.6 ChineseEEG-2

ChineseEEG-2 extends the corpus family into reading-aloud and passive-listening conditions. It may later help test whether a geometry learned during reading transfers across language modalities.

Important limitation: reading-aloud and listening participants are different groups, so this is not a within-person modality comparison.

## 2.7 SIGNAL

SIGNAL contains controlled Russian sentence conditions with semantic and grammatical manipulations. Its main potential role is not broad external replication. It is a falsification/specificity dataset that can test whether NeuroSem effects track semantic structure rather than generic anomaly, syntax, surprisal, or task difficulty.

## Validation hierarchy

For the current paper, the clean evidence hierarchy should be:

1. **ChineseEEG Little Prince**: discovery/development.
2. **ChineseEEG Garnett Dream**: different-text replication under related acquisition.
3. **TMNRED**: independent Chinese reading replication.
4. **ZuCo 2.0 Task 1 NR**: independent English reading and cross-language replication.
5. **Nature directional**: secondary out-of-task generalization.

This hierarchy should guide interpretation. A negative result lower in the hierarchy cannot automatically overturn stronger task-matched evidence higher in the hierarchy.

## Dataset provenance

Detailed dataset publications, candidate rankings, and historical selection notes remain in `DATASETS.md`. This numbered document records the **current** roles after the analyses completed through 2026-08-25.
