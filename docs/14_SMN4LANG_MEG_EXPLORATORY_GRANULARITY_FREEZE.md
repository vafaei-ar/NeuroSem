# SMN4Lang MEG exploratory temporal-granularity freeze

## Status

This document was committed only after the prospectively frozen 32-bin SMN4Lang MEG reliability gate failed, and before computing any alternative MEG reliability result or any MEG model-alignment result.

The confirmatory MEG analysis remains failed and closed. Nothing in this exploratory branch changes, replaces, or rescues that confirmatory result.

## Exploratory question

Does the failure of the frozen 32-bin sensor-level MEG story geometry reflect overly fine normalized-time granularity rather than a complete absence of reproducible cross-participant story geometry?

## Fixed candidate family

Exactly three coarser alternatives will be evaluated: 4, 8, and 16 equal normalized-time bins.

For every candidate, all other representation choices remain identical to the completed 32-bin primary analysis:

1. Use the released preprocessed 1-40 Hz task-RDR MEG.
2. Exclude samples covered by released bad annotations.
3. Concatenate the remaining valid samples in original temporal order.
4. Divide that valid-sample sequence into the candidate number of equal normalized-time bins.
5. Within each bin compute one RMS field magnitude across all retained magnetometer samples and one RMS field magnitude across all retained planar-gradiometer samples.
6. Z-score the magnetometer bin values across bins and the planar-gradiometer bin values across bins separately, using population SD (ddof=0).
7. Concatenate magnetometer values followed by gradiometer values, yielding 8D, 16D, and 32D run vectors for 4, 8, and 16 bins respectively.
8. Within each participant, compute the 60 x 60 story RDM using correlation distance between run vectors.
9. Use the same 1770 upper-triangle story-RDM edges and participant leave-one-out Spearman reliability definition as the primary analysis.
10. Keep the participant as the inferential unit (n=12).

No frequency, latency, sensor-subset, source-space, annotation, normalization, distance-metric, or model search is permitted in this exploratory family.

## Reliability inference

For each candidate report:

- mean and median participant leave-one-out Spearman reliability;
- all 12 participant values and number positive;
- participant bootstrap confidence interval using 10,000 draws and seed 20260828;
- exact one-sided sign-flip p value over all 2^12 sign assignments.

Because three alternatives are tested after the failed primary analysis, exploratory familywise reliability is defined conservatively as:

- mean reliability > 0;
- 98.333333% participant-bootstrap CI entirely > 0 (Bonferroni-adjusted two-sided familywise 95% coverage across three candidates);
- exact one-sided sign-flip p < 0.05 / 3 = 0.0166666667.

The unadjusted 95% CI and p value will also be reported descriptively.

## Deterministic selection rule for any later exploratory model test

If no candidate meets the familywise reliability rule, stop the MEG branch. Do not run E5 on MEG.

If one or more candidates meet the familywise reliability rule, designate the **finest passing candidate** (largest number of bins among 4, 8, 16) as the sole exploratory MEG representation eligible for one later model test.

That later test, if authorized, must be limited to the already frozen multilingual-E5 lambda 0.10 versus lambda 0 contrast. Candidate selection must not use model outcomes, and no MEG model result may be inspected before this reliability-only selection is complete.

## Interpretation guardrail

Any positive result from this branch is post-confirmatory and exploratory. It may support a representation-dependence or temporal-granularity interpretation, but it must not be presented as if the original 32-bin prospective MEG gate passed.
