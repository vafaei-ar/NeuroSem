# NeuroSem cross-dataset EEG validation protocol v1

Status: prospectively frozen before inspecting TMNRED neural-model alignment.

## Publication target and scientific objective

Primary target: Nature Machine Intelligence. Secondary target: Nature Neuroscience.

The central question is whether a model-blind, reproducible human EEG representational geometry can be identified in ChineseEEG, reproduced in independent EEG datasets, and then used as a transferable supervision signal for language models.

This protocol separates neural-representation validation from model validation. External EEG datasets must not be used to tune the language model before their neural representation properties are characterized and frozen.

## Dataset roles

1. ChineseEEG (OpenNeuro ds004952): development dataset. Representation development, internal run-06 selection, run-07 holdout, and model development occur here.
2. TMNRED (OpenNeuro ds005383, published snapshot v1.0.0): first prospective independent neural-representation validation dataset. No model-based feature selection is allowed.
3. ZuCo / ZuCo 2.0: planned cross-language natural-reading validation after TMNRED, subject to a separate structural audit and feasibility freeze.
4. Nature directional-word EEG: previously observed hard external stress test. It remains a boundary-condition dataset and must not be used retrospectively to tune representations or model hyperparameters.

ChineseEEG-2 may later be used as a modality-generalization bridge, but it is not the decisive independent replication because of its close corpus lineage with ChineseEEG.

## Frozen ChineseEEG representation result

Representation selection is EEG-only and model-blind. The current primary representation is all-sensor temporal mean amplitude because it had the highest nuisance-residualized leave-one-subject-out RDM reliability in the frozen common ChineseEEG cohort. Existing Nature model results do not alter this selection.

The full candidate family to be harmonized where acquisition permits is:

- all-sensor temporal mean amplitude;
- amplitude standard deviation;
- coarse time-resolved amplitude representation;
- broad nonfrontal mean amplitude;
- broad posterior mean amplitude;
- broad lateral-posterior mean amplitude;
- theta relative power, 4-7 Hz;
- alpha relative power, 8-12 Hz;
- beta relative power, 13-30 Hz;
- low-gamma relative power, 30-45 Hz, only when acquisition and preprocessing support it;
- 5.5-Hz phase feasibility;
- 10-Hz phase feasibility.

No new frequency bands, phase frequencies, spatial groups, or time windows may be introduced as confirmatory candidates after seeing TMNRED or ZuCo outcomes. Any such additions must be labeled exploratory and require a later independent dataset for confirmation.

## Harmonization principle

Representations should preserve the scientific meaning of the frozen family rather than force electrode-name identity across different montages. Spatial groups must be defined deterministically from electrode coordinates or documented anatomical montage regions before neural reliability is computed. They are nuisance/representation controls, not localization claims.

BrainVision, EEGLAB, EDF, MATLAB, or other file formats may require dataset-specific loaders, but the resulting feature definitions must remain equivalent at the representation level.

## Stage A: structural audit before signal analysis

For each new dataset, first produce a model-blind audit covering:

- exact dataset accession, snapshot/version, and local commit/tag when available;
- participant count and candidate usable cohort;
- tasks, sessions, runs, and condition labels;
- stimulus/item identifiers and repetition structure;
- events and timing fields;
- EEG file formats and materialization state;
- sampling frequency and recording duration where metadata provides them;
- number and names of channels;
- electrode coordinates and montage information;
- reference and preprocessing information;
- filtered/preprocessed derivatives;
- eye-tracking or behavioral covariates when available;
- stimulus metadata needed for nuisance controls;
- missing or non-materializable assets.

No language-model embeddings or neural-model RSA may be loaded during this audit.

## Stage B: model-blind EEG representation reliability

For each feasible frozen candidate, compute subject-level item/stimulus features and construct correlation-distance RDMs after feature-wise z-scoring across items.

Primary reliability endpoint:

- nuisance-residualized leave-one-subject-out RDM Spearman reliability.

Secondary endpoints:

- raw leave-one-subject-out reliability;
- residual and raw pairwise reliability;
- fraction of subjects with positive residual LOO reliability;
- subject-bootstrap confidence intervals;
- stimulus/item bootstrap where the design makes this valid;
- permutation nulls with exchangeability constraints matching the dataset design.

All candidates compared within a dataset must use an explicitly frozen common subject/item cohort whenever feasible. If a representation necessarily uses a different item set, such as duration-limited phase features, it must be labeled non-primary for direct ranking unless a common-item comparison is also provided.

## Nuisance control

Dataset-specific nuisance RDMs should be prespecified from variables available before outcome inspection. Candidate nuisance families include:

- trial/run position;
- stimulus duration or exposure duration;
- character/word/token length;
- lexical identity/frequency where available;
- orthographic overlap;
- sentence/context similarity;
- category/condition blocks when they reflect experimental structure rather than the scientific semantic target;
- eye-movement measures in datasets such as ZuCo;
- temporal lag or adjacency.

A nuisance is included because of design logic, not because its inclusion improves or worsens model alignment.

## Stage C: cross-dataset neural-geometry validation

After each dataset's EEG-only representation analysis is frozen, compare representation reliability across datasets. The primary question is whether the ChineseEEG-selected representation remains reproducible outside ChineseEEG.

Cross-dataset item-level RDM correlation is confirmatory only when a defensible shared item space exists. Otherwise use prespecified shared semantic anchors or model-independent category mappings. Text embeddings may later be used as a common coordinate system for secondary analyses, but they must not determine which EEG representation is selected.

## Stage D: participant-independent ChineseEEG neural supervision

Before final external model transfer, strengthen the ChineseEEG training design:

- construct neural targets using only training participants;
- train the language model without EEG from evaluation participants;
- evaluate on completely held-out participants;
- rotate participant folds;
- compare baseline, text-only, neural-guided, and structured-control models.

This analysis tests whether the learned neural direction reflects shared neural structure rather than participant leakage.

## Stage E: structured negative controls

At minimum include:

1. constrained row/item permutation preserving major run or temporal blocks;
2. nuisance-matched surrogate geometry built from prespecified non-neural variables;
3. participant/item correspondence permutation preserving participant-level signal statistics where feasible.

The real neural target should be evaluated against these controls with the same training and evaluation pipeline.

## Stage F: frozen external model transfer

Only after an external dataset's EEG representation protocol and reliability results are frozen may it be used for model evaluation.

Primary model: pinned multilingual E5 model and already selected neural-loss specification from the ChineseEEG development program. No external-dataset hyperparameter tuning.

Training data for the primary transfer test: ChineseEEG only.

External evaluation order:

1. TMNRED;
2. ZuCo, after its prospective audit and freeze;
3. Nature directional-word EEG as the previously observed hard stress test.

Primary ML endpoint: change in neural-model RSA from the frozen text-only comparator to the frozen neural-guided model on EEG datasets not used for model training.

A single architecturally distinct multilingual encoder may be used as a frozen secondary replication. It must not receive a new large hyperparameter search.

## Interpretation rules

- EEG reliability is not semanticity.
- Better spatially restricted performance would not establish localization.
- A spectral or phase feature is not 'more semantic' merely because model RSA is larger.
- Nature is not to be retrospectively rescued.
- A representation discovered after inspecting one external dataset must be confirmed on a later independent dataset before it is promoted to a general claim.
- Null or weak external transfer must be retained in the manuscript.

## Planned publication stopping rule

Stop adding confirmatory analyses and prepare the manuscript when the study contains:

1. robust ChineseEEG internal neural-geometry replication;
2. model-blind representation selection;
3. prospective TMNRED representation validation;
4. cross-language ZuCo representation validation if feasible;
5. at least one positive independent model-transfer result outside ChineseEEG for the strongest Nature Machine Intelligence claim, or a clearly bounded generalization result for the Nature Neuroscience route;
6. participant-independent neural supervision;
7. structured surrogate controls;
8. the already established neural-loss dose-response;
9. one frozen secondary language-model replication if computationally feasible.

The study should not continue feature fishing merely to turn every external dataset positive.
