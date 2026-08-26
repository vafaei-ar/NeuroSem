# NeuroSem: current project brief for Abbas

**Updated:** 2026-08-26

This is the collaborator-facing summary of what NeuroSem has done, what the results mean, and what remains unresolved. For the complete repository trail, read:

1. [`1_PROJECT_OVERVIEW.md`](1_PROJECT_OVERVIEW.md)
2. [`2_DATASETS_AND_TASKS.md`](2_DATASETS_AND_TASKS.md)
3. [`3_RESULTS_AND_COMPARISONS.md`](3_RESULTS_AND_COMPARISONS.md)
4. [`4_EXPERIMENT_LEDGER.md`](4_EXPERIMENT_LEDGER.md)
5. [`5_CURRENT_ROADMAP.md`](5_CURRENT_ROADMAP.md)

## Core idea

We are testing whether the relationships among linguistic items measured in human EEG form a reproducible geometry, whether that geometry contains information beyond ordinary nuisance structure, and whether that neural geometry can provide useful supervision for language models.

The project separates three claims:

1. Does reproducible neural language geometry exist?
2. Can neural-guided training move a language model toward the development EEG geometry?
3. Does that change transfer to independent semantic tasks or independent EEG datasets?

The ZuCo result materially strengthens claim 3 for a task-matched independent reading dataset, while generic semantic transfer and TMNRED transfer remain null. Garnett Dream now strengthens the neural-geometry part of the story by showing same-participant/new-narrative EEG reliability.

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

### EEG-only reliability

Primary all-channel temporal mean:

- nuisance-residualized LOO reliability = **0.06742**;
- bootstrap 95% CI = **[0.05831, 0.07687]**;
- **17/17 participants positive**;
- exact one-sided sign-flip p = **7.63e-06**.

### Frozen ChineseEEG-to-ZuCo E5 transfer

The sole confirmatory contrast was ChineseEEG-trained multilingual-E5 lambda 0.10 neural-guided minus matched lambda 0 text-only on the frozen ZuCo temporal-mean EEG geometry, with no ZuCo tuning.

Result:

- mean participant delta = **+0.001664**;
- median delta = **+0.001487**;
- **17/17 participants positive**;
- bootstrap 95% CI = **[+0.001229, +0.002145]**;
- exact one-sided sign-flip p = **7.63e-06**.

Interpretation: neural-guided training learned from ChineseEEG produced a small but highly consistent improvement in neural alignment in an independent English natural-reading EEG dataset.

## Garnett Dream

Garnett Dream is now substantially advanced and is no longer merely pending setup.

Its role remains **same-participant / new-text validation**, not independent-cohort replication.

### Completed Garnett steps

- model-blind structural audit;
- frozen `ROWS -> ROWE` presentation-row unit;
- structurally valid input materialization;
- prospectively frozen EEG-only reliability;
- exact segmented-XLSX row-text mapping for all 18 chapters/runs.

Primary `row_mean_all` EEG-only reliability:

- mean nuisance-residualized participant LOO reliability = **0.01863**;
- median = **0.01895**;
- **10/10 participants positive**;
- bootstrap 95% CI = **[0.01636, 0.02085]**;
- exact one-sided sign-flip p = **0.0009766**.

The exact mapping rule is:

`CHxx_ROWyyyy -> physical XLSX row yyyy + 1`

because row 1 is the validated `Chinese_text` header in the unique non-display segmented workbook for each chapter/run.

### Next Garnett step

Run exactly one confirmatory model test:

- frozen `row_mean_all` EEG target;
- ChineseEEG-trained multilingual-E5 lambda 0.10 neural-guided vs matched lambda 0 text-only;
- no Garnett tuning or lambda sweep;
- chapter-wise RSA and participant-level Fisher-z aggregation;
- full applicable nuisance family restored from exact text: order, duration, character count, punctuation count, and character-set Jaccard distance.

This result must be locked before any post-confirmatory sensitivity analysis.

## Abbas's proposed AHBA transcriptomic extension

Abbas explicitly proposed adding the **Allen Human Brain Atlas (AHBA)** as a molecular-mechanistic extension to NeuroSem. The idea is to derive spatial gene-expression weights corresponding to the 128-channel ChineseEEG montage, group genes into biologically interpretable systems, and test whether weighting the EEG spatial representation by those molecular maps changes EEG-language-model RSA.

The requested molecular families include:

- GABA receptor families, including alpha, beta, gamma, delta and related inhibitory signaling genes;
- serotonin receptor families and broader serotonergic signaling;
- curated biological pathways;
- cell-type marker sets such as excitatory neurons, inhibitory neurons, astrocytes, oligodendrocytes, OPCs, microglia, endothelial cells, and other literature-supported classes.

The scientifically preferred implementation preserves Abbas's intuition but avoids treating scalp electrodes as literal cortical parcels. The planned mapping is:

**AHBA cortical transcriptomics -> cortical spatial map -> EEG forward/source-sensitivity projection -> 128-channel molecular weighting -> frozen NeuroSem analysis.**

This replaces a direct nearest-electrode assignment, because EEG channels measure mixtures of cortical generators through volume conduction.

### AHBA model-blind preparation

Before any molecular NeuroSem outcome is inspected:

- use `abagen`-style AHBA preprocessing with default-like `ibf_threshold=0.5`;
- freeze probe/gene aggregation and normalization;
- freeze donor handling and the bilateral/hemisphere strategy;
- resolve the exact ChineseEEG 128-channel montage and reference;
- freeze the head model, cortical source space, lead-field/sensitivity metric, and normalization to electrode-level molecular weights;
- build a reproducible 128 x G molecular-sensitivity matrix.

### Biological families to freeze

- GABA-A receptor subunits;
- broader GABAergic machinery, including genes such as `GAD1`, `GAD2`, `SLC6A1`, `SLC32A1` after annotation review;
- serotonin receptor genes;
- broader serotonergic machinery;
- human cell-type marker sets: excitatory neurons, inhibitory neurons, astrocytes, oligodendrocytes, OPCs, microglia, endothelial/vascular cells, and only other justified prespecified classes;
- a small curated pathway panel rather than unrestricted pathway screening.

Genes within sets should be spatially standardized before averaging rather than summed as raw expression.

### Frozen mechanistic analyses

Two analyses can be run if both are frozen before outcome access:

1. **Molecular weighting analysis:** apply each prespecified 128-element molecular map to the frozen EEG channel representation and test change in neural-model RSA.
2. **Spatial contribution analysis:** estimate a stable channel/source contribution map for the already-established semantic effect and test association with molecular maps.

The second analysis likely gives the cleaner biological interpretation.

### Required controls

- donor robustness / leave-one-donor-out;
- spatial-autocorrelation-preserving null maps;
- gene-set-size-matched random gene sets;
- multiplicity correction;
- robustness to the frozen bilateral strategy;
- broad cortical-gradient/nonspecific spatial controls where feasible.

AHBA is a population-level spatial prior from six postmortem donors. It is not molecular measurement from the ChineseEEG participants, and positive associations will not imply causal receptor involvement.

## Current scientific conclusion

The strongest defensible statement is now:

> Reading-related EEG contains a small but reproducible relational geometry across independent datasets and languages. Neural-guided training can improve alignment to the development EEG target and, in a frozen confirmatory test, produces a small but highly consistent improvement in alignment to independent English natural-reading EEG. Garnett Dream further shows positive new-narrative neural-geometry generalization within the original participant/acquisition family. The benefit is not universal: generic semantic benchmarks, TMNRED model transfer, and the out-of-task Nature directional test remain null or weak.

## Current joint plan

The project now runs in three coordinated tracks:

1. **Finish Garnett:** run the single frozen lambda .10 vs 0 model-transfer test and lock the result.
2. **Start Abbas AHBA in parallel:** do model-blind transcriptomic processing, source-sensitivity projection, molecular-family freezing, and null-design freezing before any molecular outcome.
3. **Build the manuscript in parallel:** maintain the cross-dataset evidence table, figures, Results, Methods, and explicit null/boundary-condition narrative.

The AHBA analysis is a **separately frozen mechanistic extension**. It must not alter or retroactively optimize ChineseEEG, TMNRED, ZuCo, Nature, or Garnett primary analyses.

## Publication logic

**Nature Machine Intelligence** remains the aspirational first target if the final evidence supports a machine-learning contribution centered on transferable neural alignment and, potentially, a robust mechanistic layer.

**Nature Neuroscience** remains the main alternative if the strongest contribution ultimately centers on reproducible cross-dataset neural reading geometry and molecular mechanism.

The AHBA extension could strengthen the mechanistic story if it survives the frozen spatial-null and donor-robustness framework, but it is not required to rescue the primary manuscript claim.
