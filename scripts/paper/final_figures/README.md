# NeuroSem final figure pipeline

This directory is the canonical submission-facing figure entry point during final visual review.

It builds exactly:

- Main Figures 1-4
- Extended Data Figures 1-4
- no separate Supplementary Figures

All assets are written to a single directory:

`outputs/paper_figures_final/`

Run from the repository root:

```bash
python scripts/paper/final_figures/build_all_figures.py
```

The build ends by running `validate_all_figures.py`, which verifies that all 8 figures exist in PNG/PDF/SVG form, that each figure manifest reports `status=ok` and `scientific_values_changed=false`, and writes `submission_figure_manifest.json` with SHA-256 hashes.

The current Main Figure 1-4 visual implementations are the approved mockup-v3 designs. The Extended Data builders use the same visual grammar and read only completed/frozen NeuroSem outputs. Older experimental figure builders are intentionally retained until visual review is complete; they can be removed after parity and manuscript integration are approved.
