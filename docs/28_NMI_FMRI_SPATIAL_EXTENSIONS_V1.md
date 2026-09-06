# SMN4Lang fMRI spatial extension suite v1

## Status and scope

This protocol defines a post-confirmatory extension suite motivated by the completed language-versus-primary-control result. The analyses below are frozen before execution of this suite and are restricted to questions whose definitions do not depend on new dose-by-system or model-by-system results.

The suite consumes only the already-completed SMN4Lang participant-level regional transfer outputs at the common E5-large dose lambda = 0.10. It does not retrain a model, reprocess fMRI, select parcels from transfer outcomes, or optimize a target-side parameter.

Participant is the inferential unit throughout. The suite is post-confirmatory and must not be described as prospective confirmation.

## Frozen input

- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/participant_results.csv`
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv`

The analysis uses `delta_0p10_minus_0` as the participant-level regional transfer effect and `model_blind_reliability_mean` as the regional reliability covariate.

Expected sample size: 12 SMN4Lang participants.

## Analysis A: full-cortex reliability-adjusted language enrichment

Use all 34 left-hemisphere Desikan-Killiany parcels. For each participant, fit an ordinary least-squares model across parcels:

`regional delta = intercept + z(model-blind reliability) + DK-language-membership`

The coefficient on DK-language membership is the participant-level estimand. Inference is across the 12 participant-specific coefficients using the exact sign-flip procedure defined below. The parcel-level relationship between mean delta and reliability is descriptive only.

Frozen DK language-associated set:

- parsopercularis
- parstriangularis
- superiortemporal
- middletemporal
- inferiorparietal
- supramarginal

## Analysis B: hemispheric specificity

Using the same six DK language-associated parcels in both hemispheres, compute within participant:

`mean(left DK language delta) - mean(right homologous DK language delta)`

No hemisphere-specific parcel selection is permitted after execution.

## Analysis C: language versus other association cortex versus primary cortex

The purpose is to distinguish language enrichment from a generic preference for higher-order association cortex.

Frozen left-hemisphere groups:

### DK language-associated cortex

- parsopercularis
- parstriangularis
- superiortemporal
- middletemporal
- inferiorparietal
- supramarginal

### Other association cortex

- superiorfrontal
- rostralmiddlefrontal
- caudalmiddlefrontal
- superiorparietal
- precuneus
- posteriorcingulate

This group is labeled `other association cortex`, not `non-language cortex`, because some association parcels can contribute to language or domain-general cognition.

### Primary/control cortex

Sensorimotor:
- precentral
- postcentral
- paracentral

Visual:
- pericalcarine
- cuneus
- lingual
- lateraloccipital

The focal adjacent contrasts are:

1. `DK language-associated - other association`
2. `other association - primary/control`

The direct `DK language-associated - primary/control` difference may be reported descriptively but is not an additional focal test because it is redundant with the already completed language-versus-primary analysis.

## Analysis D: within-language temporal versus frontal organization

Use the previously defined functional language parcels.

Frontal set:
- IFG
- IFGorb
- MFG

Temporal set:
- AntTemp
- PostTemp

Angular gyrus remains a descriptive parietal language parcel and is not assigned to either side of the focal temporal-versus-frontal contrast.

For each participant compute:

`mean(temporal functional-language delta) - mean(frontal functional-language delta)`

## Five-test multiplicity family

The five focal participant-level estimands are frozen as one family:

1. full-cortex reliability-adjusted DK-language coefficient
2. left minus right DK-language effect
3. DK-language minus other-association effect
4. other-association minus primary/control effect
5. functional temporal minus frontal language effect

For each focal estimand report:

- participant mean
- participant median
- number positive / 12
- 95% participant bootstrap CI
- exact two-sided participant sign-flip P value
- exact max-statistic family-wise P value across all five focal tests

The max-statistic null uses the same participant sign vector across the five columns on each exact sign-flip draw.

## Bootstrap

- 10,000 participant bootstrap resamples
- base seed: `20260906`
- deterministic per-test seed offsets are permitted only to avoid identical resample streams across reported contrasts

## Guardrails

- No parcel may be added, removed, or reassigned after seeing suite outcomes.
- No reliability threshold may be selected from transfer outcomes.
- No participant may be dropped based on effect direction or magnitude.
- No new fMRI preprocessing or model fitting is performed.
- Region-level descriptive correlations are not treated as parcel-independent inferential tests.
- Any later dose-by-system, backbone-by-system, EEG-fMRI coupling, or semantic-cost-versus-specificity analyses remain separate because they require outputs not produced by this suite.

## Required outputs

- `outputs/smn4lang_fmri_spatial_extensions_v1/latest/summary.json`
- `outputs/smn4lang_fmri_spatial_extensions_v1/latest/report.txt`
- `outputs/smn4lang_fmri_spatial_extensions_v1/latest/participant_spatial_extensions.csv`
- `outputs/smn4lang_fmri_spatial_extensions_v1/latest/left_dk_region_summary.csv`
- `outputs/smn4lang_fmri_spatial_extensions_v1/latest/figure_spatial_extensions.png`
- `outputs/smn4lang_fmri_spatial_extensions_v1/latest/figure_spatial_extensions.pdf`
