# 15. Post-confirmatory generalization experiments: design and to-do

**Status:** design-only queue. Do not execute while the current NMI robustness suite is running. These experiments are secondary/post-confirmatory and must not be described as prospective confirmation of the already-observed ZuCo or SMN4Lang outcomes.

## Purpose

Two remaining scientific questions are distinct from the current paper's primary transfer claim:

1. **Model-family generality:** is the externally transferable neural relational effect specific to multilingual E5, or does the same training principle survive a substantially different language-model family?
2. **Source-modality bidirectionality:** does a relational constraint learned from fMRI transfer back to EEG, rather than only EEG-derived supervision transferring to fMRI?

A third, stronger question combines both dimensions in a factorial design. That should be considered only after the first two experiments are interpreted.

## Global guardrails

- Label all experiments here **post-confirmatory generalization analyses**.
- Do not change the current primary evidential chain or retroactively reclassify already-observed outcomes as fresh.
- Freeze every model, model revision, pooling rule, neural target, split, lambda-selection rule, seed set, inferential unit, metric, and stopping rule before execution.
- Do not inspect target outcomes while selecting lambda, checkpoints, layers, representations, ROIs, lags, participants, or stimulus subsets.
- Report every prespecified seed and every prespecified target, favorable or unfavorable.
- No rescue search after a null result.
- Keep the current E5/ChineseEEG -> ZuCo -> SMN4Lang result unchanged as the primary prospective chain.

---

## Experiment A. Second-model-family robustness

### Question

Does the neural-relational training principle produce externally transferable neural alignment in a substantially different multilingual sentence-representation model?

### Recommended role

**Highest-priority next experiment after the current robustness job.** This directly addresses the strongest remaining NMI machine-learning scope limitation.

### Model choice

Select exactly one multilingual encoder before external evaluation using architecture-level criteria only:

- must support both Chinese/Mandarin and English;
- must expose sentence/token embeddings suitable for a frozen pooling rule;
- should differ materially from multilingual E5 in pretraining objective and/or encoder family;
- must be computationally feasible for matched LoRA adaptation;
- selection must not use ZuCo or SMN4Lang performance.

A multilingual MPNet-family sentence encoder is a strong candidate because it is multilingual, embedding-oriented, and materially different from E5. Final model identity and immutable model revision must be frozen in a dedicated protocol before execution.

### Training design

Use the same ChineseEEG source data and the same conceptual two-arm comparison:

- **text-only arm**;
- **neural-guided arm** with the same relational-loss definition.

Prefer a fixed seed set declared in advance. At minimum, use the same number of optimization seeds in both arms and report all of them.

### Lambda rule

Do **not** choose lambda from ZuCo or SMN4Lang outcomes.

Preferred strict portability test:

- first analysis uses **lambda = 0.10**, unchanged from the E5 intervention;
- no alternative lambda is tried after external results are seen.

If model-specific loss scaling makes direct lambda portability demonstrably ill-posed before any external evaluation, an alternative protocol may prespecify a source-only calibration rule using ChineseEEG training/validation data. Such a rule must be frozen before external evaluation and must not use run-07, ZuCo, SMN4Lang, or generic downstream outcomes.

### External targets

Primary post-confirmatory external targets:

1. **ZuCo 2.0 normal-reading EEG**;
2. **SMN4Lang fMRI** using the already-frozen representation and evaluation pipeline.

No target-side search is permitted.

### Primary estimands

For each seed and target:

- participant-level neural-guided minus text-only RSA delta;
- mean and median participant delta;
- fraction of participants positive;
- participant bootstrap interval;
- exact sign-flip inference using the same directional convention as the existing external analyses.

A cross-seed summary is descriptive/post-confirmatory and must report all seeds.

### Interpretation

- Positive transfer in both targets would materially weaken the model-specificity objection.
- Positive transfer in only one target would support partial architecture robustness.
- Null transfer must remain a model-family boundary; do not tune around it.

---

## Experiment B. Bidirectional cross-modal transfer analysis

### Question

Does an **fMRI-derived relational constraint** induce a model perturbation that transfers to independent EEG data?

This is a new secondary experiment and must remain analytically separate from the current prospective EEG-derived -> fMRI result.

### Conceptual direction

Current primary direction:

> ChineseEEG-derived constraint -> model -> ZuCo EEG and SMN4Lang fMRI

New secondary direction:

> SMN4Lang fMRI-derived constraint -> model -> independent EEG

A positive result would support **source-modality bidirectionality**, not merely cross-modal target transfer.

### Source fMRI target

Use only the already-frozen SMN4Lang LanA-mask fMRI representation family and nuisance model. No new ROI, threshold, lag, HRF, temporal unit, or participant search.

Construct a group-level fMRI relational supervision target using a prespecified participant aggregation rule. The exact group-RDM construction must be frozen before training.

### Source split

Create a deterministic, outcome-independent story split before model training, for example a hash-based train/validation partition of the 60 stories. The split must be written to disk and committed before any tuning result is examined.

Recommended purpose:

- training stories: optimize text + fMRI relational loss;
- validation stories: source-only model selection/calibration;
- no EEG outcome may participate in lambda or checkpoint selection.

### Model and optimization

Start with multilingual E5 so that the only major change from the established intervention is the **source neural modality**.

Freeze:

- exact E5 revision;
- LoRA placement/rank/alpha/dropout;
- pooling and normalization;
- text objective;
- optimizer, learning rate, batch construction, and epochs;
- seed set;
- source-fMRI geometry construction.

### Lambda selection

Because fMRI and EEG relational losses can differ in scale, do not assume that lambda=0.10 has identical optimization meaning.

Preferred design:

- freeze a small source-only lambda grid before execution, e.g. the existing development grid `{0, .01, .03, .10, .30, 1}`;
- select the neural-guided candidate using **only held-out SMN4Lang source-validation stories** under a prespecified rule;
- recommended rule: choose the **smallest lambda within one standard error of the best held-out fMRI relational alignment**, with lambda=0 as the text-only control;
- once selected, lock the candidate before any EEG target is evaluated;
- no second lambda search is allowed after EEG results are known.

This is still post-confirmatory because the target datasets are historically known, but it preserves a clean source-only selection boundary.

### EEG targets

**Primary target:** ZuCo 2.0 normal-reading EEG.

Rationale: ZuCo is independent of the fMRI source participants, language/task context, and measurement modality, and it is the strongest existing external EEG target.

**Secondary target:** ChineseEEG sealed run-07, clearly labeled secondary because ChineseEEG was used historically to develop the broader framework.

Do not use either EEG target for lambda, checkpoint, layer, or representation selection.

### Primary estimand

For each EEG target, compare the frozen fMRI-guided model against its matched text-only control using the same participant-level RSA-delta logic as the current transfer analyses.

### Interpretation

- Positive fMRI -> ZuCo transfer would provide the cleanest evidence for bidirectional cross-modal relational transfer.
- Positive fMRI -> ZuCo and fMRI -> ChineseEEG would strengthen the case further, but the ZuCo result should carry more evidential weight.
- A null result would imply directional asymmetry and would not invalidate EEG -> fMRI transfer.
- Do not attribute asymmetry mechanistically without additional evidence; fMRI and EEG differ in temporal resolution, spatial aggregation, noise structure, and the relational supervision object.

---

## Experiment C. Full model-family x source-modality factorial extension

### Question

Does neural relational transfer generalize jointly across **model family** and **source neural modality**?

### Recommendation

**Do not run this immediately.** Treat it as a contingent extension after Experiments A and B.

A clean factorial design would cross:

- model family: E5 vs one prespecified second multilingual encoder;
- source modality: ChineseEEG vs SMN4Lang fMRI;
- external targets: EEG and fMRI.

However, the existing SMN4Lang dataset cannot simultaneously serve as both the fMRI training source and a genuinely independent fMRI target in the fMRI-source cells. A fully symmetric source-target factorial therefore requires either:

1. a genuinely independent reliable fMRI language dataset as the external fMRI target; or
2. a weaker within-dataset held-out participant/story design, which should not be described as equivalent to the current independent external validation.

Because of this asymmetry, running the full factorial now would add substantial complexity without a comparably clean gain in evidential strength.

### Trigger for reconsideration

Reconsider Experiment C only if:

- Experiment A supports second-model robustness; and
- Experiment B supports fMRI -> EEG transfer; and
- a suitable independent fMRI target is available under a frozen reliability-first protocol, or reviewers explicitly request the factorial extension.

---

## Priority recommendation

1. **Complete and interpret the currently running post-confirmatory robustness suite.**
2. **Experiment A: second-model-family robustness.** Highest value for the current NMI model-generality concern.
3. **Experiment B: bidirectional cross-modal transfer.** Highest conceptual value and potentially a major strengthening of the paper.
4. **Experiment C: full factorial extension.** Defer unless A and B are positive and an independent fMRI target makes the design genuinely symmetric.

## Manuscript policy

If A or B is eventually executed, add it as a clearly labeled secondary/post-confirmatory generalization section or Extended Data analysis. Do not change the historical status of the primary ChineseEEG -> ZuCo -> SMN4Lang prospective chain.
