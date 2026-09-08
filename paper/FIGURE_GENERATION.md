# Manuscript figure generation

Publication figures are assembled from completed derived artifacts. Figure-generation code does not retrain models, select representations, redefine cohorts, or introduce new hypothesis tests.

## Canonical main-figure build

The current entry point is:

```text
scripts/paper/build_nmi_main_figures_v3_4.py
```

It writes Figures 1-4 to `outputs/nmi_main_figures_v3/latest/` and records exact output hashes in `source_manifest.json`.

### Figure 1

Figure 1 has an additional provenance layer because its panels combine several development-era sources. The canonical chain is:

```text
scripts/paper/build_nmi_figure1_provenance_v1.py
  -> scripts/paper/nmi_visualizations_v4/build_figure1_chineseeeg.py
  -> outputs/nmi_v118_figure1_provenance_v1/latest/
  -> scripts/paper/build_nmi_main_figures_v3_4.py
```

The non-demo Figure 1 builder requires four machine-readable inputs:

1. `paper/figure_data/chineseeeg_development_v1.json`
2. `outputs/nmi_v118_chineseeeg_reliability_reproduction_v1/latest/summary.json`
3. `outputs/bert_neurosem_cmteb_sts_v1/20260823_122332/summary.json`
4. `outputs/bert_neurosem_cmteb_sts_v1_seed2/20260823_123910/summary.json`

Reliability is loaded from the independent replay summary rather than from a figure literal. Semantic panel values are loaded from the two frozen task-level STS summaries and checked against their eight-task means. The development JSON supplies the held-out-run and reserved run-07 summaries.

`build_nmi_main_figures_v3_4.py` accepts Figure 1 only when its provenance manifest matches the pinned SHA-256 recorded in the builder, then copies the verified PDF, SVG, and PNG into the canonical main-figure directory.

### Figures 2-4

Figures 2-4 are assembled from already-completed frozen participant-level and summary artifacts through the NMI submission figure/table builders called by `build_nmi_main_figures_v3_4.py`. The source manifest records the resulting hashes.

## Spatial and Extended Data figures

The current spatial-validation publication entry point is:

```text
scripts/paper/build_nmi_spatial_validation_publication_v1_2.py
```

The consolidated publication verification wrapper is:

```text
scripts/paper/build_publication_figures_tables_v2.py
```

Earlier versioned builders are retained because they are part of the execution history. They are not the preferred entry points for the current submission package.

## Scientific guardrails

Figure assembly must fail when a required frozen source is missing or has an unexpected identity. It must not replace missing evidence with newly calculated values. Participant-level inference, optimization-seed robustness, and presentation-only rebuilding remain distinct stages.

For SMN4Lang MEG, the reliability failure is a representation-level boundary and no transfer test is implied. Across EEG and fMRI, raw RSA deltas are not treated as a common cross-modality effect-size scale.

## Final verification

The final manuscript shipping gate is implemented in:

```text
scripts/audit/audit_nmi_v118_final_shipping_v1.py
```

It verifies the manuscript claim ledger, exact source hashes, document manifest, Figure 1 provenance link, and freshness of the safe derived submission bundle.
