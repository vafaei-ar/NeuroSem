# Manuscript Workspace

This directory contains the submission-facing NeuroSem manuscript sources. The scientific evidence is locked; manuscript work should preserve the final inferential hierarchy and should not trigger new outcome-bearing analysis.

## Authoritative current files

- `NATURE_SUBMISSION_PACKAGE.md` — final Nature-facing editorial scaffold, figure architecture, claim limits and cover-letter core argument.
- `NATURE_MANUSCRIPT_DRAFT_V3.md` — current main manuscript source. This version was synchronized from the author-edited Word working copy `NeuroSem_Nature_Manuscript_v0.1.docx` (SHA256 `1f4185dd5266a03d5de04e7e8f2991e3c9796997c146a8ce965bb7634ec5b7b7`) and supersedes v2 for substantive wording, citation placement and submission-facing figure notes.
- `REFERENCE_SOURCE_AUDIT.md` — verified literature/source audit and the distinction between external provenance references and NeuroSem-generated statistics.
- `FIGURE_GENERATION.md` — figure-build provenance and workflow notes.
- `FIGURE_TABLE_PLAN.md` — historical/working figure-table planning; where it conflicts with `NATURE_SUBMISSION_PACKAGE.md`, the submission package is authoritative.

## Retained development history

The following files are intentionally retained for provenance but are not the current manuscript source of truth:

- `NATURE_MANUSCRIPT_DRAFT_V1.md`
- `NATURE_MANUSCRIPT_DRAFT_V2.md`
- `outline.md`
- `results.md`
- `methods.md`
- `NATURE_POSITIONING.md`

Do not silently merge older wording or claims back into v3.

## Final evidence architecture

1. ChineseEEG reproducible neural relational geometry.
2. Neural-guided learning under sealed development evaluation.
3. ZuCo cross-language EEG transfer, 17/17 positive.
4. SMN4Lang prospective cross-modal fMRI transfer, 12/12 positive.
5. TMNRED, Garnett Dream and directional inner speech as transfer boundaries.
6. SMN4Lang MEG as a reliability boundary: the prospectively frozen target failed before model evaluation; a bounded 4/8/16-bin family also failed.
7. Generic semantic benchmark dissociation.
8. AHBA as secondary/Extended Data mechanistic nulls and exploratory sensitivity.

## Writing rules

1. Keep **target reliability**, **model learnability** and **external transfer** as separate empirical claims.
2. Preserve all null/inconclusive external results and the MEG reliability failure.
3. Never describe SMN4Lang MEG as negative model transfer because no model evaluation was performed.
4. Do not imply raw EEG, fMRI and MEG RSA values share a common effect-size scale.
5. Describe the SMN4Lang fMRI effect as small in absolute RSA units but prospectively frozen and directionally consistent.
6. Use **neural relational geometry** or **language-related neural geometry** rather than claiming pure semantic coding from naturalistic data.
7. Keep AHBA outside the primary transfer claim.
8. Link each main-text number to its locked source output, exact analysis status and inferential unit.
9. Do not reopen model, representation, participant, ROI, lag, frequency, sensor or molecular searches to improve the narrative.

## Current figure status

All four main-figure composites now have presentation-only reproducible builders:

- `scripts/paper/build_figure1_chineseeeg.py` — conceptual relational constraint, ChineseEEG target reliability, held-out BERT correspondence, sealed run-07 model comparison and generic semantic-benchmark dissociation.
- `scripts/paper/build_figure2_zuco.py` — frozen ChineseEEG-to-ZuCo design, participant-level ZuCo reliability, paired λ=0 versus λ=0.10 RSA and participant transfer deltas.
- `scripts/paper/build_figure3_smn4lang.py` — prospective SMN4Lang design, model-blind fMRI reliability, frozen causal E5-to-fMRI mapping, paired participant RSA and participant transfer deltas.
- `scripts/paper/build_figure4_boundaries.py` — harmonized external outcome map, SMN4Lang MEG reliability boundary, independence/design matrix and generic semantic-benchmark dissociation.

The older `build_manuscript_figures_v1.py` / `v2.py` builders remain useful for the reading-reliability overview, the final standalone MEG reliability-boundary panel, AHBA Extended Data candidate and normalized source tables.

The main figures are assembled strictly from already locked summary/participant outputs or locked numerical summaries. They do not refit models, recompute neural RDMs, select representations, or create new inferential tests.

The remaining submission-production task is to integrate Figures 1–4 into the author-edited Word manuscript, remove obsolete figure placeholders/supporting-only artwork, and render the complete DOCX for visual QA.

## Reference and Word workflow

The reference audit is stored in `REFERENCE_SOURCE_AUDIT.md`. Literature citations support dataset, model, atlas and methodological provenance. They do not replace NeuroSem-generated numerical evidence.

The author-edited Word file is explicitly synchronized into `NATURE_MANUSCRIPT_DRAFT_V3.md`. The repository Markdown remains the scientific manuscript source of truth; the Word manuscript is the submission-packaging master for Zotero fields, page layout and final figure placement. Any future substantive Word edit should be back-ported into the Markdown source before the next submission build.

## Supporting documentation

- `../docs/1_PROJECT_OVERVIEW.md`
- `../docs/3_RESULTS_AND_COMPARISONS.md`
- `../docs/4_EXPERIMENT_LEDGER.md`
- `../docs/5_CURRENT_ROADMAP.md`
- `../docs/8_SMN4LANG_PROSPECTIVE_VALIDATION.md`
- `../docs/9_SMN4LANG_FMRI_RELIABILITY_FREEZE.md`
- `../docs/10_SMN4LANG_FMRI_E5_TRANSFER_RESULT.md`
- `../docs/12_SMN4LANG_MEG_MODEL_BLIND_PROBE_PROTOCOL.md`
- `../docs/13_SMN4LANG_MEG_REPRESENTATION_FREEZE.md`
- `../docs/14_SMN4LANG_MEG_EXPLORATORY_GRANULARITY_FREEZE.md`

Detailed frozen protocols and reconciled scripts remain the methods/provenance source of truth.
