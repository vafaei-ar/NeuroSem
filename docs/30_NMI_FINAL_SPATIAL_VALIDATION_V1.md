# NMI final spatial validation suite v1

## Status and evidence tier

This protocol is frozen after the previously reported regional, dose, and model-family results were known. All analyses below are therefore post-confirmatory. They do not alter the original prospective evidence hierarchy and are intended to challenge the current interpretation rather than search for additional positive effects.

No new model training, lambda search, model search, ROI search, participant selection, story selection, checkpoint selection, or target-side tuning is permitted.

## Frozen inputs

The suite may consume only the existing NeuroSem outputs and adapters already produced by the frozen workflows:

- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/story_results.csv`
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv`
- `outputs/smn4lang_regional_atlas_preflight_v1/latest/dk68_parcels.csv`
- `outputs/nmi_remaining_regional_ideas_v1/latest/regional_participant_results.csv`
- the already-created selected-region neural cache under `outputs/nmi_remaining_regional_ideas_v1/cache_selected_regions/`, rebuilding it from the unchanged SMN4Lang inputs only if it is absent
- the three prespecified reviewer-control E5 seeds `20260829`, `20260830`, and `20260831` under `outputs/nmi_multiseed_e5_v1/`, including their matched `text_only`, `neural`, and `shuffled_neural` adapters.

The primary functional language system remains IFG, IFGorb, MFG, AntTemp, PostTemp, and AngG. The control systems remain left precentral, postcentral, and paracentral cortex for sensorimotor control and left pericalcarine, cuneus, lingual, and lateral occipital cortex for visual control. No region can enter or leave these groups after execution.

The DK language-associated set remains pars opercularis, pars triangularis, superior temporal, middle temporal, inferior parietal, and supramarginal cortex.

## Analysis 1: participant x story robustness

The two previously strongest spatial effects are tested for robustness to the 60 analyzed stories:

1. the left-DK reliability-adjusted language-membership coefficient;
2. the functional temporal-minus-frontal language contrast.

For each participant and region, story RSA values are aggregated with the same Fisher-z mean used by the frozen regional analysis. The reliability-adjusted DK coefficient is computed from all 34 left DK parcels with fixed model-blind regional reliability as a covariate. Temporal language cortex is AntTemp and PostTemp; frontal language cortex is IFG, IFGorb, and MFG.

A 10,000-replicate two-factor bootstrap resamples participants and stories independently with replacement, using the same sampled story indices for all sampled participants in each replicate. The reported sensitivity quantities are the bootstrap 95% CI and the fraction of bootstrap mean effects above zero. These are sensitivity estimates, not a new confirmatory P-value family.

A deterministic leave-one-story-out analysis repeats each effect 60 times, omitting exactly one story on each iteration. Report the minimum, maximum, and number of positive leave-one-story-out estimates. No story may be removed on the basis of its effect.

Bootstrap seed: `20260936`.

## Analysis 2: spatial-autocorrelation-aware cortical null

The observed participant-mean left-DK transfer map is tested against a spatially autocorrelated null. The outcome is the mean lambda=0.10 delta across participants for all 34 left DK parcels. Fixed model-blind reliability is first regressed from the map. Parcel locations are the frozen resampled MNI centroids from `dk68_parcels.csv`.

The null is a centroid-distance variogram-matched surrogate procedure, not a surface-sphere spin test:

1. compute pairwise Euclidean centroid distances;
2. estimate an exponential spatial range by fitting the empirical semivariogram of the reliability-residualized map in six equal-count distance bins over a fixed 64-value geometric grid;
3. generate 10,000 Gaussian spatial fields with covariance `exp(-distance/range)`;
4. rank-map each field to the empirical residual distribution so every surrogate preserves the observed marginal residual distribution while approximately preserving the fitted spatial autocorrelation;
5. add the fixed reliability fit back to each surrogate;
6. refit `delta ~ reliability + DK-language-membership` and store the language coefficient.

The focal statistic is the two-sided surrogate P value for the absolute observed language coefficient. The fitted spatial range is a nuisance parameter estimated without changing the language-region definition.

Spatial-surrogate seed: `20261037`.

## Analysis 3: regional shuffled-target control

For each of the three already-prespecified reviewer seeds, evaluate the matched E5 `text_only`, genuine-neural, and shuffled-neural adapters against the unchanged 13 selected regional SMN4Lang targets. No adapters are retrained.

For each participant and seed compute:

- genuine language specificity = `(genuine - text)` mean in the six functional language parcels minus `(genuine - text)` mean in the seven pooled control parcels;
- shuffled language specificity = `(shuffled - text)` language mean minus `(shuffled - text)` pooled-control mean;
- genuine-minus-shuffled specificity = genuine specificity minus shuffled specificity.

Average each participant's values across the three frozen seeds before primary inference.

Two focal tests share one exact max-absolute-mean sign-flip family over all `2^12` participant sign configurations:

1. genuine-minus-shuffled language specificity;
2. shuffled-minus-text language specificity.

Report participant-bootstrap 95% CIs, exact two-sided sign-flip P values, and the two-test familywise max-statistic P values. Seed-level means and temporal-minus-frontal genuine/shuffled values are descriptive.

## Analysis 4: multilevel synthesis

Use all existing selected-region participant results from the remaining-regional-ideas suite. The goal is synthesis, not discovery.

Two separate repeated-structure regressions are prespecified:

1. all five nonzero E5 doses x cortical system;
2. all six model backbones x cortical system.

For the backbone model, average the three prespecified seeds within participant x region x backbone before fitting so seeds are not treated as independent participants.

Each regression uses:

`delta ~ model-blind reliability + participant fixed effects + condition * cortical system`

where cortical system is language, sensorimotor, or visual. Inference uses Cameron-Gelbach-Miller two-way clustered covariance by participant and region. The focal statistic for each synthesis model is the omnibus Wald test of the complete condition x system interaction block. The two omnibus P values are Holm-corrected together. Incremental ordinary-least-squares R-squared from adding the interaction block is reported descriptively.

Individual interaction coefficients and their two-way-clustered standard errors may be exported for transparency but are not promoted as additional confirmatory discoveries.

## Interpretation rules

- Story robustness supports generalization only if the two-factor bootstrap CIs remain away from zero and leave-one-story-out estimates retain the original sign broadly across all 60 omissions.
- A small spatial-surrogate P value supports language enrichment beyond what is expected from the fitted spatial smoothness of the cortical map. A non-small P value requires explicitly retaining spatial autocorrelation as an alternative explanation.
- The regional shuffled control supports neural-target specificity only if genuine-minus-shuffled language specificity is positive after the frozen two-test correction. A nonzero shuffled-minus-text effect must be reported rather than hidden.
- The synthesis models summarize condition-by-system structure. A significant interaction may support dose- or architecture-dependent spatial organization, but does not convert these post-confirmatory analyses into prospective evidence.
- Negative, null, or contradictory results are retained and reported without rescue tuning or redefinition.

## Expected outputs

The task will write a compact JSON summary, a text report, story leave-one-out table, spatial-surrogate null table, shuffled-control participant and seed tables, synthesis coefficient table, and one code-generated figure for each analysis family.
