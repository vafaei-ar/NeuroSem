# 3. Results and Comparisons

**Last updated:** 2026-09-04

This file is the current numerical evidence summary for NeuroSem. The primary prospective evidence and later post-confirmatory specificity, robustness, dose, model-family, regional and transcriptomic analyses are kept explicitly separate.

## 3.1 Primary prospective evidence chain

### ChineseEEG development geometry and learnability

The whole-row temporal-mean EEG representation was selected using neural reliability before semantic testing.

- raw LOO reliability approximately **0.220**;
- nuisance-residualized LOO approximately **0.121**.

Held-out Little Prince runs 01-06 showed BERT residual neural-model correspondence of 0.0057, 0.0034, 0.0145, 0.0045, 0.0174 and 0.0056. All six were positive, mean **0.0085**, exact one-sided run-level sign-flip **p = 0.015625**.

Sealed run-07 BERT development showed neural-guided training exceeding matched text-only and shuffled-neural controls. Multilingual E5 reproduced the qualitative learnability pattern. `lambda=0.10` was an outcome-informed development-stage candidate, not a prospectively selected universal optimum.

### ZuCo 2.0 cross-language EEG transfer

Frozen neural reliability:

- mean residual LOO **0.06742**;
- 95% CI **[0.05831,0.07687]**;
- **17/17** positive;
- exact one-sided sign-flip **p = 7.63e-06**.

Frozen multilingual-E5 transfer, `lambda=0.10` minus matched `lambda=0`:

- text-only mean RSA **-0.00796**;
- neural-guided mean RSA **-0.00630**;
- mean participant delta **+0.0016637**;
- median **+0.0014871**;
- **17/17** positive;
- 95% CI **[+0.0012294,+0.0021452]**;
- exact one-sided **p = 7.63e-06**.

The primary inference concerns the paired upward displacement, not whether either absolute arm differs from zero.

### SMN4Lang fMRI prospective cross-modal transfer

SMN4Lang/OpenNeuro `ds004078` was designated prospectively for cross-modal validation. The language-network fMRI target passed a model-blind reliability gate before E5 model evaluation.

Primary representation:

- 12 participants, 60 stories, 720 participant-story runs;
- LanA probability threshold 0.20, **25,137 voxels**;
- within-story correlation-distance geometry across retained fMRI timepoints;
- nuisance adjustment for temporal separation, HRF-convolved word-onset density and HRF-convolved acoustic RMS envelope.

Reliability:

- mean residual LOO **0.65327**;
- median **0.64760**;
- **12/12** positive;
- 95% CI **[0.63945,0.66843]**;
- exact one-sided **p = 0.00024414**.

Frozen E5 transfer:

- `lambda=0` mean RSA **0.12092396**;
- `lambda=0.10` mean RSA **0.12177646**;
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

Geometry reliability generalizes, but model-transfer advantage is inconclusive.

### Directional inner speech

Frozen `lambda=0.10` minus `lambda=0` mean difference approximately **-0.001786**. This is an out-of-task boundary, not a task-matched reading refutation.

### SMN4Lang MEG reliability boundary

Prospective primary sensor-level representation:

- mean LOO **0.007713**;
- median **0.011320**;
- **7/12** positive;
- 95% CI **[-0.007627,+0.021655]**;
- exact one-sided **p = .16870**.

The model-blind gate failed, so **no model evaluation was performed**. A separately frozen 4/8/16-bin temporal-granularity family also failed familywise reliability.

## 3.3 Post-confirmatory neural-specificity control

Three fixed E5 optimization seeds compared text-only, genuine-neural and shuffled-neural arms under the same `lambda=0.10` relational-loss weight and optimization budget.

### Genuine minus shuffled

ZuCo seed-level mean delta-RSA:

- seed 20260829: **+0.0012913**, 17/17 positive;
- seed 20260830: **+0.0018972**, 17/17 positive;
- seed 20260831: **+0.0006767**, 15/17 positive.

SMN4Lang fMRI seed-level mean delta-RSA:

- seed 20260829: **+0.0006763**, 12/12 positive;
- seed 20260830: **+0.0008705**, 12/12 positive;
- seed 20260831: **+0.0004095**, 12/12 positive.

### Shuffled minus text

- ZuCo: approximately **-0.0000403**, **+0.0000547**, **-0.0000802** across the three seeds.
- SMN4Lang fMRI: approximately **+0.0000196**, **+0.0000266**, **+0.0000357**.

Interpretation: preserving neural item correspondence contributes substantially more transfer than the matched destroyed-correspondence objective. A small generic relational component remains possible in fMRI. This control does not establish uniqueness relative to every structured non-neural target.

## 3.4 Participant x stimulus robustness

A post-confirmatory 10,000-replicate two-factor bootstrap independently resampled participants and observed stimulus units.

- ZuCo 95% interval: **[+0.000996,+0.002476]**; fraction of bootstrap means > 0 = **1.000**.
- SMN4Lang fMRI 95% interval: **[+0.000653,+0.001068]**; fraction > 0 = **1.000**.

This supports robustness to the observed stimulus samples, not unrestricted random-effects inference over arbitrary linguistic stimuli.

## 3.5 Forward ChineseEEG -> external-target dose characterization

The complete already-trained E5 grid was frozen for external characterization after the primary `lambda=0.10` tests. `lambda=0` and `lambda=0.10` reuse the primary outcomes; the other doses were evaluated subsequently without target-side tuning.

| Lambda | ZuCo mean delta-RSA | SMN4Lang fMRI mean delta-RSA | Generic STS delta vs lambda=0 |
|---:|---:|---:|---:|
| 0.01 | +0.000211 | +0.000107 | -0.000088 |
| 0.03 | +0.000477 | +0.000283 | -0.000418 |
| 0.10 | +0.001664 | +0.000852 | -0.001655 |
| 0.30 | +0.008739 | +0.003038 | -0.007936 |
| 1.00 | +0.027599 | -0.000991 | -0.034533 |

ZuCo was positive in all 17 participants at every non-zero dose. Its absolute neural-guided mean became positive at `lambda=0.30` (**+0.000780**) and reached **+0.01964** at `lambda=1.0`.

SMN4Lang fMRI was positive in all 12 participants through `lambda=0.30`, where mean delta-RSA reached **+0.003038**. At `lambda=1.0`, the effect reversed: mean delta-RSA **-0.000991**, **5/12** positive, 95% CI approximately **[-0.001937,-0.000154]**.

Interpretation:

> Transfer is dose-sensitive and target-dependent. The grid does not identify a single target-independent optimum.

The STS axis was known before the external-dose freeze and is descriptive only.

## 3.6 Model-space perturbation

On the frozen 349-item ZuCo set:

| Metric | lambda=0.10 vs 0 | lambda=1.0 vs 0 |
|---|---:|---:|
| Corresponding-item cosine | 0.998389 | 0.942214 |
| Pairwise RDM Pearson | 0.997920 | 0.796530 |
| Pairwise RDM Spearman | 0.997445 | 0.778871 |
| Centered linear CKA | 0.999325 | 0.937665 |
| k=10 neighborhood Jaccard | 0.927585 | 0.579399 |

The prospective dose therefore induces a small perturbation of an otherwise highly conserved representation. The high-dose regime produces much larger relational and local-neighborhood restructuring and a much larger generic STS cost.

## 3.7 Post-confirmatory reverse fMRI -> EEG transfer

A source-only SMN4Lang fMRI calibration selected `lambda=0.01` using held-out source stories before external EEG evaluation.

### Primary reverse ZuCo target

Frozen `lambda=0.01` fMRI-guided E5 minus matched `lambda=0`:

- mean delta-RSA **+0.00001671**;
- **14/17** positive;
- exact one-sided sign-flip **p = 0.0001068**.

A later three-seed robustness analysis retained the same contrast:

- seed 20260829: **+0.0000319**, 14/17 positive, 95% CI **[+0.0000161,+0.0000467]**;
- seed 20260830: **+0.0000203**, 14/17 positive, 95% CI **[+0.0000120,+0.0000293]**;
- seed 20260831: **+0.0000170**, 14/17 positive, 95% CI **[+0.0000096,+0.0000252]**.

The original source-selected `lambda=0.01` result remains the primary reverse test.

### Reverse dose characterization on ZuCo

| Lambda | Mean delta-RSA | Positive participants |
|---:|---:|---:|
| 0.01 | +0.0000167 | 14/17 |
| 0.03 | +0.0000557 | 16/17 |
| 0.10 | +0.0002016 | 16/17 |
| 0.30 | +0.0006163 | 16/17 |
| 1.0 | +0.0017453 | 16/17 |

This is post-confirmatory characterization and does not replace `lambda=0.01` as the source-selected primary reverse candidate.

### ChineseEEG reverse multi-seed dose robustness

Lower/intermediate doses were heterogeneous. Only `lambda=1.0` had a positive seed-level mean in all three added trajectories:

- **+7.7478e-05**;
- **+6.2966e-05**;
- **+5.4571e-05**;
- mean of seed means **+6.5005e-05**.

Participant-level intervals crossed zero in each 10-participant seed evaluation. This supports suggestive high-dose consistency, not a separately established ChineseEEG reverse dose-response.

## 3.8 Post-confirmatory bidirectional model-family panel

A frozen common-protocol panel evaluated six multilingual models, three seeds and both source directions, for **36/36 completed units** with no technical omissions.

### ChineseEEG -> SMN4Lang fMRI

- E5-large: 3/3 positive.
- E5-base: 3/3 positive.
- multilingual MPNet: 3/3 positive.
- multilingual MiniLM: 3/3 positive.
- XLM-R base: mixed, 2/3 positive.
- mBERT: 3/3 positive.

### SMN4Lang fMRI -> ZuCo EEG

- E5-large: 3/3 positive.
- E5-base: 3/3 positive.
- multilingual MPNet: mixed / approximately null.
- multilingual MiniLM: 3/3 negative.
- XLM-R base: mixed.
- mBERT: 3/3 negative.

Interpretation:

> Stable bidirectional external transfer is reproduced in both tested E5 variants under the common protocol, but the broader panel is model- and direction-dependent. The experiment does not isolate the causal model property and does not establish E5 uniqueness.

## 3.9 Regional SMN4Lang fMRI characterization

The regional extension was frozen after the primary whole-network result and before regional neural/model outcomes.

### Six predefined language parcels

All six parcels passed the model-blind reliability gate. All had positive neural-guided minus text-only effects in **12/12** participants and survived the frozen six-region max-stat FWER correction.

Mean delta-RSA:

- IFGorb **+0.0005479**;
- IFG **+0.0005720**;
- MFG **+0.0006108**;
- anterior temporal **+0.0007505**;
- posterior temporal **+0.0008521**;
- angular gyrus **+0.0005446**.

### Complete DK68 phenotype

All **68/68** cortical parcel means were positive and all had **12/12** positive participant signs. The largest descriptive means included left superior temporal (**+0.0009019**), right superior temporal (**+0.0008350**) and left bankssts (**+0.0008231**).

The correct interpretation is:

> The displacement is cortex-wide in direction. The predefined language parcels establish within-network effects but do not establish language-network specificity.

No language-versus-control or temporal-versus-nontemporal contrast was prespecified, and regional effect magnitude may partly track measurement reliability.

## 3.10 AHBA mechanistic extension

The prespecified GABAergic, serotonergic and pathway gene-set analyses are null under the frozen participant-level and multiplicity-corrected framework. Exploratory whole-transcriptome and hemispheric/mirroring sensitivities do not revise those nulls. No specific molecular mechanism is established.

## 3.11 Joint interpretation

- **Target reliability:** strongly supported in ChineseEEG, ZuCo and SMN4Lang fMRI; failed for the frozen SMN4Lang MEG representation.
- **Learnability:** supported in ChineseEEG and source-side fMRI calibration.
- **Primary external transfer:** supported by ZuCo EEG and prospective SMN4Lang fMRI.
- **Neural item-correspondence specificity:** supported relative to the matched destroyed-correspondence control.
- **Stimulus robustness:** supported as a post-confirmatory sensitivity over the observed stimulus units.
- **Dose dependence:** strong within E5, with divergent high-dose behavior across ZuCo and fMRI.
- **Source-modality bidirectionality:** supported post-confirmatorily within E5 by fMRI -> ZuCo transfer.
- **Model-family scope:** stable bidirectional transfer reproduced across E5-large and E5-base but not uniformly across other multilingual encoders.
- **Regional selectivity:** not established; the fMRI displacement is cortex-wide in direction across DK68.
- **Generic semantic improvement:** not established.
- **Specific transcriptomic mechanism:** not established.

Raw RSA values across EEG, fMRI and MEG should not be interpreted as a common effect-size scale. Primary participant-level inference generalizes across individuals conditional on each dataset's fixed stimulus set; the two-factor bootstrap is a separate robustness analysis over observed stimulus units.
