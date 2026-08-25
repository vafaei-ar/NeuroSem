# TMNRED primary EEG representation freeze v1

Status: frozen after the model-blind input/cohort job `NEUROSEM-TMNRED-INPUTS-0006` passed, and before any TMNRED EEG representation reliability values were inspected.

## Frozen cohort and item rule

- Dataset: OpenNeuro ds005383, published snapshot 1.0.0.
- Signal source: published artifact-rejected epoched EEGLAB `z.set` derivative.
- Ready cohort: 29 participants, all except `sub-25`.
- `sub-25` is excluded because session 6 retained 29 trials, below the prospectively frozen 30-trial minimum.
- `sub-23` is retained. Its 500-Hz sessions are deterministically resampled to 200 Hz during feature extraction.
- Within each session, the primary item core is defined model-blind as items retained by at least 80% of the 29 ready participants. The input freeze shows all 50 sentence items satisfy this rule in every session.
- Each held-out participant must contribute at least 20 frozen core items per session.
- For each RDM edge in a held-out-participant LOO comparison, the reference edge must be supported by at least 18 of the remaining 28 participants. This threshold follows from the frozen high-coverage item rule and is fixed before signal outcomes.

## Frozen primary signal representation

The primary external replication endpoint is the ChineseEEG-selected representation: all-sensor temporal mean amplitude.

For TMNRED:

- use the post-onset interval 0.0 to <2.0 s from each artifact-rejected epoch;
- harmonize to 200 Hz before feature extraction;
- for each sentence trial, average amplitude over time separately for each of the 30 EEG channels, yielding a 30-dimensional feature vector;
- feature-wise z-score across retained items within participant x session;
- construct a correlation-distance RDM.

The 0-2 s interval is fixed before reliability outcomes. It excludes the prestimulus baseline and uses the common stimulus-period interval supported by the published epochs.

## Frozen sensitivity representations for the first replication run

The first primary replication run also computes two already-prespecified amplitude controls without using them to redefine the primary endpoint:

1. amplitude standard deviation over the same 0-2 s interval, one feature per channel;
2. eight-bin coarse time-resolved mean amplitude over the same 0-2 s interval, concatenating 8 temporal bins x 30 channels.

Spatial masks, spectral power, and phase members of the broader frozen cross-dataset panel remain planned for a subsequent model-blind panel run. They are not used to change the result of the designated primary TMNRED endpoint.

## Frozen reliability estimator

Primary metric: nuisance-residualized leave-one-subject-out RDM Spearman reliability.

For each participant x session:

1. retain RDM edges defined for the held-out participant and supported by at least 18 reference participants;
2. average the available RDM value for each edge across the other participants;
3. residualize both held-out and reference edge vectors against the same frozen nuisance matrix;
4. compute Spearman correlation between the two residualized vectors.

Participant-level reliability is the Fisher-z mean across the eight session-level correlations. Group reporting includes the mean and median participant-level reliability, fraction positive, subject-bootstrap 95% CI, raw LOO reliability, and raw/residual pairwise reliability.

## Frozen nuisance definitions

Within each 50-item session/block, nuisance RDMs are:

- absolute trial-position difference;
- CJK ideograph-count difference in the published Chinese sentence;
- Unicode punctuation-count difference;
- CJK character-set Jaccard distance.

No language-model embeddings or semantic embedding nuisance RDMs are used.

## Guardrails

- No TMNRED language-model embeddings are loaded in this run.
- No representation or time-window selection is performed from TMNRED outcomes.
- The designated replication question is whether `row_mean_all`, selected independently in ChineseEEG, has positive reproducible residual geometry in TMNRED.
- Sensitivity candidates are descriptive controls in this first run and cannot replace the primary endpoint based on their TMNRED result.
