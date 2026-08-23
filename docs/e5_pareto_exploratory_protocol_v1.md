# E5 neural-alignment / semantic-utility Pareto experiment v1

Status: exploratory/mechanistic, frozen before execution.

## Motivation

The frozen E5 replication showed a large genuine-neural increase in held-out ChineseEEG run-07 alignment but a substantial decrease on the previously frozen eight-task Chinese STS endpoint. This experiment characterizes the dose-response relationship between neural supervision strength and the two outcomes. It is not a confirmatory rescue of H3.

## Model and training

Use `intfloat/multilingual-e5-large` at revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3` with the same representation and LoRA/training recipe as `docs/e5_neural_tuning_protocol_v1.md`:

- input prefix: `query: `
- final hidden state, attention-mask mean pooling, L2 normalization
- LoRA query/value, rank 8, alpha 16, dropout 0.05
- train runs 01-05; run 06 descriptive validation; run 07 never used for gradients, model selection, hyperparameter selection, or early stopping
- seed 20260823
- 5 fixed epochs, batch 32, LR 2e-4, weight decay 0.01
- same symmetric dropout-view InfoNCE text objective
- same fixed residual neural targets and relational loss

Only the scalar neural-loss weight changes.

## Prespecified dose grid

Use the log-spaced grid:

`lambda = [0.00, 0.01, 0.03, 0.10, 0.30, 1.00]`

The `lambda=0` anchor is the already-completed E5 text-only adapter from the frozen replication. The `lambda=1` anchor is the already-completed E5 genuine-neural adapter from the frozen replication. These anchors are reused, not retrained. Only `0.01, 0.03, 0.10, 0.30` are newly trained.

Do not add, delete, or choose grid points after examining results from this experiment.

## Outcomes

For each lambda, report:

1. final run-06 residual neural correlation from the fixed five-epoch training trajectory;
2. run-07 nuisance-controlled residual neural RSA using the existing validated 10,000 within-chapter circular-shift procedure;
3. mean Spearman over the same eight Chinese STS tasks used in the frozen E5 experiment, with the exact previously resolved dataset revisions and the same public labeled splits;
4. each individual STS task score;
5. change in run-07 neural alignment and external STS relative to lambda=0.

The primary scientific object is the descriptive Pareto curve: held-out run-07 neural alignment versus mean external STS performance across lambda.

## Interpretation rules

- This entire dose-response analysis is exploratory because run-07 and the eight-task STS endpoint were already observed before the grid was run.
- Do not select a lambda on these outcomes and report its performance as confirmatory evidence.
- Do not use task-level significance testing to manufacture a positive H3 result.
- A useful mechanistic pattern would be a smooth dose-response in which neural alignment increases as lambda increases, with a corresponding semantic cost or a low-lambda region that preserves semantic utility.
- If a candidate lambda is chosen for future work, it must be evaluated on a genuinely fresh neural and/or semantic target before any confirmatory claim.

## Frozen anchor provenance

Reuse exactly:

- lambda=0: `outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter`
- lambda=1: `outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter`

No BERT tuning is part of this experiment.
