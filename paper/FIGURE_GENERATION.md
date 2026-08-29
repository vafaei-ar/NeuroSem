# Manuscript figure generation

This stage turns already-locked NeuroSem outputs into manuscript-facing figures and compact tables. It does not rerun scientific analyses or introduce new hypothesis tests.

## Existing versioned builders

- `scripts/paper/build_manuscript_figures_v1.py` builds the reading-reliability overview, AHBA molecular-null panel and normalized source tables.
- `scripts/paper/build_manuscript_figures_v2.py` retains the v1 outputs and adds the final SMN4Lang MEG reliability-boundary panel.
- `scripts/paper/build_figure3_smn4lang.py` builds the complete SMN4Lang fMRI main-text Figure 3 from the already-locked reliability and transfer summaries plus participant tables.

## Figure 3 source contract

`build_figure3_smn4lang.py` requires four completed locked artifacts:

1. `outputs/smn4lang_fmri_reliability/latest/participant_results.csv`
2. `outputs/smn4lang_fmri_reliability/latest/summary.json`
3. `outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv`
4. `outputs/smn4lang_fmri_e5_transfer_v1/latest/summary.json`

The composite contains:

- **a** prospective ChineseEEG-to-SMN4Lang design and the model-blind reliability gate;
- **b** participant-level SMN4Lang fMRI reliability with the locked participant-bootstrap interval;
- **c** the frozen causal word-onset → prefix-E5 → HRF → TR-level model-geometry mapping;
- **d** paired participant residual RSA for text-only `lambda=0` versus neural-guided `lambda=0.10`;
- **e** participant-level neural-guided-minus-text-only deltas with the locked mean confidence interval.

The builder does not access raw fMRI, reload E5 adapters, recompute RDMs, bootstrap new intervals, or perform a new statistical test. It visualizes only the completed locked outputs.

## Existing v1/v2 outputs

The earlier builders generate:

- `fig2_reading_reliability.png` and `.pdf`: participant-level residual LOO neural-geometry reliability for Little Prince, TMNRED, ZuCo 2.0 and Garnett Dream;
- `fig4b_smn4lang_meg_reliability_boundary.png` and `.pdf`: the prospectively frozen 32-bin MEG result and the separately frozen post-confirmatory 4/8/16-bin temporal-granularity family;
- `fig4_ahba_frozen_molecular_nulls.png` and `.pdf`: the frozen AHBA molecular-null summary for Extended Data consideration;
- normalized reliability, AHBA and MEG tables plus source manifests.

## Scientific guardrails

All manuscript builders are presentation-only. They must not select participants, representations, datasets, stories, genes, gene sets or plotting subsets from manuscript outcomes. They must fail if required locked artifacts are absent rather than silently substituting newly calculated values.

For SMN4Lang fMRI, the participant remains the inferential unit. The small absolute `lambda=0.10 - lambda=0` RSA increment must not be presented as a large gain in explained neural variance. The value of Figure 3 is the prospective model-blind gate, absence of SMN4Lang model tuning and 12/12 directional consistency.

For SMN4Lang MEG, the failed reliability gate is a representation-level reliability boundary, not negative model transfer. No model evaluation was performed.

For AHBA, the frozen primary mechanistic conclusion remains null; the panel is secondary/Extended Data material.

## Remaining main-figure work

The remaining main manuscript composites are:

1. **Figure 1:** conceptual framework, ChineseEEG target reliability/correspondence, sealed BERT comparison, E5 replication and generic semantic-benchmark dissociation.
2. **Figure 4a/c/d:** harmonized external-outcome map, independence/design matrix and generic semantic/conceptual conclusion, combined with the already-final Figure 4b MEG reliability boundary.

These should use the same locked-output/source-manifest pattern and should not trigger new scientific analysis.
