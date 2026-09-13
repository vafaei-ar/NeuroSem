# Manuscript figure generation

## Canonical submission architecture

The submission-ready NeuroSem figure package contains exactly:

- Main Figures 1-4
- Extended Data Figures 1-4
- no separate Supplementary Figures

The only active submission-facing entry point is:

```text
scripts/paper/final_figures/build_all_figures.py
```

Run from the repository root with:

```bash
.venv/bin/python scripts/paper/final_figures/build_all_figures.py
```

All PNG, PDF and SVG assets, per-figure provenance manifests, and the package-level manifest are written to:

```text
outputs/paper_figures_final/
```

`validate_all_figures.py` requires all 8 figures, verifies `status=ok` and `scientific_values_changed=false` for each manifest, checks that the final builders do not import deprecated visualization modules, and writes `submission_figure_manifest.json` containing final SHA-256 hashes.

## Main figures

### Figure 1. Frozen brain-derived supervision transfers across independent neural datasets

Uses committed safe snapshots under `paper/figure_data/nmi_redesign_v2/` for target reliability, participant-level ZuCo/SMN4Lang transfer, and optimization-run consistency. The snapshot manifest preserves upstream RunRelay/artifact hashes. This is the prospective transfer figure.

### Figure 2. Transfer depends on supervision strength and model displacement

Uses the frozen forward external dose characterization and the λ=0.10/λ=1.0 model-space characterization outputs. CI clouds represent uncertainty in the frozen mean estimates and are not synthetic participant distributions.

### Figure 3. Target structure and model architecture determine transfer

Uses the completed shuffled-target specificity control, genuine-neural multiseed results, structured MPNet alternative-signal control, six-backbone bidirectional panel, and seed-matched model-space comparison.

### Figure 4. fMRI transfer is cortex-wide with modest language-associated enrichment

Uses the completed language-specificity, spatial-extension, final spatial-validation, and full regional fMRI outputs. The complete DK68 phenotype is rendered on standard fsaverage Desikan-Killiany surfaces without effect-based parcel selection or thresholding.

## Extended Data figures

### Extended Data Figure 1. Source measurability and development-stage learnability

Uses the ChineseEEG reliability replay, six held-out source runs, reserved run-07 development arms, and frozen C-MTEB semantic summaries.

### Extended Data Figure 2. Story robustness and reverse-transfer boundary conditions

Uses all 60 leave-one-story-out spatial estimates plus the frozen primary and three added fMRI-to-ZuCo optimization runs.

### Extended Data Figure 3. Complete regional fMRI characterization

Shows the six prespecified functional language parcels, all 68 DK cortical parcels, and the same complete unthresholded DK68 phenotype on fsaverage cortex.

### Extended Data Figure 4. Dose and architecture reshape cortical specificity

Uses the frozen dose-by-system, backbone-by-system, forward external dose, and hierarchical synthesis outputs. Condition-level trajectories are descriptive and do not select a dose or model.

## Scientific guardrails

Figure assembly must fail when a required frozen source is missing, when an expected cohort/family size changes, or when a provenance manifest is inconsistent. The plotting code must not replace missing evidence with fabricated values or simulated observations.

Participant-level inference, optimization-seed robustness, and presentation-only rebuilding remain distinct stages. Raw RSA differences are not treated as a common standardized effect-size scale across EEG and fMRI.

## Historical figure code

Earlier `mockup`, `redesign`, and pre-final submission builders are superseded by `scripts/paper/final_figures/`. Their historical implementations remain available in Git history and exact historical commits for provenance. They are not canonical entry points for the current submission.
