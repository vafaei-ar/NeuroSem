# NeuroSem

NeuroSem tests whether reproducible human neural representational geometry can provide a relational training signal that changes language-model representations in a way that transfers to independent neural measurements.

The repository is in an **evidence-locked publication phase**. The primary prospective evidence chain is complete, the reviewer-motivated post-confirmatory robustness analyses are complete, and no additional outcome-bearing search is planned for the current manuscript.

## Current scientific result

ChineseEEG natural reading provides a reproducible development neural geometry and a learnable relational target. A frozen multilingual-E5 contrast then transfers positively to independent ZuCo English-reading EEG in **17/17** participants and prospectively to SMN4Lang language-network fMRI in **12/12** participants. Post-confirmatory specificity controls show that genuine ChineseEEG item-relational structure outperforms a matched shuffled-neural objective on both external targets across three fixed optimization seeds. Reverse fMRI-to-ZuCo transfer is detectable within E5, while a six-model panel shows that stable bidirectional transfer is reproduced by E5-large and E5-base but is not universal across the tested multilingual encoders. TMNRED, Garnett Dream, directional inner speech and the prospectively gated SMN4Lang MEG analysis define explicit boundaries.

The primary claim is therefore bounded:

> Human neural geometry can provide a transferable relational constraint on language representations, detectable in independent brains, languages and measurement modalities, but not universally across neural contexts or tested models.

## Where to start

1. [`docs/1_PROJECT_OVERVIEW.md`](docs/1_PROJECT_OVERVIEW.md) — scientific overview and claim boundaries.
2. [`docs/3_RESULTS_AND_COMPARISONS.md`](docs/3_RESULTS_AND_COMPARISONS.md) — numerical evidence summary.
3. [`docs/4_EXPERIMENT_LEDGER.md`](docs/4_EXPERIMENT_LEDGER.md) — chronological provenance.
4. [`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md) — current stopping rules and publication state.
5. [`docs/25_NMI_REVIEWER_SPECIFICITY_AND_ROBUSTNESS_V1.md`](docs/25_NMI_REVIEWER_SPECIFICITY_AND_ROBUSTNESS_V1.md) — frozen post-confirmatory neural-specificity protocol.
6. [`paper/README.md`](paper/README.md) — current manuscript workspace and submission status.

Frozen protocol and result documents under `docs/` remain the source of truth for analysis status. Exact execution provenance is retained in repository history and the experiment ledger rather than duplicated in publication-facing prose.

## Repository organization

- `docs/` — frozen protocols, result summaries, experiment ledger and current scientific roadmap.
- `scripts/` — analysis, robustness and figure-generation code.
- `configs/` — frozen model and dataset configuration.
- `paper/` — current submission-facing documentation and figure workflow.
- `.runrelay/project.yaml` — authoritative RunRelay task manifest.
- `AGENTS.md` — repository-specific execution and safety rules.

Raw neural datasets, restricted data, model checkpoints, credentials and `.env` files must not be committed. Safe derived outputs remain outside Git history unless deliberately declared as publication artifacts.

## Evidence hierarchy and stopping rules

- Preserve the original ChineseEEG → ZuCo → SMN4Lang prospective chain unchanged.
- Treat reverse-direction, dose-response, model-family, specificity, participant-by-stimulus and model-space analyses as post-confirmatory.
- Preserve all null, inconclusive and failed-reliability outcomes.
- Do not retune models or neural targets from external outcomes.
- Do not reopen failed MEG targets for model evaluation.
- Do not perform additional AHBA significance searches for the current manuscript.
- Do not infer that E5 is uniquely capable, that transfer is universal, or that raw RSA values across modalities share a common effect-size scale.

## Reproducible execution

NeuroSem uses RunRelay with exact commits, a fixed project-specific runner and manual approval for public-repository execution. The canonical task definitions are in `.runrelay/project.yaml`; arbitrary commands and environment inheritance are disabled.
