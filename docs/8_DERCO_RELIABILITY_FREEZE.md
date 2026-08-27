# DERCo EEG-only reliability freeze

This document freezes the DERCo reliability analysis before any DERCo neural reliability statistic is computed.

## Cohort and files

- Dataset: DERCo narrative-reading EEG.
- Cohort: all 22 public participants already materialized on the RunRelay DERCo execution branch.
- Articles: all five articles, analyzed separately.
- No participant or article may be selected or excluded using a neural or model outcome.

## Item identity

The authoritative item key is the retained MNE event label itself, parsed as `<word>_<article>_<stimulus_index>`.

- Primary item key: `(article, stimulus_index)`.
- Word text is the word component of the same event label.
- Within each article, reliability uses the intersection of item keys retained by all 22 participants.
- The event-label item-identity audit must already have passed: parseable labels, article consistency, unique strictly increasing stimulus indices within every participant/article file, and zero cross-participant word conflicts for a shared `(article, stimulus_index)` key.

## Primary EEG representation

For every retained epoch and EEG channel:

1. Use EEG channels only.
2. Average voltage across the full stored epoch time window to obtain one value per channel (`row_mean_all`).
3. Within participant and article, restrict to the frozen all-participant common item set.
4. Featurewise z-score each channel across items with population standard deviation (`ddof=0`). Constant channels, if any, are assigned unit scale after centering.
5. Compute the item-by-item neural RDM using correlation distance (`1 - Pearson correlation`) across channel-feature vectors.

No alternate time window, channel subset, representation, filtering choice, or item subset may be selected after seeing reliability.

## Leave-one-participant-out reliability

For each participant and article:

1. Compute that participant's neural RDM.
2. Compute the elementwise mean neural RDM of the other 21 participants on the identical common item set.
3. Primary reliability is the Pearson correlation between the participant RDM and the leave-one-out group RDM after separately residualizing both vectors against the same prespecified nuisance design.

### Prespecified nuisance design

Within each article, construct two pairwise nuisance vectors from the frozen event-label items:

- absolute stimulus-index difference;
- absolute word-length difference, using the event-label word string.

Include an intercept. Residualize the participant neural RDM and the leave-one-out group RDM separately by ordinary least squares against this nuisance design, then correlate the two residual vectors.

The raw, non-residualized leave-one-out RDM correlation is reported only as a sensitivity.

## Across-article aggregation

For each participant:

- Fisher-z transform each of the five article-level reliability correlations;
- take the unweighted mean Fisher-z across articles;
- transform back with `tanh` to obtain the participant aggregate.

All five articles are required. The analysis stops as structurally infeasible if any article has fewer than 100 all-participant common items.

## Primary inference and reliability gate

Inference is over the 22 participant aggregate reliability values.

Report:

- mean;
- median;
- number positive;
- participant bootstrap 95% confidence interval for the mean, using 10,000 bootstrap resamples and fixed seed `20260827`;
- exact one-sided sign-flip p-value for the participant mean when computationally feasible, otherwise a fixed-seed Monte Carlo sign-flip p-value with at least 100,000 draws clearly labeled as approximate.

The prospective reliability gate **passes only if**:

1. the participant-level mean primary residual reliability is greater than zero; and
2. the 95% participant bootstrap confidence interval lower bound is greater than zero.

If the gate fails, the frozen DERCo E5 transfer is not run. If the gate passes, exactly one prespecified transfer comparison may be run: ChineseEEG-trained multilingual-E5 neural-guided `lambda = 0.10` minus matched text-only `lambda = 0`, with no DERCo tuning.

## Guardrails

- This reliability job may load EEG amplitudes but may not load E5, BERT, any embedding model, or any NeuroSem model checkpoint.
- It may not compute semantic RSA or transfer outcomes.
- No participant, article, representation, nuisance, or item subset may be changed based on the reliability result.
- `row_std_all` and `relative_8bin_all` remain pre-existing sensitivities only and are not part of this gate unless run later under a separately frozen analysis.
