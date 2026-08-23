# NeuroSem BERT independent-seed replication

## Status

Frozen after completion of the v1 tuning experiment and before any seed-2 tuning result is generated or inspected.

## Purpose

The v1 experiment showed a small, directionally consistent advantage of genuine neural supervision over matched text-only and shuffled-neural controls on run-06, run-07, and the frozen external semantic benchmark. The purpose of this replication is to test whether that incremental advantage is stable to tuning stochasticity.

This is not a hyperparameter search. Only the random seed changes.

## What remains identical to v1

- model: `google-bert/bert-base-chinese`
- revision: `8d2a91f91cc38c96bb8b4556ba70c392f8d5ee55`
- training runs: 01-05
- validation run: 06
- within-dataset holdout: 07
- frozen neural targets: reuse the already generated v1 run-level targets exactly
- LoRA target modules: attention `query` and `value`
- LoRA rank: 8
- LoRA alpha: 16
- LoRA dropout: 0.05
- learning rate: 2e-4
- weight decay: 0.01
- epochs: 5
- MLM probability: 0.15
- text minibatch size: 32
- max sequence length: 64
- neural loss weight: 1.0
- four arms: base, text_only, neural, shuffled_neural
- no early stopping
- no parameter or architecture changes
- same run-07 evaluator and nuisance-controlled RSA
- same frozen external C-MTEB STS benchmark and corrected split-selection rule

## Only changed quantity

Random seed changes from `20260823` to `20260824`.

This seed controls stochastic components of tuning such as LoRA initialization, minibatch order, MLM masking, and the random samples used in auxiliary MLM steps.

The shuffled-neural target itself is not regenerated for this replication. Reusing the same fixed shuffled target keeps the negative-control geometry identical across seeds, so the replication isolates optimization stochasticity rather than changing both optimization and control target.

## Primary replication criterion

The main question is whether the direction of the genuine-neural advantage repeats.

Report, without threshold tuning:

1. run-06: neural minus text_only and neural minus shuffled_neural;
2. run-07: neural minus text_only and neural minus shuffled_neural;
3. frozen external STS mean: neural minus text_only and neural minus shuffled_neural;
4. task-win counts on the eight external tasks.

The strongest replication pattern would have both neural contrasts positive at all three evaluation levels. Failure of one or more levels must be reported as such and must not trigger post-hoc tuning changes.

## Interpretation

A second seed cannot establish broad external generalization by itself. It tests optimization stability. If the same small advantage repeats, the next clean step is independent architecture or independent neural-dataset replication. If it does not repeat, the current evidence for a unique neural contribution should be considered unstable.
