# NeuroSem multilingual E5 neural-guided tuning protocol v1

## Status

Frozen before any multilingual E5 tuning results are inspected.

This is an independent-architecture replication of the BERT neural-guided tuning experiment. The scientific question is whether the BERT result reflects a model-specific limitation or whether residual neural semantic geometry generally fails to improve external semantic behavior under the current relational objective.

## Model and representation

- model: `intfloat/multilingual-e5-large`
- revision: `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`
- input prefix: `query: `
- representation: final hidden state, mean pooling over the attention mask, then L2 normalization
- pair geometry: cosine distance

These choices match the previously frozen E5 representation used in the NeuroSem model-family screen.

## Data split

- training: ChineseEEG LittlePrince runs 01-05
- validation: run 06
- final within-dataset neural holdout: run 07
- run 07 is never used for gradients, hyperparameter selection, stopping, or model selection
- the external benchmark remains the frozen eight-task Chinese C-MTEB STS endpoint already used for BERT

The model-independent neural targets already built under `outputs/bert_neural_tuning_targets_v1` are reused. They contain text rows plus residual neural pairwise geometry and do not depend on BERT parameters.

## Four arms

1. `base`: pretrained E5, no updates
2. `text_only`: LoRA adaptation with text-only unsupervised contrastive consistency
3. `neural`: the same text-only objective plus genuine residual neural relational loss
4. `shuffled_neural`: the same text-only objective plus the fixed shuffled neural target

All tuned arms use the same rows, optimizer, number of epochs, batch sizes, LoRA configuration, random seed, and optimizer-step budget.

## Text-only objective

E5 is a sentence-embedding model rather than a masked-language-model checkpoint, so the matched text-only adaptation uses an architecture-appropriate unsupervised contrastive objective.

For each text batch, create two stochastic dropout views of the same prefixed sentences. Mean-pool and L2-normalize both views. Use symmetric in-batch InfoNCE with temperature 0.05, where each sentence's second view is its positive and all other rows in the batch are negatives.

This objective is fixed before results and is identical in the `text_only`, `neural`, and `shuffled_neural` arms.

## Neural objective

For each full training run, compute the current E5 pairwise cosine-distance vector and standardize it. Let `b_run` be the fixed standardized residual neural target.

`L_neural = 1 - corr(z(d_model), b_run)`

For the genuine neural arm:

`L = L_text + 1.0 * L_neural`

For the shuffled control, replace `b_run` with the prespecified fixed shuffled target. The training surrogate is differentiable Pearson geometry; held-out neural evaluation remains the locked nuisance-controlled rank-based RSA.

## Prespecified optimization

- LoRA target modules: attention `query` and `value`
- LoRA rank: 8
- LoRA alpha: 16
- LoRA dropout: 0.05
- learning rate: 2e-4
- weight decay: 0.01
- epochs: 5
- text batch size: 32
- max sequence length: 64
- contrastive temperature: 0.05
- neural loss weight: 1.0
- seed: 20260823
- geometry batch size: 64
- no hyperparameter sweep
- no early stopping

Each epoch contains one standard text-only pass over all training rows, followed by five matched auxiliary optimizer steps, one per training run. The neural and shuffled arms add the relational term on those same-budget auxiliary steps.

## Evaluation hierarchy

### Held-out neural geometry

Evaluate all four arms on run 07 with the same nuisance-controlled RSA used previously. Increased run-07 neural alignment is supportive but is not sufficient by itself.

### Primary external semantic endpoint

Use the already frozen C-MTEB Chinese STS set:

1. AFQMC
2. ATEC
3. BQ
4. LCQMC
5. PAWSX
6. QBQTC
7. STS22 (zh)
8. STSB

Use the same public-label split rule already fixed after the AFQMC technical failure: choose the first split in `test -> validation -> train` with finite, nonconstant gold scores before model scoring. The primary endpoint is the unweighted mean task-level Spearman correlation.

### Primary contrasts

- `neural - text_only`
- `neural - shuffled_neural`

Report all eight task scores, task-win counts, and worst task degradation versus text-only.

## Decision rule

The E5 replication supports transferable semantic benefit only if genuine neural supervision outperforms both matched controls on the external STS mean without material task-level degradation. If E5 again shows improved held-out neural alignment but no reproducible external semantic advantage, the current evidence favors the interpretation that this relational brain-guidance objective changes model geometry without reliably improving generic semantic behavior.

No pooling, prefix, loss weight, layer, temperature, epoch count, or stopping rule will be changed after results are observed in this primary E5 experiment.
