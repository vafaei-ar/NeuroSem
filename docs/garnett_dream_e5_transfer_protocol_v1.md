# Garnett Dream E5 Transfer Protocol v1

**Frozen:** 2026-08-26

## Purpose

Run the single confirmatory ChineseEEG-to-Garnett-Dream multilingual-E5 model validation after the prospectively frozen Garnett EEG reliability gate passed and the exact presentation-row to segmented-text mapping was resolved model-blind.

Garnett Dream is a **same-participant / new-text validation**. It is not an independent-cohort replication.

## Preconditions already satisfied

1. The Garnett structural/materialization freeze is complete.
2. The primary EEG representation `row_mean_all` showed positive cross-subject reliability before any Garnett model outcome was inspected.
3. Exact presentation-row text mapping is frozen for all 18 chapters using the unique non-display segmented XLSX workbook for each run.
4. The mapping rule is `CHxx_ROWyyyy -> physical XLSX row yyyy + 1`, with physical row 1 validated as the `Chinese_text` schema header.

## Frozen EEG target

Use `row_mean_all` only for the confirmatory model-transfer endpoint:

- average EEG over time separately within every retained EEG channel for each `ROWS -> ROWE` presentation interval;
- do not average across channels;
- feature-wise z-score across items within chapter;
- construct a correlation-distance neural RDM.

The predeclared `row_std_all` and `relative_8bin_all` representations remain sensitivity analyses and must not replace the primary target based on Garnett outcomes.

## Frozen model contrast

Use only the already-trained ChineseEEG multilingual-E5 adapters:

- `lambda = 0`: matched text-only adapter;
- `lambda = 0.10`: neural-guided adapter previously frozen for external transfer.

Primary contrast:

`Delta RSA = residual RSA(lambda=.10) - residual RSA(lambda=0)`

No Garnett training, fine-tuning, adapter selection, lambda selection, architecture selection, layer selection, or pooling selection is allowed.

## Frozen text mapping

For chapter/run `xx` in 1..18, use the unique non-display Garnett segmented workbook identified by the model-blind XLSX mapping freeze.

- validate the first nonempty row as the one-cell `Chinese_text` schema header;
- read each subsequent nonempty one-cell row in order as the text corresponding to the frozen presentation item;
- require the number of text rows to equal the frozen `ROWS -> ROWE` item count exactly;
- do not skip, merge, split, or reorder text rows after seeing model outcomes.

## Nuisance residualization

Now that exact text is available, restore the full applicable Little-Prince-style nuisance family prospectively for each chapter:

1. within-chapter row/order difference;
2. participant-specific presentation-duration difference;
3. Chinese-character-count difference;
4. Unicode punctuation-count difference;
5. Chinese-character-set Jaccard distance.

For Chinese character quantities, use the same CJK character definition as the existing external-transfer code. Chapter identity is constant within a chapter and is therefore not an informative within-chapter nuisance RDM.

Residualize both neural and model RDM edges using the same participant/chapter nuisance set before computing Spearman RSA.

## Analysis and inference

- Analyze each chapter separately.
- For each participant and each available chapter, compute nuisance-residualized Spearman RSA for `lambda=0` and `lambda=.10`.
- Aggregate chapter-level RSA values within participant by equal-weight Fisher-z averaging.
- Compute the participant-level `lambda=.10 - lambda=0` difference.
- Participant is the inferential unit.

Primary report:

- mean participant delta;
- median participant delta;
- fraction of participants with positive delta;
- participant-bootstrap 95% CI of the mean delta;
- exact sign-flip one-sided and two-sided inference.

## Guardrails

- No Garnett outcome-driven participant, chapter, item, sensor, window, representation, model, or lambda selection.
- No post-confirmatory search if the primary result is null.
- Do not reinterpret Garnett as independent-participant evidence.
- A positive result supports new-narrative generalization of the neural-guided alignment advantage within the original participant/acquisition family.
- A null result narrows narrative/model-transfer generalization and does not alter the independent TMNRED or ZuCo results.

## Manuscript role

This is the final planned outcome-bearing Garnett analysis for the primary manuscript unless a clearly labeled post-confirmatory sensitivity analysis is justified later.
