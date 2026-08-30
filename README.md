# NeuroSem

**NeuroSem** studies whether reproducible human neural representational geometry can constrain language-model learning in a way that transfers to independent neural measurements.

The project is in an **evidence-locked manuscript-consolidation phase** for the primary paper. The original prospective evidential chain remains unchanged, while several secondary/post-confirmatory robustness and generalization analyses are now also complete.

## Read the documentation in this order

1. [`docs/1_PROJECT_OVERVIEW.md`](docs/1_PROJECT_OVERVIEW.md) - scientific overview and claim boundaries.
2. [`docs/3_RESULTS_AND_COMPARISONS.md`](docs/3_RESULTS_AND_COMPARISONS.md) - numerical evidence summary.
3. [`docs/5_CURRENT_ROADMAP.md`](docs/5_CURRENT_ROADMAP.md) - current manuscript strategy and stopping rules.
4. [`docs/23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`](docs/23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md) - completed six-model x three-seed x two-direction explanatory model-family panel.
5. [`docs/24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`](docs/24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md) - completed fMRI-to-ChineseEEG multi-seed dose robustness analysis.
6. [`docs/4_EXPERIMENT_LEDGER.md`](docs/4_EXPERIMENT_LEDGER.md) - chronological analysis history.
7. [`paper/README.md`](paper/README.md) - manuscript workspace and submission-facing files.

For detailed methods and provenance, use the frozen protocol files under `docs/`, exact RunRelay jobs/commits, and the declared safe artifacts delivered through Google Drive.

## Current evidence in one paragraph

ChineseEEG Little Prince natural reading contains reproducible cross-participant EEG geometry after nuisance control, and neural-guided BERT/E5 training shows learnability. A frozen multilingual-E5 contrast transfers positively to independent ZuCo English natural-reading EEG in **17/17** participants and prospectively to independently defined SMN4Lang language-network fMRI during Mandarin auditory narratives in **12/12** participants. A separately frozen reverse-direction analysis shows that an fMRI-derived relational constraint transfers to independent ZuCo EEG, establishing bidirectional cross-modal transfer within multilingual E5. Post-confirmatory architecture work further shows that this bidirectional pattern is reproducible across **multilingual E5-large and multilingual E5-base** over three optimization seeds, but not uniformly across MPNet, MiniLM, XLM-R or mBERT. Transfer is therefore selective rather than universal. TMNRED and Garnett Dream remain null/inconclusive boundaries; directional inner speech is an out-of-task boundary. In SMN4Lang MEG, the frozen sensor-level target failed its model-blind reliability gate, so no model-transfer test was performed.

## Major results at a glance

| Dataset / test | Role | Current result |
|---|---|---|
| ChineseEEG Little Prince | Development target and learnability | residual LOO ~**0.121**; sealed neural-guided BERT strongest in both development seeds |
| ZuCo 2.0 Task 1 NR | Independent English reading EEG | reliability **0.06742**; original E5 delta **+0.0016637**; **17/17** positive |
| SMN4Lang fMRI | Prospective cross-modal capstone | reliability **0.65327**; original E5 delta **+0.00085250**; **12/12** positive |
| fMRI -> ZuCo E5 reverse transfer | Post-confirmatory bidirectionality | frozen lambda=.01 mean delta **+0.00001671**, **14/17** positive, one-sided p **0.0001068**; larger frozen lambdas show a strong post-confirmatory dose-response on ZuCo |
| fMRI -> ChineseEEG run-07 | Secondary consistency | lambda=.01 direction positive but inconclusive; multi-seed robustness shows lambda=1 positive in **3/3** added seeds but participant-level uncertainty remains |
| Six-model bidirectional family panel | Post-confirmatory explanatory architecture analysis | both **E5-large and E5-base** positive in all 3 seeds in both directions; other model classes do not reproduce stable bidirectional transfer |
| TMNRED | Transfer boundary | weak positive reliability; E5 transfer null, p=.402 |
| Garnett Dream | Same-participant/new-text boundary | reliability positive; E5 transfer null/inconclusive, p=.1016 |
| Directional inner speech | Out-of-task boundary | no positive transfer; delta ~**-0.001786** |
| SMN4Lang MEG | Reliability boundary | 32-bin mean LOO **0.007713**, CI crosses zero, p=.1687; no model evaluation |
| AHBA | Secondary mechanistic extension | primary molecular tests null; exploratory hemispheric sensitivity only |

Raw RSA values across EEG, fMRI and MEG are not directly comparable as a common effect-size scale.

## Primary manuscript claim

> Human neural geometry can provide a transferable relational constraint on language representations, with effects that generalize across independent brains, languages and measurement modalities, but not universally across neural contexts.

The new post-confirmatory evidence permits a more specific secondary architecture statement:

> Bidirectional external neural transfer is reproducible across the two tested multilingual E5 variants under a common relational-adaptation protocol, but is not a universal property of multilingual encoders.

This should **not** be expanded into claims that brain supervision generally improves language models, that E5 is uniquely capable among all possible model families, that SMN4Lang isolates pure semantics, that MEG showed negative transfer, or that a specific transcriptomic mechanism has been identified.

## Key post-confirmatory completed analyses

### Optimization-seed robustness within E5

Additional multilingual-E5 seeds confirm that the original external transfer is not a single lucky optimization trajectory. The reverse fMRI-to-ChineseEEG dose analysis is more nuanced: low/intermediate lambda effects are seed-heterogeneous, while lambda=1.0 is positive in all three added seeds. See [`docs/24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`](docs/24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md).

### Bidirectional model-family panel

A frozen common protocol evaluated six models, three seeds and two neural-source directions. EEG-derived constraints transfer broadly across several multilingual encoders. In contrast, stable fMRI-derived transfer to ZuCo EEG is reproducible only in both tested E5 variants. See [`docs/23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`](docs/23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md).

## Repository organization

- `docs/`: scientific protocols, results summaries, experiment ledger and roadmap
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

- Preserve the original prospective ChineseEEG -> ZuCo -> SMN4Lang evidential chain unchanged.
- Treat all bidirectional, dose-response and model-family analyses as secondary/post-confirmatory.
- Do not choose a new lambda from EEG target outcomes and retroactively promote it to confirmatory status.
- Do not rescue non-E5 model families through model-specific lambda/layer/pooling searches after the completed common-protocol panel.
- No new dataset search for positive transfer within the current primary paper.
- No reopening of ZuCo or SMN4Lang fMRI target-side model/representation choices.
- No rescue search for TMNRED or Garnett.
- No E5 evaluation on failed SMN4Lang MEG targets.
- No further MEG bands, sensor subsets, source models, latencies or temporal alternatives for this paper.
- No additional AHBA significance search or molecular-panel screening.
- Preserve all nulls, heterogeneous seeds and failed reliability gates in the manuscript record.
