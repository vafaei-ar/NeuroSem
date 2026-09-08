# NeuroSem

NeuroSem tests whether reproducible human neural representational geometry can provide relational supervision for language models and whether the resulting representational change transfers to independent neural measurements.

The project is in a submission freeze. The primary prospective analyses and the planned post-confirmatory robustness, specificity, dose, model-family, boundary, regional, and spatial analyses are complete. No additional outcome-bearing analysis is planned for the current manuscript unless a reviewer or editor asks a specific question that requires it.

## Current submission

The current author-review package is **v1.18.2**. Word masters are maintained outside Git during final review; their filenames, SHA-256 fingerprints, rendered page counts and submission-length checks are recorded in [`paper/CURRENT_MANUSCRIPT.md`](paper/CURRENT_MANUSCRIPT.md).

The primary evidential chain is unchanged:

- ChineseEEG establishes a reproducible development neural geometry and a learnable relational target.
- A frozen multilingual-E5 contrast transfers positively to independent ZuCo reading EEG in 17/17 retained participants.
- The same frozen contrast transfers prospectively to SMN4Lang fMRI in 12/12 participants after the model-blind reliability gate.

Post-confirmatory analyses define the scope and limits of that result. These include preserved-versus-shuffled neural correspondence, a structured non-neural surrogate, optimization-seed robustness, dose characterization, reverse transfer, model-family portability, model-space diagnostics, DERCo as a higher-reliability negative-transfer boundary, and regional/spatial fMRI analyses. The manuscript keeps these analyses distinct from the two primary external tests.

## Reproducibility map

Start with:

1. [`paper/CURRENT_MANUSCRIPT.md`](paper/CURRENT_MANUSCRIPT.md) for the current external Word masters.
2. [`paper/FIGURE_GENERATION.md`](paper/FIGURE_GENERATION.md) for the canonical figure-build chain.
3. [`docs/NMI_V118_PROVENANCE_LEDGER_SPEC.md`](docs/NMI_V118_PROVENANCE_LEDGER_SPEC.md) for the manuscript claim-to-artifact verification contract.
4. [`scripts/audit/audit_nmi_v118_final_shipping_v1.py`](scripts/audit/audit_nmi_v118_final_shipping_v1.py) for the final shipping gate.
5. [`scripts/audit/build_nmi_v118_shipping_bundle_v1.py`](scripts/audit/build_nmi_v118_shipping_bundle_v1.py) for the safe derived evidence bundle.
6. [`scripts/paper/build_nmi_figure1_provenance_v1.py`](scripts/paper/build_nmi_figure1_provenance_v1.py) and [`scripts/paper/build_nmi_main_figures_v3_4.py`](scripts/paper/build_nmi_main_figures_v3_4.py) for the provenance-linked main-figure path.

Frozen protocols and result documents under `docs/` preserve the analysis chronology. Historical implementations needed to interpret earlier runs are retained when they form part of the provenance record; current entry points are identified in the documentation above.

## Repository layout

- `docs/`: frozen protocols, result summaries, provenance specifications, and publication-state records.
- `scripts/`: analysis, robustness, audit, and publication code.
- `configs/`: frozen model and dataset configuration.
- `paper/`: submission-facing documentation and figure workflow.
- `.runrelay/project.yaml`: versioned task definitions used for exact-commit workstation execution.

## Data and artifacts

Raw or restricted neural data, credentials, local environments, model checkpoints, and final Word binaries are not committed. The repository contains code and publication-facing metadata; safe derived artifacts used for claim verification are distributed separately with exact hashes.

## Interpretation boundaries

The manuscript preserves the prospective ChineseEEG to ZuCo to SMN4Lang chain, reports null and negative boundaries, and does not infer universal transfer, E5 uniqueness, language-network specificity, or a specific transcriptomic mechanism. Forward and reverse dose analyses, model-family comparisons, model-space diagnostics, and regional analyses are explicitly post-confirmatory.
