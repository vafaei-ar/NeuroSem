# Analysis Plan

This document began as the preregistration-style plan for the first computational phase. It remains useful as the original methodological intent. The project has now progressed beyond Phase 1, so the final section records implemented decisions and deviations without rewriting the historical logic.

## Phase 1 goal

Determine whether reproducible semantic geometry exists in neural responses after controlling for ordinary linguistic and experimental structure.

## Unit of analysis

The exact unit depends on the dataset. Preferred units are words, phrases, or sentences with clearly aligned neural epochs. Repeated presentations should remain identifiable so that within-stimulus reliability can be estimated rather than silently averaged.

## Neural preprocessing

Dataset-specific preprocessing should follow the original publication first. Any alternative preprocessing must be a sensitivity analysis.

Minimum documentation:

- filtering and resampling;
- referencing;
- bad-channel handling;
- ocular/muscle artifact treatment;
- epoch definition;
- baseline correction if used;
- trial rejection criteria;
- dimensionality reduction or feature extraction.

Avoid aggressive preprocessing chosen after observing semantic results.

## Neural representations

Benchmark at least three representations where feasible:

1. sensor-time activity in predefined windows;
2. lower-dimensional neural representations from PCA or another unsupervised method fit only on training data;
3. learned neural encoders, only after simple representations are understood.

For EEG, time-resolved windows were originally preferred over collapsing the whole epoch. In practice, the first ChineseEEG representation benchmark showed that a simpler temporal-mean vector was substantially more cross-subject reliable than the initial flattened sensor-time representation. That practical decision is documented below rather than silently rewriting the original preference.

## Linguistic representations

For each linguistic unit, extract representations from multiple layers of at least one open language model. Include simpler baselines:

- static lexical embeddings;
- contextual language-model embeddings;
- sentence embeddings where appropriate;
- lexical identity/frequency/length features;
- syntactic features;
- phonological/orthographic features where available.

Model and tokenizer versions must be pinned.

## Representational geometry

Primary framework: representational similarity analysis (RSA).

For neural representation `x_i` and language representation `h_i`, construct representational dissimilarity matrices (RDMs):

`RDM_neural(i,j) = d(x_i, x_j)`

`RDM_model(i,j) = d(h_i, h_j)`

Benchmark correlation/distance choices rather than choosing them post hoc. Candidate choices include correlation distance, cosine distance, Euclidean distance after standardization, and cross-validated Mahalanobis distance where repeated trials permit reliable estimation.

## Nuisance RDMs

Construct nuisance geometries as data allow:

- lexical identity;
- token/word frequency;
- character or word length;
- orthographic similarity;
- phonological similarity;
- sentence position;
- syntactic structure;
- stimulus duration;
- event timing;
- trial order/block;
- acoustic structure for listening/overt speech;
- visual structure for reading;
- temporal autocorrelation/lag structure.

## Primary statistical test

Use partial RSA and/or variance partitioning to estimate the unique contribution of semantic/model geometry after conditioning on nuisance RDMs.

The first go/no-go quantity is the cross-subject distribution of the residual semantic effect.

## Generalization design

Do not use random row splitting when repeated stimuli or subjects create dependence.

Preferred tests:

- leave-one-subject-out;
- held-out stimuli;
- held-out semantic categories where sample size permits;
- held-out session/block;
- cross-task or cross-modality transfer;
- independent dataset replication.

All preprocessing parameters, dimensionality-reduction transforms, and learned mappings must be fit on training partitions only.

## Inference

Use permutation procedures that preserve the relevant dependence structure. Candidate schemes include stimulus-label permutations within valid blocks and subject-level sign/permutation tests for group inference.

Report effect sizes and uncertainty, not only p-values.

Multiple-comparison control is required for time-resolved/layer-resolved analyses. Cluster-based permutation or a prespecified FDR procedure should be considered depending on the analysis structure.

## Critical negative controls

- shuffled neural-stimulus pairing;
- time-shifted neural data;
- shuffled subjects where structurally possible;
- random RDM matched in dimensionality;
- text-semantic target instead of brain target;
- lexical baseline target;
- position/timing-only models;
- matched optimization budget for all later tuning controls.

## Original go/no-go rule

Proceed to neural-guided LLM tuning only if:

1. semantic geometry survives nuisance control;
2. the effect replicates across subjects;
3. it survives temporal/positional confound controls;
4. at least one independent split, task, or dataset shows generalization.

If these conditions fail, revise the scientific question rather than lowering the control standard.

## Phase 2: neural-guided model tuning

Only after Phase 1 succeeds, benchmark auxiliary objectives such as:

- RDM regression loss;
- contrastive InfoNCE;
- triplet relational loss;
- CKA-based alignment;
- Procrustes-aligned representation loss;
- optimal-transport geometry.

Use parameter-efficient tuning first. The decisive comparison is neural-residual supervision versus matched text-only semantic supervision.

# Implemented decisions and current deviations

This section records what actually happened so the original plan and the implemented pipeline can both be audited.

## ChineseEEG representation choice

The initial flattened sensor-time representation had weak cross-subject reliability. A simpler representation was selected using neural reliability before semantic testing:

1. for each linguistic row/epoch, average EEG across time separately within each sensor;
2. retain the sensor values as the item vector;
3. featurewise standardize as specified by the dataset-specific protocol;
4. construct correlation-distance RDMs.

This temporal mean became the primary ChineseEEG neural representation because it was more reproducible, not because it gave a stronger model-semantic result.

Richer representations, including amplitude variability, temporal bins, spectral power, and phase-oriented features, were subsequently examined as sensitivity or exploratory candidates. They should not replace the established primary representation post hoc without independent confirmation.

## ChineseEEG discovery and holdout structure

Little Prince narrative runs were used sequentially:

- runs 01-06 established cross-run residual neural/model correspondence;
- run 06 was used in later tuning/development procedures where specified by the frozen tuning protocols;
- run 07 remained sealed until the final four-arm neural holdout evaluation.

The BERT run-07 holdout showed neural-guided > text-only/shuffled in two seeds. This justified the statement that neural-guided tuning can improve held-out alignment to the development dataset's neural geometry.

## External semantic benchmark interpretation

Generic semantic benchmarks were treated as a distinct endpoint from neural alignment.

The BERT external benchmark did not show a stable brain-specific advantage across seeds. Multilingual-E5/Pareto work likewise did not establish that greater neural alignment automatically improves generic semantic performance.

Therefore the project now explicitly separates:

- improving neural-target alignment;
- improving generic semantic representations.

They are not interchangeable outcomes.

## TMNRED external replication

TMNRED was introduced as an independent Chinese-reading dataset.

The data pipeline was frozen before signal-level outcome inspection through a sequence of model-blind audits, format probes, event-alignment checks, and cohort/item freezes.

Final current rules:

- 29-participant cohort;
- eight sessions;
- sentence items retained if available for at least 80% of participants within session;
- all 50 items passed that rule in every session;
- the ChineseEEG-selected temporal mean remained the prospectively designated primary representation;
- amplitude SD and 8-bin temporal summaries were sensitivity representations.

TMNRED independently supported weak positive reliability of the temporal-mean geometry. However, the frozen ChineseEEG-trained E5 lambda-0.10 vs lambda-0 transfer contrast was null.

Post-confirmatory SD and 8-bin transfer tests were explicitly exploratory and also did not rescue transfer.

## Nature directional dataset interpretation update

The Nature directional-word dataset is not a task-matched replication of the reading datasets.

The primary NeuroSem condition is covert/inner speech of six directional concepts. This differs from silent/normal reading and may recruit internal articulation, phonological rehearsal, and speech-motor processes.

Accordingly:

- keep Nature as a secondary out-of-task generalization/mechanistic test;
- do not use its null result as direct evidence against reading-related neural geometry;
- do not rank it above task-matched reading datasets for external validation.

## ZuCo 2.0 external replication

ZuCo 2.0 Task 1 Normal Reading is the current priority external cross-language test.

The project first performed model-blind public-file inventory and representative-file event/format probes. These established a deterministic sentence extraction rule from continuous EEG before any full-cohort EEG reliability analysis.

The next stage is full-cohort materialization/QC across the 18-participant x 7-run target cohort, followed by a frozen EEG-only reliability test.

No ZuCo reliability or model-transfer claim exists yet.

## ChineseEEG Garnett Dream

The project initially underused the second ChineseEEG novel.

Garnett Dream is now designated as a high-priority different-text replication. The intended design is to freeze Little Prince-derived representation, nuisance, and RSA choices before inspecting Garnett Dream outcomes.

This provides a stronger same-acquisition replication than adding another loosely comparable dataset.

## Current stopping rule for additional model tuning

Do not continue searching neural-loss weights, representations, or datasets merely to obtain a positive transfer result.

Further model-transfer work should be justified by independent EEG evidence. In particular:

1. complete ZuCo EEG-only reliability;
2. complete Garnett Dream different-text replication;
3. then decide whether another frozen model-transfer test is scientifically warranted.

If independent neural geometry is weak or inconsistent, narrow the paper's claim rather than expanding the tuning search space.

## Current authoritative summaries

For current interpretation and results, use:

1. `docs/1_PROJECT_OVERVIEW.md`
2. `docs/2_DATASETS_AND_TASKS.md`
3. `docs/3_RESULTS_AND_COMPARISONS.md`
4. `docs/4_EXPERIMENT_LEDGER.md`

Detailed dataset-specific protocols under `docs/` remain the authoritative method records for individual analyses.
