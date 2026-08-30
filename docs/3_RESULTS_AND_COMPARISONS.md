# 3. Results and Comparisons

**Last updated:** 2026-08-30

This file is the current numerical evidence summary for NeuroSem. The primary prospective evidence and the later post-confirmatory robustness/generalization analyses are kept explicitly separate.

## 3.1 Primary prospective evidence chain

### ChineseEEG development geometry and learnability

The whole-row temporal-mean EEG representation was selected using neural reliability before semantic testing.

- raw LOO reliability approximately **0.220**;
- nuisance-residualized LOO approximately **0.121**.

Held-out Little Prince runs 01-06 showed BERT residual neural-model correspondence of 0.0057, 0.0034, 0.0145, 0.0045, 0.0174 and 0.0056. All six were positive, mean **0.0085**, exact one-sided run-level sign-flip **p = 0.015625**.

Sealed run-07 BERT development result showed neural-guided training exceeding matched text-only and shuffled-neural controls. Multilingual E5 reproduced the qualitative learnability pattern. Lambda=.10 was an outcome-informed development-stage candidate, not a prospectively selected universal optimum.

### ZuCo 2.0 cross-language EEG transfer

Frozen neural reliability:

- mean residual LOO **0.06742**;
- 95% CI **[0.05831,0.07687]**;
- **17/17** positive;
- exact one-sided sign-flip **p = 7.63e-06**.

Frozen multilingual-E5 transfer, lambda=.10 minus matched lambda=0:

- mean participant delta **+0.0016637**;
- median **+0.0014871**;
- **17/17** positive;
- 95% CI **[+0.0012294,+0.0021452]**;
- exact one-sided **p = 7.63e-06**.

Interpretation: positive external neural transfer from ChineseEEG-guided learning to independent English natural-reading EEG.

### SMN4Lang fMRI prospective cross-modal transfer

SMN4Lang/OpenNeuro `ds004078` was designated prospectively for cross-modal validation. The language-network fMRI target passed a model-blind reliability gate before E5 model evaluation.

Primary representation:

- 12 participants, 60 stories, 720 participant-story runs;
- TR 0.710 s;
- LanA probability threshold .20, **25,137 voxels**;
- within-story correlation-distance geometry across retained fMRI timepoints;
- nuisance adjustment for temporal separation, HRF-convolved word-onset density and HRF-convolved acoustic RMS envelope.

Reliability:

- mean residual LOO **0.65327**;
- median **0.64760**;
- **12/12** positive;
- 95% CI **[0.63945,0.66843]**;
- exact one-sided **p = 0.00024414**.

Frozen E5 transfer:

- lambda=0 mean RSA **0.12092396**;
- lambda=.10 mean RSA **0.12177646**;
- mean delta **+0.00085250**;
- median **+0.00086365**;
- **12/12** positive;
- 95% CI **[+0.00078966,+0.00091398]**;
- exact one-sided **p = 0.00024414**.

No SMN4Lang training, layer search, lambda search, checkpoint search, ROI search, lag/HRF search or semantic-unit search occurred from the fMRI outcome.

## 3.2 Primary transfer and reliability boundaries

### TMNRED

- residual LOO reliability **0.00724**, 95% CI **[0.00356,0.01079]**;
- frozen E5 mean transfer delta **+0.000020**;
- 95% CI **[-0.000128,+0.000176]**;
- one-sided **p = .402**.

Transfer null.

### ChineseEEG Garnett Dream

- residual mean LOO **0.01863**;
- **10/10** positive reliability;
- frozen E5 transfer mean delta **+0.0003266**;
- **6/10** positive;
- 95% CI **[-0.0001218,+0.0007560]**;
- one-sided **p = .1016**.

Geometry reliability generalizes, but model-transfer advantage is null/inconclusive.

### Directional inner speech

Frozen lambda=.10 minus lambda=0 mean difference approximately **-0.001786**. This is an out-of-task boundary, not a task-matched reading refutation.

### SMN4Lang MEG reliability boundary

Prospective primary sensor-level representation:

- mean LOO **0.007713**;
- median **0.011320**;
- **7/12** positive;
- 95% CI **[-0.007627,+0.021655]**;
- exact one-sided **p = .16870**.

The model-blind gate failed, so **no model evaluation was performed**. A separately frozen 4/8/16-bin temporal-granularity family also failed familywise reliability. The MEG branch is closed for this paper.

## 3.3 Post-confirmatory E5 optimization-seed robustness

Additional multilingual-E5 seeds `20260829`, `20260830`, and `20260831` reproduced positive external transfer in the original direction. This supports robustness to optimization trajectory within E5, not model-family invariance.

Previously frozen summary:

- ZuCo mean seed-level deltas approximately **+0.0012509**, **+0.0019519**, **+0.0005965**;
- SMN4Lang fMRI mean seed-level deltas approximately **+0.0006959**, **+0.0008971**, **+0.0004453**;
- all three seed-level means positive for both targets;
- all 36 added fMRI seed x participant contrasts positive.

A two-factor participant x stimulus bootstrap also remained positive for ZuCo and SMN4Lang fMRI, but this is a post-confirmatory sensitivity analysis rather than unrestricted random-effects inference over arbitrary linguistic stimuli.

## 3.4 Post-confirmatory reverse fMRI -> EEG transfer

A source-only SMN4Lang fMRI calibration used the frozen lambda grid `{0,.01,.03,.10,.30,1}` and selected the smallest positive lambda within one SE of the best source-validation mean. The best raw source-validation mean was at lambda=1, but the frozen one-SE rule selected **lambda=.01**. The source gate passed before any external EEG was read.

### Primary independent ZuCo target

Frozen lambda=.01 fMRI-guided E5 minus matched lambda=0:

- mean delta RSA **+0.00001671**;
- median approximately **+0.00002095**;
- **14/17** participants positive;
- bootstrap 95% CI approximately **[+0.00001108,+0.00002200]**;
- exact one-sided sign-flip **p = 0.0001068**.

Interpretation: positive post-confirmatory source-modality bidirectionality within multilingual E5.

### Secondary ChineseEEG run-07 target

Frozen lambda=.01 contrast:

- mean delta approximately **+1.32e-06**;
- **7/10** positive;
- bootstrap CI crosses zero;
- exact one-sided **p = .199**.

Directionally concordant but inconclusive. ChineseEEG carries less evidential weight because it contributed to the broader development history.

## 3.5 Post-confirmatory fMRI-guidance dose response

Using already-trained frozen E5 adapters, ZuCo showed a strong graded response as fMRI-guidance weight increased:

| Lambda | ZuCo mean delta RSA | Positive participants |
|---:|---:|---:|
| .01 | +0.0000167 | 14/17 |
| .03 | +0.0000557 | 16/17 |
| .10 | +0.0002016 | 16/17 |
| .30 | +0.0006163 | 16/17 |
| 1.0 | **+0.0017453** | 16/17 |

The participant-level ordered trend was positive in **16/17** participants, mean slope approximately **+0.000807**, bootstrap 95% CI approximately **[+0.000617,+0.000993]**, exact one-sided **p = 1.53e-05**.

This is post-confirmatory dose-response characterization. It does not replace lambda=.01 as the source-selected primary reverse-transfer candidate.

### ChineseEEG multi-seed dose robustness

A separate three-seed analysis tested whether the ChineseEEG dose pattern is optimization-seed robust. Lower/intermediate lambdas were heterogeneous. Only lambda=1.0 produced a positive seed-level mean in all three new seeds:

- seed 20260829: **+7.7478e-05**;
- seed 20260830: **+6.2966e-05**;
- seed 20260831: **+5.4571e-05**;
- mean of seed means **+6.5005e-05**.

All three seed-level ordered slope means were positive, but participant-level intervals crossed zero in each seed. Therefore ChineseEEG provides **suggestive high-dose/ordered-trend consistency**, not a separately established dose-response.

Full details: `24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`.

## 3.6 Post-confirmatory bidirectional model-family panel

A frozen common-protocol panel evaluated six multilingual models, three seeds and both source directions, for **36/36 completed units** with no technical omissions.

Models:

- E5-large;
- E5-base;
- multilingual MPNet;
- multilingual MiniLM;
- XLM-R base;
- mBERT.

Common protocol: final hidden mean pooling, L2 normalization, cosine geometry, LoRA q/v r8 alpha16 dropout .05, InfoNCE text objective, fixed lambda=.10, five epochs, no model-specific lambda/layer/pooling rescue.

### ChineseEEG -> SMN4Lang fMRI

Mean of the three seed-level external deltas:

| Model | Mean seed-level delta | Seed-sign stability |
|---|---:|---|
| E5-large | **+0.00111179** | 3/3 positive |
| E5-base | **+0.00027136** | 3/3 positive |
| multilingual MPNet | **+0.00119328** | 3/3 positive |
| multilingual MiniLM | **+0.00064239** | 3/3 positive |
| XLM-R base | +0.00052302 | mixed |
| mBERT | +0.00024877 | 3/3 positive |

Both E5 variants, MPNet and MiniLM had 12/12 positive fMRI participants in every seed. mBERT was smaller but positive in all three seed-level means. XLM-R was heterogeneous.

### SMN4Lang fMRI -> ZuCo EEG

Mean of the three seed-level external deltas:

| Model | Mean seed-level delta | Seed-sign stability |
|---|---:|---|
| E5-large | **+0.00020314** | 3/3 positive |
| E5-base | **+0.00003368** | 3/3 positive |
| multilingual MPNet | -0.00000122 | mixed / approximately null |
| multilingual MiniLM | **-0.00003740** | 3/3 negative |
| XLM-R base | +0.00003108 | mixed |
| mBERT | **-0.00044102** | 3/3 negative |

E5-large reverse-transfer seeds had 16/17 positive participants in all three runs. E5-base had 14/17, 15/17 and 15/17 positive, with positive bootstrap intervals and exact one-sided p-values .00431, .000572 and .000084 respectively.

### Model-family interpretation

The panel does **not** support a simple “sentence-embedding models work, MLM models fail” rule. MPNet and MiniLM transfer strongly in the EEG -> fMRI direction but do not reproduce reverse fMRI -> EEG transfer. mBERT is positive in the EEG -> fMRI direction under the shared InfoNCE protocol but negative in all three reverse-direction seeds. XLM-R is seed-heterogeneous.

The most defensible model-scope conclusion is:

> Neural relational supervision is architecture- and direction-dependent. EEG-derived constraints can transfer across several multilingual encoders, whereas stable reverse fMRI-to-EEG transfer was reproduced only in both tested multilingual E5 variants. Bidirectional external neural transfer is therefore reproducible within the tested E5 family under the common protocol, but is not a universal property of multilingual encoders.

Full details and exact model revisions: `23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`.

## 3.7 Earlier strict-portability mBERT boundary

An earlier post-confirmatory strict lambda=.10 portability test in multilingual BERT used a different training context, including an MLM-based text objective and a different frozen revision. It produced heterogeneous, seed-dependent external effects across ZuCo and fMRI.

This should not be summarized as “BERT never works.” The later common-protocol panel shows that mBERT can exhibit small positive EEG -> fMRI transfer under a different fixed training context, while reverse fMRI -> EEG remains strongly negative. Training context and direction therefore matter.

## 3.8 Model-space characterization

Within E5, neural supervision induced a small perturbation of an otherwise highly conserved representation. Previously completed characterization reported approximately:

- corresponding embedding cosine similarity **0.998389**;
- RDM Pearson **0.997920**;
- RDM Spearman **0.997445**;
- linear CKA **0.999325**;
- k=10 neighborhood Jaccard **0.927585**.

Interpretation:

> Neural supervision induced a small relational perturbation in an otherwise highly conserved model representation, and the direction of that perturbation was reproducibly associated with improved alignment to independent neural datasets.

## 3.9 AHBA mechanistic extension

Primary gene/pathway analyses and spatially corrected whole-transcriptome analyses remain null. A stronger no-mirror dyslexia-panel sensitivity is exploratory only. No specific molecular mechanism is established.

## 3.10 Joint interpretation

- **Target reliability:** necessary prerequisite and strongly supported in ChineseEEG, ZuCo and SMN4Lang fMRI; failed for the frozen SMN4Lang MEG representation.
- **Learnability:** supported in ChineseEEG and source-side fMRI calibration.
- **Primary external transfer:** supported selectively by ZuCo EEG and prospective SMN4Lang fMRI.
- **Source-modality bidirectionality:** supported post-confirmatorily within multilingual E5 by fMRI -> ZuCo transfer.
- **Optimization robustness:** supported within E5, with target- and lambda-dependent nuances.
- **Model-family scope:** stable bidirectional transfer reproduced across E5-large and E5-base but not uniformly across other multilingual encoders.
- **Universality:** not supported across neural contexts, targets, model families or training contexts.
- **MEG transfer:** not tested because the frozen target failed its reliability prerequisite.
- **Generic semantic improvement:** not established.
- **Specific transcriptomic mechanism:** not established.

Raw RSA values across EEG, fMRI and MEG should not be interpreted as a common effect-size scale. External participant-level inference generalizes across individuals conditional on each dataset's fixed stimulus set unless a separately described stimulus-resampling sensitivity is being discussed.
