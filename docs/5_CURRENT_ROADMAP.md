# 5. Current Roadmap

**Last updated:** 2026-08-30

NeuroSem is in an **evidence-locked manuscript-consolidation phase** for the primary paper. The prospective evidential chain is complete and must remain historically unchanged. The planned post-confirmatory robustness/generalization analyses have now also been executed and should be integrated as secondary explanatory evidence rather than used to redefine the original confirmation status.

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

## Relationship to the earlier mBERT experiment

The earlier strict-portability mBERT experiment and the new common-protocol panel used different training contexts and different frozen revisions. The earlier experiment used an MLM-based text objective and produced heterogeneous external effects. The new panel used the same InfoNCE-based sentence-geometry training objective for all six models. Under that protocol, mBERT shows small positive EEG -> fMRI transfer but strongly negative fMRI -> EEG transfer.

The correct synthesis is not “BERT does not work.” It is:

> Generic MLM encoders have not shown the stable bidirectional portability observed for E5, and transfer behavior depends on both architecture and training context.

## Manuscript integration priority

The next work should be manuscript/figure integration, not additional model fishing.

1. Preserve the original prospective result as the main evidential chain.
2. Add bidirectional E5 transfer as a secondary/post-confirmatory strengthening analysis.
3. Add the six-model panel as explanatory model-scope evidence, preferably Extended Data or a compact main-text robustness paragraph plus Extended Data figure/table.
4. Preserve all heterogeneous and negative model-family outcomes.
5. Keep the ChineseEEG multi-seed dose result secondary and nuanced.
6. Update figure legends, Methods and limitations to distinguish prospective, source-selected post-confirmatory, and exploratory/post-confirmatory analyses.
7. Recheck all exact RunRelay job/commit/artifact provenance before final submission.

## Suggested manuscript language

Primary cross-modal statement:

> Human neural geometry can provide a transferable relational constraint on language representations, with effects that generalize across independent brains, languages and measurement modalities, but not universally across neural contexts.

Bidirectional statement:

> In a post-confirmatory reverse-direction analysis, an fMRI-derived relational constraint produced a small but statistically supported improvement in independent ZuCo EEG alignment, providing evidence for source-modality bidirectionality within multilingual E5.

Architecture statement:

> In a post-confirmatory six-model panel, stable bidirectional external transfer was reproduced across multilingual E5-large and E5-base, whereas other multilingual sentence-embedding and generic masked-language encoders showed direction-specific or seed-dependent effects. Thus, the transferable relational effect is not universal across encoder architectures.

Dose statement:

> Post-confirmatory dose-response characterization showed progressively larger fMRI-guidance effects on independent ZuCo EEG, whereas the corresponding ChineseEEG pattern was less stable across optimization seeds and remained secondary.

## Current stopping rules

- Do not reopen the original ZuCo or SMN4Lang target-side model/representation choices.
- Do not promote any target-observed lambda to prospective status.
- Do not perform model-specific rescue lambda/layer/pooling searches for MPNet, MiniLM, XLM-R or mBERT after the completed panel.
- Do not add more model families merely to improve the narrative unless a reviewer/editor asks a clearly specified question.
- No new dataset search for positive transfer for the current paper.
- No rescue search for TMNRED or Garnett.
- No E5 evaluation on failed MEG targets and no further MEG representation expansion.
- No additional AHBA significance search.
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
