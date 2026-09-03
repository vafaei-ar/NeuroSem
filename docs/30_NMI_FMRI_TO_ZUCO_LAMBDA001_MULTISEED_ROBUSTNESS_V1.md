# NMI post-confirmatory fMRI-to-ZuCo lambda=0.01 multi-seed robustness v1

## Status and purpose

This analysis is frozen after the original source-selected fMRI-to-ZuCo lambda=0.01 result and the later reverse-dose/model-family results were known. It is therefore post-confirmatory optimization-seed robustness, not a fresh external confirmation and not a replacement for the original frozen lambda=0.01 test.

Its sole purpose is to estimate whether the very small source-selected lambda=0.01 fMRI-guided effect on the unchanged ZuCo target is stable across three additional fixed optimization trajectories.

## Fixed source, model and target

- Source geometry: the previously frozen SMN4Lang fMRI relational target.
- Source training/validation stories: exactly the same 20-story training and 12-story validation sets used in `run_nmi_bidirectional_fmri_source_calibration_v1.py`.
- Model: `intfloat/multilingual-e5-large`.
- Revision: `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`.
- Target: the unchanged ZuCo 2.0 Task 1 Normal Reading all-retained-channel temporal-mean EEG representation and frozen nuisance-adjusted RSA pipeline used in `evaluate_nmi_bidirectional_fmri_to_zuco_v1.py`.
- Frozen ZuCo cohort: the same 17 participants with all seven normal-reading runs.

Training architecture, LoRA configuration, text objective, fMRI relational objective, pooling, HRF construction, nuisance model, optimizer, learning rate, weight decay, five-epoch story schedule, batch sizes and memory implementation are unchanged from the original fMRI-source calibration.

## Fixed seeds and model contrast

Additional optimization seeds are exactly:

- 20260829
- 20260830
- 20260831

For every seed, train exactly two matched arms:

- lambda=0 text-only control;
- lambda=0.01 fMRI-guided arm.

Both arms execute the same source-story schedule and optimizer-step count. Lambda changes only the contribution of the frozen fMRI relational loss on the matched training steps. No other lambda values are trained or evaluated in this analysis.

No seed, lambda, checkpoint, layer, pooling rule or source-story set may be selected using ZuCo outcomes.

## Target evaluation

For every seed, evaluate both retained arms on the unchanged frozen ZuCo pipeline. No target-side representation, participant, run, item, nuisance, layer, checkpoint or model selection is permitted.

The development seed 20260823 is not retrained by this analysis. Its already-observed primary lambda=0.01 ZuCo result may be shown separately for context, but it is not pooled with the three added seeds as if it were prospectively exchangeable.

## Frozen estimands and reporting

For each added seed, report all 17 participant-level lambda=0.01 minus lambda=0 residual RSA values and the following seed-level summaries:

1. mean delta RSA;
2. median delta RSA;
3. number and fraction of participants with positive delta;
4. participant-bootstrap 95% confidence interval using the unchanged ZuCo bootstrap implementation;
5. exact paired sign-flip probability using the unchanged ZuCo implementation;
6. mean lambda=0 and lambda=0.01 participant RSA values.

Across the three added seeds, report descriptively:

- the three seed-level mean deltas;
- the number of seed-level means greater than zero;
- the mean of the three seed-level mean deltas.

There is no newly declared 3/3-positive success gate. All three trajectories must be retained and interpreted jointly regardless of sign or significance. Human participants remain the biological inferential units within each seed; optimization seeds are robustness trajectories and must not be treated as exchangeable additional human replicates.

## Interpretation guardrails

- The original source-selected lambda=0.01 ZuCo test remains the frozen primary reverse-direction result.
- This analysis can strengthen or qualify confidence in optimization-seed stability of that very small effect, but cannot make the reverse-direction experiment prospectively confirmatory.
- A heterogeneous or null result must be reported without rescue tuning.
- No higher-dose result may be substituted for lambda=0.01 on the basis of this analysis.
- The previously observed reverse-dose gradient remains post-confirmatory characterization and is not reclassified by this run.
- No new lambda search, target-side search or follow-up rescue analysis is permitted after these outcomes are inspected.
