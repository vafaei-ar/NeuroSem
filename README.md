# NeuroSem

**NeuroSem** studies whether human EEG contains reproducible relational structure associated with language meaning, whether that structure generalizes across people, texts, datasets, tasks, and languages, and whether the residual neural geometry can provide useful auxiliary supervision for language models.

The project is no longer in an initialization phase. It now contains completed ChineseEEG discovery/tuning analyses, independent multilingual-E5 replication, TMNRED EEG replication and model-transfer tests, Nature directional-word validation, a completed ZuCo 2.0 English-reading replication and positive frozen transfer test, and an advanced Garnett Dream same-participant/new-text validation track. A separately frozen AHBA transcriptomic mechanistic extension proposed by Abbas is now part of the main roadmap.

## Read the documentation in this order

For a new collaborator, reviewer, or future return to the repository:

1. **[`docs/1_PROJECT_OVERVIEW.md`](docs/1_PROJECT_OVERVIEW.md)**  
   Scientific question, how the project evolved, what is supported, what is not supported, and publication framing.

2. **[`docs/2_DATASETS_AND_TASKS.md`](docs/2_DATASETS_AND_TASKS.md)**  
   What participants actually did in every dataset, why each dataset is used, and which datasets are task-matched versus out-of-task.

3. **[`docs/3_RESULTS_AND_COMPARISONS.md`](docs/3_RESULTS_AND_COMPARISONS.md)**  
   Numerical results and head-to-head comparisons completed so far.

4. **[`docs/4_EXPERIMENT_LEDGER.md`](docs/4_EXPERIMENT_LEDGER.md)**  
   Chronological RunRelay/analysis ledger, including failed jobs, fixes, frozen decisions, and current work.

5. **[`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md)**  
   Current operational plan: final Garnett confirmatory transfer, Abbas AHBA transcriptomic extension, manuscript consolidation, and stopping rules.

Then use `ANALYSIS_PLAN.md`, `DATASETS.md`, `SCIENTIFIC_HYPOTHESES.md`, and the detailed protocol files under `docs/` for methods and provenance.

## The three claims are separate

NeuroSem explicitly separates three scientific questions:

1. **Does reproducible neural language geometry exist?**
2. **Can neural-guided training move a language model toward the development EEG geometry?**
3. **Does that change transfer to independent semantic tasks or independent EEG datasets?**

Current evidence supports the first two strongly and gives one positive frozen independent reading-EEG transfer result in ZuCo. Generic semantic transfer and TMNRED model transfer remain null.

## Current evidence in one paragraph

ChineseEEG Little Prince silent reading contains a reproducible cross-subject EEG geometry after nuisance control, and BERT shows a small but consistent residual correspondence with that geometry across six narrative runs. Neural-guided BERT tuning improves sealed run-07 neural alignment relative to matched text-only and shuffled-neural controls in two seeds. Multilingual E5 reproduces the qualitative neural-target alignment phenomenon in an independent architecture. TMNRED independently replicates the EEG geometry during Chinese reading but shows null neural-guided E5 transfer. ZuCo 2.0 independently replicates the temporal-mean geometry during English natural reading and yields a positive frozen ChineseEEG-to-ZuCo E5 transfer result. Garnett Dream now also shows positive same-participant/new-text EEG reliability, and its exact presentation-row to segmented-text mapping has been frozen; the final Garnett model-transfer test remains to be run. The AHBA transcriptomic extension is being treated as a separately frozen mechanistic track.

## Core dataset roles

| Dataset | Participant task | Role |
|---|---|---|
| ChineseEEG Little Prince | Silent Chinese natural reading | Discovery and model development |
| ChineseEEG Garnett Dream | Silent Chinese natural reading | Same-participant/new-text validation; EEG reliability and exact text mapping complete, model transfer pending |
| TMNRED | Chinese sentence reading | Independent Chinese-reading EEG replication and transfer test |
| ZuCo 2.0 Task 1 NR | English normal reading | Independent English-reading / cross-language replication and positive frozen transfer |
| Nature directional-word EEG | Covert/inner speech of directional concepts | Secondary out-of-task mechanistic/generalization test |
| Allen Human Brain Atlas | Postmortem cortical transcriptomics | Abbas-proposed molecular-mechanistic extension projected to the 128-channel ChineseEEG spatial geometry |

The Nature directional dataset should not be interpreted as a task-matched replication of reading-related geometry. AHBA should not be interpreted as participant-specific molecular measurement.

## Main results at a glance

### ChineseEEG / BERT

- selected row-mean EEG representation: raw LOO reliability approximately **0.220**, residual approximately **0.121**;
- BERT residual correspondence positive in **6/6** Little Prince runs 01-06;
- mean run effect **0.0085**;
- exact run-level sign-flip **p = 0.015625**.

Sealed run-07 neural holdout:

| Arm | Seed 1 | Seed 2 |
|---|---:|---:|
| Base | 0.0319 | 0.0319 |
| Text-only | 0.0354 | 0.0341 |
| Neural-guided | **0.0371** | **0.0375** |
| Shuffled-neural | 0.0353 | 0.0338 |

### External semantic benchmark

Seed 1 eight-task mean Spearman:

- base 0.283464;
- text-only 0.308486;
- neural-guided 0.308575;
- shuffled-neural 0.307943.

Seed 2:

- base 0.283464;
- text-only 0.305020;
- neural-guided 0.301607;
- shuffled-neural 0.305266.

The neural-specific semantic benefit is therefore not stable across seeds.

### TMNRED EEG-only replication

- primary `row_mean_all` residual LOO reliability: **0.00724**, 95% CI **[0.00356, 0.01079]**;
- 75.9% of participants positive;
- `row_std_all`: **0.01820**;
- `relative_8bin_all`: **0.01148**.

### TMNRED E5 transfer

Primary neural-guided lambda 0.10 versus text-only lambda 0:

- mean residual-RSA difference **+0.000020**;
- 95% CI **[-0.000128, +0.000176]**;
- one-sided sign-flip **p = 0.402**.

Alternative SD and 8-bin TMNRED targets also failed to rescue the lambda-0.10 transfer effect.

### ZuCo 2.0 English reading

Primary `row_mean_all` residual LOO reliability:

- mean **0.06742**;
- 95% CI **[0.05831, 0.07687]**;
- **17/17 participants positive**.

Frozen E5 lambda .10 minus lambda 0 transfer:

- mean participant delta **+0.001664**;
- 95% CI **[+0.001229, +0.002145]**;
- **17/17 participants positive**;
- one-sided sign-flip **p = 7.63e-06**.

### Garnett Dream

Primary `row_mean_all` EEG-only reliability:

- mean nuisance-residualized participant LOO reliability **0.01863**;
- median **0.01895**;
- **10/10 participants positive**;
- bootstrap 95% CI **[0.01636, 0.02085]**;
- exact one-sided sign-flip **p = 0.0009766**.

The exact presentation-row to segmented-text mapping is now frozen across all 18 chapters/runs. The single confirmatory E5 lambda .10 vs 0 model-transfer test is the next Garnett outcome-bearing analysis.

## Current next priorities

1. Run the single frozen Garnett Dream E5 lambda .10 vs 0 confirmatory model-transfer analysis, with the full text-derived nuisance family restored from the exact XLSX mapping.
2. In parallel, begin Abbas's AHBA model-blind preprocessing and 128-channel forward/source-sensitivity projection.
3. Freeze AHBA GABAergic, serotonergic, cell-type, pathway, donor/bilateral, and spatial-null choices before any molecular NeuroSem outcome.
4. Run the frozen AHBA mechanistic analysis only after those choices are locked.
5. Build manuscript figures, Results, Methods, and cross-dataset evidence tables in parallel.

See [`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md) for the operational sequence and stopping rules.

## Scientific interpretation

The current defensible statement is:

> Reading-related EEG contains a small but reproducible relational geometry across independent datasets and languages. Neural-guided training can improve alignment to the development EEG target and, in a frozen confirmatory test, produces a small but highly consistent improvement in alignment to independent English natural-reading EEG. Same-participant new-text EEG reliability is also positive in Garnett Dream. The benefit is not universal: generic semantic benchmarks, TMNRED model transfer, and the out-of-task Nature directional test remain null or weak.

Do not summarize the project as “brain supervision improves semantic representations.” The evidence does not support that broad claim.

## Repository organization

- `docs/1_PROJECT_OVERVIEW.md`: current scientific overview
- `docs/2_DATASETS_AND_TASKS.md`: current dataset/task roles
- `docs/3_RESULTS_AND_COMPARISONS.md`: current numerical results
- `docs/4_EXPERIMENT_LEDGER.md`: chronological experiment and RunRelay ledger
- `docs/5_CURRENT_ROADMAP.md`: current operational roadmap
- `docs/abbas_ahba_transcriptomic_extension.md`: AHBA molecular-mechanistic extension
- `SCIENTIFIC_HYPOTHESES.md`: hypotheses and falsification criteria
- `DATASETS.md`: primary-publication dataset catalog and historical selection rationale
- `ANALYSIS_PLAN.md`: preregistration-style computational/statistical plan and implemented-decision notes
- `docs/`: detailed frozen protocols, decisions, audit notes, and collaborator briefs
- `src/`: reusable analysis code
- `scripts/`: executable workflow entry points
- `configs/`: dataset and experiment configurations
- `outputs/`: local/RunRelay derived outputs; do not commit raw sensitive data
- `paper/`: manuscript development

## Reproducible execution

NeuroSem uses RunRelay for workstation execution. The authoritative task manifest is `.runrelay/project.yaml` and repository-specific execution rules are in `AGENTS.md`.

Bound machine: `pshjl4vf24`.

All RunRelay jobs must use exact NeuroSem commits, explicit `requested_machine_id: "pshjl4vf24"`, manual approval where configured, and safe derived artifacts only.

## Collaboration

Project leads: Alireza Vafaei Sadr and Abbas Khanbeigy.

Raw neural datasets, restricted data, large derived arrays, credentials, and model checkpoints should not be committed to GitHub. Analyses should preserve protocol provenance and clearly distinguish confirmatory from exploratory work.
