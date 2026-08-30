# NMI bidirectional model-family panel: completed results

**Status:** completed post-confirmatory explanatory analysis

**RunRelay job:** `V8K3M6R2` (`Map bidirectional model families`)

**Exact NeuroSem execution commit:** `3aa4a6259f97fe72b3ae85f6c6c91c53a7eae219`

**Runtime:** 04:22:54, exit 0, 3 declared artifacts

**Canonical Drive job folder:** https://drive.google.com/drive/folders/1UKrlv3XrO9Y6VFjFh8HFZRn7W9E3Q1uk

**Protocol:** `docs/22_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_V1.md`

## Purpose and evidential status

This analysis was designed after the E5-positive and mBERT-boundary results were already known. It is therefore post-confirmatory and explanatory, not a prospective confirmation of model-family effects. The fixed question was whether stable externally transferable neural relational supervision is associated with a broader model class or is concentrated within a specific multilingual embedding family.

The run completed all **36 planned units**: 6 models x 3 optimization seeds x 2 source directions. There were **no technical model failures and no omitted outcomes**.

## Frozen common protocol

Every model was evaluated under the same common adaptation procedure rather than model-specific rescue tuning:

- final hidden state;
- attention-mask mean pooling;
- L2 normalization;
- cosine-distance relational geometry;
- E5 inputs use `query: `; other models use no task prefix;
- LoRA on attention query/value projections, r=8, alpha=16, dropout=.05;
- AdamW, learning rate 2e-4, weight decay .01;
- 5 fixed epochs/source schedule;
- symmetric dropout-view InfoNCE text objective, temperature .05;
- neural objective `1 - corr(z(model pairwise cosine distances), frozen neural relational target)`;
- neural weight lambda=.10 for every model and both directions;
- matched lambda=0 text-only arm for every model, seed and source direction;
- no early stopping, checkpoint selection, lambda search, layer search, pooling search or target-side rescue.

Seeds were fixed as `20260829`, `20260830`, and `20260831`.

## Frozen model revisions

| Key | Model | Descriptive class | Exact revision |
|---|---|---|---|
| `e5_large` | `intfloat/multilingual-e5-large` | E5 retrieval/sentence embedding | `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3` |
| `e5_base` | `intfloat/multilingual-e5-base` | E5 retrieval/sentence embedding | `d128750597153bb5987e10b1c3493a34e5a4502a` |
| `multilingual_mpnet` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | other multilingual sentence embedding | `4328cf26390c98c5e3c738b4460a05b95f4911f5` |
| `multilingual_minilm` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | other multilingual sentence embedding | `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` |
| `xlmr_base` | `FacebookAI/xlm-roberta-base` | generic multilingual MLM encoder | `e73636d4f797dec63c3081bb6ed5c7b0bb3f2089` |
| `mbert` | `google-bert/bert-base-multilingual-cased` | generic multilingual MLM encoder | `3f076fdb1ab68d5b2880cb87a0886f315b8146f8` |

## Direction A: ChineseEEG -> model -> SMN4Lang fMRI

The source was the frozen ChineseEEG relational target. The external target was the already-frozen SMN4Lang LanA fMRI pipeline with 12 participants and 60 stories. Values below are neural-guided lambda=.10 minus matched lambda=0 participant-level RSA.

| Model | Seed | Source validation delta | External mean delta | Positive participants | 95% bootstrap CI | Exact one-sided p |
|---|---:|---:|---:|---:|---:|---:|
| E5-large | 20260829 | +.012581 | +.00113141 | 12/12 | [.001052,.001207] | .000244 |
| E5-large | 20260830 | +.020211 | +.00132740 | 12/12 | [.001207,.001440] | .000244 |
| E5-large | 20260831 | +.011894 | +.00087655 | 12/12 | [.000799,.000947] | .000244 |
| E5-base | 20260829 | +.006338 | +.00027651 | 12/12 | [.000249,.000308] | .000244 |
| E5-base | 20260830 | +.006157 | +.00026798 | 12/12 | [.000238,.000300] | .000244 |
| E5-base | 20260831 | +.005505 | +.00026959 | 12/12 | [.000241,.000302] | .000244 |
| multilingual MPNet | 20260829 | +.015001 | +.00214326 | 12/12 | [.002043,.002246] | .000244 |
| multilingual MPNet | 20260830 | +.009917 | +.00079457 | 12/12 | [.000722,.000868] | .000244 |
| multilingual MPNet | 20260831 | +.011239 | +.00064201 | 12/12 | [.000551,.000750] | .000244 |
| multilingual MiniLM | 20260829 | +.008959 | +.00072801 | 12/12 | [.000664,.000803] | .000244 |
| multilingual MiniLM | 20260830 | +.008428 | +.00074096 | 12/12 | [.000678,.000808] | .000244 |
| multilingual MiniLM | 20260831 | +.005563 | +.00045821 | 12/12 | [.000398,.000529] | .000244 |
| XLM-R base | 20260829 | -.005937 | -.00013756 | 5/12 | [-.000850,.000606] | .636719 |
| XLM-R base | 20260830 | -.004356 | +.00077728 | 10/12 | [.000298,.001261] | .006104 |
| XLM-R base | 20260831 | -.016665 | +.00092935 | 11/12 | [.000610,.001236] | .000488 |
| mBERT | 20260829 | +.021976 | +.00016183 | 10/12 | [.000021,.000279] | .022217 |
| mBERT | 20260830 | +.021019 | +.00029407 | 11/12 | [.000149,.000422] | .002197 |
| mBERT | 20260831 | +.017725 | +.00029042 | 11/12 | [.000186,.000371] | .000488 |

Seed-mean summaries:

| Model | Mean of seed-level external deltas | All 3 seed means positive? |
|---|---:|---|
| E5-large | +.00111179 | yes |
| E5-base | +.00027136 | yes |
| multilingual MPNet | +.00119328 | yes |
| multilingual MiniLM | +.00064239 | yes |
| XLM-R base | +.00052302 | no |
| mBERT | +.00024877 | yes |

**Interpretation:** ChineseEEG-derived relational supervision transfers to SMN4Lang fMRI across multiple multilingual model classes under the common protocol. The effect is especially seed-stable in both E5 models and both sentence-transformer models. Generic MLM encoders are less uniform: mBERT is positive in all three seeds but smaller, whereas XLM-R is seed-heterogeneous and its source diagnostic is negative in all three seeds.

## Direction B: SMN4Lang fMRI -> model -> ZuCo EEG

The source was the frozen SMN4Lang group fMRI relational target. The external target was frozen ZuCo 2.0 normal-reading EEG, 17 participants across seven runs. Values below are fMRI-guided lambda=.10 minus matched lambda=0 participant-level RSA.

| Model | Seed | Source validation delta | External mean delta | Positive participants | 95% bootstrap CI | Exact one-sided p |
|---|---:|---:|---:|---:|---:|---:|
| E5-large | 20260829 | +.000475 | +.00023969 | 16/17 | [.000180,.000301] | .000015 |
| E5-large | 20260830 | +.000451 | +.00014816 | 16/17 | [.000106,.000189] | .000038 |
| E5-large | 20260831 | +.000485 | +.00022158 | 16/17 | [.000164,.000278] | .000015 |
| E5-base | 20260829 | +.000185 | +.00003517 | 14/17 | [.000012,.000056] | .004311 |
| E5-base | 20260830 | +.000154 | +.00002886 | 15/17 | [.000015,.000042] | .000572 |
| E5-base | 20260831 | +.000168 | +.00003702 | 15/17 | [.000024,.000050] | .000084 |
| multilingual MPNet | 20260829 | +.001358 | +.00000326 | 9/17 | [-.000021,.000027] | .398697 |
| multilingual MPNet | 20260830 | +.001452 | -.00000925 | 8/17 | [-.000048,.000026] | .684669 |
| multilingual MPNet | 20260831 | +.001319 | +.00000232 | 8/17 | [-.000027,.000033] | .444046 |
| multilingual MiniLM | 20260829 | +.001041 | -.00002610 | 6/17 | [-.000066,.000016] | .880989 |
| multilingual MiniLM | 20260830 | +.001104 | -.00004660 | 5/17 | [-.000089,-.000002] | .970978 |
| multilingual MiniLM | 20260831 | +.000933 | -.00003950 | 4/17 | [-.000072,-.000003] | .975029 |
| XLM-R base | 20260829 | +.000926 | -.00021841 | 4/17 | [-.000398,-.000028] | .979332 |
| XLM-R base | 20260830 | +.000897 | +.00027608 | 13/17 | [.000122,.000435] | .001976 |
| XLM-R base | 20260831 | +.000736 | +.00003558 | 11/17 | [-.000017,.000089] | .112633 |
| mBERT | 20260829 | -.000085 | -.00096966 | 1/17 | [-.001282,-.000658] | .999962 |
| mBERT | 20260830 | +.001630 | -.00018040 | 2/17 | [-.000246,-.000112] | .999870 |
| mBERT | 20260831 | +.001329 | -.00017300 | 0/17 | [-.000213,-.000135] | 1.000000 |

Seed-mean summaries:

| Model | Mean of seed-level external deltas | All 3 seed means positive? |
|---|---:|---|
| E5-large | +.00020314 | yes |
| E5-base | +.00003368 | yes |
| multilingual MPNet | -.00000122 | no |
| multilingual MiniLM | -.00003740 | no, all three negative |
| XLM-R base | +.00003108 | no |
| mBERT | -.00044102 | no, all three negative |

**Interpretation:** stable reverse-direction fMRI-to-EEG transfer is selective in this panel. Both E5-large and E5-base reproduce positive transfer in all three optimization seeds. MPNet is approximately centered on zero, MiniLM is negative in all three seeds, XLM-R is highly seed-dependent, and mBERT is negative in all three seeds despite positive source diagnostics in two of the three seeds.

## Descriptive family summaries

These averages contain only two fixed models per class and are not population-level inference over arbitrary model families.

| Model class | EEG -> fMRI mean across member model seed-means | fMRI -> EEG mean across member model seed-means |
|---|---:|---:|
| E5 retrieval/sentence embedding | +.00069157 | +.00011841 |
| Other multilingual sentence embedding | +.00091783 | -.00001931 |
| Generic multilingual MLM encoder | +.00038590 | -.00020497 |

The family summaries reinforce the direction-specific pattern: EEG-derived constraints are broadly portable across several multilingual encoders, whereas positive reverse fMRI-to-EEG transfer is concentrated in the two tested E5 variants.

## Relationship to the earlier mBERT strict-portability experiment

Do not summarize the historical evidence as simply “BERT does not work.” The earlier mBERT test used a different training context, including an MLM-based text objective and a different frozen model revision, and produced heterogeneous external effects. The present panel intentionally imposed a shared InfoNCE-based sentence-geometry adaptation protocol across all six models. Under this common protocol mBERT shows small but seed-stable EEG-to-fMRI transfer, while remaining strongly negative for fMRI-to-EEG.

Therefore the combined evidence supports a more precise conclusion:

> Generic MLM encoders do not show the stable bidirectional portability observed for multilingual E5 under the tested protocols.

The difference between the two mBERT experiments is itself evidence that the training objective/context can interact with architecture; it should not be represented as a direct contradiction.

## Main scientific conclusion from this panel

A defensible manuscript-level synthesis is:

> Neural relational supervision is architecture- and direction-dependent. EEG-derived constraints can produce externally transferable perturbations across several multilingual encoders. In contrast, robust reverse transfer from fMRI to EEG was selective in the tested panel: both multilingual E5 variants reproduced the effect across all optimization seeds, whereas MPNet, MiniLM, XLM-R and mBERT did not. Bidirectional external neural transfer therefore appears to be a reproducible property of the tested multilingual E5 family under the common protocol, rather than an idiosyncrasy of a single checkpoint or a universal property of multilingual encoders.

This is an explanatory post-confirmatory conclusion. It does not establish that E5 is uniquely capable in the population of all language models, nor that non-E5 models could never transfer under model-specific optimization.

## Artifact provenance

Canonical safe artifacts from `V8K3M6R2`:

- `outputs/nmi_bidirectional_model_family_panel_v1/latest/summary.json`
- `outputs/nmi_bidirectional_model_family_panel_v1/latest/model_seed_direction_results.csv`
- `outputs/nmi_bidirectional_model_family_panel_v1/latest/resolved_models.json`

No model, seed, direction or target was removed after results were observed.
