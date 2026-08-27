# Project Plan

**Last updated:** 2026-08-27

The original NeuroSem milestones have largely been completed. This document now records the project-level plan for consolidation, publication, and any future independent follow-up.

## Milestone 1. Residual neural semantic geometry

**Status: completed.**

The project established reproducible reading-related EEG geometry in ChineseEEG and replicated the prospectively frozen temporal-mean representation in TMNRED, ZuCo, and Garnett Dream.

Key conclusion: reproducible relational neural structure associated with language meaning exists across multiple reading datasets, although effect size varies by dataset.

## Milestone 2. Neural-guided model tuning

**Status: completed.**

BERT neural-guided tuning improved sealed ChineseEEG neural alignment relative to matched text-only and shuffled-neural controls in two seeds. Multilingual E5 reproduced the qualitative within-development effect.

Key conclusion: neural-guided training can move a model toward the development EEG geometry.

## Milestone 3. External neural and semantic evaluation

**Status: completed for the current paper.**

- Generic semantic benchmark: no stable neural-specific advantage.
- TMNRED frozen E5 transfer: null.
- ZuCo frozen E5 transfer: positive and highly consistent.
- Garnett Dream frozen E5 transfer: null/inconclusive despite positive new-text EEG reliability.
- Nature directional inner-speech transfer: null out-of-task boundary condition.

Key conclusion: neural-guided alignment transfer can generalize, but it is not universal and should not be described as generic semantic improvement.

## Milestone 4. AHBA molecular-mechanistic extension

**Status: completed analysis family for the current paper.**

The project implemented the planned transcriptomic mapping through a frozen EEG forward/source-sensitivity model rather than nearest-electrode cortical assignment.

Completed components:

- AHBA `abagen` preprocessing;
- frozen 128-channel source sensitivity;
- DK68 cortical mapping;
- 128 x gene molecular-sensitivity matrix;
- prespecified GABAergic, serotonergic, pathway, and cell-type panels;
- frozen semantic channel and cortical spatial targets;
- donor and bilateral robustness;
- spatial and random-gene null frameworks.

Primary result: prespecified GABAergic/serotonergic/pathway associations are null.

Exploratory result: whole-transcriptome PLS and transcriptomic gradients are null after spatial correction.

Independent published language panels: primary null under frozen spatial and co-expression-aware criteria.

Post-hoc methodological finding: no-mirror dyslexia-panel alignment is much stronger than the primary mirrored result, driven mainly by a right-hemisphere expression-map shift. This remains exploratory because of sparse native AHBA right-hemisphere sampling.

See `docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md`.

## Milestone 5. Canonical code and provenance reconciliation

**Status: next.**

Objective: convert the late execution state into a clean, reproducible canonical repository without changing scientific conclusions.

Work packages:

1. Selectively reconcile final scripts from narrow RunRelay execution branches.
2. Do not merge reduced-manifest execution branches wholesale.
3. Remove obsolete compatibility wrappers, placeholders, and temporary notes.
4. Keep exact RunRelay job and commit provenance in the experiment ledger.
5. Ensure canonical `.runrelay/project.yaml` contains only intentional tasks.
6. Confirm that every manuscript result points to a final script and exact committed analysis definition.

## Milestone 6. Manuscript figures and tables

**Status: next.**

Required figures:

- cross-dataset EEG geometry reliability;
- neural-guided transfer comparison across TMNRED, ZuCo, Garnett, and Nature;
- AHBA spatial mapping and frozen mechanistic nulls;
- exploratory whole-transcriptome spatial-null result;
- published language-panel validation;
- AHBA mirroring hemisphere diagnostic.

Required tables:

- dataset/task/independence table;
- EEG reliability summary;
- frozen model-transfer summary;
- AHBA confirmatory/exploratory/diagnostic result table;
- RunRelay job/commit provenance supplement.

## Milestone 7. Manuscript drafting

**Status: next.**

Draft Results in scientific evidence order:

1. ChineseEEG neural geometry.
2. Neural-guided within-development tuning.
3. Independent reading EEG replication.
4. Cross-dataset model transfer, preserving both positive and null results.
5. Same-participant/new-text Garnett boundary.
6. Nature out-of-task boundary.
7. AHBA mechanistic nulls.
8. AHBA mirroring sensitivity.

Draft Methods directly from frozen protocols, final committed scripts, and exact job provenance.

## Milestone 8. Publication framing

**Status: pending manuscript integration.**

Do not add analyses to fit a target journal.

Potential framing:

- **Nature Machine Intelligence** if the strongest integrated contribution is transferable neural-guided representation learning constrained by honest null external tests.
- **Nature Neuroscience** if the strongest integrated contribution is reproducible cross-dataset/cross-language neural geometry with a disciplined biological/mechanistic extension.

The journal decision should follow the completed manuscript.

## Milestone 9. Future independent molecular validation

**Status: separate future study, not required for the current paper.**

If the AHBA hemispheric dyslexia-panel sensitivity is pursued further, use an independent and prospectively frozen validation design.

Preferred options:

- a transcriptomic resource with stronger bilateral coverage;
- preregistered left/right language-network testing;
- layer-resolved spatial transcriptomics;
- independent imaging-transcriptomic validation using the exact frozen 14-gene panel.

Do not continue post-hoc AHBA subset or pathway search.

## Collaboration workflow

Use issues for discrete scientific/technical tasks and pull requests for canonical analysis/documentation changes. Major methodological decisions should be documented in `docs/decisions.md` with date, rationale, alternatives considered, and consequences.

Do not commit raw neural datasets, restricted data, credentials, or large checkpoints. Store scripts, configurations, provenance metadata, safe derived summaries, and publication-ready outputs permitted by source licenses.
