# Manuscript workspace

This directory contains the submission-facing NeuroSem manuscript documentation and figure-generation workflow. The scientific evidence is locked; manuscript work must preserve the final inferential hierarchy and must not trigger new outcome-bearing analysis.

## Current manuscript master

The current author-review master is **NeuroSem_Nature_Manuscript_v1.4_publication_clean.docx**, with **NeuroSem_NMI_Supplementary_Technical_Tables_v1.4_publication_clean.docx** as the companion Supplementary Information. These publication-clean Word files are maintained outside the Git working tree during final author review to avoid committing large binary revisions. Historical Markdown manuscript drafts have been removed from the current tree; their history remains recoverable through Git.

The v1.4 publication-clean manuscript:

- defines neural geometry and external neural transfer in plain language;
- foregrounds the primary ChineseEEG → ZuCo → SMN4Lang evidence chain;
- keeps reverse-direction, model-family, neural-specificity, participant-by-stimulus and model-space analyses explicitly post-confirmatory;
- preserves TMNRED, Garnett Dream, directional inner speech and MEG reliability boundaries;
- removes internal workflow metadata, reviewer-response bookkeeping, Git commit hashes and drafting placeholders from publication-facing text.

## Current evidence architecture

1. ChineseEEG establishes a reproducible development neural geometry and model learnability.
2. ZuCo is the first fresh external test: 17/17 participants show positive neural-guided minus text-only transfer.
3. SMN4Lang fMRI is the prospective cross-modal test: 12/12 participants show positive transfer after the model-blind reliability gate.
4. Post-confirmatory shuffled-neural controls show that the genuine item-relational neural correspondence contributes substantially more external transfer than a matched destroyed-correspondence objective on both targets.
5. Reverse fMRI-to-ZuCo transfer establishes bidirectionality within E5; larger reverse doses are post-confirmatory characterization.
6. The six-model panel shows stable bidirectional portability in E5-large and E5-base under the common protocol, but not universally across the tested encoders.
7. TMNRED, Garnett Dream and directional inner speech define transfer boundaries.
8. SMN4Lang MEG failed its model-blind reliability gate, so no model transfer test was performed.
9. AHBA remains a secondary mechanistic extension with prespecified molecular nulls.

## Writing rules that must remain intact

- Keep reliability, learnability, candidate selection and external transfer as distinct empirical stages.
- Do not describe the exploratory lambda=0.10 development choice as confirmatory optimization.
- Do not describe the post-confirmatory reverse dose-response as a prospective result.
- Do not describe the six-model panel as isolating architecture causally or as showing E5 uniqueness.
- Do not describe SMN4Lang MEG as negative transfer.
- Do not imply that raw EEG, fMRI and MEG RSA values share a common effect-size scale.
- Describe the fMRI effect as small in absolute magnitude but prospectively consistent across all 12 participants.
- Preserve all null and inconclusive external outcomes.

## Submission-facing files retained in Git

- `FIGURE_GENERATION.md` — reproducible figure-build workflow and provenance.
- `REFERENCE_SOURCE_AUDIT.md` — literature/reference audit for datasets, models and related work.
- `NATURE_REPORTING_SUMMARY_DRAFT.md` — reporting-summary working document.
- `README.md` — this current manuscript status record.

Historical manuscript drafts, positioning notes, reviewer-streamlining notes and obsolete submission scaffolds are intentionally absent from the current tree. Git history remains the archival record.

## Figure status

The four main figures are generated from locked summaries and participant-level derived outputs only. Presentation scripts must not refit models, recompute neural targets, select representations or create new inferential tests.

## Remaining production items

Only author- and journal-production items remain, such as final author order and affiliations, contributions, funding/acknowledgements, competing interests, citation-manager refresh where needed, reporting-summary completion and final archival release/DOI. No additional outcome-bearing scientific analysis is required for the current manuscript.
