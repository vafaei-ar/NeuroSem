# Analysis Plan

This document defines the first computational phase. It should be treated as a preregistration-style plan and updated through explicit commits when scientific decisions change.

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

For EEG, evaluate time-resolved windows rather than collapsing the whole epoch initially.

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

## Go/no-go rule

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
