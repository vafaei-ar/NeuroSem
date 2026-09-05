# 1. NeuroSem Project Overview

**Last updated:** 2026-09-04

NeuroSem asks whether reproducible human neural representational geometry can constrain language-model learning in a way that transfers to independent neural measurements.

## Current scientific conclusion

The strongest defensible conclusion is now:

> Brain-derived relational supervision can transfer to independent neural representational systems, but source fit does not guarantee a target-independent transfer magnitude or sign. Under the tested protocols, transfer depends on relational-loss dose, external target and model backbone.

The historical primary chain remains unchanged:

1. ChineseEEG Little Prince establishes a reproducible development neural geometry and model learnability.
2. The frozen multilingual-E5-large `lambda=0.10` versus `lambda=0` contrast transfers positively to independent ZuCo English-reading EEG in **17/17** participants.
3. The same frozen contrast transfers prospectively to SMN4Lang fMRI in **12/12** participants after a model-blind reliability gate.

Later analyses are post-confirmatory and define specificity, dose behavior, directionality, model-family scope, stimulus robustness, representational perturbation and regional distribution. They do not revise the primary evidential status.

## Empirical stages

The project separates five questions that must not be conflated:

1. **Target reliability:** is the designated neural geometry reproducible?
2. **Learnability:** can training move the model toward the source geometry?
3. **Primary external transfer:** does a frozen learned change survive in independent neural targets?
4. **Scope:** how does transfer vary with dose, target, direction and model backbone?
5. **Mechanistic interpretation:** do regional or transcriptomic analyses identify a more specific biological mechanism?

The first four are supported to different degrees. A specific transcriptomic mechanism is not established.

## Primary locked evidence

- **ChineseEEG Little Prince:** raw LOO reliability approximately **0.220**, nuisance-residualized LOO approximately **0.121**, plus sealed run-07 neural-guided learnability.
- **ZuCo 2.0 normal reading:** target reliability **0.06742**, 95% CI **[0.05831,0.07687]**, **17/17** positive. Frozen E5 transfer `lambda=0.10 - lambda=0` = **+0.0016637**, 95% CI **[+0.0012294,+0.0021452]**, **17/17** positive, exact one-sided sign-flip **p = 7.63e-06**.
- **SMN4Lang fMRI:** target reliability **0.65327**, 95% CI **[0.63945,0.66843]**, **12/12** positive. Frozen E5 transfer = **+0.00085250**, 95% CI **[+0.00078966,+0.00091398]**, **12/12** positive, exact one-sided sign-flip **p = 0.00024414**.

## Post-confirmatory specificity and robustness

Across three fixed E5 seeds, the genuine-neural minus shuffled-neural contrast was positive on both external targets. ZuCo seed-level mean deltas were approximately **+0.001291**, **+0.001897** and **+0.000677**; SMN4Lang fMRI values were approximately **+0.000676**, **+0.000871** and **+0.000410**. The control supports specificity to preserved neural item correspondence relative to the matched destroyed-correspondence target, not uniqueness relative to every possible structured non-neural objective.

A participant x stimulus bootstrap remained positive in all 10,000 replicates for both primary external targets. This is a sensitivity over the observed participants and stimulus units, not unrestricted random-effects inference to arbitrary linguistic stimuli.

## Dose and target dependence

The complete already-trained ChineseEEG E5 grid was evaluated after the primary external tests under a frozen post-confirmatory protocol.

- **ZuCo delta-RSA:** `+0.000211`, `+0.000477`, `+0.001664`, `+0.008739`, `+0.027599` for `lambda=0.01,0.03,0.10,0.30,1.0`.
- **SMN4Lang fMRI delta-RSA:** `+0.000107`, `+0.000283`, `+0.000852`, `+0.003038`, `-0.000991` over the same doses.

Thus both targets rise through `lambda=0.30`, but at `lambda=1.0` ZuCo continues to improve while fMRI reverses. The matched generic STS decrement also grows with dose, reaching approximately **-0.03453** at `lambda=1.0`.

At `lambda=0.10`, the E5 perturbation remains small: cosine **0.99839**, RDM Pearson **0.99792**, RDM Spearman **0.99745**, CKA **0.99932**, k=10 Jaccard **0.9276**. At `lambda=1.0`, restructuring is materially larger: cosine **0.94221**, RDM Pearson **0.79653**, RDM Spearman **0.77887**, CKA **0.93766**, k=10 Jaccard **0.5794**.

## Reverse-direction evidence

The frozen fMRI-source calibration selected `lambda=0.01` before external EEG evaluation. The primary reverse ZuCo test was positive but small: mean delta-RSA approximately **+0.00001671**, **14/17** participants positive, exact one-sided **p = 0.0001068**. Three additional prespecified seeds reproduced positive means. Larger reverse doses are subsequent characterization and do not replace the source-selected primary reverse test.

## Model-family scope

The six-model x three-seed x two-direction panel completed all **36/36** planned units under one common `lambda=0.10` protocol.

- **E5-large:** 3/3 positive in both directions.
- **E5-base:** 3/3 positive in both directions.
- **multilingual MPNet:** 3/3 positive EEG -> fMRI; mixed/approximately null reverse.
- **multilingual MiniLM:** 3/3 positive EEG -> fMRI; 3/3 negative reverse.
- **XLM-R base:** heterogeneous in both directions.
- **mBERT:** 3/3 positive EEG -> fMRI; 3/3 negative reverse.

The result establishes model- and direction-dependent portability under the common protocol. It does not isolate an architecture mechanism and does not establish E5 uniqueness.

## Regional fMRI interpretation

All six predefined left-hemisphere language parcels passed the model-blind reliability gate and showed positive neural-guided minus text-only effects in **12/12** participants, surviving the frozen six-region max-stat FWER correction.

However, the complete bilateral DK68 phenotype also had positive mean delta-RSA in **all 68 parcels**, with **12/12** positive participants in every parcel. Therefore the regional result is cortex-wide in direction and **must not be described as language-network specificity**. Superior temporal regions are among the larger descriptive effects, but no temporal-versus-nontemporal or language-versus-control contrast was prespecified.

## Boundaries and mechanistic nulls

- **TMNRED:** weakly reproducible target; transfer null.
- **Garnett Dream:** modest reliability; transfer inconclusive.
- **Directional inner speech:** out-of-task negative boundary.
- **SMN4Lang MEG:** frozen target failed model-blind reliability; no model evaluation was performed.
- **Generic semantic benchmark:** no stable neural-specific advantage.
- **AHBA:** prespecified molecular gene/pathway analyses are null; exploratory transcriptomic sensitivities do not establish a mechanism.

## Publication state

The project is **evidence-locked and in final publication production**. The current author-review Word master is `NeuroSem_Nature_Manuscript_v1.11_NMI_native_vector_figures.docx`, with `NeuroSem_NMI_Supplementary_Technical_Tables_v1.11_NMI_native_vector_figures.docx` as Supplementary Information. Exact fingerprints are recorded in `paper/CURRENT_MANUSCRIPT.md`.

No additional outcome-bearing analysis is required for the current manuscript unless a reviewer/editor asks a clearly specified question.

## Stopping rules

- Preserve the original prospective chain unchanged.
- Do not promote target-observed doses to prospective status.
- Do not rescue non-E5 models with post-outcome lambda/layer/pooling searches.
- Do not reopen ZuCo or SMN4Lang target-side choices.
- Do not rescue TMNRED or Garnett.
- Do not evaluate models on failed SMN4Lang MEG representations.
- Do not interpret the regional result as language-network specificity.
- Do not expand AHBA searches for significance or add post-outcome gene sets/pathways.
- Preserve all nulls, negative effects, heterogeneous seeds and failed reliability gates.

## Read next

- [`3_RESULTS_AND_COMPARISONS.md`](3_RESULTS_AND_COMPARISONS.md)
- [`5_CURRENT_ROADMAP.md`](5_CURRENT_ROADMAP.md)
- [`4_EXPERIMENT_LEDGER.md`](4_EXPERIMENT_LEDGER.md)
- [`../paper/CURRENT_MANUSCRIPT.md`](../paper/CURRENT_MANUSCRIPT.md)
