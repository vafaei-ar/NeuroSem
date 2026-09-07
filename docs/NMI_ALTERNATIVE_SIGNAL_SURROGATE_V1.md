# NMI alternative-signal surrogate control v1

## Purpose

This post-confirmatory reviewer-response analysis tests whether a structured, item-linked but non-neural relational target can reproduce the external transfer effect attributed to neural guidance.

The control addresses a different question from the existing shuffled-neural arm. Shuffling the neural target preserves its marginal edge-value distribution while destroying pair identity. The present control instead preserves item identity and supplies a genuine alternative relational signal that is not derived from neural measurements.

## Alternative target

Use one target family only: the sentence geometry of `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`.

The exact immutable model revision must be resolved and written to the materialization summary before any E5 training or external evaluation begins. No alternative model may be substituted after observing an external result.

For ChineseEEG runs 01-06:

1. Use the same canonical text rows and row identities as the existing E5 source protocol.
2. Encode each row with the frozen multilingual MPNet model using the final hidden state, attention-mask mean pooling, L2 normalization, no prefix, maximum length 64.
3. Form the pairwise cosine-distance RDM.
4. Residualize the ranked MPNet RDM against the same six source-side nuisance RDMs used when constructing the neural target: run-position lag, duration difference, character-count difference, chapter mismatch, character-set Jaccard distance and punctuation-count difference.
5. Match the neural-target construction at the participant-metadata level: because some nuisance metadata are participant-specific, residualize the same MPNet RDM separately using each contributing participant's six nuisance RDMs, average those participant-specific residuals, then z-standardize the run-level mean target to zero mean and unit variance.

The target-materialization stage must not read EEG feature arrays, neural target values, ZuCo outcomes, SMN4Lang outcomes, transfer results or manuscript conclusions. It may read source-row metadata required to reconstruct the nuisance RDMs and canonical source text identities.

### Pre-outcome implementation clarification

The participant-specific residualization rule in step 5 was made after the first materialization attempts failed before producing any surrogate target or external outcome. The failure showed that nuisance metadata such as duration are not identical across contributing source participants. The original neural-target builder residualizes each participant separately before averaging. This clarification therefore makes the alternative-signal control mirror the already-fixed neural-target nuisance procedure rather than imposing an invalid cross-participant metadata-identity assumption. No surrogate target, E5 adapter, ZuCo result or SMN4Lang result had been produced when this clarification was committed.

## Downstream E5 comparison

After target materialization is complete, train one structured-non-neural E5 arm under exactly the same multilingual-E5 base revision and optimization schedule as the existing three-seed E5 robustness analysis:

- E5 model: `intfloat/multilingual-e5-large`, immutable revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`;
- source runs 01-05 train, run 06 validation, run 07 excluded;
- symmetric dropout-view InfoNCE text objective;
- LoRA rank 8, alpha 16, dropout 0.05, query/value projections;
- five epochs, learning rate 2e-4, weight decay 0.01;
- relational-loss weight lambda = 0.10 only;
- optimization seeds 20260829, 20260830 and 20260831 only.

Use the already-completed seed-matched text-only adapters from `outputs/nmi_multiseed_e5_v1` as the control baseline rather than retraining them.

Evaluate each structured-non-neural adapter exactly once on the unchanged frozen ZuCo and SMN4Lang fMRI external pipelines. No target-side tuning, dose search, checkpoint search, seed exclusion, rescue analysis or surrogate-model substitution is allowed.

## Reporting

Report every seed and both external targets. The primary control quantity is structured-non-neural minus matched text-only DeltaRSA for each seed and target. Participant-level signs and intervals describe consistency across people within a trained model; the three seed results describe robustness across optimization randomness and are not to be treated as three independent experiments.

No formal seed-level hypothesis test is required at n=3. The three seed values should be reported descriptively beside the genuine-neural multi-seed values.

## Interpretation rule fixed before outcomes

- If the structured non-neural target produces positive transfer of comparable direction and scale across the external targets, the manuscript must weaken or remove language implying that the transferable relational constraint is specifically brain-derived.
- If the structured non-neural target is null, negative or substantially less consistent than genuine neural guidance, this strengthens the neural-specific interpretation but does not establish uniqueness relative to every possible structured non-neural target.

This control is post-confirmatory and must be labelled as such in the manuscript.