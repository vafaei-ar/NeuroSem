# Current publication master

**Recorded:** 2026-09-13

The current Word masters are maintained outside the Git working tree during final author review. This file records the exact binaries used for submission preparation.

## Main manuscript

### Clean

- File: `NeuroSem_Nature_Manuscript_v1.19.1_submission_figures_clean.docx`
- SHA-256: `102833df47ce25aed49554022e4ca1d710ae342d9cbd78745ca3ef2583993c60`
- Size: 2,765,410 bytes
- Rendered length: 32 pages

### Tracked changes

- File: `NeuroSem_Nature_Manuscript_v1.19.1_submission_figures_tracked.docx`
- SHA-256: `8948cb9ee67f4034c4e1d1cb0cbe9795cd0d9380c3c866994dc45e59278150a1`
- Size: 2,767,951 bytes
- Rendered length: 33 pages

Current title: **Brain-derived relational supervision transfers language-model representations across independent neural datasets**

The manuscript now uses the submission-ready figure architecture: 4 main figures plus 4 Extended Data figures. The embedded PNGs are byte-identical to the approved outputs from the canonical figure pipeline.

## Supplementary Information

The technical Supplementary Information remains scientifically unchanged in this figure-architecture revision.

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.18.6.docx`
- SHA-256: `fc8938c6c38742f14323499e402bc9ffacc28656888f7b5e2882eb1da305bffd`
- Size: 70,356 bytes
- Rendered length: 12 pages

## Figure code snapshot

The immutable code snapshot cited by the v1.19.1 manuscript is commit `a7d2eaa81d5d5e59521b03fb75d7219aca3e29be`.

The canonical submission-facing figure entry point is:

```text
scripts/paper/final_figures/build_all_figures.py
```

It builds and validates exactly Main Figures 1-4 and Extended Data Figures 1-4 into `outputs/paper_figures_final/`. Exact-commit RunRelay job `K4T9M2VR` completed successfully at this snapshot with exit code 0.

## Status

v1.19.1 is a presentation and manuscript-integration revision of the scientifically locked analysis. It replaces the earlier five-main-figure organization with the approved four-main plus four-Extended-Data architecture, updates in-text figure citations and legends, embeds the final code-generated figures, and updates Code Availability to the verified figure-code snapshot. It adds no new outcome-bearing analysis or scientific inference.

The repository intentionally does not commit `.docx` masters. Frozen protocol and result documents remain authoritative for analysis chronology, while these Word files are authoritative for current submission wording and layout.
