# NeuroSem: current project brief for Abbas

**Updated:** 2026-08-25

This brief is a collaborator-facing summary of what NeuroSem has done so far, what the results mean, and what remains unresolved. For the complete repository trail, read the numbered documents:

1. [`1_PROJECT_OVERVIEW.md`](1_PROJECT_OVERVIEW.md)
2. [`2_DATASETS_AND_TASKS.md`](2_DATASETS_AND_TASKS.md)
3. [`3_RESULTS_AND_COMPARISONS.md`](3_RESULTS_AND_COMPARISONS.md)
4. [`4_EXPERIMENT_LEDGER.md`](4_EXPERIMENT_LEDGER.md)

## Core idea

We are testing whether the relationships among linguistic items measured in human EEG form a reproducible geometry, whether that geometry contains information beyond ordinary nuisance structure, and whether that neural geometry can provide useful supervision for language models.

The project now separates three claims:

1. Does reproducible neural language geometry exist?
2. Can neural-guided training move a language model toward the development EEG geometry?
3. Does that change transfer to independent semantic tasks or independent EEG datasets?

The results currently support claims 1 and 2 more strongly than claim 3.

## What we did in ChineseEEG

### Task

Participants silently read Chinese text while EEG and eye tracking were recorded. The analyses so far have centered on *The Little Prince*.

ChineseEEG also contains *Garnett Dream*. We now consider this an important different-text replication that should be analyzed with the Little Prince pipeline frozen prospectively.

### EEG representation

The initial flattened sensor-time representation was not sufficiently reliable across subjects. We therefore selected a simpler representation based on neural reliability before semantic testing.

For each linguistic item, we average EEG across time separately within every electrode. If there are 128 channels, one item becomes a 128-dimensional vector. We then compute pairwise distances between item vectors to obtain the EEG representational geometry.

For this selected mean representation:

- raw leave-one-subject-out reliability was approximately 0.220;
- residual reliability after nuisance control was approximately 0.121;
- the residual reliability was above the circular-shift null.

### BERT correspondence

Across Little Prince runs 01-06, the final-layer BERT residual neural-semantic effect was positive in all six runs.

- mean run effect: 0.0085;
- exact run-level sign-flip p = 0.015625;
- common-subject aggregate positive in 8/9 participants;
- exact subject-level sign-flip p = 0.0391.

The effect is small, but its direction is consistent across narrative runs.

## What happened when we trained BERT with neural supervision

We compared four matched arms:

- pretrained base;
- text-only tuning;
- neural-guided tuning;
- shuffled-neural control.

Run-07 remained sealed until final evaluation.

### Seed 1 run-07 mean partial-Spearman

- base: 0.0319
- text-only: 0.0354
- neural-guided: **0.0371**
- shuffled-neural: 0.0353

### Seed 2

- base: 0.0319
- text-only: 0.0341
- neural-guided: **0.0375**
- shuffled-neural: 0.0338

So the neural-guided arm improved held-out alignment to ChineseEEG neural geometry in two seeds.

## Did that improve generic semantics?

Not robustly.

On the frozen eight-task external semantic benchmark, seed 1 produced almost identical text-only and neural-guided performance:

- base 0.283464
- text-only 0.308486
- neural-guided 0.308575
- shuffled-neural 0.307943

Seed 2 went against a brain-specific benefit:

- base 0.283464
- text-only 0.305020
- neural-guided 0.301607
- shuffled-neural 0.305266

This is an important result. Improving neural alignment is not the same as improving generic semantic performance.

## Independent architecture: multilingual E5

We repeated the central tuning question using multilingual E5 so that the result did not depend only on Chinese BERT.

E5 reproduced the qualitative finding that neural-guided optimization can move an independent architecture toward the ChineseEEG neural target. We then explored neural-loss dose-response/Pareto behavior.

The key conclusion is architectural replication of the neural-target alignment phenomenon, not evidence that neural supervision broadly improves semantic benchmarks.

## TMNRED: independent Chinese-reading validation

TMNRED is important because it is another reading task rather than imagined speech.

We first performed a long sequence of model-blind audits, materialization probes, event checks, and cohort/item freezes before looking at EEG reliability.

The final frozen cohort contains:

- 29 participants;
- eight sessions;
- all 50 high-coverage sentence items in each session under the prospective >=80% participant-coverage rule.

### EEG-only reliability

The prospectively selected ChineseEEG-style mean representation replicated weakly but positively:

- residual LOO reliability = **0.00724**;
- bootstrap 95% CI = **[0.00356, 0.01079]**;
- 75.9% of participants positive.

Two secondary representations were more reliable in TMNRED:

- amplitude SD = **0.01820**;
- 8-bin temporal representation = **0.01148**.

This tells us that the neural geometry itself generalizes modestly, but the exact best EEG representation is not invariant across datasets.

## Did the ChineseEEG-trained E5 model transfer to TMNRED?

No detectable advantage.

The frozen primary contrast was neural-guided lambda 0.10 versus matched text-only lambda 0, with no TMNRED tuning.

- mean residual-RSA difference = +0.000020;
- bootstrap 95% CI = [-0.000128, +0.000176];
- one-sided sign-flip p = 0.402;
- 55.2% participants positive.

We then explicitly labeled the follow-up as exploratory and tested the more reliable TMNRED SD and 8-bin representations.

They also did not rescue transfer:

- SD target: delta -0.000294, p = 0.997;
- 8-bin target: delta +0.000041, p = 0.322.

So the TMNRED model-transfer null is not plausibly explained only by our use of temporal mean EEG.

## Nature directional-word dataset

This dataset should now be interpreted differently from TMNRED and ZuCo.

Participants perform overt or covert articulation of six directional concepts. Our primary analysis uses covert/inner speech. This is not the same behavioral task as reading connected language.

Therefore:

- it is useful as an out-of-task mechanistic/generalization test;
- it should not be treated as a task-matched external validation of the reading result;
- a null result there does not directly falsify reading-related EEG geometry.

This point is important for interpreting the total evidence fairly.

## ZuCo 2.0: current work

ZuCo 2.0 Task 1 Normal Reading is our current priority external dataset because participants read English sentences while EEG and eye tracking are recorded.

We deliberately audited structure and timing before looking at any EEG reliability result.

The representative NR1 file is continuous EEG with:

- 105 channels;
- 500 Hz sampling;
- 50 sentences;
- 110 events.

Sentence boundaries map cleanly to 50 ordered pairs:

- 42 use `10 -> 11`;
- 8 use `12 -> 13`;
- `15` is an auxiliary trigger after question-associated sentences;
- `90` and `20` behave as run-level markers.

This gives us a prospective sentence-extraction rule before full-cohort analysis.

The next stage is full 18-participant x 7-run model-blind materialization/QC, followed by a frozen EEG-only reliability test.

## Garnett Dream: newly elevated priority

ChineseEEG contains a second and much larger novel, *Garnett Dream*. We did not use this sufficiently in the first analysis sequence.

This is now important because it allows a clean question:

> Does the Little Prince neural geometry replicate in a different text under the same general acquisition family?

We should freeze the Little Prince representation, nuisance controls, and RSA pipeline before examining Garnett Dream outcomes.

## Current scientific conclusion

The strongest defensible statement today is:

> Reading-related EEG contains a small but reproducible relational geometry. Neural-guided training can improve alignment to the development EEG target, but evidence that this improvement transfers to generic semantic tasks or independent EEG datasets is currently weak or null.

That is more precise than saying that brain supervision improves language-model semantics.

## Current publication logic

We are keeping **Nature Machine Intelligence** as the aspirational first target and **Nature Neuroscience** as the second target, but the final target must follow the evidence.

For an NMI-level machine-learning claim, we would need substantially stronger evidence that neural supervision produces useful transferable model behavior.

For a neuroscience-centered story, the key may instead become reproducible neural language geometry across:

- Little Prince;
- Garnett Dream;
- independent Chinese reading in TMNRED;
- independent English reading in ZuCo.

That evidence chain is now the priority.
