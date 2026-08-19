# Scientific Hypotheses

## Core scientific question

Does human neural activity contain reproducible semantic relational structure that is not already explained by conventional linguistic representations, and can that residual structure improve language-model representations when used as an auxiliary supervision signal?

## H1. Residual neural semantic geometry exists

Human neural responses should contain semantic relational structure that remains after controlling for nuisance structure such as lexical identity, token frequency, orthography, phonology, syntax, sentence position, stimulus timing, and temporal autocorrelation.

### Primary test

Estimate neural representational dissimilarity matrices (RDMs) and test the association with semantic RDMs using partial RSA or variance partitioning while conditioning on nuisance RDMs.

### Support criterion

The semantic component should be positive, statistically significant under permutation testing, and reproducible across participants.

### Failure criterion

If the semantic component disappears after nuisance control or fails to generalize across participants, we should not proceed to brain-guided LLM tuning as the main project direction.

## H2. Residual neural geometry generalizes

Residual semantic geometry should show stability beyond a single participant, task, or dataset.

### Generalization axes

- leave-one-subject-out replication;
- cross-session replication;
- cross-task or cross-modality replication where paired stimuli exist;
- cross-language replication where equivalent concepts exist;
- cross-dataset replication using an independent neural-language resource;
- cross-recording-technology replication when EEG, ECoG, sEEG, MEG, or fMRI resources permit.

### Support criterion

A geometry learned from one partition should predict held-out neural geometry above matched null models.

## H3. Biological supervision adds information beyond text-only supervision

A language model trained with residual neural geometry as an auxiliary target should improve semantic generalization beyond matched text-only, lexical, random-geometry, and shuffled-neural controls.

### Required comparison

The central comparison is not brain-tuned versus base model. It is:

`brain-residual tuned` versus `matched text-semantic tuned`

with identical parameter budget, optimizer budget, data exposure, and evaluation protocol.

### Evaluation targets

- unseen semantic similarity items;
- paraphrase and entailment;
- cross-lingual semantic retrieval;
- held-out semantic domains;
- alignment with held-out participants;
- alignment with independent neural datasets.

## Interpretation rules

1. Higher neural correlation alone does not establish a better or more human-like model.
2. Improvements on neural training stimuli do not count as evidence of semantic generalization.
3. Results must survive temporal and positional confound controls.
4. A positive H1 with negative H3 is still scientifically meaningful. It would indicate measurable brain-specific semantic organization that does not provide a useful inductive bias for the tested language model.
5. A negative H1 is a stop signal for the tuning direction, not a reason to weaken nuisance controls.
