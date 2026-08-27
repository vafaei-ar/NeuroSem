# NeuroSem figure and table plan

**Status:** working manuscript plan, 2026-08-27

The goal is to present the locked evidence hierarchy without hiding null results. Main figures should emphasize the core neural-geometry and transfer story. AHBA should be a mechanistic extension with explicit confirmatory/exploratory labels.

## Main Figure 1. NeuroSem concept and analysis framework

Panels:

A. Scientific question: text items -> EEG relational geometry -> model geometry -> neural-guided training -> external validation.

B. Primary EEG representation: average each item epoch across time within channel, retain the channel vector, standardize features, construct correlation-distance RDM.

C. Residual RSA: separately rank-transform neural/model RDM edges and nuisance RDMs, residualize, then correlate residuals.

D. Validation hierarchy: ChineseEEG Little Prince discovery; TMNRED independent Chinese reading; ZuCo independent English reading; Garnett same-participant/new-text; Nature out-of-task boundary condition.

Do not include AHBA in the same visual causal chain as model training. Show it as a later mechanistic branch.

## Main Figure 2. Reproducible reading-related neural geometry

Suggested plot: participant-level residual LOO reliability distributions or compact forest/interval plot across datasets.

Include:

- ChineseEEG Little Prince primary reliability;
- TMNRED primary `row_mean_all`: mean 0.00724, 95% CI [0.00356, 0.01079];
- ZuCo primary `row_mean_all`: mean 0.06742, 95% CI [0.05831, 0.07687], 17/17 positive;
- Garnett primary `row_mean_all`: mean 0.01863, 95% CI [0.01636, 0.02085], 10/10 positive.

A secondary panel can show sensitivity representations, but the primary temporal mean must remain visually privileged.

## Main Figure 3. Neural-guided model alignment and external transfer

Panel A. ChineseEEG sealed run-07 BERT result, four arms and two seeds.

Panel B. External transfer effects for frozen E5 lambda 0.10 minus text-only lambda 0:

- TMNRED: +0.000020, CI crosses zero;
- ZuCo: +0.001664, 95% CI [+0.001229, +0.002145], 17/17 positive;
- Garnett: +0.0003266, 95% CI [-0.0001218, +0.0007560], one-sided p=0.1016;
- Nature directional: approximately -0.001786, out-of-task null.

Panel C. Generic semantic benchmark boundary: neural-specific advantage is not stable across seeds.

Use the same effect direction convention across datasets.

## Main Figure 4. AHBA mechanistic pipeline and frozen molecular nulls

Panel A. Schematic:

AHBA DK cortical expression -> mapped fsaverage ico5 cortex -> EEG forward/source sensitivity -> 128-channel molecular map and deterministic DK68 semantic phenotype.

Important label: "population postmortem spatial prior, not participant molecular data."

Panel B. Forest plot of the seven prespecified primary GABA/serotonin/pathway associations with sign-flip p/q and random-set nulls.

All should be shown, not only the largest effects.

Panel C. Control cell-type panels, visually separated from the primary family.

The panel title should explicitly say that prespecified molecular systems were not supported.

## Main Figure 5. Exploratory transcriptomics and published language panels

Panel A. Whole-transcriptome PLS1: observed score-phenotype r=0.457, R2=0.209, with the 5,000-spin null distribution and two-sided p=0.2745.

Panel B. Intrinsic transcriptomic gradients, emphasizing no FDR-significant component. Gradient 10 may be labeled as the closest nominal trend, p=0.0566, q=0.4747, without promotion.

Panel C. Wong published panels:

- connectivity 6: rho=-0.152, spatial p=0.463, coexpression-aware p=0.389;
- dyslexia 14: rho=-0.273, spatial p=0.0516, spatial q=0.103, coexpression-aware p=0.099, q=0.198.

This figure should visually separate frozen validation from later post-hoc diagnostics.

## Main Figure 6. AHBA bilateral-handling diagnostic

This is optional for the main paper. If space is limited, move it to Extended Data.

Panel A. Dyslexia panel whole-cortex association: mirrored rho=-0.273 vs no-mirror rho=-0.478.

Panel B. Hemisphere decomposition:

- left: mirrored -0.567 vs no-mirror -0.580;
- right: mirrored +0.0038 vs no-mirror -0.431.

Panel C. Mirrored vs no-mirror map similarity:

- full dyslexia map rho=0.738;
- left hemisphere rho=0.988;
- right hemisphere rho=0.505.

Panel D. Donor LODO matched-support dyslexia results showing that every no-mirror estimate remains more negative than its mirrored counterpart.

Interpretation label: "post-hoc method-sensitivity diagnostic; does not revise the frozen primary null."

## Extended Data / Supplementary figures

1. ChineseEEG representation-selection reliability benchmark.
2. Little Prince run-wise residual BERT RSA and subject influence.
3. TMNRED sensitivity representations and null transfer follow-ups.
4. ZuCo structural/material mapping QC and subject-level transfer deltas.
5. Garnett structural mapping, reliability sensitivities, and chapter-level transfer estimates.
6. AHBA registration and forward-model QC.
7. AHBA DK mapping and channel sensitivity QC.
8. AHBA donor coverage and bilateral expression support.
9. Random-gene-set null diagnostics.
10. Published-panel gene-level decomposition.
11. Mirroring parcel-level decomposition.

## Main Table 1. Dataset and validation design

Columns:

- dataset;
- task;
- language;
- participant independence;
- text independence;
- primary EEG representation;
- role in project;
- whether model tuning occurred on the dataset;
- confirmatory/exploratory status.

## Main Table 2. Frozen neural-geometry and model-transfer results

Rows: Little Prince, TMNRED, ZuCo, Garnett, Nature.

Columns:

- reliability effect and CI;
- primary model-transfer contrast;
- mean delta;
- CI;
- fraction positive;
- exact inference;
- interpretation.

## Main Table 3. AHBA hypothesis families

Rows:

- GABA-A;
- GABA-B;
- GABA machinery;
- serotonin receptors;
- serotonin machinery;
- Reactome GABA activation;
- Reactome serotonin receptors;
- seven cell-type controls;
- Wong connectivity 6;
- Wong dyslexia 14.

Columns:

- family type;
- frozen vs exploratory;
- n genes;
- effect;
- spatial/sign-flip p;
- random/coexpression-aware p;
- FDR q;
- conclusion.

## Supplementary Table S1. RunRelay provenance

For every outcome-bearing analysis include:

- job id;
- exact NeuroSem commit;
- task name;
- status;
- runtime;
- artifact directory;
- confirmatory/exploratory label;
- whether a preceding failed job changed only engineering code or changed scientific protocol.

## Supplementary Table S2. AHBA preprocessing freeze

Include abagen version/settings, donor handling, bilateral strategy, retained genes, parcel support, forward-model conventions, DK mapping coverage, and null-generation settings.

## Figure-generation guardrails

- Plot all prespecified families, not selected significant-looking subsets.
- Use identical axes when comparing transfer deltas where scale permits.
- Distinguish confirmatory, exploratory, and post-hoc diagnostic results by labels and layout, not by overstated visual emphasis.
- Show uncertainty intervals and null distributions where they are central to the inference.
- Do not label the no-mirror dyslexia sensitivity as a validated molecular mechanism.
- Preserve exact numerical values from locked artifacts when figure scripts are implemented.
