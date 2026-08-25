# NeuroSem

**NeuroSem** studies whether human EEG contains reproducible relational structure associated with language meaning, whether that structure generalizes across people, texts, datasets, tasks, and languages, and whether the residual neural geometry can provide useful auxiliary supervision for language models.

The project is no longer in an initialization phase. It now contains completed ChineseEEG discovery/tuning analyses, independent multilingual-E5 replication, independent TMNRED EEG replication and model-transfer tests, Nature directional-word validation, and an active ZuCo 2.0 English-reading replication pipeline.

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

Then use `ANALYSIS_PLAN.md`, `DATASETS.md`, `SCIENTIFIC_HYPOTHESES.md`, and the detailed protocol files under `docs/` for methods and provenance.

## The three claims are separate

NeuroSem explicitly separates three scientific questions:

1. **Does reproducible neural language geometry exist?**
2. **Can neural-guided training move a language model toward the development EEG geometry?**
3. **Does that change transfer to independent semantic tasks or independent EEG datasets?**

Current evidence supports the first two more strongly than the third.

## Current evidence in one paragraph

ChineseEEG Little Prince silent reading contains a reproducible cross-subject EEG geometry after nuisance control, and BERT shows a small but consistent residual correspondence with that geometry across six narrative runs. Neural-guided BERT tuning improves sealed run-07 neural alignment relative to matched text-only and shuffled-neural controls in two seeds. Multilingual E5 reproduces the qualitative neural-target alignment phenomenon in an independent architecture. However, brain-specific gains do not robustly transfer to generic semantic benchmarks, and the frozen ChineseEEG-to-TMNRED E5 transfer test is null. TMNRED nevertheless provides independent evidence that the EEG geometry itself is reproducible during Chinese reading. Thus, neural geometry generalizes better than the model-learning benefit so far.

## Core dataset roles

| Dataset | Participant task | Role |
|---|---|---|
| ChineseEEG Little Prince | Silent Chinese natural reading | Discovery and model development |
| ChineseEEG Garnett Dream | Silent Chinese natural reading | Different-text replication, still to be completed |
| TMNRED | Chinese sentence reading | Independent Chinese-reading EEG replication and transfer test |
| ZuCo 2.0 Task 1 NR | English normal reading | Independent English-reading / cross-language replication, in progress |
| Nature directional-word EEG | Covert/inner speech of directional concepts | Secondary out-of-task mechanistic/generalization test |

The Nature directional dataset should not be interpreted as a task-matched replication of reading-related geometry.

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

## Current next priorities

1. Complete full-cohort model-blind ZuCo 2.0 Task 1 Normal Reading materialization/QC and then the frozen EEG-only reliability test.
2. Add ChineseEEG **Garnett Dream** as a prospectively frozen different-text replication using the Little Prince analysis decisions.
3. Only after those results decide whether any further model-transfer experiment is justified.

## Scientific interpretation

The current defensible statement is:

> Reading-related EEG contains a small but reproducible relational geometry. Neural-guided training can improve alignment to the development EEG target, but evidence that this change transfers to generic semantic tasks or independent EEG datasets is currently weak or null.

Do not summarize the project as “brain supervision improves semantic representations.” The evidence does not support that broad claim yet.

## Repository organization

- `docs/1_PROJECT_OVERVIEW.md`: current scientific overview
- `docs/2_DATASETS_AND_TASKS.md`: current dataset/task roles
- `docs/3_RESULTS_AND_COMPARISONS.md`: current numerical results
- `docs/4_EXPERIMENT_LEDGER.md`: chronological experiment and RunRelay ledger
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
