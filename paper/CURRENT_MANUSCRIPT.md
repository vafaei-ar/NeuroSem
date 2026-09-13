# Current publication master

**Recorded:** 2026-09-13

The current Word masters are maintained outside the Git working tree during final author review. This file records the exact binaries used for submission preparation.

## Main manuscript

### Clean

- File: `NeuroSem_Nature_Manuscript_v1.19.2_submission_readiness_clean.docx`
- SHA-256: `24cf248bf783f157376c4879360f801b0a8ee5d21f33599eaaaf16a7ac65fb0a`
- Size: 3,185,341 bytes
- Rendered length: 32 pages

### Tracked changes

- File: `NeuroSem_Nature_Manuscript_v1.19.2_submission_readiness_tracked.docx`
- SHA-256: `25c85cd930cbd8fe842806f2bdfe778782ec8c4d62a17d1b163362f58835e77b`
- Size: 3,186,326 bytes
- Rendered length: 33 pages

Current title: **Brain-derived relational supervision transfers language-model representations across independent neural datasets**

The manuscript uses the submission-ready figure architecture: 4 main figures plus 4 Extended Data figures. The embedded scientific figures remain the approved code-generated assets from the canonical figure pipeline.

The v1.19.2 submission-readiness pass is editorial/provenance-only. It tightens prospective/post-confirmatory terminology, adds the exact primary sign-flip P values to the Results, improves statistical/sample-size detail in figure legends, adds an umbrella citation to Supplementary Tables 1-17 and Supplementary Notes 1-9, clarifies the generative-AI disclosure, and corrects three embedded Zotero given-name metadata records. It adds no outcome-bearing analysis or scientific inference.

## Supplementary Information

### Clean Word master

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.2_clean.docx`
- SHA-256: `c59e815ec5e4170eaf7d05f51ac41151f876b3f6091164345d5cffd7b196644e`
- Size: 65,644 bytes
- Rendered length: 12 pages

### Tracked changes

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.2_tracked.docx`
- SHA-256: `c6c80175521a7576910d53132e3e237effe50b9aefb8ab73cde79a084f744e83`
- Size: 66,289 bytes
- Rendered length: 12 pages

### Combined submission PDF

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.2.pdf`
- SHA-256: `ec3f8e2cec130223de1a627198cd325a0bf02b64b814a9f581195ade37c0d555`
- Rendered length: 12 pages

The Supplement remains scientifically unchanged. The v1.19.2 edits standardize prospective/frozen terminology, `λ=0.10` notation, selected P-value spacing, and optimization-run wording without changing reported values.

## Quality checks

- Every page of the clean and tracked manuscript and Supplement was rendered and visually inspected.
- DOCX ZIP/package integrity passes for all four Word files.
- Main manuscript retains 22 `ZOTERO_ITEM` citation fields plus one `ZOTERO_BIBL` bibliography field.
- Accessibility audit: 0 high and 0 medium findings in all four Word files. The 11 low findings in the manuscript are raw-URL display text in Data/Code Availability.
- The tracked-change versions resolve to the same final visible text as the corresponding clean versions when changes are accepted.

## Figure code snapshot

The immutable figure-code snapshot cited by the v1.19.2 manuscript remains commit `a7d2eaa81d5d5e59521b03fb75d7219aca3e29be`.

The canonical submission-facing figure entry point is:

```text
scripts/paper/final_figures/build_all_figures.py
```

It builds and validates exactly Main Figures 1-4 and Extended Data Figures 1-4 into `outputs/paper_figures_final/`. Exact-commit RunRelay job `K4T9M2VR` completed successfully at this snapshot with exit code 0.

## Status

v1.19.2 is a final submission-readiness scientific/editorial pass over the scientifically locked v1.19.1 package. It does not reopen model training, target definition, dose selection, statistical families or any outcome-bearing analysis.

Two author-level submission decisions remain external to this document record: whether the initial submission will be double-anonymized, which determines whether author/affiliation/contribution/competing-interest metadata should be present in the manuscript file; and whether to shorten the current 112-character title to match the older Nature Machine Intelligence brief-guide recommendation of no more than 100 characters. The current live content-type page specifies the 150-word abstract and 3,500-word Article main-text limits but does not surface a title-length cap.

The repository intentionally does not commit `.docx` masters. Frozen protocol and result documents remain authoritative for analysis chronology, while these Word files are authoritative for current submission wording and layout.
