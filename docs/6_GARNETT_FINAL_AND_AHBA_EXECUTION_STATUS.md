# 6. Garnett Final Result and AHBA Execution Status

**Updated:** 2026-08-26

This document records the first completed outcome-bearing Garnett Dream model-transfer result and the current model-blind AHBA execution state. It supplements `3_RESULTS_AND_COMPARISONS.md`, `4_EXPERIMENT_LEDGER.md`, and `5_CURRENT_ROADMAP.md` until those consolidated summaries are next refreshed.

## Garnett Dream: confirmatory E5 transfer is complete

Garnett Dream remains a **same-participant / new-text validation**, not an independent-cohort replication.

The required sequence was respected:

1. structural/event unit frozen model-blind;
2. primary EEG representation fixed as `row_mean_all`;
3. EEG-only reliability demonstrated before any model outcome;
4. exact segmented-XLSX row-text mapping frozen model-blind;
5. full applicable nuisance family restored;
6. exactly one prespecified model contrast evaluated: ChineseEEG-trained multilingual-E5 lambda 0.10 neural-guided minus matched lambda 0 text-only.

No Garnett model training, lambda selection, architecture selection, sensor search, time-window search, representation switch, participant selection, or item selection was performed from the transfer outcome.

### Frozen Garnett transfer result

Participant inferential unit, equal-weight Fisher-z aggregation across available chapters:

- mean delta RSA (`lambda=.10 - lambda=0`): **+0.0003266**;
- median delta: **+0.0003319**;
- participants positive: **6/10 (60%)**;
- participant-bootstrap 95% CI: **[-0.0001218, +0.0007560]**;
- exact one-sided sign-flip p: **0.1015625**;
- exact two-sided sign-flip p: **0.203125**.

Interpretation: the point estimate is positive, but the confidence interval crosses zero and the prespecified participant-level sign-flip test is not significant. Therefore the confirmatory Garnett model-transfer result is **null / inconclusive**, not positive evidence for neural-guided new-narrative transfer.

This does **not** change the already-positive Garnett EEG-only result. The neural geometry itself generalized strongly to the new narrative (`row_mean_all` residual LOO mean about 0.01863, 10/10 positive). What failed to establish is a reliable advantage of the ChineseEEG-trained lambda=.10 neural-guided model over matched text-only tuning on this new narrative.

### Garnett stopping rule

The prespecified stopping rule now applies:

- do not run a Garnett lambda sweep;
- do not promote `row_std_all` or `relative_8bin_all` to primary based on this result;
- do not search sensors, windows, layers, architectures, pooling rules, participants, chapters, or items for a favorable model-transfer effect;
- treat any later Garnett sensitivity work as explicitly exploratory and only if scientifically necessary.

The manuscript claim should therefore distinguish:

- **neural-geometry narrative generalization: supported**;
- **neural-guided model advantage on the new narrative: not established**.

## AHBA transcriptomic extension: current execution state

The AHBA track remains outcome-blind with respect to NeuroSem molecular effects.

### Preflight completed

The model-blind preflight established that:

- exact ChineseEEG CapTrak coordinate files exist with **128 finite XYZ electrode positions**;
- channel-name overlap with the MNE `GSN-HydroCel-256` standard montage is complete for the 128 channel names, but this is diagnostic only and does not supersede the measured CapTrak coordinates;
- MNE is available in the project environment;
- the preflight opened no EEG samples and computed no NeuroSem/model/gene-expression outcomes.

### First dependency setup attempt

`abagen==0.1.3` and `nibabel` installed successfully, but importing `abagen` failed because the Python 3.13 project environment lacked `pkg_resources`:

`ModuleNotFoundError: No module named 'pkg_resources'`

This is an infrastructure compatibility failure, not a scientific failure and not an AHBA outcome.

### Frozen infrastructure fix

The setup script now pins:

- `setuptools==80.9.0` to provide the legacy `pkg_resources` module required by `abagen 0.1.3`;
- `abagen==0.1.3` unchanged.

The rerun must verify both `pkg_resources` and `abagen` imports before the AHBA track proceeds.

## Next steps

1. Rerun the fixed AHBA dependency setup.
2. If import verification passes, freeze and run the next **model-blind** AHBA preparation stage: AHBA preprocessing choices plus measured ChineseEEG CapTrak-to-cortical forward/source-sensitivity construction.
3. Freeze donor handling, bilateral strategy, source space/head model, sensitivity convention, and gene-set definitions before any molecular-NeuroSem outcome.
4. Only after that preparation is locked run the separately frozen GABAergic, serotonergic, cell-type, and curated-pathway mechanistic tests with spatial nulls, size-matched gene-set controls, donor robustness, and multiplicity correction.
5. Preserve the Garnett null model-transfer result in the manuscript; do not optimize it away.
