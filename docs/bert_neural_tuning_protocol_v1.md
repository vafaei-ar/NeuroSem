# NeuroSem BERT neural-guided tuning protocol v1

## Status

Frozen before any neural-guided BERT tuning results are inspected.

The alignment/discovery stage is complete. The primary tuning model is `google-bert/bert-base-chinese` at revision `8d2a91f91cc38c96bb8b4556ba70c392f8d5ee55`. Multilingual E5 is reserved for a later independent architecture confirmation. BGE-M3 remains an architectural replication model and is not part of the first tuning experiment.

## Scientific question

Does residual neural semantic geometry provide useful supervision beyond ordinary text-only adaptation?

The primary claim is not that tuning can increase alignment to the same EEG used for training. The critical test is whether genuine neural supervision improves held-out semantic geometry or semantic behavior beyond matched text-only tuning and a shuffled-neural control.

## Data split

- Training: ChineseEEG LittlePrince runs 01-05.
- Validation: run 06.
- Final within-dataset neural holdout: run 07.
- Run 07 is never used for gradient updates, model selection, hyperparameter selection, or early stopping.
- External semantic evaluation must be fixed before training results are interpreted.

## Neural target

For each training run and subject:

1. use the locked `row_mean` EEG representation;
2. featurewise z-score channels across rows within subject;
3. compute a correlation-distance neural RDM;
4. rank-z transform the neural RDM;
5. residualize against the locked nuisance set used in the alignment analysis;
6. standardize the residual vector;
7. average residual neural vectors across subjects to form one run-level target.

The run-level target is a residual relational signal. It is not treated as a Euclidean coordinate system and is never matched coordinatewise to language-model hidden states.

## Model representation during tuning

For each clean text row, use the same BERT representation as the primary alignment analysis:

- final hidden layer;
- mean pooling over non-special, non-padding tokens;
- cosine distance between row embeddings.

The neural relational objective uses the vector of pairwise cosine distances among rows in a run.

## Four arms

1. `base`: frozen pretrained BERT, no updates.
2. `text_only`: LoRA adaptation with masked-language-model loss only.
3. `neural`: identical LoRA adaptation and MLM loss plus genuine residual neural relational loss.
4. `shuffled_neural`: identical to `neural`, but the run-level neural target is replaced by one fixed structure-breaking permutation generated before training with the locked seed.

The three tuning arms use the same training rows, optimizer, number of epochs, masking probability, batch size, learning rate, LoRA configuration, random seed, and number of optimizer steps.

## Prespecified optimization

- base model: `google-bert/bert-base-chinese`
- revision: `8d2a91f91cc38c96bb8b4556ba70c392f8d5ee55`
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
- random seed: 20260823
- no hyperparameter sweep in the primary experiment
- no early stopping in the primary experiment

## Relational neural loss

For one complete run, let `d_model` be the vector of pairwise cosine distances among the current clean-text BERT embeddings. Let `b_run` be the fixed run-level residual neural target, already centered and standardized.

The primary neural loss is:

`L_neural = 1 - corr(z(d_model), b_run)`

where `z(d_model)` centers and scales the model pair-distance vector. Because `b_run` is constructed after nuisance residualization, this objective rewards the component of current model geometry that covaries with the residual neural target rather than raw nuisance geometry.

The primary combined objective for the neural arms is:

`L = L_MLM + 1.0 * L_neural`

The text-only arm uses `L = L_MLM`.

The primary experiment does not change the relational loss after results are observed. Triplet, CKA, RDM-regression variants, or alternative nuisance projections are sensitivity analyses only.

## Shuffled-neural control

The shuffled target must preserve the target value distribution but break the mapping between semantic pair identity and neural residual value. One fixed permutation is generated per run with the locked seed and stored with provenance before training. The same shuffled target is reused for every epoch.

## Evaluation hierarchy

### Primary comparison

`neural` versus `text_only` on evaluation data not used for gradient updates.

### Required negative control

`neural` versus `shuffled_neural` under the same optimization budget.

### Within-dataset neural evaluation

For each arm, compute the locked nuisance-controlled RSA on run 07 without refitting the model. Report the change from the pretrained base model, but do not treat increased run-07 neural alignment alone as proof of useful neural supervision.

### External semantic evaluation

Before interpreting tuning results, freeze a compact external semantic benchmark set. The primary analysis should report each arm on exactly the same external tasks with no task-specific tuning. Neural-guided tuning is considered scientifically useful only if it improves at least one prespecified semantic generalization endpoint over `text_only` without material degradation on the others, and the shuffled-neural arm does not show the same pattern.

## Decision rule

Advance the neural-guided approach only if all of the following are satisfied:

1. the genuine-neural arm outperforms text-only tuning on the prespecified primary held-out semantic endpoint;
2. the genuine-neural arm outperforms the shuffled-neural control;
3. the gain is not explained solely by stronger alignment to training EEG;
4. general language/semantic behavior does not show material degradation;
5. the effect is reproducible in at least one independent seed or independent model family before a strong publication claim.

## Interpretation guardrails

- Runs and subjects remain the inferential units, not individual RDM edges.
- Do not optimize lambda, pooling, layer choice, target construction, or stopping time after observing the primary result.
- Do not use run 07 for tuning or hyperparameter selection.
- Do not claim that residual neural geometry contains unique information merely because the neural arm increases brain alignment. The unique-information claim requires superiority to matched text-only and shuffled-neural controls on held-out behavior or geometry.
