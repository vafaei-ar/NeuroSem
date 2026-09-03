# 26. Regional SMN4Lang fMRI and AHBA extension v1

**Status:** frozen post-confirmatory protocol before any regional SMN4Lang model-alignment outcome or new fMRI-derived AHBA association is computed.

## Purpose and evidential status

The completed primary SMN4Lang analysis established a small, consistent neural-guided E5 advantage within one independently defined whole language-network mask. This extension asks where that representational relationship is expressed within cortex and whether the resulting spatial pattern has a reproducible relationship to frozen cortical transcriptomic annotations.

This is a **post-confirmatory regional and mechanistic characterization**. It does not alter the prospective status of the original whole-network SMN4Lang result, and it cannot revise or rescue the already-completed NeuroSem AHBA null results. All existing GABAergic, serotonergic, pathway, transcriptome-wide and published-language-panel conclusions remain locked.

No regional SMN4Lang reliability, regional text-only RSA, regional neural-guided RSA, regional delta-RSA, or new AHBA association outcome has been inspected before this protocol freeze.

## Questions

The analysis separates three questions that must not be conflated.

1. **Baseline regional model-brain correspondence:** where does the frozen text-only multilingual-E5 representation already resemble regional fMRI geometry?
2. **Regional NeuroSem transfer:** where is the representational perturbation induced by the frozen ChineseEEG neural constraint expressed most strongly, measured as neural-guided minus text-only residual RSA?
3. **Spatial molecular interpretation:** does the cortical distribution of that regional transfer phenotype covary with independently frozen AHBA molecular features?

The principal NeuroSem regional estimand is

`delta_RSA(region, participant) = RSA(neural-guided E5, region, participant) - RSA(text-only E5, region, participant)`.

Baseline text-only RSA is reported separately and is not a substitute for the delta-RSA estimand.

## Frozen SMN4Lang inputs

Reuse the existing SMN4Lang fMRI pipeline without alteration:

- dataset: SMN4Lang / OpenNeuro `ds004078`;
- all 12 participants;
- all 60 shared story runs;
- TR = 0.71 s;
- released word timing and audio;
- retained stimulus-period TR family and post-stimulus tail exactly as in the frozen whole-network analysis;
- voxelwise z-scoring across retained TRs with population SD;
- correlation-distance neural RDM;
- nuisance family: absolute temporal separation, canonical-HRF-convolved word-onset density and canonical-HRF-convolved acoustic RMS envelope;
- causal within-sentence multilingual-E5 semantic state;
- word-to-TR mapping by `floor(word_start / 0.71)`;
- the same fixed canonical HRF;
- cosine-distance model RDM;
- story-wise nuisance-residualized Spearman RSA;
- unweighted Fisher-z aggregation across all 60 stories within participant.

No participant, story, temporal window, lag, HRF, nuisance variable, distance metric, semantic unit, model, layer, checkpoint or pooling choice may change in this extension.

## Frozen model contrast

Use only the already-established ChineseEEG-trained multilingual-E5 contrast:

- text-only arm: `lambda = 0`;
- genuine-neural arm: `lambda = 0.10`.

Use the same pinned multilingual-E5-large base revision and the same completed adapters used for the original SMN4Lang transfer result. Do not train a new model or choose a new adapter from regional outcomes.

## Stage 0: atlas-only preflight before neural outcomes

Before loading SMN4Lang BOLD values, materialize and validate two independent regional systems.

### A. Language-region parcels

Use the current EvLab/Fedorenko group-constrained language parcels created from the probabilistic overlap map from 220 independent participants, distributed by EvLab as the `allParcels-language-SN220` resource.

The source of truth is the EvLab public Parcels resource page and its linked current parcel NIfTI plus ROI-index text file. The preflight must record:

- requested source page;
- resolved download URLs;
- file names;
- SHA-256 hashes;
- NIfTI shape, affine and voxel size;
- the exact integer-label-to-name mapping from the distributed ROI-index file.

The accepted left-hemisphere language family is exactly six parcels:

1. inferior frontal gyrus (IFG);
2. orbital inferior frontal gyrus (IFGorb);
3. middle frontal gyrus (MFG);
4. anterior temporal cortex (AntTemp);
5. posterior temporal cortex (PostTemp);
6. angular gyrus (AngG).

The source label file must resolve exactly one left-hemisphere label for each of these six regions. If the distributed resource has changed so that this cannot be established unambiguously, stop before reading neural outcomes. Do not manually redefine parcels after outcome inspection.

Use the distributed group parcel masks directly. Do not intersect, dilate, erode or optimize them using SMN4Lang or LanA outcomes. The parcel image must match the SMN4Lang MNI grid exactly. If it does not, stop before neural outcomes rather than choosing a resampling rule after seeing results.

### B. Desikan-Killiany cortical atlas

Use the volumetric standard-space Desikan-Killiany atlas shipped with the already-pinned `abagen` environment via `abagen.fetch_desikan_killiany(surface=False)`.

The preflight must record the atlas image and information-file hashes and verify:

- exact grid/affine compatibility with the SMN4Lang MNI derivatives;
- exactly 68 cortical parcels, 34 per hemisphere;
- parcel IDs, names and hemisphere labels;
- exact ID/name/hemisphere agreement with the frozen AHBA Desikan-Killiany expression bundle.

If the volumetric atlas does not match the SMN4Lang grid or the frozen expression metadata, stop before neural outcomes. No post-outcome atlas substitution or spatial resampling is allowed.

## Stage 1: model-blind regional neural reliability

The model-blind reliability stage must complete for the six language parcels and all 68 Desikan-Killiany cortical parcels before any multilingual-E5 model is loaded.

For each participant, story and region, construct the neural RDM exactly as in the whole-network reliability analysis but using only voxels inside that fixed region.

A region is structurally usable only if its fixed mask contains enough finite, nonconstant voxels for the existing regional RDM implementation. The implementation threshold is frozen at **100 nonconstant voxels**. A region that fails this structural requirement for any required run is retained in the audit table and marked structurally unavailable. The mask, threshold and story/participant set must not be changed to rescue it.

For each structurally usable region:

1. compute the participant neural RDM per story;
2. form the leave-one-participant-out mean RDM from the other 11 participants;
3. residualize both against the unchanged three-variable nuisance family;
4. compute residual Pearson reliability per story;
5. aggregate 60 story coefficients within participant by unweighted Fisher-z mean and `tanh`;
6. report all 12 participant values, mean, median and fraction positive;
7. bootstrap the participant mean with 10,000 resamples using seed `20260902`;
8. report the exact two-sided sign-flip p-value as a post-confirmatory sensitivity statistic.

A regional reliability gate is considered passed only if both:

- mean residual reliability is greater than zero; and
- the participant-bootstrap 95% CI lower bound is greater than zero.

Reliability is an interpretation gate, not a region-selection device. All predefined regions remain in the report. Model results for reliability-limited regions may be computed because the model stage is fully frozen here, but such regions must be labeled reliability-limited and cannot support a positive or negative regional transfer claim.

## Stage 2: regional model-brain correspondence and transfer

Only after Stage 1 has been completed and written to disk may the script import/load the frozen E5 adapters.

### Six language parcels: primary regional characterization

For every structurally usable language parcel and every participant:

- compute text-only residual RSA;
- compute neural-guided residual RSA;
- compute `delta_RSA = neural-guided - text-only`;
- retain all 60 story-level values;
- aggregate to one participant-level value per arm and region using the frozen Fisher-z rule.

For each of the six predefined parcels report:

- model-blind reliability;
- mean and median text-only RSA;
- mean and median neural-guided RSA;
- mean and median delta-RSA;
- number and fraction of participants with positive delta-RSA;
- 10,000-resample participant-bootstrap 95% CI for mean delta-RSA, seed `20260902`;
- exact two-sided participant sign-flip p-value;
- exact family-wise corrected p-value across the six-region family.

Family-wise correction uses all `2^12` participant sign-flip configurations. For each configuration, apply the same participant sign vector to every region, compute each region's absolute mean delta-RSA, and record the maximum across the six-region family. A region's FWER p-value is the fraction of configurations whose family maximum is at least as large as that region's observed absolute mean. This preserves dependence across regions and prevents region-by-region significance searching.

No region is designated a priori as the expected winner. Frontal-versus-temporal/parietal and hemisphere statements are descriptive only unless separately frozen before outcome inspection.

### Participant-by-story robustness

For each language parcel, run a post-confirmatory two-factor bootstrap over participants and the 60 analyzed stories using 10,000 replicates, seed `20260902`, on the neural-guided minus text-only contrast. Report the percentile 95% CI and fraction of bootstrap means greater than zero. This is a sensitivity over the observed participant and story units, not unrestricted population inference over arbitrary language stimuli.

### Desikan-Killiany cortical phenotype

For every structurally usable Desikan-Killiany parcel, compute the same participant-level text-only RSA, neural-guided RSA and delta-RSA using the frozen SMN4Lang pipeline.

The DK68 map is a **spatial characterization phenotype**, not a 68-region significance screen. Do not select, rank-filter or threshold parcels by observed delta-RSA before molecular analysis. Store for every parcel:

- parcel ID, name and hemisphere;
- voxel count and structural-availability status;
- model-blind reliability summary;
- each participant's text-only RSA, neural-guided RSA and delta-RSA;
- participant mean and median delta-RSA.

No uncorrected parcel-level p-value is used to choose regions for AHBA analysis.

## Stage 3: frozen AHBA molecular interpretation

### Expression data

Reuse the already-frozen NeuroSem AHBA expression preparation. Do not rerun or alter probe selection, sample assignment, normalization, donor aggregation or gene filtering in response to the new fMRI map.

The frozen preprocessing is:

- `abagen 0.1.3`;
- all six AHBA donors;
- Desikan-Killiany cortical parcellation;
- intensity-based filtering threshold 0.5;
- differential-stability probe selection;
- donor-probe aggregation;
- `srs` sample normalization;
- `srs` gene normalization;
- matched-sample normalization enabled;
- corrected MNI coordinates and reannotated probes;
- donor-level matrices retained;
- primary population bundle uses the existing left-to-right mirroring convention;
- existing no-mirror bundle is a mandatory sensitivity.

The previous AHBA results remain separate outcomes based on a different NeuroSem spatial phenotype.

### Primary molecular spatial domain

The primary molecular domain is the **left-hemisphere 34-parcel DK map**. This choice is frozen before regional fMRI outcomes because AHBA sampling is substantially denser in the left hemisphere and the cortical language network is strongly left-lateralized.

For each participant, define a 34-element phenotype vector from that participant's DK left-hemisphere delta-RSA values. Do not average participants before the principal gene-set association. This preserves participant as the human inferential unit.

For each tested molecular gene set:

1. spatially z-score each retained gene expression column across the 34 left-hemisphere parcels;
2. take the unweighted arithmetic mean across genes to form one 34-parcel molecular vector;
3. compute Spearman correlation between that molecular vector and each participant's 34-parcel delta-RSA vector;
4. Fisher-z transform the 12 participant correlations and average them for the group statistic.

### Frozen molecular families

Do not define new gene sets from the regional fMRI result.

Primary mechanistic family, exactly as previously frozen:

1. GABA-A receptor subunits;
2. GABA-B receptors;
3. non-receptor GABA machinery;
4. serotonin receptors;
5. non-receptor serotonin machinery;
6. Reactome GABA receptor activation pathway;
7. Reactome serotonin receptor pathway.

Separate specificity-control family, exactly as previously frozen:

- excitatory-neuron markers;
- inhibitory-neuron markers;
- astrocyte markers;
- oligodendrocyte markers;
- OPC markers;
- microglia markers;
- endothelial markers.

The exact gene memberships must be loaded from the existing frozen NeuroSem gene-set artifact. No membership edits are allowed.

The two previously frozen published language-related panels may be reported as a separate secondary family using their already-frozen memberships. They do not join the seven-set primary mechanistic multiplicity family.

### Spatial null

Use 5,000 spherical rotations with seed `20260902`.

For the left-hemisphere primary analysis, obtain DK parcel centroids on the frozen fsaverage sphere using the existing frozen DK-to-ico5 mapping. For each random rotation, rotate the left-hemisphere centroids and use one-to-one Hungarian reassignment within the 34 left-hemisphere parcels.

Apply each spatial permutation to every participant's delta-RSA map using the same parcel permutation. Recompute the 12 participant correlations and the group mean Fisher-z statistic. The primary spatial p-value is two-sided:

`(1 + number(|null group statistic| >= |observed group statistic|)) / (5000 + 1)`.

### Random-gene-set null

For each gene set, draw 5,000 size-matched random gene sets from the same frozen AHBA gene universe using seed `20260902`. For every random set, repeat the same gene standardization, molecular-vector construction and 12-participant group statistic. Report a two-sided empirical random-gene-set p-value.

Apply Benjamini-Hochberg correction separately to the seven prespecified mechanistic sets for spatial p-values and for random-gene-set p-values. Apply a separate correction to the seven cell-type controls. A prespecified mechanistic family member is considered supported only if **both** its spatial-null q-value and size-matched random-gene-set q-value are below 0.05. Direction and effect size must also be reported.

### Donor robustness

For every frozen gene set, repeat the molecular-vector construction after leaving out each of the six donors in turn. Report the six group association estimates and directional stability. Leave-one-donor-out stability is robustness evidence, not an independent significance test.

### Bilateral and mirroring sensitivities

Because the previous NeuroSem AHBA work showed substantial right-hemisphere sensitivity to mirroring, the following analyses are mandatory sensitivities and cannot replace the left-hemisphere primary result:

1. left-hemisphere association using the existing no-mirror expression bundle;
2. bilateral DK68 association using the existing primary mirrored population expression, with hemisphere-constrained spherical rotations;
3. bilateral DK68 association using the existing no-mirror expression bundle where the frozen expression artifact provides finite parcel support.

Any discrepancy must be reported explicitly. A positive sensitivity cannot rescue a null primary molecular result.

## Stage 4: exploratory whole-transcriptome characterization

Run one prespecified exploratory PLS1-style analysis on the participant-mean left-hemisphere DK34 delta-RSA phenotype using the frozen primary AHBA population expression matrix.

- spatially standardize gene columns across the 34 parcels;
- compute one PLS1 weight vector from the observed phenotype;
- assess the score-phenotype correlation using 5,000 left-hemisphere spherical rotations, rebuilding the PLS solution for each rotated phenotype;
- report the two-sided spatial p-value;
- repeat PLS1 after leaving out each AHBA donor and report rank correlation of gene weights with the full-donor solution.

This stage is exploratory regardless of p-value. Individual high-weight genes are not discoveries and may not be promoted into new within-dataset hypothesis tests or post-hoc pathway screens for the current paper.

## Interpretation rules

The following interpretations are frozen before outcome inspection.

- If positive delta-RSA is broadly distributed across reliable language parcels, describe the effect as network-distributed.
- If one or more parcels show larger, reproducible delta-RSA while others are smaller, describe a graded regional concentration. Do not claim a unique causal locus.
- A region with low neural reliability cannot support a negative-transfer conclusion.
- Baseline text-only RSA and neural-guided delta-RSA are distinct maps and must be interpreted separately.
- A molecular association describes spatial covariation between a postmortem population transcriptomic annotation and the fMRI-derived transfer phenotype. It does not establish receptor, cell-type or gene-level causality.
- The existing NeuroSem AHBA primary nulls remain unchanged regardless of this new phenotype.
- A transcriptome-wide PLS result is exploratory and cannot redefine the frozen molecular family after outcome inspection.

## Stopping rules

After this protocol is frozen:

- do not change the six language parcels based on regional results;
- do not change the DK atlas, hemisphere definition or parcel subset based on delta-RSA;
- do not search alternative LanA thresholds, ROI radii, parcel intersections or voxel-selection rules;
- do not change E5 model, lambda, layer, pooling, checkpoint, semantic unit, HRF, lag, nuisance family or story/participant set;
- do not select the highest-delta region and then define a molecular hypothesis from it;
- do not add gene sets, pathways or cell types after seeing the fMRI spatial map;
- do not use a bilateral/no-mirror sensitivity to rescue a null left-hemisphere molecular primary result;
- do not search for an alternative parcellation if this analysis is null;
- report all predefined regional, molecular and exploratory outcomes, including nulls and hemisphere sensitivities.

## Required safe derived outputs

The execution should emit only derived, non-sensitive results and provenance, including:

- atlas preflight summary with hashes and label mappings;
- language-region model-blind reliability table;
- language-region participant and story transfer tables;
- language-region inferential summary including FWER correction;
- DK68 model-blind reliability table;
- DK68 participant transfer table and population spatial map;
- frozen gene-set association results;
- donor and mirroring sensitivity results;
- exploratory PLS summary and gene-weight file;
- top-level machine-readable summary.

Raw fMRI volumes, raw AHBA data, model checkpoints and restricted data must not be exported as artifacts.

## Design-rationale literature

The regional design follows the group-constrained subject-specific language-network framework introduced by Fedorenko et al. (2010) and the current EvLab 220-participant language parcels. Lipkin et al. (2022) provides the large-sample LanA reference used in the original SMN4Lang analysis. Recent model-brain work supports graded regional variation in language-model correspondence rather than assuming a single language-model locus, including Kumar et al. (Nature Communications, 2024) and Ryskina et al. (COLM, 2025), the latter explicitly using the six SN220 left-hemisphere language parcels for language-model brain analyses.

The molecular analysis reuses the standardized imaging-transcriptomic principles implemented in `abagen` (Markello et al., eLife, 2021) and spatial-autocorrelation-preserving null logic emphasized by Burt et al. (NeuroImage, 2020) and related spatial-map frameworks. These references motivate the design but do not determine or predict the NeuroSem regional outcome.