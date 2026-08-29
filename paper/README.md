# Manuscript Workspace

This directory contains the submission-facing NeuroSem manuscript sources. The scientific evidence is locked; manuscript work should preserve the final inferential hierarchy and should not trigger new outcome-bearing analysis.

## Current review master

- `NeuroSem_Nature_Manuscript_v0.5_nature_streamlined.docx` is the current author-review master outside the repository working tree. It incorporates the Nature-reviewer revisions, final main figures, ethics/data/code statements, explicit lambda-selection chronology, full neural-guided objective details, and the reviewer-facing Extended Data reorganization.
- `NATURE_REVIEWER_STREAMLINING_V05.md` records the exact editorial decisions applied in v0.5.
- `NATURE_MANUSCRIPT_DRAFT_V3.md` remains the last fully synchronized Markdown source before the reviewer-stage Word revisions. Do not treat it as the latest submission wording while v0.5 is under author review. A full Markdown synchronization should be performed after this review round to avoid maintaining two simultaneous substantive masters.
- `NATURE_SUBMISSION_PACKAGE.md` remains the Nature-facing editorial scaffold, figure architecture, claim limits and cover-letter core argument.
- `REFERENCE_SOURCE_AUDIT.md` contains the verified literature/source audit and the distinction between external provenance references and NeuroSem-generated statistics.
- `FIGURE_GENERATION.md` documents figure-build provenance and workflow.

## Final evidence architecture

1. ChineseEEG reproducible neural relational geometry.
2. Neural-guided learning under sealed development evaluation.
3. An explicitly exploratory E5 dose-response identified lambda=0.10 as a development-stage candidate only; ChineseEEG run-07 and generic semantic outcomes had already been observed, so they do not provide confirmatory evidence for that candidate.
4. ZuCo provides the fresh cross-language EEG test, with 17/17 positive participant-level transfer effects.
5. SMN4Lang fMRI provides the prospective cross-modal validation, with 12/12 positive participant-level effects after a model-blind reliability gate.
6. TMNRED, Garnett Dream and directional inner speech are explicit transfer boundaries.
7. SMN4Lang MEG is a reliability boundary: the prospectively frozen 32-bin target failed before model evaluation, and the bounded 4/8/16-bin family also failed.
8. Generic semantic benchmark performance is distinct from neural alignment.
9. AHBA is secondary/Extended Data material and does not establish a molecular mechanism.

## Reviewer-stage writing rules

1. Keep **target reliability**, **model learnability**, **candidate selection** and **fresh external transfer** as separate empirical stages.
2. Preserve the explicit history that lambda=0.10 was selected in exploratory development and was tested confirmatorily only on genuinely fresh external neural targets.
3. Preserve all null/inconclusive external results and the MEG reliability failure.
4. Never describe SMN4Lang MEG as negative model transfer because no model evaluation was performed.
5. Do not imply raw EEG, fMRI and MEG RSA values share a common effect-size scale.
6. Describe the SMN4Lang fMRI effect as a small directional representational shift. The manuscript explicitly notes that +0.00085250 is about 0.7% of the text-only mean RSA; the evidential value lies in prospective independence and 12/12 directional consistency, not magnitude.
7. Use **neural relational geometry** or **language-related neural geometry** rather than claiming pure semantic coding from naturalistic data.
8. Keep AHBA outside the primary transfer narrative; it is Extended Data/secondary material.
9. Do not reopen model, lambda, participant, representation, ROI, lag, frequency, sensor or molecular searches to improve the narrative.

## Figure status

All four main figures have presentation-only reproducible builders:

- `scripts/paper/build_figure1_chineseeeg.py`
- `scripts/paper/build_figure2_zuco.py`
- `scripts/paper/build_figure3_smn4lang.py`
- `scripts/paper/build_figure4_boundaries.py`

The main figures are assembled strictly from locked summaries/participant outputs or locked numerical summaries. They do not refit models, recompute neural RDMs, select representations or create new inferential tests.

Figure 4 should remain an **outcome-status/generalization map**, not a cross-modality effect-size comparison. The final standalone MEG panel and AHBA molecular-null panel remain available for Extended Data/supporting use.

## Extended Data organization for v0.5

- **Extended Data Table 1:** analysis provenance and outcome visibility, including development, sealed holdout, exploratory dose-response, fresh ZuCo validation, prospective SMN4Lang fMRI validation and the MEG reliability boundary.
- **Extended Data Note 1:** secondary AHBA transcriptomic analyses and their frozen null conclusion.

The full provenance table is referenced prominently from Methods but is no longer embedded in the main Methods flow.

## Reference and Word workflow

The reference audit is stored in `REFERENCE_SOURCE_AUDIT.md`. Literature citations support dataset, model, atlas and methodological provenance; they do not replace NeuroSem-generated numerical evidence.

The current v0.5 Word file preserves Zotero-compatible citation fields and the Zotero bibliography field. Once the authors complete this review round, synchronize the accepted wording back into a new Markdown manuscript version before the final submission build.

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
- `../docs/e5_neural_tuning_protocol_v1.md`
- `../docs/e5_pareto_exploratory_protocol_v1.md`

Detailed frozen protocols and reconciled scripts remain the methods/provenance source of truth.