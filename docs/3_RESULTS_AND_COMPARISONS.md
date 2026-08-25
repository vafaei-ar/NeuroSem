# 3. Results and Comparisons

**Last updated:** 2026-08-25

This file is the current numerical results summary for NeuroSem. It separates EEG reliability, neural-model correspondence, model tuning, external semantic benchmarks, and independent EEG transfer. It should be updated whenever a result changes the scientific interpretation.

## 3.1 ChineseEEG neural geometry and BERT correspondence

The initial flattened sensor-time representation had weak cross-subject reliability. A simpler whole-row temporal-mean representation was selected based on neural reliability before semantic testing.

For the selected row-mean representation:

- raw leave-one-subject-out cross-subject reliability: approximately **0.220**;
- after nuisance control: approximately **0.121**;
- residual reliability above circular-shift null: approximately **p = 0.001**.

Held-out Little Prince runs 01-06 showed small but consistently positive BERT final-layer residual neural-semantic correspondence:

| Run | Mean partial-Spearman | Run permutation p |
|---|---:|---:|
| 01 | 0.0057 | 0.051 |
| 02 | 0.0034 | 0.083 |
| 03 | 0.0145 | 0.00060 |
| 04 | 0.0045 | 0.110 |
| 05 | 0.0174 | 0.040 |
| 06 | 0.0056 | 0.083 |

Cross-run summary:

- positive primary effect in **6/6** runs;
- mean run effect = **0.0085**;
- exact one-sided run-level sign-flip **p = 0.015625**;
- common-subject aggregate positive in **8/9** subjects;
- exact subject-level sign-flip **p = 0.0391**;
- every leave-one-run-out aggregate remained positive.

Interpretation: the effect is small, but the direction is unusually consistent across narrative runs.

## 3.2 BERT neural-guided tuning: run-07 holdout

Four arms were compared:

- base pretrained BERT;
- text-only LoRA tuning;
- neural-guided LoRA tuning;
- shuffled-neural control.

### Seed 1

Run-07 mean partial-Spearman:

| Arm | Mean |
|---|---:|
| Base | 0.0319 |
| Text-only | 0.0354 |
| Neural-guided | **0.0371** |
| Shuffled-neural | 0.0353 |

The neural-guided arm was the strongest of the four on this sealed neural holdout.

### Seed 2

Run-07 mean partial-Spearman:

| Arm | Mean |
|---|---:|
| Base | 0.0319 |
| Text-only | 0.0341 |
| Neural-guided | **0.0375** |
| Shuffled-neural | 0.0338 |

The same qualitative ordering reproduced in seed 2.

Interpretation: brain-guided training can improve alignment to held-out ChineseEEG neural geometry relative to matched text-only and shuffled-neural controls. This supports a within-dataset learning effect, not yet transfer.

## 3.3 BERT external semantic benchmark

Frozen eight-task external semantic benchmark:

| Arm | Mean Spearman across 8 tasks |
|---|---:|
| Base | 0.283464 |
| Text-only | 0.308486 |
| Neural-guided | **0.308575** |
| Shuffled-neural | 0.307943 |

Primary deltas:

- neural - text-only = **+0.000089**;
- neural - shuffled-neural = **+0.000632**;
- neural - base = **+0.025111**;
- neural wins vs text-only on **5/8** tasks;
- neural wins vs shuffled-neural on **6/8** tasks.

Seed 2 did not reproduce a neural advantage:

| Arm | Mean Spearman across 8 tasks |
|---|---:|
| Base | 0.283464 |
| Text-only | **0.305020** |
| Neural-guided | 0.301607 |
| Shuffled-neural | **0.305266** |

Seed-2 deltas:

- neural - text-only = **-0.003413**;
- neural - shuffled-neural = **-0.003659**;
- neural - base = **+0.018143**;
- neural wins vs text-only on **1/8** tasks;
- neural wins vs shuffled-neural on **1/8** tasks.

Interpretation: the external semantic advantage is not stable across seeds. Neural-guided tuning improves over the pretrained baseline largely because tuning itself helps, but the brain-specific component does not show a robust generic semantic benefit.

## 3.4 Multilingual-E5 replication

An independent multilingual-E5 architecture was used to test whether the ChineseEEG neural-guided effect was specific to BERT.

The E5 program reproduced the key qualitative result that neural-guided optimization can move an independent architecture toward the ChineseEEG neural target. The subsequent Pareto/dose-response work showed that neural alignment and generic semantic performance can trade off rather than improve together.

The important scientific conclusion is therefore architectural replication of the **neural-target alignment phenomenon**, not evidence of broad semantic improvement.

For exact E5 numerical summaries, use the derived outputs produced by the `run_e5_replication`, `collect_e5_results`, `run_e5_pareto_exploratory`, and `evaluate_e5_pareto_existing` tasks. This status file intentionally does not invent values that are not currently duplicated in repository documentation.

## 3.5 TMNRED EEG-only independent replication

Frozen cohort:

- 29 participants;
- eight sessions;
- 50 high-coverage sentence items retained in every session under the prospective >=80% participant-coverage rule.

Primary and sensitivity EEG representations:

| Representation | Mean residual LOO reliability | Positive participants | Interpretation |
|---|---:|---:|---|
| `row_mean_all` | **0.00724** | 75.9% | Prospectively designated primary representation replicates weakly but positively |
| `row_std_all` | **0.01820** | 89.7% | Stronger secondary reliability in TMNRED |
| `relative_8bin_all` | **0.01148** | not primary | Secondary temporal representation also reliable |

For `row_mean_all`, bootstrap 95% CI = **[0.00356, 0.01079]**.

Interpretation: the ChineseEEG-selected mean representation generalizes modestly to an independent Chinese reading dataset. The exact representation ranking is not invariant across datasets because SD was more reliable in TMNRED.

## 3.6 TMNRED frozen E5 transfer

Primary contrast: ChineseEEG-trained neural-guided E5 at lambda 0.10 versus matched text-only lambda 0, evaluated on prospectively designated TMNRED `row_mean_all` geometry with no TMNRED tuning.

Results:

- mean residual-RSA difference = **+0.000020**;
- median difference = **+0.000053**;
- positive participants = **55.2%**;
- bootstrap 95% CI = **[-0.000128, +0.000176]**;
- one-sided sign-flip **p = 0.402**.

Raw-RSA comparison was also null, with approximately **p = 0.416**.

Interpretation: the neural-guided E5 advantage learned in ChineseEEG did not transfer detectably to independent TMNRED mean-EEG geometry.

## 3.7 TMNRED alternative EEG representations

Exploratory post-confirmatory tests asked whether the transfer null was caused only by the choice of mean EEG target.

### `row_std_all`

- mean residual-RSA difference, lambda 0.10 - lambda 0 = **-0.000294**;
- bootstrap 95% CI = **[-0.000479, -0.000107]**;
- one-sided sign-flip **p = 0.997**;
- positive participants = **31.0%**.

This goes slightly in the wrong direction.

### `relative_8bin_all`

- mean residual-RSA difference = **+0.000041**;
- bootstrap 95% CI = **[-0.000111, +0.000207]**;
- one-sided sign-flip **p = 0.322**;
- positive participants = **51.7%**.

Interpretation: stronger TMNRED EEG reliability did not rescue transfer. The failure is unlikely to be explained only by the temporal-mean target.

## 3.8 Nature directional-word dataset

The directional-word dataset is an out-of-task test because its primary NeuroSem condition is covert/inner speech rather than reading.

The analysis did not provide convincing evidence that the ChineseEEG-trained neural-guided model transfers to this dataset. This result must be interpreted cautiously because the task differs substantially from reading and contains only six directional concepts.

Current role: secondary mechanistic/generalization evidence, not a task-matched external replication.

## 3.9 ZuCo 2.0 status

ZuCo results are **not yet available**. Structural and event-mapping work is complete enough to define sentence extraction prospectively.

Current representative-file facts:

- continuous EEG;
- 105 channels;
- 500 Hz;
- 50 sentences in NR1;
- sentence windows delimitable by ordered event pairs `10 -> 11` or `12 -> 13`;
- full-cohort model-blind QC is the next stage.

No EEG reliability or model-transfer result should be claimed until full-cohort materialization/QC completes.

## 3.10 ChineseEEG Garnett Dream status

No Garnett Dream result has yet been incorporated into the core NeuroSem evidence chain.

This is now a high-priority gap because Garnett Dream offers a strong different-text replication under the same general dataset/acquisition family. Analysis should be frozen from the Little Prince pipeline before looking at Garnett Dream outcomes.

## 3.11 What the results jointly say

The current evidence supports the following hierarchy:

### Claim A: reproducible reading-related EEG geometry exists

**Supported.** Strongest evidence comes from ChineseEEG and independent TMNRED EEG reliability.

### Claim B: brain-guided training can improve alignment to the development EEG target

**Supported within ChineseEEG.** BERT run-07 holdout improvements reproduced across two seeds, and E5 reproduced the qualitative phenomenon.

### Claim C: brain-guided training improves generic semantic representations

**Not supported.** External STS/C-MTEB benefits are unstable and largely indistinguishable from ordinary text-only tuning.

### Claim D: brain-guided training transfers to independent EEG datasets

**Not supported so far.** Frozen TMNRED transfer is null, and alternative TMNRED EEG representations do not rescue it. The Nature directional dataset is also not convincing, but it is a different task.

This separation should govern manuscript wording and all future analysis decisions.
