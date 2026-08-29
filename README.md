# NeuroSem

**NeuroSem** studies whether reproducible human neural representational geometry can constrain language-model learning in a way that transfers to independent neural measurements.

The project is now in an **evidence-locked manuscript-consolidation phase**. The primary outcome-bearing analyses for the present paper are complete. The current scientific center is the transfer chain from Chinese natural-reading EEG to independent English-reading EEG and prospectively to language-network fMRI, with explicit transfer and reliability boundaries.

## Read the documentation in this order

1. [`docs/1_PROJECT_OVERVIEW.md`](docs/1_PROJECT_OVERVIEW.md) — final scientific overview and claim boundaries.
2. [`docs/2_DATASETS_AND_TASKS.md`](docs/2_DATASETS_AND_TASKS.md) — dataset/task roles.
3. [`docs/3_RESULTS_AND_COMPARISONS.md`](docs/3_RESULTS_AND_COMPARISONS.md) — final numerical evidence summary, including SMN4Lang fMRI and MEG.
4. [`docs/4_EXPERIMENT_LEDGER.md`](docs/4_EXPERIMENT_LEDGER.md) — chronological analysis/RunRelay history; older entries reflect the state at the time they were written.
5. [`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md) — final manuscript-consolidation roadmap and stopping rules.
6. [`paper/README.md`](paper/README.md) — current manuscript workspace and authoritative submission files.

For detailed methods and provenance, use `ANALYSIS_PLAN.md`, `DATASETS.md`, `SCIENTIFIC_HYPOTHESES.md`, the frozen protocol files under `docs/`, and exact RunRelay job/commit records.

## Current evidence in one paragraph

ChineseEEG Little Prince natural reading contains reproducible cross-participant EEG geometry after nuisance control, and neural-guided BERT training improves sealed held-out neural alignment relative to matched controls. A frozen multilingual-E5 contrast then transfers positively to independent ZuCo English natural-reading EEG in **17/17** participants and prospectively to independently defined SMN4Lang language-network fMRI during Mandarin auditory narratives in **12/12** participants. Transfer is not universal: TMNRED and Garnett Dream are null/inconclusive and directional inner speech is an out-of-task boundary. In SMN4Lang MEG, the prospectively frozen sensor-level target failed its model-blind reliability gate, and a separately frozen 4/8/16-bin family also failed; therefore no MEG model-transfer test was performed. Generic semantic benchmarks show no stable neural-specific gain. AHBA transcriptomic analyses do not establish a specific molecular mechanism.

## Major results at a glance

| Dataset / test | Final role | Current result |
|---|---|---|
| ChineseEEG Little Prince | Development target and learnability | residual LOO ~**0.121**; sealed neural-guided BERT strongest in both seeds |
| ZuCo 2.0 Task 1 NR | Cross-language EEG validation | reliability **0.06742**; E5 delta **+0.0016637**; **17/17** positive |
| SMN4Lang fMRI | Prospective cross-modal capstone | reliability **0.65327**; E5 delta **+0.00085250**; **12/12** positive |
| TMNRED | Transfer boundary | weak positive reliability; E5 transfer null, p=.402 |
| Garnett Dream | Same-participant/new-text boundary | reliability positive; E5 transfer null/inconclusive, p=.1016 |
| Directional inner speech | Out-of-task boundary | no positive transfer; delta ~**-0.001786** |
| SMN4Lang MEG | Reliability boundary | 32-bin mean LOO **0.007713**, CI crosses zero, p=.1687; no model evaluation |
| AHBA | Secondary mechanistic extension | primary molecular tests null; exploratory hemispheric sensitivity only |

Raw RSA values across EEG, fMRI and MEG are not directly comparable as a common effect-size scale.

## Final manuscript claim

> Human neural geometry can provide a transferable relational constraint on language representations, with effects that generalize across independent brains, languages and measurement modalities, but not universally across neural contexts.

This should **not** be expanded into claims that brain supervision generally improves language models, that SMN4Lang isolates pure semantics, that MEG showed negative transfer, or that a specific transcriptomic mechanism has been identified.

## Manuscript workspace

Current submission-facing sources are under `paper/`:

- `NATURE_SUBMISSION_PACKAGE.md`
- `NATURE_MANUSCRIPT_DRAFT_V2.md`
- `REFERENCE_SOURCE_AUDIT.md`

The remaining substantive manuscript task is figure completion and integration, not new outcome-bearing analysis. See `docs/5_CURRENT_ROADMAP.md` for the exact stopping rules.

## Repository organization

- `docs/`: scientific protocols, final results summaries, experiment ledger and roadmap
- `scripts/`: executable analysis/audit/figure workflows
- `paper/`: manuscript source and submission-facing documentation
- `outputs/`: local/RunRelay derived outputs; raw sensitive data and large outputs must not be committed
- `.runrelay/project.yaml`: authoritative RunRelay named-task manifest
- `AGENTS.md`: repository-specific execution and safety rules

## Reproducible execution

NeuroSem uses RunRelay for workstation execution with exact commits and fixed machine binding.

- project id: `neurosem`
- bound machine: `pshjl4vf24`
- approval default: manual
- arbitrary commands: disabled

Raw neural datasets, restricted data, model checkpoints, credentials and `.env` files must not be committed. Safe derived artifacts only should be transported through RunRelay/Google Drive.

## Current stopping rules

- No new dataset search for positive transfer.
- No reopening of ZuCo or SMN4Lang fMRI model/representation choices.
- No rescue search for TMNRED or Garnett.
- No E5 evaluation on failed SMN4Lang MEG targets.
- No further MEG bands, sensor subsets, source models, latencies or temporal alternatives for this paper.
- No additional AHBA significance search or molecular-panel screening.
- Preserve all nulls and failed reliability gates in the manuscript record.
