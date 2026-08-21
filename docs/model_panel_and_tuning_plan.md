# NeuroSem model-panel and tuning plan

## Purpose

This plan prevents model shopping while allowing broad testing across major language-model families. The goal is not to find whichever model gives the smallest p-value. The goal is to determine whether residual neural-semantic geometry is reproducible across model families and to identify a small number of defensible candidates for neural-guided tuning.

## Stage A: finish the current BERT replication first

Keep the current analysis completely locked for LittlePrince runs 05-07:

- neural representation: row_mean;
- featurewise z-scoring across rows within subject;
- neural RDM: correlation distance;
- semantic target: pinned google-bert/bert-base-chinese final hidden layer, mean pooled over non-special tokens;
- nuisance set and residualization: unchanged from runs 01-04;
- within-chapter structure-preserving permutation: unchanged;
- run-level aggregation: exact one-sided sign-flip test;
- no additional model or layer choices based on runs 05-07.

This stage tests H1. It should be completed before model-family screening.

## Stage B: broad but prespecified model-family screen

After Stage A, test one canonical representation from each major, scientifically distinct family. Do not sweep many layers, prompts, pooling rules, or model sizes at this stage.

Initial panel:

1. `google-bert/bert-base-chinese` - existing Chinese BERT baseline.
2. `FacebookAI/xlm-roberta-large` - general multilingual masked-language-model encoder.
3. `intfloat/multilingual-e5-large` - multilingual sentence-embedding model.
4. `BAAI/bge-m3` - multilingual retrieval/embedding model with strong Chinese support.
5. `Qwen/Qwen3-Embedding-0.6B` - modern multilingual embedding model derived from the Qwen3 family.

Optional decoder-family representation panel, only after the encoder/embedding panel is stable:

6. one small open Qwen3 base model suitable for LoRA;
7. one non-Qwen decoder family with practical local tuning requirements.

For every model, pin the exact repository revision, tokenizer, software versions, pooling rule, input formatting, and output dimension. If a model normally uses task instructions, define one neutral semantic-similarity instruction before inspecting neural results and keep it fixed.

## Why not test every available model?

Testing dozens of near-duplicate checkpoints, sizes, layers, prompts, and pooling variants on the same EEG data would create a large researcher-degrees-of-freedom problem. A representative family panel gives broader scientific coverage with less multiple-testing and selection bias.

Model size variants may be tested later as a prespecified scaling analysis, not as a rescue strategy for weak results.

## Model-screening dataset split

To preserve a genuine cross-model holdout:

- use runs 01-06 for model-family screening after the BERT-only replication is complete;
- keep run 07 unopened for non-BERT models during model selection;
- select at most three candidate models using only runs 01-06;
- test those selected candidates on run 07 and then, where practical, on ChineseEEG-2 or another independent neural-language dataset.

Seeing the BERT result on run 07 does not invalidate run 07 as a cross-model holdout as long as alternative-model representations are not generated or inspected there until model selection is frozen.

## Primary model-comparison metrics

Do not rank models by minimum p-value alone. For each model report:

- mean residual semantic-neural effect across runs;
- proportion of runs with positive effects;
- exact run-level sign-flip inference;
- leave-one-run-out stability;
- common-subject direction consistency;
- sensitivity to lexical/orthographic nuisance controls;
- computational cost and tunability.

A candidate should be favored only if its alignment is reproducible rather than dominated by one run or one subject.

## Multiple-comparison policy

The five-model family panel is confirmatory only at the family-comparison level. Report all models. Use a prespecified correction across model families, preferably a permutation max-statistic if implemented cleanly; otherwise use Benjamini-Hochberg FDR as a secondary analysis. The current BERT model remains the original primary target and is not redefined post hoc.

## Stage C: candidate selection for tuning

Select at most two or three models for tuning. Selection should require:

1. reproducible positive residual neural-semantic alignment across runs;
2. evidence that the effect is not explained by the nuisance geometries already modeled;
3. acceptable performance on the sealed run-07 cross-model evaluation;
4. practical parameter-efficient tuning support;
5. preferably evidence from an independent neural dataset.

The strongest neural-alignment model is not automatically the best tuning model if it is impractical to train or if the effect is unstable.

## Stage D: neural-guided tuning

Start with LoRA/adapters rather than full fine-tuning.

Primary experimental comparison:

- base model, no tuning;
- matched text-only tuning;
- neural-residual relational tuning;
- shuffled-neural control with identical optimization budget.

Primary neural objective should preserve relational geometry rather than force coordinatewise equality. Candidate losses include triplet/ranking loss, RDM regression, or CKA-style relational alignment. The first implementation should use one prespecified loss, with alternatives treated as later sensitivity analyses.

## Required evaluation after tuning

A tuned model is useful only if neural supervision provides information beyond ordinary language training. Evaluate:

- held-out semantic stimuli;
- held-out subjects;
- held-out run or dataset;
- standard semantic similarity/retrieval tasks where appropriate;
- degradation on general language behavior;
- comparison with matched text-only tuning;
- shuffled-neural negative control.

Do not claim success solely from increased alignment to the same EEG used for tuning.

## Decision rule

Proceed to tuning only after the BERT H1 replication is sufficiently consistent across the remaining held-out runs. Then screen the prespecified family panel, freeze candidate selection, test selected models on the sealed cross-model holdout, and only then begin neural-guided LoRA experiments.
