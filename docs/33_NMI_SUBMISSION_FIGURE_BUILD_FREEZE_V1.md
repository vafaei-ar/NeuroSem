# NMI submission figure build freeze v1

Status: presentation-only production freeze before canonical figure regeneration.

## Purpose

Generate the final manuscript figure set from repository code and already-completed frozen NeuroSem outputs, then use those generated figures to update the manuscript and Supplement. This pass performs no model training, model evaluation, neural analysis, target selection, dose selection, or new hypothesis test.

## Canonical entry point

`scripts/paper/build_nmi_main_figures_v3_4.py`

This entry point delegates to `scripts/paper/nmi_visualizations_v4/build_nmi_visualizations_v4.py`. Main figures are written to `outputs/nmi_main_figures_v3/latest/` as PDF, SVG and 600-dpi PNG. The regional Extended Data candidate is written to `outputs/nmi_visualizations_v4/latest/extdata_regional.*` for subsequent manuscript/Supplement integration.

## Frozen manuscript bases

- `NeuroSem_Nature_Manuscript_v1.10_presentation_final.docx`
- `NeuroSem_NMI_Supplementary_Technical_Tables_v1.10_presentation_final.docx`

These local document filenames identify the editorial bases. They are not scientific inputs to the repository figure build.

## Figure-data guardrails

1. Read only already-completed derived outputs and the frozen ChineseEEG development summary used by the existing publication system.
2. Use the completed prospective ZuCo and SMN4Lang participant-level outputs, the completed forward external-dose characterization, the completed six-model family panel, and the completed regional Stage-2 output.
3. Do not use any demo or synthetic figure input.
4. Do not recompute or alter scientific estimands. Presentation-only arithmetic needed to display already-completed quantities is allowed.
5. Preserve evidence-status distinctions in labels and annotations, especially prospective lambda=0.10 versus post-confirmatory dose characterization.
6. Do not select participants, models, regions, doses or outcomes based on figure appearance.
7. If the production build fails or reveals an input/schema mismatch, fix only the deterministic plotting/integration code and rerun the same frozen build.

## QA before document replacement

Inspect every generated main figure for panel lettering, clipping, legends, numerical labels, dose/target framing, and stale wording before replacing any embedded manuscript image. The regional figure must preserve the cortex-wide interpretation and must not imply language-network specificity.
