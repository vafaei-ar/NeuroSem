# NeuroSem current NMI and mechanism status

**Updated:** 2026-09-26

This file separates the submission-facing Nature Machine Intelligence (NMI) work from the post-confirmatory target-compatibility mechanism project. The separation is intentional: the mechanism analyses use outcomes that were already known when the mechanism protocol was frozen, so they are explanatory follow-up analyses rather than prospective confirmation of the original transfer claim.

## NMI submission lane

### Current Word master

The current external Word master remains **v1.19.5**. Exact filenames, hashes and QA details remain in `paper/CURRENT_MANUSCRIPT.md`.

### New specificity result that should be integrated before submission

The displacement-matched structured MPNet surrogate experiment is complete under the frozen protocol in `docs/NMI_MATCHED_MPNET_SURROGATE_V1.md`.

The selected surrogate dose was `lambda=0.03`, chosen from source-side displacement only before either external outcome was opened. Mean source-side displacement was closely matched to genuine neural guidance:

- genuine neural mean `1 - CKA = 0.00188195`;
- matched MPNet mean `1 - CKA = 0.00193669`.

External results:

- **ZuCo:** genuine neural minus matched surrogate mean **+0.00138471**, 15/17 participant-averaged contrasts positive, 95% CI **[+0.00087856,+0.00190007]**, Holm-adjusted two-sided sign-flip **P=0.00012207**. Matched surrogate minus text-only mean **-0.00011827** and was near-zero/inconsistent across seeds.
- **SMN4Lang fMRI:** genuine neural minus matched surrogate mean **+0.00189761**, 12/12 positive, 95% CI **[+0.00172727,+0.00204934]**, Holm-adjusted two-sided sign-flip **P=0.00048828**. Matched surrogate minus text-only mean **-0.00121820**, 0/12 positive after seed averaging.

Interpretation: specificity relative to this structured non-neural target survives displacement matching. This does **not** establish neural uniqueness over all possible structured targets.

### Planned NMI revision

Prepare **v1.19.6** by integrating the matched-surrogate result into the main specificity narrative, Figure 3/legend as needed, Results, Methods, Discussion and Supplement. Retain the earlier unmatched `lambda=0.10` surrogate as historical/contextual evidence rather than the primary specificity control.

The target-compatibility mechanism analyses below are **not NMI submission blockers** and should not be added wholesale to v1.19.6. Their role is a technical/mechanistic follow-up unless an explicit manuscript decision is made after they are complete.

## Target-compatibility mechanism lane

Protocol: `docs/TARGET_COMPATIBILITY_MECHANISM_V1.md`.

Central question: why does the same ChineseEEG-derived E5 update help some reliable neural targets, hurt others, and leave others inconclusive?

Historical target taxonomy was frozen before the new mechanism outcomes:

- ZuCo: reliable-positive;
- SMN4Lang fMRI: reliable-positive;
- DERCo: reliable-negative;
- TMNRED: reliable-null/inconclusive;
- Garnett Dream: reliable-null/inconclusive.

### Stage 1: fixed E5 dose curves

**Complete** via RunRelay job `S4K7M2V9`. All historical `lambda=0` and `lambda=0.10` values were reproduced with zero numerical error before new dose values were accepted.

Observed patterns:

| Target | Fixed-grid behavior |
|---|---|
| ZuCo | positive from `lambda=.01`, increasingly positive through `lambda=1` |
| SMN4Lang fMRI | positive through `lambda=.30`, reverses at `lambda=1` |
| DERCo | negative at every nonzero dose, including `lambda=.01` |
| TMNRED | near-zero/heterogeneous across the grid |
| Garnett Dream | weak/inconclusive at low dose, positive at `lambda=.30` and `1` |

DERCo is the cleanest evidence against a simple "wrong dose" explanation. Its mean delta-RSA is already **-1.2569e-5** at `lambda=.01` and becomes more negative as dose rises.

### Stage 2: source-target gradient compatibility

Common reference: primary seed-20260823 text-only E5. Gradients are restricted to the same ordered LoRA query/value parameter subspace.

Completed:

- **ZuCo** (`G7V2K9M4`): mean cosine **+0.0944104**, median **+0.0928263**, 17/17 positive, participant-bootstrap 95% CI **[+0.0760572,+0.1122710]**.
- **DERCo** (`C9V4N7K2`): mean cosine **-0.0692558**, median **-0.0925521**, 8/22 positive, participant-bootstrap 95% CI **[-0.1175057,-0.0191199]**.

These two completed targets match the mechanistic hypothesis: the reliable-positive target is locally aligned with the ChineseEEG objective, while the reliable-negative target is locally conflicting.

In progress:

- **SMN4Lang fMRI**: `M8R4K7V2`, using the numerically validated memory-efficient two-pass chain-rule implementation. The earlier fMRI failure was GPU-memory exhaustion, not a scientific result.

Still to run sequentially after fMRI:

- TMNRED;
- Garnett Dream.

Their earlier `WORKFLOW_FAILED` states were dispatch-authorization expiry before task execution, not scientific failures.

After all five targets finish, run the frozen aggregate task and report the five-target compatibility table without target redefinition, rescue analysis or parameter-subspace search.

## After Stage 2

For the **NMI paper**, stop at the matched-surrogate v1.19.6 revision unless an editor/referee requests more.

For the **mechanism/technical paper**, proceed only after the five-target gradient table is complete:

1. decompose the ChineseEEG-induced E5 relational displacement;
2. build shared interpretable neural-geometry fingerprints;
3. consider model-independent Gromov-Wasserstein comparison;
4. use one orthogonal robustness method, not a metric battery.

The organizing technical hypothesis remains:

`Transfer = f(source-target objective compatibility, model baseline geometry, update displacement, adaptation operator)`.
