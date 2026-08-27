# 6. AHBA Current Status, Findings, and Next Steps

**Last updated:** 2026-08-27

This document is the current authoritative summary of the Allen Human Brain Atlas (AHBA) mechanistic extension. It records the completed model-blind preparation, frozen mechanistic tests, exploratory transcriptomic work, published language-gene validation, the post-hoc mirroring diagnostic, and the forward plan. It does not replace the original frozen protocols or job artifacts.

## Scientific question

The AHBA extension asks whether cortical locations contributing more strongly to the established ChineseEEG semantic neural geometry preferentially align with specific molecular systems.

The required mapping is:

`AHBA cortical transcriptomics -> cortical spatial map -> EEG forward/source-sensitivity projection -> molecular weighting / cortical comparison -> frozen NeuroSem analysis`

A literal nearest-cortex-under-electrode mapping is not used.

AHBA is a population postmortem transcriptomic prior from six adult donors. It is not participant-specific molecular measurement and cannot establish causal receptor involvement.

## Completed model-blind spatial and transcriptomic preparation

### EEG geometry and forward model

The ChineseEEG dataset provides a 128-channel CapTrak-labeled geometry that is highly standardized across participants and should be described as dataset-provided rather than individualized digitization.

The frozen spatial pipeline uses:

- fsaverage ico-5 cortical source space;
- three-layer BEM;
- explicit rigid measured-head-to-fsaverage registration;
- average reference;
- fixed surface-normal orientation;
- absolute lead-field sensitivity;
- per-channel L1 normalization.

The forward-sensitivity matrix contains 128 channels x 20,484 cortical vertices. The DK-to-ico5 mapping contains 68 cortical parcels, with 18,742 / 20,484 source vertices mapped to DK cortex. Molecular projection renormalizes sensitivity within the mapped DK domain.

### AHBA expression

Frozen preprocessing uses `abagen 0.1.3` with all six donors and the prespecified probe, filtering, normalization, donor aggregation, and bilateral settings.

Primary left-to-right-mirrored expression:

- 68 DK cortical parcels;
- 15,677 genes.

No-mirror sensitivity:

- 15,633 genes.

Donor matrices preserve missingness rather than imputing absent parcels.

### Molecular-sensitivity matrix

The model-blind molecular matrix projects spatially standardized cortical gene maps through the frozen EEG sensitivity model.

Primary mirrored matrix:

- 15,677 genes x 128 channels;
- common donor support uses 66 parcels / 18,701 mapped vertices for LODO reconstruction.

No-mirror matrix:

- 15,633 genes;
- common donor support uses 64 parcels / 18,606 mapped vertices.

The actual implemented gene standardization is unweighted vertex-wise z-scoring after DK expansion to mapped ico5 vertices, with `ddof=0`.

## Frozen biological families

Fourteen gene sets were frozen before outcome testing.

Primary mechanistic family:

1. GABA-A receptor subunits, 13 genes.
2. GABA-B receptors, `GABBR1`, `GABBR2`.
3. Broader GABA machinery: `GAD1`, `GAD2`, `SLC6A1`, `SLC32A1`, `ABAT`, `ALDH5A1`.
4. Serotonin receptors, 10 genes.
5. Serotonin machinery: `DDC`, `SLC18A2`, `MAOA`, `MAOB`.
6. Reactome GABA activation pathway, 52 retained genes.
7. Reactome serotonin receptor pathway, 8 retained genes.

Specificity-control family:

- excitatory neuron markers;
- inhibitory neuron markers;
- astrocyte markers;
- oligodendrocyte markers;
- OPC markers;
- microglia markers;
- endothelial markers.

## Frozen semantic spatial phenotype

Two spatial targets were constructed from already-established ChineseEEG semantic geometry.

### Channel target

The 128-channel contribution target uses the pinned `bert-base-chinese` residual semantic RSA, with the established `row_mean` neural representation and full nuisance family. It is AHBA-blind but not model-independent because it explicitly uses the pinned BERT semantic target.

### DK68 parcel target

A cortical parcel phenotype was then derived without fitting an inverse solution:

- restrict frozen forward sensitivity to mapped DK cortex;
- renormalize each channel in the mapped domain;
- compute each channel's sensitivity fraction for each DK parcel;
- back-project the frozen channel contribution target by deterministic sensitivity weighting.

This is a coarse sensitivity-weighted cortical phenotype, not anatomical EEG source localization.

## Frozen prespecified molecular association: null

Job: `NEUROSEM-AHBA-FROZEN-GENE-SET-ASSOCIATION-0001`.

The seven prespecified GABAergic/serotonergic/pathway sets were tested using participant-level Spearman associations, Fisher-z aggregation, exact two-sided sign-flip inference, BH correction, donor robustness, bilateral sensitivity, and random-gene-set controls.

No primary mechanistic family survived inference.

Representative primary results:

| Gene set | Mean rho | Exact sign-flip p | Random-set p | BH q |
|---|---:|---:|---:|---:|
| GABA-A receptors | 0.0398 | 0.695 | 0.586 | 0.695 |
| GABA-B receptors | 0.0560 | 0.594 | 0.259 | 0.695 |
| GABA machinery | -0.0497 | 0.621 | 0.369 | 0.695 |
| Serotonin receptors | 0.0370 | 0.613 | 0.611 | 0.695 |
| Serotonin machinery | 0.0542 | 0.523 | 0.246 | 0.695 |
| Reactome GABA | 0.0456 | 0.684 | 0.411 | 0.695 |
| Reactome serotonin | 0.0372 | 0.500 | 0.591 | 0.695 |

The primary mechanistic conclusion is therefore:

> Population cortical transcriptomic variation in the prespecified GABAergic and serotonergic systems did not reliably explain the spatial channel-contribution pattern of established ChineseEEG semantic neural geometry.

This null is locked and must not be redefined by later exploratory work.

## Exploratory whole-transcriptome analysis: null after spatial correction

Job: `NEUROSEM-AHBA-EXPLORATORY-TRANSCRIPTOME-0001`.

The exploratory analysis used the frozen AHBA-blind DK68 semantic phenotype and the primary mirrored AHBA expression matrix.

### PLS1

- observed PLS1 score-phenotype Pearson `r = 0.4574`;
- `R^2 = 0.2092`;
- 5,000 hemisphere-constrained spherical-rotation nulls;
- two-sided spatial p = `0.2745`.

The moderate in-sample PLS alignment did not survive the spatial null and is not evidence of a transcriptomic mechanism.

### Transcriptomic gradients

No intrinsic transcriptomic gradient survived FDR correction. Gradient 10 was the closest nominal trend (`rho = 0.2256`, spin `p = 0.0566`) but had `q = 0.4747` and must not be promoted.

### Donor stability

PLS gene-weight rankings were stable across five valid leave-one-donor-out analyses, with rank correlations approximately 0.95 to 0.98. This indicates ranking stability, not statistical significance.

## Independent published language-gene panels

To avoid outcome-driven subset definition, two exact literature-defined panels from Wong et al. 2024 were frozen before NeuroSem testing.

### Structural-connectivity panel

Six genes, all retained in AHBA:

`BHLHE22, COL5A2, NELL2, RYR3, SLIT1, SLIT2`

### Dyslexia-associated panel

Fourteen genes, all retained in AHBA:

`BHLHE22, CDH10, DAB1, DIAPH1, FBXO32, GABRD, GPR26, KCNH5, KIRREL3, NEFH, OXR1, SLIT1, SLIT2, SNCA`

The panel freeze did not load the NeuroSem semantic phenotype or previous AHBA outcomes.

## Published language-panel validation: primary null

Job: `NEUROSEM-AHBA-PUBLISHED-LANGUAGE-PANEL-VALIDATION-0003`.

The primary analysis used the frozen DK68 semantic phenotype, mean spatially standardized panel-gene expression maps, Spearman association, 5,000 spatial spins, 5,000 size-matched random gene sets, 5,000 co-expression-profile-matched random gene sets, and BH correction across the two published panels.

A panel was prospectively defined as supported only if both the spatial-spin and co-expression-profile BH q values were below 0.05.

### Six-gene connectivity panel

- observed Spearman `rho = -0.1515`;
- spatial-spin `p = 0.4631`, `q = 0.4631`;
- co-expression-profile gene-null `p = 0.3889`, `q = 0.3889`;
- jointly supported: **false**.

### Fourteen-gene dyslexia panel

- observed Spearman `rho = -0.2733`;
- spatial-spin `p = 0.0516`, `q = 0.1032`;
- size-matched gene-null `p = 0.1018`, `q = 0.2036`;
- co-expression-profile gene-null `p = 0.0990`, `q = 0.1980`;
- jointly supported: **false**.

The dyslexia panel is suggestive but does not meet the frozen primary criterion.

## No-mirror sensitivity and post-hoc mirroring diagnostic

The no-mirror sensitivity produced a much stronger dyslexia-panel result:

- no-mirror `rho = -0.4776`;
- spatial-spin `p = 0.00320`;
- size-matched gene-null `p = 0.00120`;
- co-expression-profile gene-null `p = 0.00100`.

Because no-mirror was a sensitivity analysis and the primary mirrored test was null, this cannot rescue the confirmatory result.

A dedicated post-hoc diagnostic then asked why the no-mirror result was stronger.

Job: `NEUROSEM-AHBA-LANGUAGE-MIRRORING-DIAGNOSTIC-0001`.

### Main diagnostic finding

The difference is not explained by parcel loss. Both mirrored and no-mirror dyslexia maps had all 68 parcels available.

The stronger no-mirror association is almost entirely a **right-hemisphere expression-map shift**:

| Subset | Mirrored rho | No-mirror rho | Difference |
|---|---:|---:|---:|
| Full 68 parcels | -0.2733 | -0.4776 | -0.2043 |
| Left hemisphere, 34 parcels | -0.5670 | -0.5804 | -0.0134 |
| Right hemisphere, 34 parcels | +0.0038 | -0.4310 | -0.4348 |

The left-hemisphere association is strong under both preprocessing choices. Left-to-right mirroring largely removes the right-hemisphere transcriptomic alignment that appears in the native no-mirror map.

For the dyslexia panel, mirrored versus no-mirror whole-map similarity was `rho = 0.7381`; in the right hemisphere it fell to approximately `rho = 0.5047`.

### Gene-level contributors

The no-mirror shift is distributed across multiple frozen panel genes rather than a single post-hoc hit. Larger changes toward a more negative semantic association include:

- `OXR1`: delta rho about `-0.283`;
- `GABRD`: about `-0.163`;
- `SLIT2`: about `-0.150`;
- `CDH10`: about `-0.117`;
- `GPR26`: about `-0.097`.

These are diagnostic contributors, not individually significant gene discoveries.

### Donor robustness

For the dyslexia panel, all six matched-support leave-one-donor-out comparisons remained more negative without mirroring. No-mirror LODO estimates were approximately `-0.406` to `-0.488`, while mirrored estimates were approximately `-0.188` to `-0.335`.

This shows that the mirroring sensitivity is not driven by one donor, but AHBA right-hemisphere sampling remains substantially sparser than left-hemisphere sampling, so the no-mirror finding remains exploratory.

## Current AHBA interpretation

The defensible molecular story is:

1. Prespecified GABAergic and serotonergic mechanisms are null.
2. Whole-transcriptome PLS and intrinsic-gradient discovery are null after spatial correction.
3. The independent six-gene published language-connectivity panel is null.
4. The independent fourteen-gene dyslexia panel is suggestive in the mirrored primary analysis but fails the frozen spatial and co-expression-aware criteria.
5. A strong no-mirror dyslexia-panel sensitivity is reproducible across donor leave-one-out analyses and is driven mainly by a right-hemisphere transcriptomic shift.
6. That no-mirror result is a methodological/hemispheric sensitivity finding, not confirmatory molecular evidence.

The AHBA work should not be extended by searching additional gene subsets until significance is obtained.

## Recommended next steps

### Priority 1: lock the AHBA analysis family

Treat the current AHBA analyses as complete for the main paper. Preserve the frozen nulls and the no-mirror diagnostic as a methodological sensitivity result. Do not add unrestricted pathway screens, post-hoc gene subsets, or alternative spatial phenotypes based on these outcomes.

### Priority 2: reconcile execution branches into canonical documentation/code

The AHBA execution branches were intentionally narrow and may contain reduced manifests or compatibility wrappers. Do not merge them wholesale into `main`.

Instead:

- selectively reconcile the scientifically final analysis scripts;
- remove temporary compatibility/placeholder files where they are no longer needed;
- preserve exact job/commit provenance in the experiment ledger;
- keep the primary mirrored and sensitivity no-mirror conventions explicit.

### Priority 3: manuscript figures and tables

Build a compact mechanistic-extension figure set:

1. AHBA-to-EEG spatial mapping schematic.
2. Prespecified GABA/serotonin gene-set null results.
3. Exploratory PLS/spatial-null result.
4. Published language-panel primary results.
5. Mirrored versus no-mirror dyslexia-panel hemisphere diagnostic.

The figure captions must distinguish confirmatory, exploratory, and post-hoc diagnostic analyses.

### Priority 4: manuscript narrative

The main paper should use AHBA as a constraint on mechanistic interpretation, not as a headline positive mechanism.

Recommended wording:

> Prespecified neurochemical and published language-related transcriptomic systems did not survive the frozen spatial and co-expression-aware null framework. A post-hoc bilateral diagnostic identified a reproducible sensitivity to AHBA left-to-right mirroring, driven primarily by a right-hemisphere expression-map shift, highlighting the importance of hemispheric sampling assumptions in imaging transcriptomics.

### Priority 5: future independent molecular validation, not more AHBA fishing

If the hemispheric dyslexia-panel pattern is scientifically important enough to pursue beyond the current paper, the next test should use an independent molecular resource or a prospectively designed lateralization analysis rather than more AHBA subset search.

Potential future directions include:

- an independent cortical transcriptomic dataset with better bilateral coverage;
- prospectively frozen left/right language-network analyses;
- spatial transcriptomic resources with cortical layer information;
- external imaging-transcriptomic replication using the same frozen 14-gene panel and hemisphere hypothesis.

These should be new studies or clearly separate follow-up analyses, not post-hoc rescue analyses within the current AHBA family.

## Project-wide next steps

With the AHBA family now complete, the project should shift from analysis expansion to consolidation:

1. Update all authoritative summaries and the experiment ledger.
2. Selectively reconcile final analysis code from execution branches into canonical `main` without wholesale branch merges.
3. Build manuscript-ready figures and tables across ChineseEEG, TMNRED, ZuCo, Garnett, Nature, and AHBA.
4. Draft Results in evidence order, preserving positive and null findings.
5. Draft Methods from frozen protocols and exact job provenance.
6. Decide the final journal framing after the full manuscript narrative is visible, rather than adding analyses to fit a target journal.
