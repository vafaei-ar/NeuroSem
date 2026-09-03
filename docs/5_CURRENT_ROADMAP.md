# 5. Current Roadmap

**Last updated:** 2026-09-03

NeuroSem is in an **evidence-locked manuscript-consolidation phase** for the primary paper. The prospective evidential chain is complete and must remain historically unchanged. The planned post-confirmatory robustness/generalization analyses have also been executed. A separately frozen post-confirmatory regional SMN4Lang extension has now completed its atlas, model-blind reliability, and regional E5-transfer stages; its prespecified AHBA molecular interpretation remains pending.

## Primary scientific position

The primary paper remains centered on the following claim:

> Human neural geometry can provide a transferable relational constraint on language representations, with effects that generalize across independent brains, languages and measurement modalities, but not universally across neural contexts.

The original prospective evidence is still:

1. ChineseEEG Little Prince: reproducible neural geometry and learnability.
2. ZuCo 2.0 normal reading: independent cross-language EEG transfer.
3. SMN4Lang fMRI: model-blind reliability gate followed by prospectively frozen cross-modal E5 transfer.
4. Explicit boundaries: TMNRED, Garnett Dream, directional inner speech and SMN4Lang MEG reliability failure.

None of the post-confirmatory analyses below changes the historical status of that chain.

## Completed post-confirmatory analyses

### 1. E5 optimization-seed robustness

The original E5 external-transfer direction is robust across additional optimization seeds. This argues against a single lucky training trajectory within multilingual E5 but does not establish model-family independence.

### 2. Bidirectional fMRI -> EEG transfer

A frozen source-only calibration selected lambda=.01 before any EEG target was read. The primary reverse-direction test on independent ZuCo EEG was positive:

- mean delta RSA **+0.00001671**;
- **14/17** participants positive;
- bootstrap 95% CI approximately **[+0.00001108,+0.00002200]**;
- exact one-sided sign-flip **p = 0.0001068**.

A secondary ChineseEEG run-07 check was directionally positive but inconclusive. Therefore the strongest reverse-direction statement is based on ZuCo.

Interpretation:

> Cross-modal relational transfer is supported in both source-to-target directions within multilingual E5, but the reverse direction is smaller and not uniformly established across all EEG targets.

### 3. Post-confirmatory fMRI-guidance dose response

Using the already-trained E5 lambda grid, ZuCo shows a strong ordered increase in fMRI-to-EEG transfer with larger neural weight. This is a post-confirmatory dose-response characterization, not a new confirmatory lambda search.

On ChineseEEG, the original single-seed curve suggested the same direction, but the subsequent three-seed robustness analysis showed substantial heterogeneity at low/intermediate lambdas. Only lambda=1.0 had positive seed-level mean delta in all three added seeds. All three seed-level ordered slopes were positive, but participant-level intervals crossed zero.

Therefore ChineseEEG should be described as **suggestive high-dose/ordered-trend consistency**, not as an independently established dose-response. See `24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`.

### 4. Bidirectional model-family panel

The six-model x three-seed x two-direction common-protocol panel is complete. See `23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`.

The central pattern is:

- **E5-large:** positive in all three seeds for EEG -> fMRI and fMRI -> EEG.
- **E5-base:** positive in all three seeds for EEG -> fMRI and fMRI -> EEG.
- **multilingual MPNet:** stable EEG -> fMRI transfer, but reverse fMRI -> EEG approximately null/mixed.
- **multilingual MiniLM:** stable EEG -> fMRI transfer, but reverse fMRI -> EEG negative in all three seeds.
- **XLM-R base:** heterogeneous in both directions.
- **mBERT:** small positive EEG -> fMRI under the common protocol, but reverse fMRI -> EEG negative in all three seeds.

The defensible secondary architecture conclusion is:

> Neural relational supervision is architecture- and direction-dependent. EEG-derived constraints can transfer across several multilingual encoders, whereas stable reverse fMRI-to-EEG transfer was reproduced only in both tested multilingual E5 variants. Bidirectional external neural transfer is therefore reproducible within the tested E5 family under the common protocol, but is not a universal multilingual-encoder property.

Do not claim that E5 is uniquely capable among all possible language models. The panel used one common adaptation protocol and fixed lambda=.10, intentionally avoiding model-specific rescue tuning.

### 5. Regional SMN4Lang fMRI characterization

The frozen regional extension is documented in `26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md` and the completed neural/model result in `29_NMI_REGIONAL_FMRI_TRANSFER_RESULT_V1.md`.

The final atlas gate passed after two pre-outcome technical amendments, both made before regional model outcomes. Model-blind regional reliability then passed for all **6/6** language parcels and all **68/68** DK cortical parcels.

The regional E5 contrast used only the already-established ChineseEEG-trained lambda=.10 genuine-neural and lambda=0 text-only arms. Across the six frozen left-hemisphere language parcels:

- every region had positive delta-RSA in **12/12** participants;
- every region had a participant-bootstrap CI above zero;
- every region had exact two-sided sign-flip `p = 0.000488`;
- every region survived the prespecified six-region max-stat FWER correction.

The largest language-parcel effects were:

- posterior temporal cortex: **+0.000852**, FWER `p = 0.000488`;
- anterior temporal cortex: **+0.000751**, FWER `p = 0.000977`.

The correct frozen interpretation is:

> The neural-guided representational improvement is distributed across the independently defined language network, with a graded concentration in temporal language cortex.

The complete DK68 map is retained as an unthresholded spatial phenotype. All 68 parcels had positive mean delta-RSA and 12/12 positive participants, but the DK map is not a 68-region significance screen and no parcel is selected from these outcomes for the molecular stage.

The participant x story bootstrap was also positive in 100% of 10,000 replicates for every language parcel. This is a sensitivity over the 12 analyzed participants and 60 analyzed stories, not unrestricted stimulus-population inference.

## Relationship to the earlier mBERT experiment

The earlier strict-portability mBERT experiment and the new common-protocol panel used different training contexts and different frozen revisions. The earlier experiment used an MLM-based text objective and produced heterogeneous external effects. The new panel used the same InfoNCE-based sentence-geometry training objective for all six models. Under that protocol, mBERT shows small positive EEG -> fMRI transfer but strongly negative fMRI -> EEG transfer.

The correct synthesis is not “BERT does not work.” It is:

> Generic MLM encoders have not shown the stable bidirectional portability observed for E5, and transfer behavior depends on both architecture and training context.

## Current active analysis

The only currently authorized outcome-bearing extension is the already-frozen molecular continuation of the regional SMN4Lang analysis.

Stage 3 must use the complete participant-level DK delta-RSA phenotype without significance-based parcel filtering. The primary molecular domain remains left DK34, using the previously frozen AHBA expression preparation, seven GABA/serotonin/pathway sets, seven cell-type specificity controls, 5,000 spatial rotations, 5,000 size-matched random gene sets, donor leave-one-out robustness, and the mandatory mirroring sensitivities. Stage 4 remains the prespecified exploratory PLS1 analysis.

This new phenotype is distinct from the previous EEG-derived AHBA phenotype. A positive or null result cannot revise or rescue the already-completed AHBA primary conclusions.

## Manuscript integration priority

The next work should remain disciplined and evidence-locked.

1. Preserve the original prospective result as the main evidential chain.
2. Add bidirectional E5 transfer as a secondary/post-confirmatory strengthening analysis.
3. Add the six-model panel as explanatory model-scope evidence, preferably Extended Data or a compact main-text robustness paragraph plus Extended Data figure/table.
4. Integrate the regional fMRI result as post-confirmatory spatial characterization, clearly distinct from the prospective whole-network SMN4Lang result.
5. Preserve all heterogeneous and negative model-family outcomes.
6. Keep the ChineseEEG multi-seed dose result secondary and nuanced.
7. Complete only the already-frozen regional AHBA Stage 3/4 analysis; do not use it to generate new within-dataset molecular hypotheses.
8. Update figure legends, Methods and limitations to distinguish prospective, source-selected post-confirmatory, regional post-confirmatory, and exploratory analyses.
9. Recheck all exact RunRelay job/commit/artifact provenance before final submission.

## Suggested manuscript language

Primary cross-modal statement:

> Human neural geometry can provide a transferable relational constraint on language representations, with effects that generalize across independent brains, languages and measurement modalities, but not universally across neural contexts.

Bidirectional statement:

> In a post-confirmatory reverse-direction analysis, an fMRI-derived relational constraint produced a small but statistically supported improvement in independent ZuCo EEG alignment, providing evidence for source-modality bidirectionality within multilingual E5.

Architecture statement:

> In a post-confirmatory six-model panel, stable bidirectional external transfer was reproduced across multilingual E5-large and E5-base, whereas other multilingual sentence-embedding and generic masked-language encoders showed direction-specific or seed-dependent effects. Thus, the transferable relational effect is not universal across encoder architectures.

Dose statement:

> Post-confirmatory dose-response characterization showed progressively larger fMRI-guidance effects on independent ZuCo EEG, whereas the corresponding ChineseEEG pattern was less stable across optimization seeds and remained secondary.

Regional statement:

> In a separately frozen post-confirmatory regional analysis, the neural-guided improvement was positive throughout the independently defined language network and survived family-wise correction in all six parcels, with the largest effects in posterior and anterior temporal language cortex.

## Current stopping rules

- Do not reopen the original ZuCo or SMN4Lang target-side model/representation choices.
- Do not promote any target-observed lambda to prospective status.
- Do not perform model-specific rescue lambda/layer/pooling searches for MPNet, MiniLM, XLM-R or mBERT after the completed panel.
- Do not add more model families merely to improve the narrative unless a reviewer/editor asks a clearly specified question.
- No new dataset search for positive transfer for the current paper.
- No rescue search for TMNRED or Garnett.
- No E5 evaluation on failed MEG targets and no further MEG representation expansion.
- Do not change the six regional language parcels, DK atlas, lambda, layer, HRF, nuisance family, story set, model, or voxel threshold from regional outcomes.
- Do not select or rank-filter DK parcels before AHBA.
- For the new regional AHBA phenotype, use only the already-frozen molecular families and sensitivity analyses. Do not add gene sets, pathways, parcel subsets, or transcriptomic follow-ups from observed outcomes.
- Preserve the previous AHBA nulls regardless of the regional extension.
- Preserve all nulls, negative effects, heterogeneous seeds and reliability failures.

## Key completed protocol/result documents

- `15_POSTCONFIRMATORY_GENERALIZATION_TODO.md` - historical design queue; now superseded operationally by completed result documents.
- `17_NMI_BIDIRECTIONAL_FMRI_SOURCE_FREEZE_V1.md`
- `18_NMI_BIDIRECTIONAL_FMRI_SOURCE_CALIBRATION_V1.md`
- `19_NMI_BIDIRECTIONAL_FMRI_TO_ZUCO_V1.md`
- `22_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_V1.md`
- `22_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_V1.md`
- `23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`
- `24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`
- `26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md`
- `27_NMI_REGIONAL_FMRI_ATLAS_PREFLIGHT_AMENDMENT_V1.md`
- `28_NMI_REGIONAL_FMRI_DK_RESAMPLING_AMENDMENT_V1.md`
- `29_NMI_REGIONAL_FMRI_TRANSFER_RESULT_V1.md`
