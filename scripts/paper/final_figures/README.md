# NeuroSem canonical submission figure pipeline

This directory is the **only active submission-facing visualization pipeline** for the NeuroSem manuscript.

It builds the frozen final architecture:

- **4 Main Figures**
- **4 Extended Data Figures**
- **0 Supplementary Figures**

All eight figures use the same visual grammar and all assets are written to one directory:

`outputs/paper_figures_final/`

## Build

From the repository root:

```bash
.venv/bin/python scripts/paper/final_figures/build_all_figures.py
```

The build creates PNG, PDF, and SVG files for every figure and then runs `validate_all_figures.py`.

## Scientific contract

The figure code is presentation-only. It reads completed/frozen NeuroSem outputs and does not retrain models, tune doses, select participants, select regions, redefine targets, or introduce new statistical inference. Each figure writes a manifest containing exact builder, input, and output SHA-256 hashes and `scientific_values_changed=false`.

Main Figure 1 is additionally grounded in the committed safe figure snapshots under `paper/figure_data/nmi_redesign_v2/`, whose manifest preserves the upstream RunRelay/artifact lineage.

FreeSurfer fsaverage/Desikan-Killiany files used by Figure 4 and Extended Data Figure 3 are anatomical rendering scaffolds only.

## Canonical code

The complete active visualization code is contained here:

- `style.py`
- `common.py`
- `build_figure1.py` ... `build_figure4.py`
- `build_extended_data_figure1.py` ... `build_extended_data_figure4.py`
- `build_all_figures.py`
- `validate_all_figures.py`

The final builders are self-contained and do not import earlier `mockup`, `redesign`, or `nmi_visualizations_v4` plotting modules. Earlier figure implementations remain recoverable from Git history for provenance but are not part of the submission workflow.
