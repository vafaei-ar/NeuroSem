# NeuroSem: current project brief for Abbas

**Updated:** 2026-08-26

This is the collaborator-facing summary of what NeuroSem has done, what the results mean, and what remains unresolved. For the complete repository trail, read:

1. [`1_PROJECT_OVERVIEW.md`](1_PROJECT_OVERVIEW.md)
2. [`2_DATASETS_AND_TASKS.md`](2_DATASETS_AND_TASKS.md)
3. [`3_RESULTS_AND_COMPARISONS.md`](3_RESULTS_AND_COMPARISONS.md)
4. [`4_EXPERIMENT_LEDGER.md`](4_EXPERIMENT_LEDGER.md)

## Core idea

We are testing whether the relationships among linguistic items measured in human EEG form a reproducible geometry, whether that geometry contains information beyond ordinary nuisance structure, and whether that neural geometry can provide useful supervision for language models.

The project separates three claims:

1. Does reproducible neural language geometry exist?
2. Can neural-guided training move a language model toward the development EEG geometry?
3. Does that change transfer to independent semantic tasks or independent EEG datasets?

The new ZuCo result materially strengthens claim 3 for a task-matched independent reading dataset, while generic semantic transfer and TMNRED transfer remain null.

## ChineseEEG: Little Prince

Participants silently read Chinese text while EEG and eye tracking were recorded.

The selected EEG representation averages across time separately within each electrode. It does not average across channels. Pairwise distances among these channel vectors form the neural geometry.

For this representation:

- raw leave-one-subject-out reliability was approximately 0.220;
- residual reliability after nuisance control was approximately 0.121.

Across Little Prince runs 01-06, the BERT residual neural-semantic effect was positive in all six runs:

- mean run effect: 0.0085;
- exact run-level sign-flip p = 0.015625;
- common-subject aggregate positive in 8/9 participants.

## BERT neural-guided tuning

Four matched arms were compared: base, text-only, neural-guided, and shuffled-neural.

Run-07 mean partial-Spearman:

| Arm | Seed 1 | Seed 2 |
|---|---:|---:|
| Base | 0.0319 | 0.0319 |
| Text-only | 0.0354 | 0.0341 |
| Neural-guided | **0.0371** | **0.0375** |
| Shuffled-neural | 0.0353 | 0.0338 |

The neural-guided arm improved held-out ChineseEEG neural alignment in two seeds.

## Generic semantics

The neural-specific gain did not robustly transfer to generic semantic similarity benchmarks.

Seed 1 neural - text-only: +0.000089.

Seed 2 neural - text-only: -0.003413.

Thus improving neural alignment is not the same as broadly improving semantic benchmark performance.

## Multilingual E5

An independent multilingual-E5 architecture reproduced the qualitative finding that neural-guided optimization can move a model toward the ChineseEEG neural target.

The E5 program then froze lambda 0.10 neural-guided versus matched lambda 0 text-only as the main external neural-transfer contrast.

## TMNRED: independent Chinese reading

Frozen cohort: 29 participants x 8 sessions, with all 50 sentence items retained per session under the prospective >=80% coverage rule.

Primary EEG reliability:

- temporal mean residual LOO = **0.00724**;
- 95% CI = **[0.00356, 0.01079]**.

Frozen E5 transfer:

- lambda .10 - 0 mean delta = **+0.000020**;
- 95% CI = **[-0.000128, +0.000176]**;
- one-sided p = **0.402**.

Interpretation: the neural geometry itself replicates weakly, but the neural-guided model advantage does not transfer detectably to TMNRED.

## Nature directional-word dataset

The primary NeuroSem condition is covert/inner speech, not natural reading.

The frozen lambda .10 - 0 result was negative/null (mean approximately -0.001786). This is best treated as an out-of-task boundary condition rather than a direct test of the reading hypothesis.

## ZuCo 2.0: independent English reading

This is now the strongest external result.

### Structural freeze

The public dataset contained 18 participants x 7 normal-reading runs. Model-blind QC froze 17 participants with all seven runs structurally valid; YTL was excluded before outcome analysis because three runs failed structural event checks.

Sentence identity and public text mapping were frozen before reliability/model analysis. No model outcome was used to choose the mapping.

### EEG-only reliability

Primary all-channel temporal mean:

- nuisance-residualized LOO reliability = **0.06742**;
- bootstrap 95% CI = **[0.05831, 0.07687]**;
- **17/17 participants positive**;
- exact one-sided sign-flip p = **7.63e-06**.

The predeclared SD and 8-bin sensitivity representations were also positive but weaker.

### Frozen ChineseEEG-to-ZuCo E5 transfer

The sole confirmatory contrast was ChineseEEG-trained multilingual-E5 lambda 0.10 neural-guided minus matched lambda 0 text-only on the frozen ZuCo temporal-mean EEG geometry, with no ZuCo tuning.

Result:

- mean participant delta = **+0.001664**;
- median delta = **+0.001487**;
- **17/17 participants positive**;
- bootstrap 95% CI = **[+0.001229, +0.002145]**;
- exact one-sided sign-flip p = **7.63e-06**.

The first execution attempt failed immediately because of a Python import-path error. The rerun changed only import handling; the scientific protocol was unchanged.

Interpretation: neural-guided training learned from ChineseEEG produced a small but highly consistent improvement in neural alignment in an independent English natural-reading EEG dataset.

## Garnett Dream

ChineseEEG also contains a second and much larger narrative, *Garnett Dream*, recorded in the same participant/acquisition family.

Its role is now precisely defined as **same-participant / new-text validation**, not independent-cohort replication.

A prospective protocol has been frozen in [`garnett_dream_validation_protocol_v1.md`](garnett_dream_validation_protocol_v1.md). The primary representation remains the Little Prince all-channel temporal mean. Outcome-driven changes in representation, windows, sensors, lambda, architecture, participant exclusions, or item selection are prohibited.

## Abbas's proposed AHBA transcriptomic extension

Abbas explicitly proposed adding the **Allen Human Brain Atlas (AHBA)** as a molecular-mechanistic extension to NeuroSem. The idea is to derive spatial gene-expression weights corresponding to the 128-channel ChineseEEG montage, group genes into biologically interpretable systems, and test whether weighting the EEG spatial representation by those molecular maps changes EEG-language-model RSA.

The requested molecular families include:

- GABA receptor families, including alpha, beta, gamma, delta and related inhibitory signaling genes;
- serotonin receptor families and broader serotonergic signaling;
- curated biological pathways;
- cell-type marker sets such as excitatory neurons, inhibitory neurons, astrocytes, oligodendrocytes, OPCs, microglia, endothelial cells, and other literature-supported classes.

The scientifically preferred implementation preserves Abbas's intuition but avoids treating scalp electrodes as literal cortical parcels. The planned mapping is:

**AHBA cortical transcriptomics -> cortical spatial map -> EEG forward/source-sensitivity projection -> 128-channel molecular weighting -> frozen NeuroSem RSA test.**

This replaces a direct nearest-electrode assignment, because EEG channels measure mixtures of cortical generators through volume conduction.

The transcriptomic preparation should be model-blind and outcome-blind. Current planned guardrails are:

- use `abagen`-style AHBA preprocessing with the default-like intensity-based filtering threshold (`ibf_threshold=0.5`);
- freeze donor handling, bilateral mapping, probe/gene preprocessing, and spatial normalization before any NeuroSem outcome is inspected;
- standardize gene maps spatially before averaging genes within a pathway or cell-type set rather than summing raw expression;
- prespecify a limited pathway panel instead of screening thousands of pathways;
- use donor robustness / leave-one-donor-out checks;
- use spatial-autocorrelation-preserving null maps;
- use size-matched random gene-set controls;
- correct for multiplicity across the prespecified molecular families.

The mechanistic question should be phrased as:

> Are cortical locations that contribute more strongly to the established semantic neural geometry preferentially weighted by specific molecular systems?

This AHBA analysis must remain a **separately frozen mechanistic extension**. It must not alter or retroactively optimize the existing ChineseEEG, TMNRED, ZuCo, or Garnett primary analyses.

A dedicated planning document is maintained in [`abbas_ahba_transcriptomic_extension.md`](abbas_ahba_transcriptomic_extension.md).

## Current scientific conclusion

The strongest defensible statement is now:

> Reading-related EEG contains a small but reproducible relational geometry across independent datasets and languages. Neural-guided training can improve alignment to the development EEG target and, in a frozen confirmatory test, produces a small but highly consistent improvement in alignment to independent English natural-reading EEG. The benefit is not universal: generic semantic benchmarks, TMNRED model transfer, and the out-of-task Nature directional test remain null or weak.

This is stronger and more precise than saying that brain supervision broadly improves language-model semantics.

## Publication logic

**Nature Machine Intelligence** remains a plausible aspirational first target because we now have a positive independent cross-language neural-transfer result, but the manuscript must present the null generic semantic and TMNRED findings prominently rather than hide them.

**Nature Neuroscience** remains a strong alternative if the main contribution ultimately centers on reproducible cross-dataset neural reading geometry with neural-guided modeling as a secondary mechanism.

The AHBA extension could add a molecular-mechanistic layer if it survives the frozen spatial-null and donor-robustness tests, but it should not be required to rescue the primary manuscript claim.

## What we should discuss with Abbas next

Abbas's AHBA proposal is now explicitly recorded rather than treated as missing. The immediate discussion points are:

1. confirm the molecular hierarchy to freeze before outcome analysis: GABAergic, serotonergic, cell-type, and a small curated pathway panel;
2. confirm that the electrode mapping should use cortical source/lead-field sensitivity rather than a literal nearest-electrode cortical assignment;
3. decide the preferred human cell-type marker references and pathway database before any weighted RSA is run;
4. agree on donor/bilateral handling and spatial-null strategy for AHBA;
5. decide whether Garnett Dream should be completed before the AHBA outcome test or whether model-blind AHBA preparation can proceed in parallel;
6. decide whether the final manuscript should lead with cross-language reading neural geometry, neural-guided representation learning, or—if AHBA succeeds—a combined computational/molecular mechanism story.
