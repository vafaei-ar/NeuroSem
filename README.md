# NeuroSem

**NeuroSem** studies whether human EEG contains reproducible relational structure associated with language meaning, whether that structure generalizes across people, texts, datasets, tasks, and languages, and whether residual neural geometry can provide useful auxiliary supervision for language models.

The project is now in a **consolidation phase**, not an analysis-expansion phase. The core reading-EEG validation chain is complete, Garnett Dream same-participant/new-text transfer is complete, and the AHBA mechanistic extension has completed its frozen, exploratory, and mirroring-sensitivity analyses.

## Read the documentation in this order

1. **[`docs/1_PROJECT_OVERVIEW.md`](docs/1_PROJECT_OVERVIEW.md)**  
   Scientific question, supported claims, boundary conditions, and publication framing.

2. **[`docs/2_DATASETS_AND_TASKS.md`](docs/2_DATASETS_AND_TASKS.md)**  
   Dataset/task roles and why task comparability matters.

3. **[`docs/3_RESULTS_AND_COMPARISONS.md`](docs/3_RESULTS_AND_COMPARISONS.md)**  
   Numerical results and cross-dataset comparisons.

4. **[`docs/4_EXPERIMENT_LEDGER.md`](docs/4_EXPERIMENT_LEDGER.md)**  
   Chronological RunRelay and analysis ledger.

5. **[`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md)**  
   Current consolidation and manuscript plan.

6. **[`docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md`](docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md)**  
   Completed AHBA preparation, frozen nulls, exploratory transcriptomics, published language-panel validation, mirroring diagnostic, and the forward molecular plan.

For detailed methods and provenance, use `ANALYSIS_PLAN.md`, `DATASETS.md`, `SCIENTIFIC_HYPOTHESES.md`, and the protocol files under `docs/`.

## The major claims remain separate

NeuroSem explicitly separates four questions:

1. **Does reproducible neural language geometry exist?**
2. **Can neural-guided training move a language model toward the development EEG geometry?**
3. **Does that change transfer to independent semantic tasks or independent EEG datasets?**
4. **Can the established semantic neural geometry be linked to specific transcriptomic systems?**

The current evidence supports the first two, gives one positive frozen independent reading-EEG transfer result in ZuCo, gives a null/inconclusive same-participant/new-text Garnett model-transfer result, and does **not** establish a specific AHBA molecular mechanism.

## Current evidence in one paragraph

ChineseEEG Little Prince silent reading contains reproducible cross-subject EEG geometry after nuisance control, and BERT shows small but consistent residual correspondence with that geometry across six narrative runs. Neural-guided BERT tuning improves sealed run-07 neural alignment relative to matched text-only and shuffled-neural controls in two seeds, and multilingual E5 reproduces the qualitative within-ChineseEEG effect. TMNRED independently replicates the reading EEG geometry but shows null neural-guided E5 transfer. ZuCo 2.0 independently replicates the temporal-mean geometry during English natural reading and yields a positive frozen ChineseEEG-to-ZuCo E5 transfer result. Garnett Dream shows positive same-participant/new-text EEG reliability, but the frozen E5 neural-guided-minus-text-only transfer contrast is null/inconclusive. The AHBA extension is also primarily null: prespecified GABAergic/serotonergic systems, exploratory whole-transcriptome PLS, transcriptomic gradients, and independent published language-gene panels do not survive the frozen inferential framework. A strong no-mirror dyslexia-panel sensitivity remains an exploratory hemispheric-method finding rather than confirmatory molecular evidence.

## Core dataset and extension roles

| Dataset / resource | Role | Current status |
|---|---|---|
| ChineseEEG Little Prince | Discovery and model development | Reproducible geometry; positive sealed neural-guided alignment |
| ChineseEEG Garnett Dream | Same-participant/new-text validation | EEG reliability positive; frozen E5 transfer null/inconclusive |
| TMNRED | Independent Chinese-reading replication | EEG geometry positive; model transfer null |
| ZuCo 2.0 Task 1 NR | Independent English-reading / cross-language replication | EEG geometry positive; frozen E5 transfer positive |
| Nature directional-word EEG | Out-of-task inner-speech boundary condition | Transfer null |
| Allen Human Brain Atlas | Population transcriptomic mechanistic extension | Frozen primary molecular tests null; exploratory mirroring sensitivity documented |

AHBA should not be interpreted as participant-specific molecular measurement.

## Main results at a glance

### Reading EEG geometry

- ChineseEEG Little Prince selected temporal-mean representation: residual LOO reliability approximately **0.121**.
- TMNRED primary `row_mean_all`: **0.00724**, 95% CI **[0.00356, 0.01079]**.
- ZuCo primary `row_mean_all`: **0.06742**, 95% CI **[0.05831, 0.07687]**, **17/17** positive.
- Garnett Dream primary `row_mean_all`: **0.01863**, 95% CI **[0.01636, 0.02085]**, **10/10** positive.

### Model transfer

- TMNRED E5 lambda .10 minus 0: mean **+0.000020**, 95% CI crossing zero, p=.402, null.
- ZuCo E5 lambda .10 minus 0: mean **+0.001664**, 95% CI **[+0.001229, +0.002145]**, **17/17** positive, one-sided p=`7.63e-06`.
- Garnett Dream E5 lambda .10 minus 0: mean **+0.0003266**, 95% CI **[-0.0001218, +0.0007560]**, **6/10** positive, one-sided exact sign-flip p=`0.1016`. This is confirmatory null/inconclusive.

### AHBA mechanistic extension

Primary frozen GABAergic/serotonergic/pathway tests are null. Exploratory whole-transcriptome PLS showed moderate in-sample alignment (`r = 0.4574`) but failed the spatial null (`p = 0.2745`). No transcriptomic gradient survived FDR.

Two exact published Wong et al. language-related panels were then frozen independently. The 6-gene connectivity panel was null. The 14-gene dyslexia panel was suggestive in the mirrored primary analysis (`rho = -0.2733`, spatial p=`0.0516`) but failed both multiple-comparison and co-expression-aware criteria.

The no-mirror dyslexia-panel sensitivity was much stronger (`rho = -0.4776`, spatial p=`0.0032`, co-expression-profile p=`0.0010`). A post-hoc diagnostic showed that this difference is driven mainly by the **right hemisphere**, not by parcel missingness: mirrored right-hemisphere `rho = +0.0038` versus no-mirror `rho = -0.4310`. This remains exploratory because native AHBA right-hemisphere sampling is sparse and the primary mirrored test was null.

See [`docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md`](docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md) for the full mechanistic record.

## Current next priorities

1. **Stop expanding the AHBA significance search.** Preserve the frozen nulls and treat the mirroring result as a methodological sensitivity finding.
2. **Selectively reconcile final analysis code and documentation from execution branches into canonical `main`.** Do not merge reduced-manifest execution branches wholesale.
3. **Build manuscript-ready figures and tables** across ChineseEEG, TMNRED, ZuCo, Garnett, Nature, and AHBA.
4. **Draft Results and Methods from the frozen evidence chain**, including nulls and failed confirmatory tests.
5. **Use future molecular work only for independent validation**, preferably a resource with stronger bilateral transcriptomic coverage or a prospectively frozen hemispheric analysis.
6. **Choose the final journal framing after manuscript consolidation**, rather than adding analyses to fit a target journal.

## Scientific interpretation

The current defensible statement is:

> Reading-related EEG contains a small but reproducible relational geometry across independent datasets and languages. Neural-guided training can improve alignment to the development EEG target and, in a frozen confirmatory test, produces a small but highly consistent improvement in alignment to independent English natural-reading EEG. This model-transfer benefit is not universal: TMNRED and Garnett transfer are null/inconclusive, generic semantic benchmarks are not stably improved, and the out-of-task Nature directional test is null. Transcriptomic extension analyses do not establish a specific molecular mechanism, although a post-hoc AHBA mirroring diagnostic identifies a reproducible hemispheric preprocessing sensitivity that warrants independent future validation.

Do not summarize the project as “brain supervision improves semantic representations” or as evidence for a specific GABAergic/serotonergic molecular mechanism. The data do not support either broad claim.

## Repository organization

- `docs/1_PROJECT_OVERVIEW.md`: current scientific overview
- `docs/2_DATASETS_AND_TASKS.md`: dataset/task roles
- `docs/3_RESULTS_AND_COMPARISONS.md`: numerical results
- `docs/4_EXPERIMENT_LEDGER.md`: chronological experiment and RunRelay ledger
- `docs/5_CURRENT_ROADMAP.md`: current operational roadmap
- `docs/6_AHBA_CURRENT_STATUS_AND_NEXT_STEPS.md`: completed AHBA findings and forward plan
- `docs/abbas_ahba_transcriptomic_extension.md`: original AHBA mechanistic plan and current outcome update
- `SCIENTIFIC_HYPOTHESES.md`: hypotheses and falsification criteria
- `ANALYSIS_PLAN.md`: preregistration-style plan and implemented-decision notes
- `scripts/`: executable workflows
- `outputs/`: local/RunRelay derived outputs; raw sensitive data must not be committed
- `paper/`: manuscript development

## Reproducible execution

NeuroSem uses RunRelay for workstation execution. The authoritative task manifest is `.runrelay/project.yaml` and repository-specific execution rules are in `AGENTS.md`.

Bound machine: `pshjl4vf24`.

All RunRelay jobs must use exact NeuroSem commits, explicit `requested_machine_id: "pshjl4vf24"`, manual approval where configured, and safe derived artifacts only.

## Collaboration

Project leads: Alireza Vafaei Sadr and Abbas Khanbeigy.

Raw neural datasets, restricted data, large derived arrays, credentials, and model checkpoints should not be committed to GitHub. Analyses should preserve protocol provenance and clearly distinguish confirmatory, exploratory, and post-hoc diagnostic work.
