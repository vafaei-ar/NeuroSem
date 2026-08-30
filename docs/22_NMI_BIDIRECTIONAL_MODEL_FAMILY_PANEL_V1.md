# NMI bidirectional model-family panel v1

## Status

Frozen post-confirmatory explanatory model-family experiment. This experiment is designed after observing that multilingual E5 showed robust external neural transfer while multilingual BERT did not under the earlier strict-portability test. It is therefore not a prospective confirmation of model-family effects.

## Scientific question

Which classes of multilingual encoder models support externally transferable neural relational supervision, and is the relevant distinction associated with sentence-level metric pretraining rather than transformer backbone identity alone?

## Model panel

The panel is fixed before execution and spans three descriptive classes, two models per class:

1. E5 retrieval/sentence-embedding family
   - `intfloat/multilingual-e5-large`
   - `intfloat/multilingual-e5-base`
2. Other multilingual sentence-embedding models
   - `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
   - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
3. Generic multilingual masked-language encoders
   - `FacebookAI/xlm-roberta-base`
   - `google-bert/bert-base-multilingual-cased`

Exact Hugging Face revision SHAs are resolved once at job start, written to `resolved_models.json`, and then held fixed for every seed, source direction and arm in the run. No model may be substituted after outcomes are seen.

## Common representation and adaptation protocol

To avoid giving any model a model-specific rescue procedure, every model is adapted under one common representation protocol:

- final hidden layer;
- attention-mask mean pooling;
- L2 normalization;
- cosine-distance relational geometry;
- E5 inputs use the frozen `query: ` prefix; all other models use no task prefix;
- LoRA on attention query/value projections, rank 8, alpha 16, dropout 0.05;
- AdamW, learning rate 2e-4, weight decay 0.01;
- 5 fixed epochs / source schedule;
- no early stopping and no checkpoint selection;
- standard text objective: symmetric dropout-view InfoNCE, temperature 0.05;
- neural objective: `1 - corr(z(model pairwise cosine distances), frozen neural relational target)`;
- fixed neural weight lambda = 0.10 for all models and both directions;
- matched lambda=0 text-only arm for every model, seed and source direction.

The purpose of the common protocol is explanatory comparability, not optimization of each architecture. A model that fails under this common protocol is a portability boundary, not proof that the architecture can never support neural transfer under any tuning strategy.

## Optimization seeds

All models are run at exactly three prespecified seeds:

- 20260829
- 20260830
- 20260831

All seeds are reported. No seed is selected or discarded based on source or external outcomes.

## Direction A: ChineseEEG source -> SMN4Lang fMRI target

Source:
- same frozen ChineseEEG residual relational targets already used in NeuroSem;
- runs 01-05 are training sources;
- run 06 is source-only descriptive validation;
- run 07 is not read in this direction.

Training:
- matched text-only lambda=0 and neural-guided lambda=0.10 arms;
- fixed five-epoch budget and no outcome-based selection.

External target:
- the prospectively frozen SMN4Lang LanA fMRI pipeline;
- 12 participants, 60 stories;
- same causal within-sentence prefixes, word-onset placement, canonical HRF, LanA mask, retained timepoints and three nuisance RDMs;
- participant-level delta RSA is the inferential unit.

Primary per-seed contrast:
`ChineseEEG-guided lambda=.10 minus matched lambda=0` on SMN4Lang fMRI.

## Direction B: SMN4Lang fMRI source -> ZuCo EEG target

Source:
- same frozen SMN4Lang group relational targets from the bidirectional source-freeze stage;
- same 20 source-training stories and same fixed five-epoch story schedule used by the source-calibration stage;
- same 12 source validation stories are used descriptively only;
- no lambda selection is performed.

Training:
- matched text-only lambda=0 and fMRI-guided lambda=0.10 arms;
- fixed five-epoch/source schedule and no outcome-based selection.

External target:
- frozen ZuCo 2.0 Task 1 normal-reading EEG pipeline;
- same 17-participant cohort and seven runs;
- same row-mean representation, nuisance controls, session aggregation and participant-level inference.

Primary per-seed contrast:
`fMRI-guided lambda=.10 minus matched lambda=0` on ZuCo EEG.

## Interpretation plan

For each model and each direction report:
- source diagnostic delta between neural-guided and matched text-only arms;
- external participant-level mean and median delta RSA;
- fraction / count of participants with positive delta;
- participant bootstrap 95% confidence interval;
- exact paired sign-flip p-value;
- all three seed-specific results;
- mean of seed-level mean deltas;
- whether all three seed-level mean deltas have the same sign.

Descriptive family summaries will average seed-level effects within the two fixed members of each class. These are explanatory summaries only; with two models per class they are not treated as population-level inference over arbitrary model families.

The key pattern of interest is whether E5 and/or other sentence-embedding models show more stable bidirectional transfer than generic MLM encoders. A mixed pattern must be reported as such. No model, seed, direction or target may be removed to improve the narrative.

## Guardrails

- post-confirmatory explanatory analysis;
- fixed model panel, lambda and seeds before execution;
- no per-model lambda search;
- no per-model layer or pooling search;
- no target-side selection;
- no rescue training after external outcomes;
- same external neural targets as previously frozen;
- model failures caused by technical incompatibility are reported explicitly and are not silently replaced;
- exact resolved model revisions are saved before training starts.

## Operational plan

The whole panel runs as one RunRelay job. The task requests two GPUs and schedules independent model x seed x direction units across the two leased GPUs. This resource request also ensures the panel waits until both GPUs are available before starting, so it can follow the currently running ChineseEEG multi-seed task without manual intervention after approval.
