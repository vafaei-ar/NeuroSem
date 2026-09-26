# NeuroSem target-compatibility mechanism protocol v1

**Status:** frozen after the existing transfer outcomes were known, but before any new boundary-target dose curves, gradient-compatibility values, model-displacement decompositions, target fingerprints, Gromov-Wasserstein values, or alternative-metric compatibility outcomes are computed.

This is a separate post-confirmatory mechanism project. It does not alter the prospective status of the original NeuroSem transfer tests.

## Central question

What property of a neural target determines whether the fixed ChineseEEG-induced multilingual-E5 displacement improves, worsens, or leaves unchanged its neural-model alignment?

The working hypothesis is that positive transfer requires both a measurable neural geometry and compatibility between the ChineseEEG relational objective and the target relational objective. Reliability alone is not sufficient.

## Frozen target taxonomy

The taxonomy below is based only on already-completed results audited by RunRelay job `C7M4K2V9` before this protocol freeze.

### Primary mechanism set: reliable target geometries with completed E5 transfer

1. **ZuCo EEG: reliable-positive**
   - primary residual reliability mean 0.0674193, 17/17 participants positive;
   - lambda=.10 minus lambda=0 transfer mean +0.00166370, 17/17 positive, bootstrap CI entirely above zero.

2. **SMN4Lang fMRI: reliable-positive**
   - reliability gate passed, mean residual LOO approximately 0.653;
   - lambda=.10 minus lambda=0 transfer mean +0.00085250, 12/12 positive, bootstrap CI entirely above zero.

3. **DERCo EEG: reliable-negative**
   - reliability gate passed, mean approximately 0.1589, 22/22 positive;
   - lambda=.10 minus lambda=0 transfer mean -0.000118929, 4/22 positive, bootstrap CI entirely below zero.

4. **TMNRED EEG: reliable-null/inconclusive**
   - primary row_mean_all reliability bootstrap CI is above zero;
   - lambda=.10 minus lambda=0 transfer mean +0.00002036, bootstrap CI crosses zero, 16/29 approximately positive.

5. **Garnett Dream EEG: reliable-null/inconclusive**
   - primary row_mean_all reliability is positive, 10/10 participants positive;
   - lambda=.10 minus lambda=0 transfer mean +0.00032659, bootstrap CI crosses zero, 6/10 positive.

These labels are historical outcome labels for this mechanism study and may not be changed after any new compatibility result.

### Excluded from the primary mechanism set

- **SMN4Lang MEG:** excluded because the prospectively frozen primary reliability gate failed. It remains a measurement-failure boundary and no transfer/compatibility mechanism is inferred from it.
- **Nature directional-word EEG:** excluded from the primary mechanism set because split-half reliability was prespecified as diagnostic only and was never a reliability gate. It may be used later only as explicitly labeled descriptive sensitivity.

## Stage 1: fixed E5 dose curves on every reliable target

Use exactly the already-trained ChineseEEG-source E5 arms:

`lambda = {0, .01, .03, .10, .30, 1.0}`

All use `intfloat/multilingual-e5-large` revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`, primary seed 20260823, and the original five-epoch training recipe. No adapter is trained or selected in this project.

Adapter provenance:

- 0.00: `outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter`
- 0.01: `outputs/e5_neural_tuning_pareto_v1/lambda_0p01/neural/20260823_192219/adapter`
- 0.03: `outputs/e5_neural_tuning_pareto_v1/lambda_0p03/neural/20260823_192323/adapter`
- 0.10: `outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural/20260823_192425/adapter`
- 0.30: `outputs/e5_neural_tuning_pareto_v1/lambda_0p30/neural/20260823_192528/adapter`
- 1.00: `outputs/e5_neural_tuning_v1/neural/20260823_181609/adapter`

ZuCo and SMN4Lang full six-dose curves are already completed and are reused unchanged from `outputs/nmi_forward_external_dose_characterization_v1/latest`.

DERCo, TMNRED, and Garnett Dream are evaluated on the full fixed grid using exactly their already-frozen primary target pipelines. No representation, nuisance set, participant, item, run/article/chapter, layer, pooling rule, or dose is selected from the new outcomes.

### Reproduction gate

Before any new dose value for DERCo, TMNRED, or Garnett is accepted, the multi-dose implementation must reproduce the already-observed lambda=0 and lambda=.10 participant-level outputs from the original frozen evaluator to numerical tolerance. If the reproduction gate fails, stop that target and report the implementation mismatch rather than continuing.

### Stage-1 outputs

For every target and every nonzero dose report participant-level:

`DeltaRSA(lambda) = RSA(lambda) - RSA(lambda=0)`

and summarize mean, median, positive count/fraction, participant bootstrap 95% CI, and exact two-sided sign-flip P where exact enumeration is computationally feasible. These are characterization statistics. No multiplicity-adjusted "best dose" claim and no target-specific dose selection is permitted.

The scientifically relevant descriptive patterns are:

- same-sign effect from the smallest nonzero dose onward: compatible/incompatible direction is plausible;
- near-zero low doses with divergence at larger doses: magnitude sensitivity is plausible;
- sign reversal across dose: non-linear or overshoot behavior;
- near-zero throughout: weak coupling/orthogonality.

No new dose may be added after the curves are opened.

## Stage 2: source-target gradient compatibility

This is the primary mechanistic analysis.

### Reference model and trainable parameter space

Use the primary seed-20260823 **lambda=0 text-only E5 adapter** as the common reference point.

Compute gradients only with respect to the same LoRA query/value trainable parameter subspace used by the original E5 intervention. Backbone weights remain frozen.

### Differentiable relational objective

For every source/target unit, use a differentiable nuisance-adjusted relational objective:

1. encode the unit's fixed text items with E5 using the frozen query prefix, final-hidden attention-mask mean pooling and L2 normalization;
2. compute pairwise cosine-distance model edges;
3. residualize model edges against the unit's already-frozen nuisance design using the same linear projection as the external pipeline, where applicable;
4. use the already-frozen neural RDM/target for that unit and apply the corresponding fixed nuisance residualization;
5. z-standardize the residual edge vectors;
6. define `L = 1 - PearsonCorr(model_residual_edges, neural_residual_edges)`.

This objective is deliberately differentiable and is not claimed to be identical to the rank-based external Spearman RSA. It tests local objective compatibility in the same nuisance-adjusted relational space.

### Source gradient

For ChineseEEG source runs 01-05, compute the gradient of the existing group neural relational target loss at the common text-only reference model. Average the five run losses with equal weight before differentiation:

`g_S = grad_theta mean_r L_ChineseEEG,r`.

Run 06 remains source validation and run 07 is not used.

### Target participant gradients

For each participant in each primary-mechanism target, compute the equal-weight mean target loss across that participant's frozen units before differentiation:

- ZuCo: seven NR runs;
- SMN4Lang fMRI: 60 stories;
- DERCo: five articles;
- TMNRED: eight sessions;
- Garnett Dream: all frozen available chapters for that participant.

Then:

`g_T,i = grad_theta mean_u L_T,i,u`.

### Compatibility statistic

Flatten the same ordered LoRA q/v gradient coordinates for source and target and compute:

`C_i = dot(g_S, g_T,i) / (norm(g_S) norm(g_T,i))`.

Interpretation is local and first-order:

`Delta L_T approx -eta dot(g_T, g_S)`.

Therefore positive cosine means a small source-gradient descent step is locally aligned with decreasing the target objective; negative cosine means local conflict.

### Reporting

For each target report all participant cosines, mean, median, positive count/fraction, and a fixed 10,000-resample participant bootstrap 95% CI of the mean. The bootstrap RNG seed is fixed at `20260926`.

### Differentiable residualization implementation clarification

This clarification is frozen before any Stage-2 gradient-compatibility value is computed.

- For pipelines whose historical nuisance regression used ordinary linear residualization, construct the identical fixed nuisance design (including the intercept) and apply its linear projection to differentiable raw model cosine-distance edges.
- For ChineseEEG, the frozen neural target was built by participant-specific regression on rank-z nuisance columns before participant averaging. The differentiable model side therefore uses the same participant-specific **rank-z nuisance design matrices**, residualizes the raw model cosine-distance edge vector separately for each contributing source participant, averages those residual model vectors, and then z-standardizes before correlation with the already-frozen group neural target.
- For Garnett Dream, where the historical reliability/transfer pipeline rank-transformed the neural/model RDM and nuisance columns before regression, the fixed rank-z nuisance design is retained but the differentiable model edge vector itself is not rank-transformed. It is linearly residualized against that frozen rank-z nuisance design and z-standardized. The neural comparator remains the historical rank-residualized target. This is the prespecified differentiable approximation required for a valid parameter gradient.
- No alternative differentiable ranking surrogate, nuisance parameterization, or source-participant aggregation may be introduced after Stage-2 outcomes are opened.

Because the positive/null/negative transfer labels were already known when this analysis was designed, the association between gradient sign and historical transfer class is explicitly post-confirmatory mechanistic evidence, not a prospective prediction.

No parameter subset, layer, gradient normalization, participant subset, target unit, or nuisance set may be changed after the compatibility values are opened.

## Stage 3: decompose the ChineseEEG-induced E5 displacement

For each target's own fixed text items, compute model RDMs for lambda=0 and the original genuine lambda=.10 arm:

`DeltaD_model = D_.10 - D_0`.

Use one fixed interpretable candidate family shared across applicable datasets:

- frozen sentence-embedding semantic distance from one external sentence model;
- lexical overlap/Jaccard distance;
- length difference;
- punctuation-count difference;
- temporal/order distance where defined.

Dataset-specific already-frozen nuisance terms remain nuisances and are not rebranded as candidate mechanisms.

Fit the same standardized linear edge decomposition to `DeltaD_model` within each fixed unit and summarize coefficients across units/participants. This stage explains what relations E5 changed; it is not treated as an independent transfer predictor.

## Stage 4: neural relational fingerprints

Construct the same candidate-RDM coefficient fingerprint for each neural target after its existing nuisance treatment. Compare each target fingerprint to the ChineseEEG fingerprint using cosine similarity and Pearson correlation.

No candidate RDM may be added, removed, or relabeled after the target fingerprints are inspected. Dataset-inapplicable features are marked unavailable rather than replaced.

## Stage 5: model-independent geometry comparison

Only after Stages 1-4 are complete, compute entropic Gromov-Wasserstein distances between ChineseEEG and each reliable target neural metric space.

Before any GW result is opened:

- use the same normalized distance scaling rule across datasets;
- equalize item count by repeated deterministic subsampling;
- use participant/run/story/article/chapter resampling where feasible;
- use the same residualization status as the primary target;
- include shuffled-geometry nulls;
- predefine regularization and iteration tolerance.

GW is exploratory secondary mechanism evidence and cannot override the gradient analysis.

## Stage 6: one orthogonal robustness method

After the mechanism is identified, repeat only the central positive-versus-negative comparison using one prespecified orthogonal method. Prefer an encoding-style analysis if the fixed target pipelines make it technically comparable; otherwise use one global linear-CKA analysis.

Do not run a metric zoo.

## Stop rules

- Do not add targets based on Stage-1/2 outcomes.
- Do not rescue a null/negative target with a new representation, time window, dose, layer, pooling rule, or nuisance set.
- Do not add gradient variants after seeing compatibility values.
- Do not promote this project to prospective confirmation.
- The current NMI manuscript remains scientifically separate; these analyses are for a mechanism/technical follow-up unless explicitly incorporated later.

## Pre-outcome provenance

Read-only preflight:
- RunRelay job `C7M4K2V9`
- target inventory SHA-256 `278e9ea6135d56a8e1b2de4c3490596ed75976090f642bff93c5af41aa5b6662`
- dose adapter inventory SHA-256 `8f977b6369f43fae468f7f7278435b75cf0f606cdc8d5ddb6852545f3075a1bc`

DERCo reconstruction probe:
- successful RunRelay job `F4N7K2V8`;
- original frozen DERCo transfer evaluator identified at historical commit `62cef6c3a521d4b653e24451db610d62b7f634bf`.

The executable Stage-1 implementation must be committed after this protocol and before new DERCo/TMNRED/Garnett dose outcomes are opened.
