# 4. Experiment Ledger

**Last updated:** 2026-08-25

This is the chronological audit trail for major NeuroSem analyses. It records what was run, why it was run, whether it was confirmatory or exploratory, and what changed afterward. It is not a replacement for the detailed protocol files or raw RunRelay results.

## How to use this ledger

- **Confirmatory / frozen** means the key analysis choices were fixed before inspecting the target outcome.
- **Exploratory** means the analysis was motivated by earlier results and should not be promoted to primary evidence without independent replication.
- Failed jobs are retained when they changed the workflow or exposed a data/engineering constraint.
- Exact code/configuration should be recovered from the NeuroSem commit associated with the RunRelay job.
- Safe derived artifacts are transported through Google Drive. Raw/restricted neural data are not GitHub artifacts.

## Phase A. ChineseEEG discovery and BERT tuning

### Discovery representation work

The early flattened sensor-time EEG representation had weak cross-subject reliability. A simpler temporal mean within each channel was selected on neural reliability before semantic testing.

The selected representation produced approximately 0.220 raw LOO reliability and approximately 0.121 after nuisance control, with residual reliability above the circular-shift null.

### BERT semantic RSA, Little Prince runs 01-06

Purpose: test whether BERT geometry shows residual correspondence with reproducible EEG geometry after nuisance control.

Result: positive effect in 6/6 runs; mean run effect 0.0085; exact run-level sign-flip p=0.015625.

### BERT neural-guided tuning, seed 1

Four arms: base, text-only, neural-guided, shuffled-neural.

Run-07 mean partial-Spearman:

- base 0.0319;
- text-only 0.0354;
- neural-guided 0.0371;
- shuffled-neural 0.0353.

Result: neural-guided arm strongest on sealed run-07 neural holdout.

### BERT external semantic benchmark, seed 1

Eight-task mean Spearman:

- base 0.283464;
- text-only 0.308486;
- neural-guided 0.308575;
- shuffled-neural 0.307943.

Result: essentially no meaningful neural-specific semantic gain.

### BERT tuning, seed 2 replication

Run-07 mean partial-Spearman:

- base 0.0319;
- text-only 0.0341;
- neural-guided 0.0375;
- shuffled-neural 0.0338.

External semantic benchmark:

- base 0.283464;
- text-only 0.305020;
- neural-guided 0.301607;
- shuffled-neural 0.305266.

Result: neural holdout advantage reproduced; external semantic advantage did not.

## Phase B. Independent architecture replication with multilingual E5

### `NEUROSEM-E5-REP-0001`

Status: failed/malformed control job.

Reason: `requested_machine_id` was null. This job must not be reused as evidence or as a template.

Workflow lesson: every NeuroSem RunRelay job must explicitly request `pshjl4vf24`, and the saved job file must be read back and verified before claiming it is queued.

### `NEUROSEM-E5-REP-0002`

Status: failed.

Role: infrastructure/debugging only.

### `NEUROSEM-E5-REP-0003`

Status: completed.

Purpose: independent-architecture replication of neural-guided tuning with multilingual E5.

Scientific result: the qualitative ChineseEEG neural-target alignment effect reproduced in a second architecture. This argues against a BERT-specific implementation artifact.

### `NEUROSEM-E5-PARETO-0001`

Status: failed.

Role: exploratory dose-response infrastructure/debugging.

### `NEUROSEM-E5-PARETO-EVAL-0001`

Status: completed.

Artifacts: `combined_summary.json`, `pareto_points.csv`.

Purpose: evaluate already-trained E5 dose-response/Pareto points without retraining.

Interpretation: neural-target alignment and generic semantic performance do not simply improve together. Treat the Pareto work as exploratory.

## Phase C. Nature directional-word dataset

### `NEUROSEM-NATURE-DL-0001`

Status: completed.

Purpose: download/checksum the public Scientific Data directional-word EEG dataset.

### `NEUROSEM-NATURE-AUDIT-0001`

Status: completed.

Purpose: model-blind structural audit.

Artifacts: subject inventory and summary.

### `NEUROSEM-NATURE-PROBE-0001`

Status: completed.

Purpose: inspect event labels/structure before model comparison.

### Subsequent Nature validation analyses

Purpose: test directional-concept neural/model alignment, with covert/inner speech as the primary condition.

Interpretation: no convincing transfer evidence. This dataset is now classified as out-of-task because covert articulation is not equivalent to natural reading.

## Phase D. ChineseEEG representation refinement

### `NEUROSEM-EEGREP-AUDIT-0001`

Status: completed.

Purpose: audit locally available time-resolved/spectral/phase inputs before representation refinement.

### `NEUROSEM-EEGREP-OVERNIGHT-0001`

Status: completed unusually quickly.

Interpretation: the run did not exercise all intended signal-processing families. It should not be treated as a completed representation benchmark.

### `NEUROSEM-EEGREP-SPECTRALPHASE-0001`

Status: completed.

Purpose: execute fuller spectral/phase candidate pipeline.

### `NEUROSEM-EEGREP-SPECTRALPHASE-0002`

Status: failed.

### `NEUROSEM-EEGREP-SPECTRALPHASE-0003`

Status: failed rapidly because required subject assets were `NOT TRACKED` in the dataset index.

Important workflow lesson: `NOT TRACKED` is a dataset-availability condition, not something `git annex get` can repair.

### `NEUROSEM-EEGREP-SPECTRALPHASE-0004`

Status: failed.

Scientific/workflow correction: freeze the common **tracked and materializable** subject intersection across every required derivative combination before comparing representations.

### `NEUROSEM-EEGREP-SPECTRALPHASE-0005`

Status: failed after longer execution.

Interpretation: representation refinement exposed dataset-availability and execution complexity. Mean remained the established primary representation; richer families remain sensitivity/exploratory unless prospectively validated elsewhere.

## Phase E. TMNRED independent Chinese-reading replication

### `NEUROSEM-TMNRED-DOWNLOAD-0001`

Status: completed.

Purpose: create pinned OpenNeuro/DataLad checkout without recursively materializing the entire dataset.

### `NEUROSEM-TMNRED-AUDIT-0001`

Status: completed.

Purpose: prospective model-blind structural/materialization audit.

### `NEUROSEM-TMNRED-DOCS-0001`

Status: completed.

Purpose: inspect documentation, sidecars, event schemas, and derivative paths.

### `NEUROSEM-TMNRED-PREPROC-PROBE-0001`

Status: completed.

Purpose: inspect one representative preprocessed EEGLAB file set before freezing signal-level analysis.

### `NEUROSEM-TMNRED-EVENT-ALIGN-0001`

Status: completed.

Purpose: establish event/trial identity mapping.

### `NEUROSEM-TMNRED-STIMULUS-META-0001`

Status: completed.

Purpose: inspect source-material metadata and freeze semantic analysis units.

### `NEUROSEM-TMNRED-INPUTS-0001`

Status: failed.

### `NEUROSEM-TMNRED-MATERIALIZATION-PROBE-0001`

Status: completed.

Purpose: diagnose file-format/materialization failure modes.

### `NEUROSEM-TMNRED-INPUTS-0002`

Status: failed.

### `NEUROSEM-TMNRED-INPUTS-0003`

Status: completed.

Key cohort result: 29 participants structurally ready across eight sessions; `sub-25` excluded; `sub-23` retained with deterministic resampling.

### `NEUROSEM-TMNRED-INPUTS-0004`

Status: failed.

Reason: overly strict complete-case/common-item logic and initial trial-identity extraction issue.

### `NEUROSEM-TMNRED-INPUTS-0005`

Status: failed scientifically rather than technically.

Exact all-29-subject item intersections were too sparse in early sessions: 8, 13, 14, 18, 30, 29, 34, 20 common items across sessions 1-8.

Protocol decision: switch prospectively to an >=80% participant-coverage item rule rather than lowering the complete-case minimum opportunistically.

### `NEUROSEM-TMNRED-INPUTS-0006`

Status: completed.

Frozen cohort/item result:

- 29 participants;
- eight sessions;
- all 50 sentence items retained in every session under >=80% coverage.

This is the input freeze for subsequent TMNRED analyses.

### `NEUROSEM-TMNRED-PRIMARY-RELIABILITY-0001`

Status: completed.

Type: frozen/model-blind EEG-only replication.

Key results:

- `row_mean_all`: residual LOO 0.00724, 95% CI [0.00356, 0.01079], 75.9% positive participants;
- `row_std_all`: residual LOO 0.01820, 89.7% positive participants;
- `relative_8bin_all`: residual LOO 0.01148.

Interpretation: mean geometry independently replicates weakly; SD is more reliable in TMNRED but is secondary.

### `NEUROSEM-TMNRED-E5-TRANSFER-0001`

Status: completed.

Type: frozen confirmatory external model-transfer test.

Primary contrast: E5 neural-guided lambda 0.10 vs text-only lambda 0, no TMNRED tuning.

Result:

- mean residual-RSA difference +0.000020;
- 95% CI [-0.000128, +0.000176];
- one-sided sign-flip p=0.402;
- 55.2% positive participants.

Interpretation: null transfer.

### `NEUROSEM-TMNRED-E5-ALTREP-0001`

Status: completed.

Type: explicitly exploratory post-confirmatory analysis.

Results:

- SD target: delta -0.000294, 95% CI [-0.000479, -0.000107], p=0.997;
- 8-bin target: delta +0.000041, 95% CI [-0.000111, +0.000207], p=0.322.

Interpretation: alternative TMNRED representations do not rescue lambda-0.10 transfer.

## Phase F. ZuCo 2.0 independent English-reading replication

### `NEUROSEM-ZUCO-OSF-INVENTORY-0001`

Status: completed.

Purpose: model-blind inventory of ZuCo 1.0 and 2.0 before large downloads.

Decision: prioritize **ZuCo 2.0 Task 1 Normal Reading** because the public inventory provides 18 participants with seven NR EEG runs each and a stronger cohort than ZuCo 1.0 for the intended test.

### `NEUROSEM-ZUCO2-NR-FORMAT-0001`

Status: failed.

Reason: initial MATLAB-format handling assumption.

### `NEUROSEM-ZUCO2-NR-FORMAT-0002`

Status: failed rapidly.

Reason: HDF5/MATLAB v7.3 support required `h5py`, which was not yet installed in the project environment.

### `NEUROSEM-ZUCO2-SETUP-H5PY-0001`

Status: completed.

Purpose: refresh project environment with `h5py` support.

### `NEUROSEM-ZUCO2-NR-FORMAT-0003`

Status: completed.

Key result: seven NR runs contain 349 sentence units in total; representative EEG is MATLAB v7.3/HDF5.

### `NEUROSEM-ZUCO2-NR-FORMAT-0004`

Status: completed.

Key result: representative YDG NR1 EEG is continuous, not epoched: 105 channels, 500 Hz, 198,585 time points, 110 events.

### `NEUROSEM-ZUCO2-NR-FORMAT-0005`

Status: completed on the same code state as the later resend. Operationally duplicated because completion was not initially visible in the interactive status path.

### `NEUROSEM-ZUCO2-NR-FORMAT-0006`

Status: completed; harmless duplicate/resend.

Key event-mapping result for YDG NR1:

- 110 events total;
- 100 core sentence events = 50 ordered sentence pairs;
- 42 pairs use `10 -> 11`;
- 8 pairs use `12 -> 13`;
- trigger `15` is auxiliary after question-associated sentences;
- `90` and `20` behave as run-level start/end markers.

Conclusion: sentence identity can be prospectively defined by run + sentence order, with windows delimited by the two allowed start/end trigger pairs.

### Current ZuCo next stage

Full 18-participant x 7-run materialization/QC is the next model-blind step. No ZuCo EEG reliability or model-transfer result exists yet.

## Phase G. ChineseEEG Garnett Dream

Status: not yet incorporated into the core analysis pipeline.

Reason for prioritization now: it provides a different-text replication using the same general ChineseEEG acquisition family and should be exploited before broad publication claims.

Recommended design: freeze the Little Prince representation/nuisance/RSA pipeline prospectively, then evaluate Garnett Dream without using its outcome to choose the representation.

## Current evidence summary

| Question | Current answer |
|---|---|
| Is there reproducible reading-related EEG geometry? | **Yes, modestly supported.** ChineseEEG strong within-dataset evidence; TMNRED independent positive reliability. |
| Does neural-guided training improve held-out alignment to the development EEG target? | **Yes.** BERT reproduced across two seeds; E5 qualitative architecture replication. |
| Does that improvement robustly improve generic semantic benchmarks? | **No evidence so far.** BERT external benchmark unstable; E5 Pareto work does not show simple joint improvement. |
| Does the ChineseEEG-trained neural advantage transfer to independent TMNRED EEG? | **No.** Frozen primary test null; alternative EEG summaries do not rescue it. |
| Does the Nature directional result directly test the reading hypothesis? | **No.** It is covert/inner speech and should be treated as out-of-task. |
| Is cross-language reading geometry established? | **Not yet.** ZuCo is the key next test. |
| Has different-text replication within ChineseEEG been completed? | **Not yet.** Garnett Dream is a priority. |
