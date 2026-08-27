# Run Next: NeuroSem Consolidation

**Last updated:** 2026-08-27

The project is no longer at the dataset-download or first-audit stage. The core ChineseEEG, TMNRED, ZuCo, Garnett, Nature, and AHBA analysis families have been run.

The next work is **reconciliation and manuscript production**, not another exploratory outcome search.

## 1. Lock current scientific conclusions

Preserve the following without reopening analysis choices:

- ChineseEEG Little Prince: reproducible neural geometry and positive held-out within-dataset neural-guided alignment.
- TMNRED: independent reading geometry replication, frozen model transfer null.
- ZuCo: independent English-reading geometry replication and positive frozen E5 transfer.
- Garnett Dream: same-participant/new-text EEG reliability positive, frozen E5 transfer null/inconclusive.
- Nature directional: out-of-task null boundary condition.
- AHBA: frozen GABA/serotonin/pathway null, exploratory transcriptome spatial null, published language-panel primary null, exploratory no-mirror hemispheric sensitivity.

Do not run new lambda, representation, gene-set, pathway, hemisphere, or subset searches to improve these outcomes.

## 2. Reconcile final analysis code into canonical `main`

Several late AHBA analyses were executed on narrow RunRelay branches. Those branches may contain reduced manifests, compatibility wrappers, temporary notes, or technical fixes.

Do **not** merge those branches wholesale.

Instead:

1. identify the final scientific script for each completed analysis;
2. selectively port only the final analysis code to canonical `main`;
3. remove temporary compatibility and placeholder files that are no longer needed;
4. preserve exact RunRelay job and commit provenance in `docs/4_EXPERIMENT_LEDGER.md`;
5. verify that canonical `.runrelay/project.yaml` contains only intentional tasks.

## 3. Build manuscript figures

Priority figure set:

1. Cross-dataset EEG geometry reliability: ChineseEEG, TMNRED, ZuCo, Garnett.
2. Neural-guided model-transfer contrasts: TMNRED, ZuCo, Garnett, Nature.
3. AHBA spatial mapping schematic and prespecified molecular nulls.
4. Exploratory transcriptome PLS with spatial-null comparison.
5. Published language-panel primary results.
6. Mirrored versus no-mirror dyslexia-panel hemisphere decomposition.

Every AHBA figure must label analyses as confirmatory, exploratory, or post-hoc diagnostic.

## 4. Build manuscript tables

Required tables:

- dataset/task/independence table;
- EEG reliability summary;
- frozen model-transfer summary;
- AHBA molecular-result summary;
- RunRelay job/commit provenance table for supplement/reproducibility.

## 5. Draft Results

Use scientific evidence order, not debugging chronology:

1. ChineseEEG discovery geometry.
2. Within-development neural-guided tuning.
3. Independent reading EEG replication.
4. Cross-dataset transfer, including both positive and null tests.
5. Garnett same-participant/new-text boundary.
6. Nature out-of-task boundary.
7. AHBA mechanistic nulls.
8. AHBA mirroring sensitivity as a separate methodological observation.

## 6. Draft Methods

Build Methods directly from frozen protocols and final committed scripts.

For every major analysis, record:

- frozen input cohort/items;
- representation and nuisance family;
- inference unit and null procedure;
- model/version/seed where relevant;
- exact RunRelay job ID and NeuroSem commit;
- confirmatory/exploratory/diagnostic classification.

## 7. Decide whether any analysis is genuinely missing

Only after the figures and Results/Methods draft exist should the team decide whether a missing analysis prevents a defensible paper.

A new analysis should be added only if it closes a clear methodological gap, not because an existing result is null.

## 8. Future molecular work

If the no-mirror dyslexia-panel finding is pursued beyond the current paper, treat it as a new prospectively frozen validation study.

Preferred options:

- an independent transcriptomic resource with stronger bilateral coverage;
- a preregistered left/right language-network analysis;
- layer-resolved spatial transcriptomic data;
- independent imaging-transcriptomic validation using the same frozen 14-gene panel.

Do not continue within-AHBA subset fishing.

## Current authoritative docs

- `docs/1_PROJECT_OVERVIEW.md`
- `docs/3_RESULTS_AND_COMPARISONS.md`
- `docs/4_EXPERIMENT_LEDGER.md`
- `docs/5_CURRENT_ROADMAP.md`
- `docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md`
