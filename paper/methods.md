# Methods

**Working manuscript scaffold.** This document organizes the frozen NeuroSem methods into manuscript order. Exact implementation details remain authoritative in the analysis scripts, frozen protocol documents, RunRelay job commits, and safe derived artifacts.

## Study design and evidence hierarchy

NeuroSem was designed to distinguish three claims: reproducibility of neural language geometry, learnability of that geometry by language models, and transfer of any neural-guided advantage beyond the development setting. Analysis choices were frozen prospectively whenever possible. Later exploratory or post-hoc analyses are labeled explicitly and are not used to revise prior confirmatory conclusions.

The main datasets were ChineseEEG Little Prince for discovery and model development, TMNRED for independent Chinese sentence-reading replication, ZuCo 2.0 Task 1 Normal Reading for independent English-reading replication, ChineseEEG Garnett Dream for same-participant/new-text validation, and the Nature directional-word EEG dataset for an out-of-task boundary condition. The Allen Human Brain Atlas was used only as a population-level postmortem transcriptomic spatial prior.

## ChineseEEG primary neural representation

For each linguistic item, the EEG epoch was represented as a channel-by-time matrix. The primary representation averaged activity across time separately within each channel, retaining one value per channel. Across items, each channel feature was standardized before construction of the neural representational dissimilarity matrix. Pairwise neural dissimilarity was correlation distance.

This temporal-mean representation was selected using cross-subject neural reliability before semantic-model testing because it was more reproducible than the initial flattened sensor-time representation. Richer alternatives, including amplitude variability, temporal bins, spectral power, and phase-oriented features, were treated as sensitivity or exploratory representations unless prospectively frozen for an independent dataset.

## Representational similarity analysis

For each analysis unit, a neural RDM and a model-semantic RDM were constructed over the same ordered items. The established primary semantic analysis used pinned `bert-base-chinese` final-layer mean-pooled representations for the ChineseEEG BERT correspondence analysis.

Partial Spearman RSA was implemented as Pearson correlation between separately rank-transformed and nuisance-residualized RDM edge vectors. For the established ChineseEEG semantic analysis, nuisance RDMs included within-run position, presentation duration, character count, chapter mismatch where applicable, character-set Jaccard distance, and punctuation count where exact text was available. Dataset-specific frozen protocols defined the applicable nuisance subset when some text-derived quantities were unavailable.

## Neural reliability

Cross-subject reliability was evaluated using leave-one-subject-out reference geometry. For each participant, that participant's neural RDM was compared with the aggregate geometry derived from the remaining participants over the valid common item set. Nuisance-residualized reliability used the same applicable nuisance framework defined before outcome testing.

Group uncertainty was summarized with participant-level bootstrap confidence intervals and exact sign-flip inference where prespecified. Sensitivity representations were reported separately and did not replace the prospectively designated primary representation based on stronger numerical effects.

## ChineseEEG model-guided training

BERT and multilingual-E5 neural-guided training compared an auxiliary neural relational objective with matched language-only controls under frozen training and evaluation procedures. The decisive within-ChineseEEG BERT test used sealed Little Prince run 07 after development on earlier runs. Four arms were compared: base, text-only, neural-guided, and shuffled-neural.

For the later cross-dataset E5 validations, the frozen primary contrast was the already-trained neural-guided lambda 0.10 model minus the matched text-only lambda 0 model. External datasets were not used to tune lambda, representation, subject inclusion, item inclusion, pooling, or architecture.

## TMNRED validation

TMNRED was processed through model-blind structural, format, event-alignment, stimulus, and materialization freezes before signal-level outcome analysis. The frozen cohort contained 29 participants across eight sessions. Sentence items were retained if present for at least 80% of participants within session; all 50 items passed in every session.

The primary EEG representation was the ChineseEEG-selected `row_mean_all` temporal mean. `row_std_all` and `relative_8bin_all` were frozen sensitivity representations. After the EEG-only reliability analysis, the previously trained ChineseEEG E5 lambda 0.10 and lambda 0 models were evaluated without TMNRED tuning. Post-confirmatory transfer tests on the sensitivity EEG representations were explicitly exploratory.

## ZuCo 2.0 normal-reading validation

The target dataset was ZuCo 2.0 Task 1 Normal Reading. Model-blind format and structural QC identified a full target cohort of 18 participants and seven runs, with 17 participants retained across all seven runs after one participant was excluded for prespecified structural event failures.

Sentence identity was frozen before outcome testing using a deterministic monotonic alignment between EEG sentence order and the public task-material rows. The unique zero-cost mapping skipped the first three public material rows in each run and mapped all remaining rows one-to-one to EEG sentence order.

The primary EEG representation was the prospectively inherited temporal mean. The frozen model-transfer comparison used the already-trained ChineseEEG multilingual-E5 neural-guided lambda 0.10 and matched text-only lambda 0 models, with no ZuCo tuning or outcome-based selection.

## Garnett Dream validation

Garnett Dream was treated as same-participant/new-text validation within the ChineseEEG acquisition family rather than as an independent cohort replication. Structural preparation froze the `ROWS -> ROWE` presentation-row unit, the filtered BrainVision source family, valid participant/run coverage, and chapter identities before EEG reliability analysis.

The final exact text mapping used the authors' non-display segmented XLSX workbooks. Physical row 1 was the validated `Chinese_text` schema header, and the frozen mapping was `CHxx_ROWyyyy -> physical XLSX row yyyy + 1`. Across 18 chapters, 9,047 linguistic items were mapped.

The EEG-only primary target remained `row_mean_all`. The final model-transfer analysis compared ChineseEEG-trained E5 lambda 0.10 neural-guided with matched lambda 0 text-only, analyzing chapters separately and aggregating chapter RSA within participant using Fisher z. The full available text-derived nuisance family was restored before this outcome-bearing test.

## Nature directional-word boundary analysis

The Nature directional-word dataset involved covert/inner speech of directional concepts rather than natural reading. It was therefore analyzed as a secondary out-of-task generalization test. The same frozen E5 lambda 0.10 versus lambda 0 contrast was evaluated without using the result to redefine the reading-dataset analysis choices.

## AHBA transcriptomic preprocessing

The Allen Human Brain Atlas analysis used `abagen 0.1.3` with all six donors. Frozen preprocessing included intensity-based filtering with threshold 0.5, differential-stability probe selection, donor-level probe aggregation, sample and gene normalization using the frozen scaled robust sigmoid settings, corrected MNI coordinates, reannotation, donor aggregation, and explicit bilateral handling.

The primary expression analysis used left-to-right mirroring. A no-mirror analysis was retained as a prespecified bilateral sensitivity. The primary mirrored cortical expression matrix retained 15,677 genes; the no-mirror sensitivity retained 15,633 genes. Donor-level parcel missingness was preserved rather than imputed.

## EEG forward/source-sensitivity model for AHBA projection

The ChineseEEG dataset-provided 128-channel CapTrak-labeled geometry was treated as standardized dataset geometry, not individualized digitization. A model-blind template forward model was frozen before molecular outcome testing.

The final spatial model used fsaverage ico-5 cortical source space, a three-layer BEM, explicit rigid measured-head-to-fsaverage registration, average reference, fixed surface-normal source orientation, absolute lead-field sensitivity, and per-channel L1 normalization. The resulting forward-sensitivity matrix contained 128 channels by 20,484 cortical vertices.

The Desikan-Killiany cortical mapping contained 68 parcels. Of 20,484 source vertices, 18,742 mapped to the DK cortical domain. For transcriptomic projection, channel sensitivity was renormalized within the mapped DK domain before applying cortical gene maps.

## Molecular-sensitivity matrix

For each gene, the aggregated cortical expression map was expanded over the mapped ico-5 vertices according to the frozen DK parcel mapping. Each gene map was standardized spatially across the available cortical vertices using the frozen unweighted vertex z-scoring convention. For channel `e` and cortical vertex `v`, the projected molecular weight was computed as the sensitivity-weighted sum of the standardized cortical map.

This produced gene-by-channel molecular sensitivity matrices for the primary mirrored expression analysis, no-mirror sensitivity, and donor leave-one-out variants on common observed parcel support.

## Frozen biological gene sets

Before the primary molecular outcome analysis, 14 biological sets were frozen. The seven primary mechanistic sets were GABA-A receptor subunits, GABA-B receptors, broader GABA machinery, serotonin receptors, serotonin machinery, Reactome GABA receptor activation, and Reactome serotonin receptors. Seven broad cell-type panels were treated as specificity controls: excitatory neurons, inhibitory neurons, astrocytes, oligodendrocytes, oligodendrocyte precursor cells, microglia, and endothelial cells.

Each multi-gene molecular map was formed after spatial standardization of individual gene maps. Gene-set membership was not altered after NeuroSem outcomes were inspected.

## Frozen AHBA semantic spatial target

The established ChineseEEG semantic contribution target was derived from the pinned residual BERT RSA. At the channel level, the contribution of each channel was quantified by the change in the full residual semantic RSA after leaving that channel out, averaged across frozen runs within participant.

For cortical transcriptomic comparison, a deterministic DK68 parcel phenotype was constructed by sensitivity-weighted back-projection through the already-frozen forward model. Channel sensitivity to each DK parcel was computed as the fraction of mapped channel sensitivity falling in that parcel. The parcel target was then the sensitivity-weighted average of the frozen channel contribution values. This is a deterministic back-projection and not an anatomical inverse solution or individualized source localization.

## Frozen gene-set association inference

For each participant and gene set, the participant semantic spatial target and molecular map were rank standardized and compared using Spearman correlation. Participant effects were Fisher-z transformed for aggregation. Exact two-sided sign-flip inference was performed at the participant level, with BH-FDR correction within the prespecified mechanistic and control families.

Gene-set-size-matched random controls used 5,000 random sets with frozen seed 20260827. Donor leave-one-out and no-mirror analyses were treated as robustness or sensitivity analyses and were not allowed to rescue a failed primary test.

## Exploratory whole-transcriptome analysis

After the prespecified mechanistic null, a separate explicitly exploratory transcriptomic analysis used the frozen AHBA-blind DK68 semantic phenotype and the primary mirrored AHBA expression matrix. PLS1 was fit across the whole transcriptome, intrinsic transcriptomic gradients were evaluated, and donor leave-one-out gene-weight ranking stability was quantified.

Spatial inference used 5,000 hemisphere-constrained spherical rotations on fsaverage spherical parcel centroids followed by within-hemisphere one-to-one Hungarian reassignment. This procedure preserves hemispheric assignment and approximate spatial structure; it should not be described as a reflection-coupled bilateral spin implementation.

## Published language-gene validation

Two exact language-related panels explicitly listed in the Wong et al. 2024 main article were frozen independently of NeuroSem outcomes: a six-gene structural-connectivity subset and a fourteen-gene dyslexia-related subset. These panels are exact published subsets within the reported language-gene framework, not a reconstruction of the inaccessible full 56-gene supplementary panel.

Each panel map was formed from retained AHBA genes after spatial standardization. Association with the frozen DK68 semantic phenotype was tested using Spearman correlation. Inference used 5,000 spatial rotations, 5,000 size-matched random gene sets, and 5,000 panel-coexpression-profile-matched random gene sets with frozen seed 20260827. The two panels formed one multiple-testing family. A panel was considered supported only if both spatial and coexpression-profile BH q values were below 0.05.

Donor leave-one-out and no-mirror analyses were reported as robustness/sensitivity analyses and could not revise the primary mirrored conclusion.

## Post-hoc mirroring diagnostic

Because the no-mirror dyslexia-panel sensitivity was substantially stronger than the failed primary mirrored result, a post-hoc method-sensitivity diagnostic was conducted without changing the frozen panel membership or confirmatory conclusion.

The diagnostic compared mirrored and no-mirror panel maps on identical common parcel support, decomposed associations by hemisphere and individual frozen panel gene, quantified parcel-level map shifts and donor coverage, and repeated matched-support leave-one-donor-out comparisons. This analysis was designed to explain sensitivity to bilateral preprocessing rather than to generate a new confirmatory molecular claim.

## Reproducibility and execution

All workstation analyses were executed through RunRelay using exact NeuroSem commits, the project-bound machine, and Telegram manual approval under the repository's safe execution profile. Safe derived artifacts were mirrored to Google Drive. Raw neural datasets, PHI, credentials, and restricted data were not declared as transport artifacts.

The experiment ledger records failed engineering jobs when they affected provenance. Engineering-only failures did not authorize changes to frozen scientific choices unless explicitly documented.
