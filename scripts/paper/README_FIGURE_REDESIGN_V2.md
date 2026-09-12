# NeuroSem NMI figure redesign v2

This directory contains the code-first rebuild of the manuscript figures. The image-generation mockups are design references only; publication figures are generated from frozen NeuroSem outputs by Python.

## Figure 1

Builder:

```bash
.venv/bin/python scripts/paper/build_nmi_figure1_transfer_redesign_v2.py
```

Outputs:

```text
outputs/nmi_figure1_transfer_redesign_v2/latest/figure1.pdf
outputs/nmi_figure1_transfer_redesign_v2/latest/figure1.svg
outputs/nmi_figure1_transfer_redesign_v2/latest/figure1.png
outputs/nmi_figure1_transfer_redesign_v2/latest/figure1_reliability_source.csv
outputs/nmi_figure1_transfer_redesign_v2/latest/figure1_transfer_source.csv
outputs/nmi_figure1_transfer_redesign_v2/latest/figure1_seed_source.csv
outputs/nmi_figure1_transfer_redesign_v2/latest/source_manifest.json
outputs/nmi_figure1_transfer_redesign_v2/latest/report.txt
```

The builder is presentation-only. It reads the frozen ZuCo and SMN4Lang reliability and transfer outputs plus the completed E5 optimization-run robustness summary. It does not train or evaluate models and does not recompute scientific inference.

### Validation

The builder fails if expected cohort sizes, participant-level deltas, frozen summary means, confidence intervals, or optimization-seed identities are inconsistent. On success it writes:

- exact SHA-256 hashes for every input and figure output;
- source-data CSVs containing the values actually displayed;
- a `source_manifest.json` recording provenance and guardrails;
- a concise `report.txt` with the headline displayed values and output hashes.

For byte-level comparisons, use the same repository commit, Python environment, Matplotlib version, and installed fonts. Cross-platform PDF/SVG/PNG bytes can differ because of renderer/font metadata even when the plotted scientific values are identical; `source_manifest.json` is the scientific provenance record.

### Design conventions

- ZuCo EEG is blue; SMN4Lang fMRI is orange.
- Participant-level paired transfer uses one x-position per participant, open baseline points, filled neural-guided points, and arrows from baseline to intervention.
- Half-violins are secondary density layers only and are used for n=12/17 participant distributions, never for n=3 optimization seeds.
- The right-side delta rainclouds show participant-level displacement and the already-reported participant-bootstrap 95% CI.
- Optimization-run consistency shows run means and positive-participant counts only; it deliberately does not invent confidence intervals for runs where participant-level outputs are not available in the frozen summary.
