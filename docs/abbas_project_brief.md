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

## Current scientific conclusion

The strongest defensible statement is now:

> Reading-related EEG contains a small but reproducible relational geometry across independent datasets and languages. Neural-guided training can improve alignment to the development EEG target and, in a frozen confirmatory test, produces a small but highly consistent improvement in alignment to independent English natural-reading EEG. The benefit is not universal: generic semantic benchmarks, TMNRED model transfer, and the out-of-task Nature directional test remain null or weak.

This is stronger and more precise than saying that brain supervision broadly improves language-model semantics.

## Publication logic

**Nature Machine Intelligence** remains a plausible aspirational first target because we now have a positive independent cross-language neural-transfer result, but the manuscript must present the null generic semantic and TMNRED findings prominently rather than hide them.

**Nature Neuroscience** remains a strong alternative if the main contribution ultimately centers on reproducible cross-dataset neural reading geometry with neural-guided modeling as a secondary mechanism.

## What we should discuss with Abbas next

The repository currently preserves this brief **for Abbas**, but it does not preserve a verbatim list of Abbas's own comments or proposals. We therefore should not attribute specific ideas to him unless they are recorded elsewhere or confirmed directly.

The most useful discussion points for Abbas now are:

1. whether the positive ZuCo transfer is strong enough, together with the null TMNRED/generic-semantic results, to support the NMI framing;
2. whether Garnett Dream should be the final major validation before manuscript lock;
3. whether an additional experiment would add a genuinely orthogonal claim, rather than merely increasing the number of datasets;
4. what mechanistic interpretation can explain positive transfer to ZuCo but null transfer to TMNRED;
5. whether the manuscript should lead with **cross-language reading neural geometry** or with **neural-guided representation learning**.

Until Abbas's actual comments are recorded, these should be treated as questions to bring to him, not as ideas already attributed to him.
