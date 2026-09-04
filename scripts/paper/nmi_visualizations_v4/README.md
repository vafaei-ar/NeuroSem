# NMI visualization v4

Presentation-only figure builders implementing the September 2026 visualization recommendations for NeuroSem.

The integrated entry point is:

```bash
python scripts/paper/nmi_visualizations_v4/build_nmi_visualizations_v4.py
```

It reads existing frozen derived outputs only and writes:

- `outputs/nmi_visualizations_v4/latest/figure1.pdf|png`
- `outputs/nmi_visualizations_v4/latest/figure2.pdf|png`
- `outputs/nmi_visualizations_v4/latest/figure3.pdf|png`
- `outputs/nmi_visualizations_v4/latest/figure4.pdf|png`
- `outputs/nmi_visualizations_v4/latest/extdata_regional.pdf|png`
- `outputs/nmi_visualizations_v4/latest/source_manifest.json`

## Design changes

- Shared Nature-style typography, panel lettering, line weights and colour-blind-safe palette.
- No baked-in figure titles, panel titles or statistical prose blocks.
- Figure 1 categorical arms are shown as seed dots plus arm means rather than connected categorical lines.
- Figures 2 and 3 foreground participant-level reliability, paired arm values and sorted participant deltas.
- Figure 4 shows the external dose curve on log-log axes, a slope-1 visual reference, the fMRI sign reversal, the ZuCo absolute sign crossing, the STS trade-off and the six-model bidirectional panel with direction-specific x ranges.
- The regional Extended Data figure uses unordered parcel summaries and a diverging scale symmetric about zero for the complete DK68 phenotype.

## Scientific guardrails

This builder is presentation-only. It does not fit models, select targets, change cohorts, calculate new inferential tests or search over visualization-dependent scientific outcomes. Figure 4 consumes the already-completed forward-dose and six-model panel outputs. Regional values are read directly from the completed Stage-2 regional summary. Figure 1 neural values are read from `paper/figure_data/chineseeeg_development_v1.json`; the generic semantic panel retains the already-reported fixed development values used in the supplied visualization specification.
