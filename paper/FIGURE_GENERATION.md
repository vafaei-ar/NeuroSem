# Manuscript figure generation

This stage turns already-locked NeuroSem outputs into manuscript-facing figures and compact tables. It does not rerun scientific analyses or introduce new hypothesis tests.

## Main-figure builders

- `scripts/paper/build_figure1_chineseeeg.py` builds Figure 1 from locked ChineseEEG development/sealed-validation summaries.
- `scripts/paper/build_figure2_zuco.py` builds Figure 2 from the completed ZuCo reliability and transfer participant tables/summaries.
- `scripts/paper/build_figure3_smn4lang.py` builds Figure 3 from the completed SMN4Lang fMRI reliability and transfer participant tables/summaries.
- `scripts/paper/build_figure4_boundaries.py` builds Figure 4 from the locked external-outcome summaries, completed MEG reliability table and generic semantic benchmark values.

## Main-figure architecture

### Figure 1
- **a** relational neural-constraint concept;
- **b** reliability-led ChineseEEG target;
- **c** held-out BERT residual correspondence across runs 01–06;
- **d** sealed run-07 BERT comparison;
- **e** multilingual-E5 replication context and generic semantic-benchmark dissociation.

### Figure 2
- **a** frozen ChineseEEG-to-ZuCo cross-language validation design;
- **b** participant-level ZuCo primary EEG reliability;
- **c** paired text-only λ=0 versus neural-guided λ=0.10 participant RSA;
- **d** participant-level transfer deltas and locked mean confidence interval.

### Figure 3
- **a** prospective ChineseEEG-to-SMN4Lang design and model-blind reliability gate;
- **b** participant-level SMN4Lang fMRI reliability;
- **c** frozen causal word-onset → prefix-E5 → HRF → TR-level mapping;
- **d** paired participant residual RSA;
- **e** participant-level neural-guided-minus-text-only deltas and locked mean confidence interval.

### Figure 4
- **a** harmonized external generalization map without a common raw RSA effect-size axis;
- **b** SMN4Lang MEG reliability boundary, including prospective 32-bin and separately frozen post-confirmatory 4/8/16-bin results;
- **c** independence/design matrix;
- **d** generic semantic-benchmark dissociation and conceptual conclusion.

## Existing v1/v2 supporting outputs

The earlier versioned builders remain available:

- `scripts/paper/build_manuscript_figures_v1.py` builds the reading-reliability overview, AHBA molecular-null panel and normalized source tables.
- `scripts/paper/build_manuscript_figures_v2.py` retains those outputs and adds the final standalone SMN4Lang MEG reliability-boundary panel.

These supporting outputs are not substitutes for the final Figure 2 or Figure 4 composites.

## Scientific guardrails

All manuscript builders are presentation-only. They must not select participants, representations, datasets, stories, genes, gene sets or plotting subsets from manuscript outcomes. Required locked artifacts must be supplied explicitly; missing artifacts should cause failure rather than silent substitution with newly calculated results.

For ZuCo and SMN4Lang fMRI, participant is the inferential unit and plotted confidence intervals are the already-locked participant-bootstrap intervals. No target-dataset model retuning is performed.

For SMN4Lang fMRI, the small absolute λ=0.10 − λ=0 RSA increment is shown as a representational shift, not a large gain in explained neural variance. The main value is prospective independence, model-blind reliability gating and 12/12 directional consistency.

For SMN4Lang MEG, the failed reliability gate is a representation-level reliability boundary, not negative model transfer. No model evaluation was performed.

Raw RSA deltas across EEG and fMRI are not treated as a common cross-modality effect-size scale.

For AHBA, the frozen primary mechanistic conclusion remains null; AHBA is secondary/Extended Data material.

## Submission-production state

All four main-figure composites have now been assembled and visually inspected. The next step is packaging: replace the obsolete figure placeholders/supporting-only artwork in the author-edited Word manuscript with Figures 1–4, preserve Zotero fields and manuscript text, and render the complete DOCX for final visual QA.
