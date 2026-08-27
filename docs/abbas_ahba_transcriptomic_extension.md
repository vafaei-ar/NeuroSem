# Abbas AHBA Transcriptomic Extension

**Status:** completed primary mechanistic analysis family; primary molecular results are null, with one exploratory hemispheric mirroring sensitivity.

**Last updated:** 2026-08-27

## Origin

Abbas proposed using the **Allen Human Brain Atlas (AHBA)** to add a transcriptomic spatial layer to the 128-channel ChineseEEG analysis. The goal was to determine whether cortical locations contributing more strongly to the established semantic neural geometry preferentially align with biologically meaningful molecular systems.

The original requested families included:

- GABA receptor families and broader GABAergic machinery;
- serotonin receptors and broader serotonergic machinery;
- biologically motivated pathways;
- literature-supported human cell-type marker sets.

The project preserved the central idea but rejected a literal nearest-cortex-under-electrode mapping because scalp EEG channels measure mixtures of cortical generators.

## Core scientific question

> Are cortical locations that contribute more strongly to the established semantic neural geometry preferentially associated with specific molecular systems?

AHBA is interpreted as a population-level postmortem spatial prior, not as molecular measurement from ChineseEEG participants.

## Implemented spatial mapping

The implemented chain is:

`AHBA cortical transcriptomics -> cortical spatial map -> EEG forward/source-sensitivity projection -> 128-channel molecular weighting / DK68 cortical comparison -> frozen NeuroSem analysis`

For gene or gene-set map `X(v)`, electrode-level sensitivity weighting follows:

`w_e = sum_v L(e,v) X(v)`

where `L(e,v)` is the frozen EEG forward sensitivity from electrode `e` to cortical location `v`.

### Frozen EEG/source conventions

The final model-blind source pipeline uses:

- dataset-provided ChineseEEG 128-channel CapTrak geometry;
- fsaverage ico-5 cortical source space;
- three-layer BEM;
- explicit rigid measured-head-to-fsaverage registration;
- average reference;
- fixed surface-normal orientation;
- absolute lead-field sensitivity;
- per-channel L1 normalization.

The forward-sensitivity matrix contains 128 channels x 20,484 cortical vertices.

The Desikan-Killiany mapping contains 68 cortical parcels and maps 18,742 / 20,484 source vertices. Sensitivity is renormalized within the mapped DK domain rather than assigning unknown/corpus-callosum territory to a cortical parcel.

## Implemented AHBA preprocessing

The final expression pipeline uses `abagen 0.1.3` with all six AHBA donors and the frozen probe, intensity-filtering, normalization, donor aggregation, and bilateral choices.

Primary left-to-right mirrored expression:

- 68 cortical DK parcels;
- 15,677 retained genes.

No-mirror sensitivity:

- 15,633 retained genes.

Donor-level missingness is preserved rather than imputed.

The final molecular projection standardizes each gene spatially after expansion to mapped ico5 vertices using unweighted vertex-wise z-scoring (`ddof=0`) and then applies the frozen EEG sensitivity matrix.

## Frozen biological gene sets

The primary mechanistic family was frozen before molecular outcome testing.

### GABAergic

- GABA-A receptor subunits: 13 genes.
- GABA-B: `GABBR1`, `GABBR2`.
- Broader GABA machinery: `GAD1`, `GAD2`, `SLC6A1`, `SLC32A1`, `ABAT`, `ALDH5A1`.
- Reactome GABA activation pathway: 52 retained genes.

### Serotonergic

- Serotonin receptor panel: 10 genes.
- Serotonin machinery: `DDC`, `SLC18A2`, `MAOA`, `MAOB`.
- Reactome serotonin receptor pathway: 8 retained genes.

### Specificity-control cell types

Compact published marker panels were frozen for:

- excitatory neurons;
- inhibitory neurons;
- astrocytes;
- oligodendrocytes;
- OPCs;
- microglia;
- endothelial cells.

## Frozen semantic spatial targets

### 128-channel semantic contribution target

The channel target uses the established pinned `bert-base-chinese` residual semantic RSA, the frozen temporal-mean EEG representation, and the full nuisance family. It is AHBA-blind but not model-independent because it uses the pinned BERT semantic target.

### DK68 cortical phenotype

A deterministic sensitivity-weighted back-projection converts the already-frozen channel contribution map into a 68-parcel cortical phenotype.

This back-projection does **not** fit an EEG inverse solution and must not be described as anatomical source localization.

## Primary frozen molecular result: null

The seven prespecified GABAergic/serotonergic/pathway systems were tested with participant-level Spearman association, Fisher-z aggregation, exact sign-flip inference, BH correction, donor robustness, bilateral sensitivity, and random-gene-set controls.

No primary mechanistic family survived inference.

Representative results:

| Gene set | Mean rho | Exact p | Random-set p | BH q |
|---|---:|---:|---:|---:|
| GABA-A receptors | 0.0398 | 0.695 | 0.586 | 0.695 |
| GABA-B receptors | 0.0560 | 0.594 | 0.259 | 0.695 |
| GABA machinery | -0.0497 | 0.621 | 0.369 | 0.695 |
| Serotonin receptors | 0.0370 | 0.613 | 0.611 | 0.695 |
| Serotonin machinery | 0.0542 | 0.523 | 0.246 | 0.695 |
| Reactome GABA | 0.0456 | 0.684 | 0.411 | 0.695 |
| Reactome serotonin | 0.0372 | 0.500 | 0.591 | 0.695 |

The locked mechanistic conclusion is:

> Population cortical transcriptomic variation in the prespecified GABAergic and serotonergic systems did not reliably explain the spatial channel-contribution pattern of established ChineseEEG semantic neural geometry.

The result is not a failure of the EEG validation chain. It narrows the molecular interpretation.

## Exploratory whole-transcriptome analysis

A separate exploratory analysis used the frozen AHBA-blind DK68 phenotype and the primary mirrored expression matrix.

PLS1:

- score-phenotype Pearson `r = 0.4574`;
- `R^2 = 0.2092`;
- 5,000 hemisphere-constrained spherical rotations;
- two-sided spatial `p = 0.2745`.

Thus the moderate in-sample alignment is not significant under the spatial null.

No intrinsic transcriptomic gradient survived FDR. Gradient 10 was the closest nominal trend (`rho = 0.2256`, spatial `p = 0.0566`, `q = 0.4747`) and is not promoted.

PLS gene-weight rank stability was high across five valid leave-one-donor-out runs, but stable ranking is not inferential evidence.

## Independent published language-gene validation

To avoid outcome-driven panel construction, the project froze two exact Wong et al. 2024 language-related panels independently of NeuroSem outcomes.

### Six-gene structural-connectivity panel

`BHLHE22, COL5A2, NELL2, RYR3, SLIT1, SLIT2`

Primary mirrored result:

- `rho = -0.1515`;
- spatial-spin `p = 0.4631`;
- co-expression-profile gene-null `p = 0.3889`;
- jointly supported: false.

### Fourteen-gene dyslexia-associated panel

`BHLHE22, CDH10, DAB1, DIAPH1, FBXO32, GABRD, GPR26, KCNH5, KIRREL3, NEFH, OXR1, SLIT1, SLIT2, SNCA`

Primary mirrored result:

- `rho = -0.2733`;
- spatial-spin `p = 0.0516`, BH `q = 0.1032`;
- size-matched gene-null `p = 0.1018`, BH `q = 0.2036`;
- co-expression-profile gene-null `p = 0.0990`, BH `q = 0.1980`;
- jointly supported: false.

This panel is suggestive but does not pass the prospectively frozen criterion.

## No-mirror sensitivity

The no-mirror dyslexia-panel sensitivity was substantially stronger:

- `rho = -0.4776`;
- spatial-spin `p = 0.00320`;
- size-matched gene-null `p = 0.00120`;
- co-expression-profile gene-null `p = 0.00100`.

This remains exploratory because the primary mirrored result was null and the bilateral choice was already designated as a sensitivity.

## Mirroring diagnostic

A dedicated post-hoc diagnostic compared mirrored and no-mirror maps on identical support and decomposed the difference by hemisphere, gene, parcel, and donor.

The main finding is that the no-mirror boost is **not** caused by parcel loss. Both dyslexia maps had all 68 parcels available.

The shift is primarily right-hemispheric:

| Subset | Mirrored rho | No-mirror rho |
|---|---:|---:|
| Full 68 | -0.2733 | -0.4776 |
| Left hemisphere | -0.5670 | -0.5804 |
| Right hemisphere | +0.0038 | -0.4310 |

The left-hemisphere association is nearly unchanged. Left-to-right mirroring largely attenuates a right-hemisphere transcriptomic pattern that aligns with the semantic phenotype in the native no-mirror map.

Multiple genes contribute to the shift. Larger changes include `OXR1`, `GABRD`, `SLIT2`, `CDH10`, and `GPR26`. These are diagnostic contributors, not individually significant discoveries.

All six matched-support leave-one-donor-out comparisons for the dyslexia panel remained more negative without mirroring, so the sensitivity is not explained by a single donor. However, native AHBA right-hemisphere sampling is much sparser than left-hemisphere sampling, which is why this result remains exploratory.

## Interpretation guardrails

- AHBA contains six adult postmortem donors and is a population spatial prior.
- A positive spatial association does not establish causal receptor involvement.
- Scalp channel weights are not local gene expression beneath electrodes.
- The primary mirrored molecular null remains the confirmatory result.
- The no-mirror dyslexia result is a post-hoc methodological/hemispheric sensitivity finding.
- Individual genes from the decomposition are not discoveries.
- No molecular outcome may redefine the established EEG representation or model-transfer analyses.
- Negative results must not trigger unrestricted gene/pathway fishing.

## Manuscript role

The AHBA extension should now be presented as a **disciplined mechanistic constraint**, not as a positive receptor mechanism.

Recommended summary:

> Prespecified neurochemical and published language-related transcriptomic systems did not survive the frozen spatial and co-expression-aware null framework. A post-hoc bilateral diagnostic identified a reproducible sensitivity to AHBA left-to-right mirroring, driven primarily by a right-hemisphere expression-map shift, highlighting the importance of hemispheric sampling assumptions in imaging transcriptomics.

## Next step for this mechanistic line

For the current paper, stop the AHBA significance search.

If the hemispheric dyslexia-panel finding is pursued later, use independent validation rather than additional AHBA subsets. Preferred future tests include:

- a molecular resource with stronger bilateral cortical coverage;
- a prospectively frozen left/right language-network analysis;
- layer-resolved spatial transcriptomic data;
- an independent imaging-transcriptomic dataset using the same frozen 14-gene panel and hemisphere hypothesis.

See `6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md` for the project-wide forward plan.
