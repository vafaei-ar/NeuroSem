# NMI fMRI language-specificity analysis v1

## Status

Post-confirmatory spatial-specificity analysis. This protocol is frozen after the completed regional SMN4Lang fMRI analysis showed positive mean transfer in all six predefined language parcels and all 68 Desikan-Killiany (DK68) parcels. It cannot convert the regional analysis into a prospective selectivity test. Its purpose is narrower: test whether the already-observed positive displacement is larger in language-related cortex than in predefined non-language control systems.

No new model training, fMRI preprocessing, neural target construction, region selection from transfer outcomes, dose selection, layer selection, checkpoint selection or participant/stimulus exclusion is permitted.

## Frozen inputs

Use only the completed outputs from:

- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/participant_results.csv`
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv`

The model contrast remains the existing ChineseEEG-trained multilingual-E5 genuine-neural `lambda=0.10` arm minus the matched text-only `lambda=0` arm. The 12 SMN4Lang participants and 60 stories are unchanged.

## Primary question

Is participant-level transfer larger in the predefined functional language network than in clearly non-language left-hemisphere sensorimotor or visual cortex?

For participant `s` and region family `G`, define

`mean_delta(s,G) = mean_r delta(s,r)`

where `delta(s,r)` is the existing participant-level residual-RSA difference `lambda=0.10 minus lambda=0`.

The two frozen primary contrasts are:

1. `functional_language minus left_sensorimotor`
2. `functional_language minus left_visual`

Positive values indicate preferential transfer to the functional language network.

## Frozen region definitions

### Functional language network

Use all six already-predefined left-hemisphere EvLab language parcels, with no change:

- IFG
- IFGorb
- MFG
- AntTemp
- PostTemp
- AngG

### Left sensorimotor control

Use all three left-hemisphere DK68 parcels:

- precentral
- postcentral
- paracentral

### Left visual control

Use all four left-hemisphere DK68 parcels:

- pericalcarine
- cuneus
- lingual
- lateraloccipital

No control parcel may be removed or replaced based on transfer magnitude.

## Primary inference

Participant is the inferential unit. For each primary contrast report:

- mean and median participant contrast
- number of positive participant contrasts
- 10,000-resample participant-bootstrap 95% percentile interval
- exact two-sided participant sign-flip P value

Control the two primary comparisons using one exact max-absolute-mean sign-flip family across the two participant contrast vectors. Report both uncorrected and family-wise P values.

Bootstrap seed: `20260905`.

## Frozen sensitivity 1: reliability-matched non-language control

Regional measurement reliability can affect observable transfer magnitude. Construct a reliability-matched control set without reading transfer outcomes:

- candidate pool is exactly the seven left sensorimotor and visual DK parcels above;
- match the six EvLab language parcels to six distinct candidate controls;
- choose the one-to-one assignment minimizing the total absolute difference in model-blind regional reliability;
- break exact ties lexicographically by control parcel name;
- use no transfer value in matching.

Average the six matched controls within participant and compare with the six functional language parcels. Report the same participant-level descriptive statistics, bootstrap interval and exact two-sided sign-flip P value. This is a sensitivity analysis, not an additional primary family.

## Frozen sensitivity 2: same-atlas DK68 anatomical replication

To remove the functional-atlas versus anatomical-atlas definition difference, define a left-hemisphere DK68 language-associated set before computing its contrast:

- parsopercularis
- parstriangularis
- superiortemporal
- middletemporal
- inferiorparietal
- supramarginal

Compare this six-parcel same-atlas set separately with the frozen left sensorimotor and left visual control sets above. Report participant-bootstrap intervals and exact two-sided sign-flip P values. These are secondary anatomical-replication contrasts and are not used to redefine the primary result.

## Frozen sensitivity 3: reliability-adjusted same-atlas contrast

Use only the 13 left-DK parcels comprising the six anatomical language-associated parcels and the seven sensorimotor/visual controls. For each participant separately:

1. regress the 13 regional transfer deltas on an intercept and the already-computed model-blind regional reliability values;
2. retain the 13 residualized deltas;
3. compute mean residualized language-associated delta minus mean residualized pooled non-language-control delta.

Across participants report the mean/median adjusted contrast, positive-participant count, 10,000-resample participant-bootstrap 95% interval and exact two-sided sign-flip P value.

This adjustment is a sensitivity analysis. It does not establish causal language specificity and does not remove all regional measurement confounds.

## Secondary descriptive gradient

For presentation only, report participant means for four fixed systems:

1. functional language
2. DK language-associated
3. left sensorimotor
4. left visual

No ordered-trend hypothesis test is added after seeing outcomes.

## Stopping rule

Run exactly this protocol once on the completed frozen regional outputs. Retain all frozen groups and all 12 participants regardless of outcome. Do not add, remove, split or merge regions; do not search alternative control groups; do not change hemisphere; do not tune reliability matching; and do not add a rescue analysis after results are observed.

## Interpretation rules

- If both primary language-versus-control contrasts are positive with family-wise support, and the same-atlas/reliability-adjusted sensitivities point in the same direction, describe the result as evidence for **preferential language-related expression within a cortex-wide positive displacement**.
- If primary contrasts are positive but reliability adjustment or same-atlas comparisons weaken substantially, describe the spatial concentration as suggestive and partly compatible with measurement reliability or atlas-definition differences.
- If primary contrasts do not support a language advantage, retain the current interpretation: **cortex-wide positive displacement without demonstrated language-network specificity**.

Under no outcome should the result be described as prospective, confirmatory, language-exclusive, or proof that the intervention targets a uniquely linguistic neural mechanism.
