# NeuroSem manuscript outline

**Status:** working scaffold, 2026-08-27

This outline follows the locked scientific evidence hierarchy rather than the chronological debugging history. Null results and post-hoc diagnostics are part of the story and must remain visible.

## Central claim

Reading-related EEG contains a small but reproducible relational geometry across datasets, texts, and languages. Neural-guided training can improve alignment to that geometry, but transfer is not universal. A frozen cross-language transfer result is positive in ZuCo, whereas TMNRED and Garnett model-transfer tests are null or inconclusive. Population AHBA transcriptomics does not provide confirmatory support for the prespecified GABAergic or serotonergic mechanisms; exploratory language-panel work identifies a hemispheric preprocessing sensitivity that should not be promoted to confirmatory molecular evidence.

## Results narrative

### 1. Reproducible semantic neural geometry in Chinese natural reading

- Introduce ChineseEEG Little Prince and the reliability-led selection of the temporal-mean channel vector.
- Show residual cross-subject neural geometry after nuisance control.
- Show small but consistent residual correspondence with pinned Chinese BERT across six narrative runs.
- Establish the neural geometry before discussing model tuning.

### 2. Neural-guided training improves held-out alignment within the development dataset

- Present the sealed Little Prince run-07 BERT comparison.
- Show replication of the qualitative effect with multilingual E5.
- Separate neural-target alignment from generic semantic benchmark performance.
- Preserve the null/unstable generic semantic result.

### 3. Independent reading datasets separate neural-geometry replication from model-transfer replication

Present datasets by scientific independence rather than acquisition chronology.

#### TMNRED

- EEG geometry replicates weakly but positively.
- Frozen E5 lambda 0.10 versus text-only lambda 0 transfer is null.
- Exploratory SD and 8-bin follow-ups do not rescue transfer.

#### ZuCo 2.0 normal reading

- Strong independent English-reading reliability replication.
- Frozen ChineseEEG-to-ZuCo E5 transfer is positive across all 17 participants.
- Emphasize cross-dataset and cross-language generalization without claiming generic semantic improvement.

#### Garnett Dream

- Same participants/acquisition family, different narrative.
- EEG reliability replicates with the frozen representation.
- Frozen E5 neural-guided minus text-only transfer is null/inconclusive.
- Use this to distinguish generalization of neural geometry from generalization of the trained model advantage.

#### Nature directional-word EEG

- Treat as an out-of-task boundary condition, not a task-matched reading replication.

### 4. Molecular-mechanistic extension using AHBA

#### Model-blind spatial/transcriptomic preparation

- Show the cortical transcriptomic to EEG sensitivity pipeline.
- State that dataset-provided CapTrak geometry is standardized and not individualized source localization.
- Explain the deterministic DK68 parcel phenotype as sensitivity-weighted back-projection, not an inverse solution.

#### Frozen prespecified mechanisms

- GABA-A, GABA-B, broader GABA machinery, serotonin receptors/machinery, Reactome pathways, and cell-type controls.
- All primary GABA/serotonin mechanistic tests are null after the frozen inference framework.
- Preserve the conclusion that population cortical transcriptomic variation in these prespecified systems does not reliably explain the established ChineseEEG semantic spatial pattern.

### 5. Exploratory transcriptomic analyses do not produce a spatially robust genome-wide mechanism

- Whole-transcriptome PLS1 gives moderate in-sample alignment but is not significant under hemisphere-constrained spatial rotations.
- Intrinsic transcriptomic gradients are not FDR significant.
- Stable LODO gene ranks are robustness of ranking, not evidence of phenotype association.

### 6. Independent published language panels remain primary-null but reveal a bilateral-handling sensitivity

- Freeze the two exact Wong 2024 main-article subsets before outcome testing.
- Six-gene connectivity panel is null.
- Fourteen-gene dyslexia panel shows a suggestive negative primary trend but fails the frozen spatial and coexpression-aware criteria after correction.
- No-mirror sensitivity is strong, but remains exploratory because the primary mirrored analysis failed.

### 7. Mirroring diagnostic localizes the sensitivity to the right hemisphere

- Matched-support analysis rules out parcel-coverage loss as the explanation.
- Left-hemisphere dyslexia-panel association is strong under both mirrored and no-mirror processing.
- Right-hemisphere association changes from approximately zero under mirroring to strongly negative without mirroring.
- Donor LODO preserves the direction of the no-mirror shift.
- Interpret as a methodological warning about bilateral AHBA handling, not confirmatory molecular evidence.

## Discussion structure

### What is supported

1. Reading-related EEG contains reproducible relational geometry.
2. Neural-guided training can improve held-out neural alignment.
3. That advantage can transfer across dataset and language, as shown in ZuCo.
4. Neural-geometry replication is more robust than model-transfer replication.

### What is not supported

1. A broad claim that brain-guided training improves generic semantic representations.
2. Universal neural-guided transfer across reading datasets.
3. A confirmatory GABAergic or serotonergic molecular mechanism from AHBA.
4. A confirmatory published-language-gene association after the frozen primary null framework.

### Mechanistic interpretation

- Treat AHBA as a population postmortem spatial prior from six donors.
- Do not claim receptor causality or participant-specific molecular biology.
- Discuss the mirroring diagnostic as evidence that bilateral preprocessing can materially alter language-related transcriptomic maps when right-hemisphere sampling is sparse.

### Limitations

- EEG spatial localization is coarse and based on standardized dataset geometry and fsaverage forward modeling.
- Cross-dataset acquisition and task differences constrain transfer interpretation.
- Neural-model effects are small in absolute RSA units.
- AHBA donor number and asymmetric right-hemisphere sampling limit molecular inference.
- No-mirror dyslexia result is post-hoc diagnostic and requires independent bilateral transcriptomic validation.

## Final framing

The paper should not be framed as "brain supervision improves language models." The stronger framing is that reproducible neural semantic geometry can serve as a biologically grounded relational target whose learnability and transfer can be tested prospectively, revealing both successful cross-language neural transfer and clear boundaries on semantic and molecular generalization.
