# 29. Regional SMN4Lang fMRI transfer result v1

**Status:** completed post-confirmatory regional fMRI reliability and model-transfer stages under the frozen protocol in `26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md`. The molecular AHBA stage remains pending.

**Result date:** 2026-09-03

## Evidential status

This extension is post-confirmatory. It does not change the prospective status of the original whole-language-network SMN4Lang result and does not revise any previously completed AHBA result.

The scientific protocol was frozen before any regional model-alignment outcome at commit `92207415e223cc1aacdb2c9ffad44d148d64994c`. Two pre-outcome technical amendments were subsequently required to make the frozen atlases executable without inspecting regional model outcomes:

- `27_NMI_REGIONAL_FMRI_ATLAS_PREFLIGHT_AMENDMENT_V1.md`, resolving the EvLab label-source issue;
- `28_NMI_REGIONAL_FMRI_DK_RESAMPLING_AMENDMENT_V1.md`, freezing deterministic nearest-neighbor resampling of the discrete DK label atlas into the fixed SMN4Lang grid after the original exact-grid gate failed.

No model or regional transfer outcome was used to choose either amendment.

## Stage 0 atlas preflight

The final outcome-blind atlas gate completed in RunRelay job `K6T3P9M4` at NeuroSem commit `fa9db0c6f96468f4b10c90b1efeb71a6d354429a`.

The final preflight established:

- exact EvLab SN220 parcel-grid compatibility with SMN4Lang;
- all six frozen left-hemisphere language parcels present and above the 100-voxel structural threshold;
- deterministic nearest-neighbor DK resampling into the SMN4Lang grid;
- all 68 cortical DK parcel IDs preserved after resampling;
- exact DK ID/name/hemisphere agreement with the frozen AHBA expression metadata;
- all 34 left-hemisphere DK parcels and all 68 bilateral DK parcels above the frozen structural atlas threshold;
- no regional BOLD or model outcomes inspected during the preflight.

The successful preflight summary SHA256 is `ec2ad390faadb846f287b7af5fcf4d21e0a5d77b5b56108dddba5cdba036356a`.

## Stage 1 model-blind regional reliability

RunRelay job `R7K3M8Q5` completed at exact NeuroSem commit `27db03936eaf315cbe3ed4c1dc9cb96d8a4f1576`.

The analysis used all 12 participants and all 60 stories, with the unchanged SMN4Lang nuisance family and the frozen minimum of 100 finite nonconstant voxels per required run. It did not import or load language-model representations.

All predefined regions passed the reliability gate:

- language parcels structurally available: **6/6**;
- language parcels passing reliability gate: **6/6**;
- DK parcels structurally available: **68/68**;
- DK parcels passing reliability gate: **68/68**.

Language-region mean residual LOO reliability:

| Region | Mean reliability | 95% participant-bootstrap CI |
|---|---:|---:|
| IFG | 0.47705 | [0.45524, 0.49728] |
| IFGorb | 0.49355 | [0.47846, 0.50950] |
| MFG | 0.49552 | [0.48042, 0.50960] |
| AntTemp | **0.64026** | [0.62553, 0.65515] |
| PostTemp | **0.60651** | [0.58499, 0.62896] |
| AngG | 0.46606 | [0.44789, 0.48745] |

All six language regions were positive in 12/12 participants and had exact two-sided sign-flip `p = 0.00048828125`.

The DK map was broadly reliable. Descriptively, the highest mean reliability included right insula (0.70888), left insula (0.69057), right superior temporal cortex (0.66542), left fusiform (0.65682), left superior temporal cortex (0.65636), and right fusiform (0.65166). The reliability map is an interpretation gate, not a model-correspondence result and was not used for ROI selection.

## Stage 2 regional multilingual-E5 transfer

RunRelay job `T5N8C3V7` completed at exact NeuroSem commit `50663663115d1f5f648445ee940fd64cdff5dc07` with exit 0 and six declared safe artifacts.

Frozen contrast:

`ChineseEEG-trained multilingual-E5 lambda=0.10 genuine-neural - lambda=0 text-only`

The analysis retained the original SMN4Lang story-level nuisance-residualized Spearman RSA and Fisher-z participant aggregation. No model retraining, target-side model selection, lambda search, layer search, pooling search, checkpoint search, or outcome-based ROI selection occurred.

### Six frozen language parcels

| Region | Text-only RSA | Neural-guided RSA | Mean delta-RSA | Participant-bootstrap 95% CI | Positive participants | Exact two-sided p | Six-region max-stat FWER p |
|---|---:|---:|---:|---:|---:|---:|---:|
| IFG | 0.102856 | 0.103428 | +0.000572 | [+0.000469, +0.000670] | 12/12 | 0.000488 | 0.020996 |
| IFGorb | 0.102308 | 0.102856 | +0.000548 | [+0.000485, +0.000610] | 12/12 | 0.000488 | 0.027832 |
| MFG | 0.101381 | 0.101992 | +0.000611 | [+0.000506, +0.000716] | 12/12 | 0.000488 | 0.010742 |
| AntTemp | **0.114362** | **0.115112** | **+0.000751** | [+0.000675, +0.000822] | 12/12 | 0.000488 | **0.000977** |
| PostTemp | **0.113118** | **0.113970** | **+0.000852** | [+0.000748, +0.000960] | 12/12 | 0.000488 | **0.000488** |
| AngG | 0.102779 | 0.103323 | +0.000545 | [+0.000473, +0.000624] | 12/12 | 0.000488 | 0.029297 |

Every predefined language region therefore showed a positive participant-level neural-guided improvement and every region survived the frozen dependence-aware six-region max-stat FWER correction.

The strongest regional improvement was in posterior temporal cortex, followed by anterior temporal cortex. The baseline text-only model-brain correspondence was also highest in the two temporal language parcels, but baseline RSA and delta-RSA remain distinct estimands.

Frozen interpretation:

> The neural-guided representational improvement is distributed across the independently defined language network, with a graded concentration in temporal language cortex.

This is not evidence for a unique causal locus.

### Participant-by-story robustness

The prespecified 10,000-replicate participant x story bootstrap used seed `20260902`. For every language parcel, the bootstrap fraction with mean delta greater than zero was **1.0**.

Two-factor bootstrap 95% intervals:

- IFG: [+0.000384, +0.000768];
- IFGorb: [+0.000390, +0.000714];
- MFG: [+0.000433, +0.000796];
- AntTemp: [+0.000555, +0.000951];
- PostTemp: [+0.000629, +0.001087];
- AngG: [+0.000381, +0.000726].

These are sensitivities over the 12 analyzed participants and 60 analyzed stories, not unrestricted population inference over arbitrary language stimuli.

### DK68 spatial phenotype

The complete DK68 map was retained without significance-based filtering. Descriptively:

- all 68 parcels had positive mean delta-RSA;
- every parcel had positive delta-RSA in 12/12 participants;
- largest mean deltas included left superior temporal (+0.000902), right superior temporal (+0.000835), and left banks STS (+0.000823);
- the smallest mean delta was still positive, left frontal pole (+0.000371).

The DK map is a continuous spatial characterization phenotype. These parcel-wise exact sign-flip values are not used as a 68-region discovery screen and no parcel is selected from them for the molecular stage.

Regional reliability and regional transfer are related but not identical. For example, right insula had the highest model-blind reliability (0.70888) but a more moderate delta-RSA (+0.000633), whereas left superior temporal cortex had lower reliability (0.65636) but the largest DK delta-RSA (+0.000902). The temporal transfer concentration therefore cannot be reduced to reliability alone.

## Authoritative artifacts

RunRelay/R2 artifacts for `T5N8C3V7`:

- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/summary.json`, SHA256 `a9236aed6f7c2c90c0050465eb10ca6124c6c397066c744688fb01f68df9e7af`;
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/region_summary.csv`, SHA256 `e13c95c8c20149e64c67ea182d5874909ed2295c983fc58c1e08b68c9b3bcb9b`;
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/participant_results.csv`, SHA256 `cb7fe65edeac4016e418102ef8d850016cbc9d71035001d9b54c1f5258ebaa14`;
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/story_results.csv`, SHA256 `5b33b6846e3ba2e45eff1bf5333648c142fd252c1ba9314a0de8f42958c396e4`;
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/language_twofactor_bootstrap.csv`, SHA256 `db4e8506033a7b6856af1fde9de0d0e2cfe9994b708f2c243c8efce91e2be1e1`;
- `outputs/smn4lang_regional_fmri_e5_transfer_v1/latest/dk68_participant_delta_matrix.csv`, SHA256 `14a1dd051a2f2f54be482e290b9ea5bb0c390507e9acc8ac5299d9dac8f9771b`.

## Decision and next stage

Stages 0-2 are complete. The frozen regional result supports a network-distributed transfer effect with graded temporal concentration.

The next authorized analysis is Stage 3 of `26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md`: apply the complete, unthresholded participant-level DK delta-RSA phenotype to the already-frozen AHBA expression and gene-set resources. The primary molecular domain remains left DK34, with the frozen spatial-spin, size-matched random-gene-set, donor-robustness and mirroring-sensitivity rules.

The new molecular analysis is a distinct post-confirmatory phenotype and cannot revise or rescue the previous NeuroSem AHBA nulls. No new gene sets, parcel selection, model tuning, or post-hoc pathway fishing is permitted.