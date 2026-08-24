# EEG representation refinement plan v1

Status: exploratory/mechanistic plan motivated by collaborator feedback after the first project report.

## Motivation

The current NeuroSem neural target uses a simple row-level mean EEG representation. This was useful because it was reproducible and easy to align to natural-reading presentation units, but it collapses potentially important spatial and temporal structure.

Two collaborator suggestions are scientifically important:

1. Reduce contribution from EEG activity more likely to reflect ocular, motor, or other non-semantic processes rather than treating every sensor equally.
2. Test richer signal representations, especially time-resolved and oscillatory information such as phase, rather than relying only on a mean-amplitude summary.

These suggestions must not be used to retroactively rescue the prospective Nature null result. The Nature result remains the primary result under its frozen protocol. Any reanalysis of Nature with new features is exploratory only.

## Key scientific caution

Scalp electrodes are not clean labels for cortical function. We therefore will not call individual electrodes "semantic electrodes" or remove sensors simply because they sit over motor cortex. Volume conduction, referencing, eye movements, and distributed language networks make that interpretation too strong.

Instead, spatial filtering will be defined by one of the following before model comparison:
- artifact removal already present in the published preprocessing;
- prespecified scalp regions motivated by language/ERP literature;
- EEG-only reliability or semantic-task criteria that do not use model alignment;
- component-level filtering when component provenance is available.

## Feature families

The baseline remains the existing full-sensor row mean.

Candidate families for exploratory comparison are:

### 1. Time-resolved ERP features

Preserve post-stimulus timing rather than averaging the full row. Candidate windows include broad early, N400-range, and late windows, with exact windows frozen before model comparison after inspecting event timing and available derivatives.

Primary rationale: semantic processing is often expressed in temporally localized evoked responses, and full-row averaging can cancel or dilute these effects.

### 2. Spatially restricted or component-cleaned amplitude features

Compare the full 128-channel representation with prespecified centro-parietal/temporal language-relevant sensor groups and with artifact-cleaned/component-based representations when the distributed derivatives allow it.

Selection must not use neural-model RSA.

### 3. Spectral power features

Evaluate log power in canonical low-frequency bands supported by the available sampling/filtering, initially theta, alpha, and beta. Low gamma may be evaluated only when the 0.5-80 Hz derivative and artifact quality are adequate.

### 4. Phase-sensitive features

Evaluate phase-derived representations only when the event alignment and number of samples per analysis unit make the statistic identifiable and stable. Candidate summaries include instantaneous phase-derived features, phase consistency/locking measures, or phase relationships across sensors. We will not force ITPC/PLV when the trial structure does not support repeated-event estimation.

## Selection rule

This is a representation-development stage, not a model-selection stage.

Candidate neural representations will first be judged using EEG-only properties:
- cross-subject or split-half reliability;
- stability across runs;
- sensitivity to known nuisance variables;
- dependence on eye movement or timing structure;
- robustness to reasonable preprocessing sensitivity analyses.

Model embeddings are not used to choose the winning EEG representation.

## Dataset sequence

1. ChineseEEG is used for exploratory representation development because it has rich natural language, 128-channel EEG, eye tracking, and existing row-level alignment.
2. ChineseEEG-2 is the preferred bridge replication for the refined representation because it changes task/modality and participant group while remaining close enough to make engineering feasible.
3. ZuCo should remain a high-value independent natural-reading validation target after the representation is frozen.

The existing Nature directional-word result remains unchanged and is not redefined as confirmatory evidence under any new representation.

## Immediate next step

Before implementing phase/time-frequency extraction, audit the local ChineseEEG checkout and outputs to determine which time-resolved EEG derivatives, event files, eye-tracking files, ICA/component information, and previously materialized runs are already available on the workstation. Do not download the entire approximately 748 GB annexed dataset.

The audit is model-blind and should produce only a compact inventory. Based on that inventory we will choose the smallest feasible set of files required for a first representation benchmark.

## Interpretation guardrails

- A feature that improves EEG reliability is not automatically more semantic.
- A feature that improves model alignment on already-seen data is exploratory.
- A spatial restriction should be described as artifact-control or language-relevant weighting, not proof of localization.
- Phase features are only meaningful when the statistic is supported by the event/trial structure.
- Any final claim that the refined representation captures transferable semantic neural geometry requires a fresh external neural validation target.
