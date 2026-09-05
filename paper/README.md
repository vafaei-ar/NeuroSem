# Manuscript workspace

This directory contains the submission-facing NeuroSem manuscript documentation and figure-generation workflow. The scientific evidence is locked. Manuscript work must preserve the final inferential hierarchy and must not trigger new outcome-bearing analysis.

## Current manuscript master

The current author-review master is **`NeuroSem_Nature_Manuscript_v1.11_NMI_native_vector_figures.docx`**, with **`NeuroSem_NMI_Supplementary_Technical_Tables_v1.11_NMI_native_vector_figures.docx`** as the companion Supplementary Information.

These Word files are maintained outside the Git working tree during final author review to avoid committing large binary revisions. Their exact SHA-256 fingerprints and sizes are recorded in [`CURRENT_MANUSCRIPT.md`](CURRENT_MANUSCRIPT.md). Older Word versions, including the previously referenced v1.4 publication-clean files, are superseded for author review.

The current manuscript title is:

> **External transfer of brain-derived relational constraints depends on dose, target and model backbone**

The v1.11 manuscript:

- preserves ChineseEEG -> ZuCo -> SMN4Lang fMRI as the primary evidential chain;
- keeps forward/reverse dose, reverse-direction, model-family, neural-specificity, participant-by-stimulus, model-space and regional analyses explicitly subsequent to the primary external tests;
- reports that forward E5 transfer increases through `lambda=0.30` on both targets, while `lambda=1.0` further increases ZuCo transfer but reverses SMN4Lang fMRI and incurs a larger generic STS cost;
- reports the three-seed destroyed-correspondence control, showing that preserved neural item correspondence contributes substantially more transfer than the matched shuffled-neural objective;
- reports stable bidirectional portability in E5-large and E5-base under the common protocol without claiming an architecture mechanism or E5 uniqueness;
- states explicitly that all 68 DK parcel means were positive, so the regional fMRI phenotype is cortex-wide in direction and does not establish language-network specificity;
- preserves TMNRED, Garnett Dream, directional inner speech and the MEG reliability failure as boundaries;
- retains AHBA as a secondary mechanistic extension with prespecified molecular nulls;
- uses native/editable vector main figures and the current regional Extended Data figure.

## Current evidence architecture

1. ChineseEEG establishes a reproducible development neural geometry and model learnability.
2. ZuCo is the first fresh external test: **17/17** participants show positive neural-guided minus text-only transfer.
3. SMN4Lang fMRI is the prospective cross-modal test: **12/12** participants show positive transfer after the model-blind reliability gate.
4. Post-confirmatory specificity controls show that genuine item-relational neural correspondence contributes substantially more external transfer than a matched destroyed-correspondence objective on both targets.
5. Forward E5 dose characterization shows target-dependent scaling: ZuCo continues to increase through `lambda=1.0`, whereas fMRI peaks at `lambda=0.30` and reverses at `lambda=1.0`.
6. Reverse fMRI-to-ZuCo transfer establishes bidirectionality within E5; larger reverse doses and added seeds are post-confirmatory characterization/robustness.
7. The six-model panel shows stable bidirectional portability in E5-large and E5-base under the common protocol, but not universally across the tested encoders.
8. Regional fMRI characterization is positive across the six predefined language parcels and the complete DK68 cortex; it supports a cortex-wide displacement rather than language-network selectivity.
9. TMNRED, Garnett Dream and directional inner speech define transfer boundaries.
10. SMN4Lang MEG failed its model-blind reliability gate, so no model transfer test was performed.
11. AHBA remains a secondary mechanistic extension with prespecified molecular nulls.

## Writing rules that must remain intact

- Keep reliability, learnability, development-stage candidate selection and external transfer as distinct empirical stages.
- Do not describe the exploratory `lambda=0.10` development choice as confirmatory optimization or a universal optimum.
- Do not describe the forward or reverse dose curves as prospective tests.
- Do not describe the six-model panel as isolating architecture causally or as showing E5 uniqueness.
- Do not describe the regional result as language-network specificity.
- Do not describe SMN4Lang MEG as negative transfer.
- Do not imply that raw EEG, fMRI and MEG RSA values share a common effect-size scale.
- Describe the prospective fMRI effect as small in absolute magnitude but directionally consistent across all 12 participants.
- Preserve all null, inconclusive and negative external outcomes.
- Preserve the distinction between participant-level inference and the post-confirmatory participant x stimulus sensitivity analyses.

## Submission-facing files retained in Git

- `CURRENT_MANUSCRIPT.md` — exact identity/fingerprint of the external Word masters.
- `FIGURE_GENERATION.md` — reproducible figure-build workflow and provenance.
- `REFERENCE_SOURCE_AUDIT.md` — literature/reference audit for datasets, models and related work.
- `NATURE_REPORTING_SUMMARY_DRAFT.md` — reporting-summary working document.
- `README.md` — this current manuscript status record.

Historical manuscript drafts, positioning notes, reviewer-streamlining notes and obsolete submission scaffolds are intentionally absent from the current tree. Git history remains the archival record.

## Figure status

The main figures and regional Extended Data figure are generated from locked summaries and participant-level derived outputs only. Presentation scripts must not refit models, recompute neural targets, select representations or create new inferential tests. The canonical publication figure system is the current NMI v4 workflow documented in `FIGURE_GENERATION.md`.

## Remaining production items

Only author- and journal-production items remain: final author order and affiliations, contributions, funding/acknowledgements, competing interests, citation-manager refresh if needed, reporting-summary completion, journal formatting, and the final archived code release/DOI. No additional outcome-bearing scientific analysis is required for the current manuscript.
