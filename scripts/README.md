# Scripts

This directory contains the executable analysis, robustness, audit, and publication workflows used in NeuroSem.

## Directory map

- `analysis/`: neural reliability and final spatial-validation analyses.
- `robustness/`: transfer controls, dose/model-family analyses, alternative-signal experiments, and model-space diagnostics.
- `audit/`: provenance, reconciliation, shipping, and reproducibility checks.
- `paper/`: manuscript figure/table assembly and publication verification.
- `tuning/`: frozen model-adaptation and external-evaluation workflows.

## Current submission entry points

The main publication build is `paper/build_nmi_main_figures_v3_4.py`. Figure 1 is generated through `paper/build_nmi_figure1_provenance_v1.py`, which supplies artifact-backed inputs to `paper/nmi_visualizations_v4/build_figure1_chineseeeg.py`.

The current spatial-publication build is `paper/build_nmi_spatial_validation_publication_v1_2.py`, and the consolidated figure/table verification wrapper is `paper/build_publication_figures_tables_v2.py`.

Final manuscript provenance and bundle checks are in:

- `audit/audit_nmi_v118_final_shipping_v1.py`
- `audit/build_nmi_v118_shipping_bundle_v1.py`
- `audit/reproduce_nmi_chineseeeg_reliability_v1.py`
- `audit/audit_nmi_run07_history_v1.py`

The structured non-neural alternative-signal workflow uses the versioned MPNet materialization and evaluation code under `robustness/`; later versioned entry points supersede earlier implementations while the earlier files remain available to interpret historical runs.

## Versioned historical scripts

Some workflows have `v1`, `v1_1`, `v1_2`, or similar variants. These files are retained when an executed result or provenance record depends on them. The preferred current entry point is identified in the publication documentation rather than inferred from filename order.

Scripts should use explicit inputs, fail on missing required artifacts, and avoid dependence on local absolute paths. Raw or restricted data and local credentials do not belong in the repository.
