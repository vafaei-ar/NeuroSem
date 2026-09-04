# NeuroSem lambda=1 model-space characterization v1

**Status:** post-confirmatory descriptive characterization, frozen before lambda=1 model-space metrics are inspected.

## Purpose

Characterize how strongly the already-trained ChineseEEG-guided multilingual-E5 lambda=1.0 arm differs from the matched lambda=0 text-only arm on the same frozen 349 ZuCo Task 1 normal-reading texts used in the existing lambda=0.10 model-space characterization.

This analysis is motivated by the completed, previously frozen forward external-dose characterization, in which lambda=1.0 showed much larger external transfer and a larger already-observed STS decrement than lambda=0.10. It does not test a new neural target, retrain a model, select a dose, or alter the prospective lambda=0.10 evidence.

## Frozen model arms

Use exactly:

- lambda=0 text-only anchor: `outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter`
- lambda=1 genuine-neural anchor: `outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter`

Both arms use `intfloat/multilingual-e5-large` revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`, seed 20260823, the same data split, LoRA configuration, optimizer-step schedule, five epochs, batch sizes, learning rate, weight decay, text objective and neural objective. The original Pareto-grid protocol explicitly states that only the scalar neural-loss weight differs.

No retraining, replacement, checkpoint search, seed search or additional lambda is permitted.

## Frozen stimulus set

Use the exact same frozen ZuCo 2.0 Task 1 normal-reading item set as `scripts/robustness/nmi_model_space_characterization_v1.py`:

- all seven NR runs;
- the frozen zero-cost item mapping from `outputs/zuco2_nr_format_probe/latest/summary.json`;
- 349 texts total;
- identical `query: ` prefix, final hidden state, attention-mask mean pooling and L2 normalization.

Do not inspect, rank, filter or select item subsets by model change.

## Frozen metrics

Compute exactly the same descriptive metric family as the existing lambda=0.10 characterization, with no additions or substitutions:

1. mean corresponding-item cosine similarity between lambda=0 and lambda=1 embeddings;
2. median corresponding-item cosine similarity, retained because the existing script reports it;
3. Pearson correlation between the two pairwise cosine-distance RDM vectors;
4. Spearman correlation between the two pairwise cosine-distance RDM vectors;
5. centered linear CKA between the two embedding matrices;
6. mean k-nearest-neighbour Jaccard overlap with exactly `k=10`.

The five headline representation summaries remain item cosine, RDM Pearson, RDM Spearman, CKA and k=10 Jaccard. The item-cosine median is a prespecified companion descriptive statistic inherited from the existing implementation.

No neural outcome, STS outcome or forward-dose result enters these calculations.

## Interpretation rules

- Higher similarity/overlap means the lambda=1 representation remains closer to the matched text-only geometry under that metric.
- Lower similarity/overlap means stronger representational displacement.
- Do not define a threshold for whether the model is "still E5" or "materially altered."
- Do not compare against alternative k values, layers, pooling rules, distance metrics or item subsets.
- Compare lambda=1 descriptively with the already-completed lambda=0.10 characterization only after this frozen lambda=1 output is produced.
- No inferential p-values, bootstrap intervals, item-category analyses or target-conditioned diagnostics are added.

## Stop rule

After these metrics are computed once for lambda=1 versus lambda=0, stop. Do not add lambda=0.30 or other doses to the perturbation family based on the result, and do not open subspace, anisotropy, spectral or displacement-vector analyses.

## Safe outputs

Export only:

- `outputs/nmi_model_space_characterization_lambda1_v1/latest/summary.json`
- `outputs/nmi_model_space_characterization_lambda1_v1/latest/item_metrics.csv`

These contain model-derived descriptive values only and no raw neural data.
