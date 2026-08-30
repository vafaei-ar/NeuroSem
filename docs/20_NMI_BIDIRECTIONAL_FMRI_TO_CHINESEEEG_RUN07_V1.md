# NMI bidirectional fMRI-to-ChineseEEG run-07 secondary check v1

## Status
Post-confirmatory secondary consistency analysis. This is not a new prospective confirmation because ChineseEEG contributed to the broader NeuroSem development history.

## Frozen question
Does the already-selected SMN4Lang-fMRI-guided multilingual-E5 candidate produce a positive paired change in neural alignment on the sealed ChineseEEG run-07 holdout relative to its matched lambda=0 control?

## Candidate lock
- Model: intfloat/multilingual-e5-large
- Revision: 3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3
- Source: SMN4Lang fMRI only
- Selected lambda: 0.01
- Selection occurred before ZuCo and before this ChineseEEG run-07 evaluation.
- Control: matched fMRI-source lambda=0 adapter from the same calibration run.

## Target and analysis
- Target: ChineseEEG sealed run-07 temporal-mean EEG representation already used by the frozen holdout evaluator.
- Subjects: the same ten frozen run-07 subjects used by the existing evaluator.
- Nuisance set, row identity, partial-Spearman statistic and within-chapter permutation machinery are unchanged from scripts/analysis/assess_chineseeeg_run07_holdout_fast.py.
- No ChineseEEG representation, item, subject, model, layer, checkpoint or lambda selection is permitted.

## Primary secondary statistic
For each frozen subject, compute the existing run-07 partial-Spearman RSA for the fMRI-guided lambda=.01 candidate and matched lambda=0 control. Define delta = guided - control.

Report:
- mean and median paired delta;
- number/fraction of subjects with positive delta;
- exact paired sign-flip p-value over all 2^10 sign patterns, one-sided greater and two-sided;
- 10,000-resample participant bootstrap percentile 95% CI, seed 20260830.

## Interpretation
A positive result is a secondary directional consistency result. It does not upgrade ChineseEEG to a fresh independent confirmation and does not alter the primary status of the ZuCo fMRI-to-EEG test. A null or negative result is retained as a boundary result; no rescue tuning is permitted.
