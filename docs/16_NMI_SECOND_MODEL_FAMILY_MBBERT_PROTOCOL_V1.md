# 16. NMI second-model-family robustness protocol v1

**Analysis status:** post-confirmatory generalization analysis.

This experiment addresses one narrow question: whether the externally transferable neural-relational effect observed with multilingual E5 is detectable in a second multilingual model family under a completely frozen analysis. ZuCo and SMN4Lang outcomes are already historically known, so this experiment is not a new prospective confirmation and must never be described as such.

## Frozen question

Does ChineseEEG-derived relational supervision produce a positive neural-guided minus text-only representational-alignment shift in a multilingual BERT model when evaluated on the already-frozen ZuCo EEG and SMN4Lang fMRI targets?

## Model

- model: `google-bert/bert-base-multilingual-cased`
- immutable Hugging Face revision: `c298d193a40f7d74951e9b8de1e278db2723f10b`
- architecture: multilingual BERT encoder with masked-language-model pretraining
- language coverage criterion: supports Chinese/Mandarin and English
- choice rationale: architecture/pretraining family differs from the XLM-R-derived multilingual E5 family and the model is computationally feasible with the already-established NeuroSem BERT LoRA pipeline
- model choice was made without using ZuCo or SMN4Lang performance

The previously suggested `paraphrase-multilingual-mpnet-base-v2` is not used because its transformer backbone is XLM-R, making it a weaker architecture-level contrast with multilingual E5.

## Source neural target

Use the existing frozen ChineseEEG neural targets generated for runs 01-06. No neural representation is recomputed or reselected.

- training runs: 01-05
- source-only validation run: 06, descriptive only
- run 07: not accessed by training or selection

## Training arms

For each prespecified seed, train exactly two matched arms with the established NeuroSem BERT LoRA trainer:

1. `text_only`: LoRA + masked-language modeling, no neural term
2. `neural`: identical optimization budget plus the existing relational loss

The relational loss remains `1 - corr(z(d_model), b_run)` using pairwise cosine-distance model geometry and the frozen ChineseEEG residual neural target.

### Fixed optimization

- LoRA target modules: query and value
- rank: 8
- alpha: 16
- dropout: 0.05
- max length: 64
- MLM probability: 0.15
- batch size: 32
- epochs: 5 fixed
- learning rate: 2e-4
- weight decay: 0.01
- no early stopping
- no checkpoint selection
- final hidden layer mean over non-special, non-padding tokens
- L2 normalization before external model-RDM construction

## Lambda

The primary robustness test uses **lambda = 0.10 exactly**, carried over from the frozen E5 intervention.

No alternative lambda will be run after external outcomes are inspected. No source-only lambda calibration is included in v1. Therefore a null result is interpreted conservatively as failure to establish second-family robustness under strict hyperparameter portability, not proof that BERT-family models cannot support neural-relational transfer.

## Prespecified optimization seeds

Use the same three seed values used in the E5 post-confirmatory seed-robustness suite:

- 20260829
- 20260830
- 20260831

Every seed must be reported. No seed may be dropped, replaced, rerun selectively, or selected by source or target performance.

## External targets

Evaluate every seed on both already-frozen targets with no target-side search:

1. ZuCo 2.0 Task 1 normal-reading EEG, frozen 17-participant representation and nuisance model
2. SMN4Lang fMRI, frozen LanA mask, story/timepoint geometry, nuisance controls, HRF, participants and inference

The existing target evaluation code is reused. Only model loading/encoding is replaced so that it loads the frozen multilingual-BERT adapters and computes the prespecified BERT embedding.

## Per-seed estimands

For each target and seed report:

- participant-level neural-guided minus text-only RSA delta
- mean delta
- median delta
- number/fraction positive
- participant bootstrap 95% interval
- exact sign-flip inference using the existing target-specific implementation

Cross-seed summaries are descriptive and must report all three seeds.

## Decision interpretation

- all three seed means positive on both targets: strong post-confirmatory evidence against E5 optimization/model-family specificity
- mixed seeds or one-target-only transfer: partial model-family robustness
- no positive transfer: model-family robustness not established under this frozen strict-portability test

No result triggers lambda, layer, pooling, checkpoint, target, participant, ROI, lag, HRF, representation, or model search.

## Guardrails

- no ZuCo or SMN4Lang data enter training
- no external target enters model/lambda/seed selection
- no ChineseEEG run-07 access
- no new downstream benchmark search
- no rescue tuning after seeing results
- all outcomes are labeled post-confirmatory
