# NMI displacement-matched MPNet surrogate protocol v1

**Status:** frozen after source-side genuine-arm calibration and before any displacement-matched surrogate adapter is trained or any matched-surrogate external outcome is observed.

## Scientific question

Does genuine ChineseEEG relational guidance at lambda = 0.10 still outperform a structured non-neural MPNet target after the two interventions are matched as closely as prespecified on achieved E5 representation-space displacement?

This analysis is post-confirmatory with respect to the original NeuroSem evidence hierarchy. It is outcome-blind with respect to the displacement-matched surrogate experiment itself.

## Fixed surrogate and training components

Use exactly the already-defined structured non-neural target from `docs/NMI_ALTERNATIVE_SIGNAL_SURROGATE_V1.md`:

- target model: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`;
- immutable revision: `4328cf26390c98c5e3c738b4460a05b95f4911f5`;
- same ChineseEEG source rows and identities as the existing surrogate protocol;
- final-hidden-state attention-mask mean pooling;
- L2 normalization;
- no prefix;
- max length 64;
- participant-specific residualization against the same six source nuisance RDMs;
- participant residuals averaged and each run target z-standardized.

Train multilingual E5 revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3` with the same LoRA, symmetric dropout-view InfoNCE and five-epoch schedule as the existing three-seed genuine-neural robustness analysis. Reuse the completed seed-matched text-only adapters.

Fixed seeds:

- 20260829
- 20260830
- 20260831

No checkpoint search, seed exclusion, target substitution, pooling change, layer change, or model substitution is allowed.

## Source-side displacement calibration

Dose selection uses no ZuCo or SMN4Lang stimulus text, neural data, or transfer outcomes.

The calibration item set is the ordered concatenation of the canonical ChineseEEG source texts from runs 01-06 already materialized for the frozen MPNet surrogate target. The set contains 2,045 items.

RunRelay calibration job `M7K4V2R9` measured the genuine-neural lambda=0.10 displacement relative to each seed-matched text-only adapter on these source-side items before this protocol freeze.

Primary displacement metric:

`delta = 1 - linear centered CKA(guided, seed-matched text-only)`

Genuine-neural per-seed delta values:

- seed 20260829: 0.0017345938544773842
- seed 20260830: 0.002738781503764942
- seed 20260831: 0.0011724880535533

Three-seed mean:

`delta_g = 0.001881954470598542`

Observed maximum absolute seed deviation from the mean:

`d_seed = 0.0008568270331664001`

Fixed 25% relative floor:

`d_floor = 0.25 * delta_g = 0.0004704886176496355`

Tolerance half-width:

`t = max(d_seed, d_floor) = 0.0008568270331664001`

Accepted displacement band:

`[delta_g - t, delta_g + t] = [0.001025127437432142, 0.002738781503764942]`

This is a deterministic tolerance anchored to the observed three-seed variation of the genuine arm with a prespecified 25% minimum width. It is not presented as an estimated population noise distribution.

Calibration summary SHA-256:

`c9b9a8039068604629188153d29bcc236a9f32bcc2bb5f5e89a4d17f0d4855c1`

## Fixed surrogate dose grid

Train all three seeds at each of:

`lambda in {0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05}`

For each lambda, compute the primary source-side displacement metric separately by seed and average delta across the three fixed seeds. One common lambda is selected for all three seeds.

Secondary diagnostics are reported but cannot change dose selection:

- mean corresponding-item cosine similarity;
- pairwise cosine-distance RDM Pearson correlation;
- pairwise cosine-distance RDM Spearman correlation;
- centered linear CKA;
- k=10 nearest-neighbour Jaccard overlap.

The companion median corresponding-item cosine may be retained because the existing diagnostic implementation exports it.

## Matching rule

A grid point is matched if its three-seed mean surrogate delta lies inside the fixed accepted displacement band.

If several grid points match, select the point minimizing:

`abs(log(delta_surrogate / delta_g))`

If exactly tied, select the lower lambda.

### One permitted displacement-only refinement

If no initial grid point matches, exactly one additional lambda may be trained under one of the following deterministic rules:

1. If all grid means are below the lower tolerance bound, double the largest grid lambda.
2. If all grid means are above the upper tolerance bound, halve the smallest grid lambda.
3. If two adjacent lambdas bracket the tolerance band but neither falls inside it, add the geometric midpoint `sqrt(lambda_low * lambda_high)`.

The refinement decision uses only source-side displacement. No external stimulus, neural, or transfer outcome may be read.

After this single refinement, stop. If no point falls inside the band, report that no displacement-matched surrogate was available within the prespecified grid/refinement rule and do not run external evaluation.

## External evaluation

External evaluation is allowed only after one matched lambda and all three corresponding adapters are fixed and hashed.

Evaluate each selected surrogate adapter exactly once on the unchanged frozen:

- ZuCo 2.0 Task 1 Normal Reading pipeline, n = 17 participants;
- SMN4Lang fMRI pipeline, n = 12 participants.

For each seed and target, retain:

- matched-surrogate minus seed-matched text-only participant effects;
- mean DeltaRSA;
- participant-bootstrap 95% CI;
- participant sign count.

### Primary specificity estimand

For each participant and target, first compute within seed:

`genuine-neural DeltaRSA - matched-surrogate DeltaRSA`

Then average this difference across the three fixed seeds within participant.

Participant is the inferential unit.

For each target separately report:

- mean participant genuine-minus-surrogate effect;
- median participant effect;
- number of positive participants;
- 10,000-resample participant-bootstrap percentile 95% CI;
- exact two-sided participant sign-flip P value.

The two target P values form one family and are Holm-corrected across ZuCo and SMN4Lang.

Individual seed results are descriptive robustness information and are not treated as independent inferential units.

No equivalence conclusion is permitted from a non-significant genuine-minus-surrogate test.

## Interpretation fixed before matched-surrogate outcomes

- If matched-surrogate transfer remains non-positive on both targets and genuine-minus-surrogate effects are positive, the experiment strengthens specificity for genuine neural guidance relative to this structured non-neural target at comparable displacement. It still does not establish uniqueness over all possible structured targets.
- If matched-surrogate transfer is positive on either target, the neural-origin interpretation must be narrowed for that target. Report the magnitude and the genuine-minus-surrogate contrast without rescue tuning.
- If genuine-minus-surrogate is positive but matched-surrogate transfer is also positive, report partial separation rather than neural uniqueness.
- If no displacement match is obtained under the frozen grid and one permitted refinement, do not evaluate external targets; report the no-match outcome and displacement curve.
- All outcomes are retained.

## Provenance and stop rules

The executable specification is `configs/nmi_matched_mpnet_surrogate_v1.json`. The grid/selection entry point is `scripts/robustness/run_nmi_matched_mpnet_grid_v1.py`; the external entry point is `scripts/robustness/run_nmi_matched_mpnet_external_v1.py`.

The protocol and executable config must be committed before the first matched-surrogate grid job. The exact public commit and RunRelay job chronology are retained as verifiable pre-outcome timestamps. A separate OSF/Zenodo registration may be added by the authors, but is not required for the executable guardrails to operate.

This is the single canonical displacement-matched MPNet experiment for NeuroSem and any later technical-paper reuse. It is not redesigned after seeing an outcome.
