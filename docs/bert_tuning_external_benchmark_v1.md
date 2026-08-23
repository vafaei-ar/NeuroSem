# NeuroSem external semantic benchmark v1

Frozen before any BERT tuning result is interpreted.

## Primary external endpoint

Use the current C-MTEB Chinese semantic textual similarity task set with no task-specific tuning:

1. AFQMC
2. ATEC
3. BQ
4. LCQMC
5. PAWSX
6. QBQTC
7. STS22 (zh)
8. STSB

For every model arm, generate sentence embeddings with the same representation rule used in the NeuroSem BERT analysis: final hidden layer, mean pooled over non-special and non-padding tokens, followed by cosine similarity.

The primary external endpoint is the unweighted mean of the eight task-level Spearman correlation scores. Report all eight task scores separately as secondary endpoints.

## Arms

Evaluate exactly the following four models:

- pretrained base BERT;
- text-only LoRA;
- genuine-neural LoRA;
- shuffled-neural LoRA.

No task-specific tuning, prompt optimization, pooling change, layer selection, whitening, or post-hoc calibration is allowed.

## Primary comparisons

1. genuine-neural minus text-only mean C-MTEB STS score;
2. genuine-neural minus shuffled-neural mean C-MTEB STS score.

The sign and magnitude of both contrasts are reported. The neural-guided approach is not considered useful if its apparent advantage is restricted to increased EEG alignment and does not generalize to these external semantic tasks.

## Secondary checks

- number of the eight tasks on which genuine-neural exceeds text-only;
- number on which genuine-neural exceeds shuffled-neural;
- worst task-level degradation relative to text-only;
- mean change relative to the pretrained base model.

A sensitivity analysis may later use additional C-MTEB retrieval or clustering tasks, but those results cannot replace this primary v1 endpoint.
