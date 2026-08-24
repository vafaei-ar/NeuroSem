# ChineseEEG EEG representation overnight benchmark protocol v2

Status: frozen before running the richer EEG representation benchmark.

## Purpose

Use one long RunRelay job with independent sub-analyses to test the collaborator-motivated EEG representation ideas while the workstation is available overnight. This stage is model-blind. No language-model embeddings, adapters, neural-model RSA, or lambda comparisons are loaded.

The goal is to determine whether the current whole-row mean EEG target is unnecessarily discarding reproducible neural structure and whether a richer representation should be frozen for later NeuroSem testing.

## Scientific guardrails

1. The prospective Nature directional-word result remains unchanged. Nothing in this benchmark is a confirmatory reanalysis of Nature.
2. Do not call scalp electrodes semantic or motor electrodes. Scalp sensors mix distributed sources.
3. Spatial variants are treated as artifact-control / broad region-weighting variants, not localization claims.
4. Candidate representations are selected only by EEG-only reproducibility and nuisance robustness.
5. Run 06 is the representation-development run. Run 07 is an EEG-only holdout and must not influence the winner chosen from run 06.
6. Phase features are exploratory feasibility analyses because there are no repeated identical semantic trials in the natural-reading rows. They are not eligible to win the primary representation selection unless a future protocol defines a repeated-event phase statistic.
7. Eye tracking is not used in this overnight benchmark because the model-blind input audit found eye-tracking files are not materialized locally. This is documented, not silently ignored.

## Subjects and rows

Use the already materialized ChineseEEG LittlePrince run-06 and run-07 row-feature outputs and the author preprocessed EEG derivatives. The script will use the largest common set among the prespecified ChineseEEG subjects for which the required feature metadata and signal files are materialized.

Canonical row identity and timing come from the existing row-feature `metadata.csv` files. Structural/chapter-number rows remain excluded exactly as in the existing row-feature pipeline.

## Discovery and holdout sequence

### Stage A: run-06 development

Benchmark all technically available candidate families on run 06 using EEG-only metrics.

Primary selection statistic: nuisance-residualized leave-one-subject-out RDM reliability.

Tie-breakers, in order:
1. raw leave-one-subject-out reliability;
2. nuisance-residualized pairwise reliability;
3. stability of subject-level effects (fraction of subjects with positive LOO reliability).

No model correspondence enters selection.

### Stage B: run-07 locked EEG-only holdout

After the run-06 winner is written to the in-memory/final run state, evaluate that exact representation on run 07 without changing its definition.

After the winner holdout is complete, the script may evaluate the remaining candidates on run 07 as a clearly labeled exploratory panel. Those secondary run-07 results do not alter the frozen run-06 winner.

## Candidate families

### 1. Existing amplitude baselines

- `row_mean_all`: existing whole-row mean voltage across all channels.
- `row_std_all`: existing whole-row voltage standard deviation across all channels.
- `relative_8bin_all`: existing duration-normalized eight-bin mean voltage, flattened across bin x channel. This preserves coarse within-row temporal evolution while retaining every eligible row.

These are primary-selection eligible because they use the same row set.

### 2. Spatial amplitude variants

Using deterministic standard HydroCel-128 sensor coordinates when channel names can be matched:

- `row_mean_nonfrontal`: whole-row mean using sensors outside the most anterior 40% by montage anterior-posterior coordinate.
- `row_mean_posterior`: whole-row mean using the posterior half of sensors by montage anterior-posterior coordinate.
- `row_mean_lateral_posterior`: posterior-half sensors with absolute left-right coordinate at or above the 35th percentile, producing a broad bilateral temporal/parietal-weighted subset.

These definitions are frozen before model comparison and are intended to reduce frontal/ocular or broad non-language contamination. They are not anatomical source-localization claims.

### 3. Spectral-power variants

From the author 0.5-30 Hz derivative, compute channel-wise log relative power within each row for:

- theta: 4-7 Hz;
- alpha: 8-12 Hz;
- beta: 13-30 Hz.

Relative power is band power divided by total 1-30 Hz power before log transform, with a small numerical floor.

When the author 0.5-80 Hz signal is materialized, additionally compute:

- low gamma: 30-45 Hz relative to 1-45 Hz total power.

These are primary-selection eligible when finite values are available for all canonical rows and subjects. If signal duration/resolution makes a band invalid for some rows, that candidate is marked unavailable rather than silently changing the row set.

### 4. Phase-sensitive feasibility variants

For rows at least 1.0 s long, compute row-onset-referenced Fourier phase at fixed center frequencies:

- theta phase at 5.5 Hz;
- alpha phase at 10 Hz.

For each channel, encode phase as cosine and sine. These phase candidates are evaluated on the common >=1.0-s row subset and are reported as exploratory feasibility metrics only. They are not eligible for primary winner selection because their row set differs and the task lacks repeated identical semantic trials needed for a conventional ITPC/PLV endpoint.

## Neural geometry

For each subject and candidate:
1. z-score every feature across rows within subject;
2. compute correlation-distance RDM across rows;
3. rank-transform the RDM;
4. residualize against the prespecified nuisance RDMs;
5. estimate cross-subject reliability.

## Nuisance RDMs

Use the existing run metadata to control:
- run position lag;
- row duration difference;
- character-count difference;
- chapter mismatch;
- character-set Jaccard distance;
- punctuation-count difference.

The same nuisance definition is used across eligible candidates within a run.

## Outputs

Safe derived artifacts only:
- `summary.json`: protocol, feasibility, frozen run-06 winner, run-07 holdout result, and subjob statuses;
- `candidate_metrics.csv`: run-level candidate reliability metrics;
- `subject_metrics.csv`: subject-level LOO reliability by candidate/run;
- `sensor_groups.json`: deterministic sensor-group definitions actually used.

No raw EEG, EEG arrays, model weights, embeddings, or restricted data are artifacts.

## Failure isolation

Each candidate family is a subjob. A technically unavailable phase, gamma, or spatial candidate must not terminate the entire overnight run. The script records the failure/unavailability and continues. The overall job fails only if the baseline representation cannot be evaluated or no primary-selection-eligible candidate can be completed.

## Interpretation

A richer representation can replace row mean for future NeuroSem work only if it improves EEG-only reproducibility on run 06 and shows non-catastrophic run-07 holdout reliability. This benchmark alone does not establish semantic specificity. The next semantic/model analysis must use the frozen representation and must preserve external validation targets.