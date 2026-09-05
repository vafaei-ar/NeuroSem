# NeuroSem

NeuroSem tests whether reproducible human neural representational geometry can provide a relational training signal that changes language-model representations in a way that transfers to independent neural measurements.

The repository is now in an **evidence-locked publication phase**. The primary prospective chain and the planned post-confirmatory specificity, robustness, dose, model-family, regional and transcriptomic analyses are complete. No outcome-bearing analysis is currently authorized for the main paper.

## Current scientific result

ChineseEEG natural reading provides a reproducible development neural geometry and a learnable relational target. A frozen multilingual-E5-large contrast then transfers positively to independent ZuCo English-reading EEG in **17/17** participants and prospectively to SMN4Lang fMRI in **12/12** participants.

Subsequent analyses define the limits of that transfer rather than revise the primary tests:

- preserved neural item correspondence outperforms a matched shuffled-neural objective on both external targets across three fixed E5 seeds;
- forward E5 dose characterization is positive on both targets through `lambda=0.30`, but at `lambda=1.0` ZuCo transfer continues to increase while SMN4Lang fMRI reverses and the generic STS cost becomes much larger;
- stable bidirectional transfer under the common protocol is reproduced in E5-large and E5-base, but not uniformly across MPNet, MiniLM, XLM-R or mBERT;
- regional SMN4Lang characterization shows positive displacement in all six predefined language parcels **and all 68 DK cortical parcels**, so the result does **not** establish language-network specificity;
- TMNRED, Garnett Dream, directional inner speech and the prospectively gated SMN4Lang MEG analysis remain explicit boundaries;
- prespecified AHBA molecular analyses remain null, and exploratory transcriptomic sensitivities do not revise those nulls.

The current bounded conclusion is:

> Brain-derived relational supervision can transfer to independent neural representational systems, but source fit does not guarantee a target-independent transfer magnitude or sign. Transfer depends on relational-loss dose, external target and model backbone under the tested protocols.

## Current manuscript master

The current author-review master is **`NeuroSem_Nature_Manuscript_v1.11_NMI_native_vector_figures.docx`**, with **`NeuroSem_NMI_Supplementary_Technical_Tables_v1.11_NMI_native_vector_figures.docx`** as the companion Supplementary Information. The Word masters are intentionally kept outside the Git working tree during final review. Their exact filenames and SHA-256 fingerprints are recorded in [`paper/CURRENT_MANUSCRIPT.md`](paper/CURRENT_MANUSCRIPT.md).

## Where to start

1. [`paper/CURRENT_MANUSCRIPT.md`](paper/CURRENT_MANUSCRIPT.md) — authoritative publication-master identity and fingerprints.
2. [`paper/README.md`](paper/README.md) — submission workspace and writing guardrails.
3. [`docs/1_PROJECT_OVERVIEW.md`](docs/1_PROJECT_OVERVIEW.md) — scientific overview and claim boundaries.
4. [`docs/3_RESULTS_AND_COMPARISONS.md`](docs/3_RESULTS_AND_COMPARISONS.md) — numerical evidence summary.
5. [`docs/4_EXPERIMENT_LEDGER.md`](docs/4_EXPERIMENT_LEDGER.md) — chronological provenance.
6. [`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md) — current stopping rules and publication state.
7. [`paper/FIGURE_GENERATION.md`](paper/FIGURE_GENERATION.md) — canonical figure-build workflow.

Frozen protocol and result documents under `docs/` remain the source of truth for analysis chronology. Exact execution provenance is retained in repository history and RunRelay records rather than duplicated in publication-facing prose.

## Repository organization

- `docs/` — frozen protocols, result summaries, experiment ledger and publication-state roadmap.
- `scripts/` — analysis, robustness and figure-generation code.
- `configs/` — frozen model and dataset configuration.
- `paper/` — submission-facing documentation and figure workflow.
- `.runrelay/project.yaml` — authoritative RunRelay task manifest.
- `AGENTS.md` — repository-specific execution and safety rules.

Raw neural datasets, restricted data, model checkpoints, credentials, `.env` files and final Word manuscript binaries must not be committed. Safe derived outputs remain outside Git history unless deliberately declared as publication artifacts.

## Evidence hierarchy and stopping rules

- Preserve the original ChineseEEG -> ZuCo -> SMN4Lang prospective chain unchanged.
- Treat forward/reverse dose, reverse-direction, model-family, specificity, participant-by-stimulus, model-space, regional fMRI and AHBA analyses as post-confirmatory or secondary exactly as frozen.
- Preserve all null, inconclusive, negative and failed-reliability outcomes.
- Do not retune models, targets, layers, ROIs, checkpoints or doses from external outcomes.
- Do not reopen failed MEG targets for model evaluation.
- Do not infer E5 uniqueness, a universal neural-semantic axis, language-network specificity, or a specific transcriptomic mechanism.
- No new outcome-bearing analysis is planned for the current manuscript unless an editor/reviewer asks a clearly specified question that requires it.

## Reproducible execution

NeuroSem uses RunRelay with exact commits, a fixed project-specific runner and manual approval for public-repository execution. Canonical task definitions are in `.runrelay/project.yaml`; arbitrary commands and environment inheritance are disabled.
