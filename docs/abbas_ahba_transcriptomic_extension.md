# Abbas AHBA Transcriptomic Extension

**Status:** planned mechanistic extension; no NeuroSem outcome test has been run under this plan.

## Origin

Abbas proposed using the **Allen Human Brain Atlas (AHBA)** to add a transcriptomic spatial weighting to the 128-channel ChineseEEG analysis. His central idea is to derive gene-expression maps corresponding approximately to the EEG spatial pattern, organize those genes into biologically meaningful systems, and test whether EEG-language-model representational similarity depends on those molecular weightings.

The requested biological groups include:

- GABA receptor families, including alpha, beta, gamma, delta and related GABAergic genes;
- serotonin receptors and broader serotonergic genes;
- biological pathways;
- literature-supported cell-type marker sets, including excitatory neurons, inhibitory neurons, astrocytes, oligodendrocytes, OPCs, microglia, endothelial cells, and other relevant classes.

Abbas also suggested adding other biologically motivated receptor or signaling groups if they are well justified.

## Core scientific question

The mechanistic extension asks:

> Are cortical locations that contribute more strongly to the established semantic neural geometry preferentially weighted by specific molecular systems?

A related operational question is whether prespecified transcriptomic spatial weightings systematically change the already-frozen EEG-model RSA.

## Important correction to the literal electrode-parcellation idea

A scalp EEG montage is not a 128-region cortical parcellation. Each electrode measures a weighted mixture of cortical generators because of volume conduction.

Therefore the preferred mapping is not:

`AHBA -> nearest cortical point under electrode -> EEG channel`

but:

`AHBA cortical transcriptomics -> cortical spatial map -> EEG forward/source-sensitivity projection -> 128-channel molecular weighting`

For gene or gene-set map `X(v)`, a conceptually appropriate electrode-level weight is:

`w_e = sum_v L(e,v) X(v)`

where `L(e,v)` is the sensitivity of electrode `e` to cortical location/source `v` under a frozen EEG forward model.

This preserves Abbas's intended 128-element spatial weighting while respecting EEG physics.

## Stage 1: model-blind transcriptomic preparation

This stage must be completed without inspecting whether any molecular map improves or worsens NeuroSem RSA.

### AHBA preprocessing

Use a reproducible `abagen`-style workflow and freeze preprocessing before outcome analysis.

Planned defaults/choices to verify and document:

- intensity-based filtering threshold: `ibf_threshold = 0.5`;
- probe selection / gene aggregation consistent with a standard `abagen` workflow;
- robust across-sample normalization;
- explicit donor handling;
- explicit bilateral strategy because AHBA right-hemisphere sampling is limited in several donors;
- deterministic mapping to the chosen cortical surface/parcellation used by the EEG forward model.

The expected retained gene count is on the order of ~15,000-16,000 genes, but the exact count is an output of the frozen preprocessing rather than a target to force.

### ChineseEEG 128-channel spatial mapping

Resolve the exact 128-channel montage used by the primary ChineseEEG analysis and construct a cortical forward/source-sensitivity model using a standard head model.

Freeze before outcome analysis:

- montage coordinates;
- reference convention;
- head model;
- cortical source space;
- lead-field/sensitivity metric;
- sign/absolute-value or power sensitivity convention;
- normalization from cortical sensitivity to electrode-level weights.

The output should be a reproducible **128 x G** molecular-sensitivity matrix, where `G` is the retained AHBA gene set.

## Stage 2: freeze biological gene sets

### GABAergic groups

At minimum separate:

1. **GABA receptor subunits**, especially GABA-A families such as `GABRA1-6`, `GABRB1-3`, `GABRG1-3`, `GABRD`, and other clearly annotated receptor subunits;
2. **broader GABAergic machinery**, potentially including synthesis, transport, and vesicular genes such as `GAD1`, `GAD2`, `SLC6A1`, `SLC32A1`, subject to final annotation review.

### Serotonergic groups

Separate:

1. **serotonin receptors**;
2. **broader serotonergic machinery**, including well-supported synthesis, transport, and metabolism genes if prespecified.

### Cell-type groups

Use published **human** single-cell/snRNA-seq marker sets rather than single-gene proxies.

Planned broad classes include:

- excitatory neurons;
- inhibitory neurons;
- astrocytes;
- oligodendrocytes;
- oligodendrocyte precursor cells;
- microglia;
- endothelial / vascular cells;
- other classes only if justified before outcome analysis.

The exact marker reference(s) must be recorded before any weighted RSA is computed.

### Pathways

Do not screen every available pathway.

Freeze a limited curated panel from a source such as Reactome or Gene Ontology before outcome analysis. Pathway inclusion should be biologically motivated and documented.

For any gene set `S`, build the spatial score after standardizing each gene across cortical locations/electrode sensitivities, for example:

`P_r = mean_{g in S} z(X_{r,g})`

rather than summing raw expression values with incomparable dynamic ranges.

PCA-derived gene-set scores may be used only as a prespecified sensitivity analysis.

## Stage 3: frozen NeuroSem molecular analysis

The primary analysis must not search across representations, windows, channels, models, lambdas, or gene sets after seeing outcomes.

Two related but distinct analyses are acceptable if frozen in advance:

### A. Molecular weighting of the EEG representation

For frozen EEG item vector `x` and molecular map `w`:

`x^(w)_e = x_e * w_e`

Construct the weighted neural RDM using the same standardization, distance, nuisance residualization, and inferential framework as the existing NeuroSem primary analysis.

Compare the weighted effect against the unweighted frozen baseline using a predeclared statistic.

### B. Spatial contribution analysis

Estimate a stable channel/source contribution map for the already-established semantic neural effect, then test whether that spatial contribution pattern associates with prespecified AHBA molecular maps.

This may offer the cleaner biological interpretation because it asks whether the spatial anatomy of the semantic effect corresponds to a molecular system rather than merely whether arbitrary weighting changes RSA.

## Required nulls and controls

Because AHBA maps are strongly spatially autocorrelated, standard random permutations are not sufficient.

Required controls should include:

- spatial-autocorrelation-preserving null maps;
- gene-set-size-matched random gene sets;
- donor robustness / leave-one-donor-out analysis;
- multiplicity correction across the small prespecified family panel;
- robustness to the frozen bilateral AHBA handling choice;
- comparison against broad cortical-gradient or nonspecific spatial structure where feasible.

## Interpretation guardrails

- AHBA contains postmortem tissue from six adult donors; it is a population-level spatial prior, not molecular data from ChineseEEG participants.
- A positive molecular association does not imply causal receptor involvement.
- Scalp electrode weights must not be interpreted as local gene expression directly beneath the electrode.
- No molecular result may be used to revise the already-frozen ChineseEEG, TMNRED, ZuCo, or Garnett primary choices.
- Negative results should narrow the mechanistic claim rather than trigger unrestricted pathway or gene-set fishing.

## Manuscript role

This work should be treated as a **separately frozen mechanistic extension**, tentatively titled:

**Transcriptomic modulation of semantic neural geometry**

If successful and robust to spatial nulls and donor checks, it could add a molecular-neurobiological dimension to the main NeuroSem paper. If null, the primary cross-dataset neural-geometry and model-transfer findings remain intact.
