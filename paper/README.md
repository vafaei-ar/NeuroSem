# Manuscript Workspace

This directory contains the submission-facing NeuroSem manuscript sources. The scientific evidence is locked; manuscript work should preserve the final inferential hierarchy and should not trigger new outcome-bearing analysis.

## Current NMI review master

- `NeuroSem_Nature_Manuscript_v0.6_NMI_revised.docx` is the current Nature Machine Intelligence-focused author-review master outside the repository working tree. It incorporates the multi-reviewer NMI revision, final main figures, ethics/data/code statements, explicit lambda-selection chronology, the complete neural-guided objective, and reviewer-facing Extended Data organization.
- `NMI_REVIEW_RESPONSE_V1.md` records how the NMI reviewer concerns were addressed and the scope limits that must remain intact.
- `NATURE_REVIEWER_STREAMLINING_V05.md` is retained as the preceding Nature-style reviewer-stage record.
- `NATURE_MANUSCRIPT_DRAFT_V3.md` is the last fully committed historical Markdown manuscript before the reviewer-stage Word revisions. Do not treat it as the latest NMI wording.
- `NATURE_SUBMISSION_PACKAGE.md` remains a historical Nature-facing editorial scaffold; the current submission strategy is NMI-focused.
- `REFERENCE_SOURCE_AUDIT.md` is updated for the NMI literature set and distinguishes external provenance/related-work references from NeuroSem-generated statistics.
- `FIGURE_GENERATION.md` documents figure-build provenance and workflow.

The NMI Word master remains the current submission-text master for this review round. A final Markdown back-port should be made after author review, once wording is no longer changing rapidly, rather than maintaining two competing substantive masters during revision.

## NMI central contribution

The manuscript is not positioned as a general downstream-performance improvement. Its central machine-learning claim is:

> Biological supervision should be evaluated by whether the representation it induces transfers to independent biological targets, not merely by improved fit to the training brain or conventional downstream benchmarks.

NeuroSem tests this criterion using a neural relational intervention developed from ChineseEEG and challenged on genuinely independent neural targets.

## Final evidence architecture

1. ChineseEEG provides reproducible neural relational geometry and the development target.
2. Neural-guided learning is established under sealed development evaluation in BERT and replicated qualitatively in multilingual E5.
3. An explicitly exploratory E5 dose-response identified lambda=0.10 as a development-stage candidate only; ChineseEEG run-07 and generic semantic outcomes had already been observed.
4. ZuCo provides the genuinely fresh cross-language EEG test, with 17/17 positive participant-level transfer effects.
5. SMN4Lang fMRI provides the prospective cross-modal validation, with 12/12 positive participant-level effects after a model-blind reliability gate.
6. TMNRED, Garnett Dream and directional inner speech are explicit transfer boundaries.
7. SMN4Lang MEG is a reliability boundary: the prospectively frozen 32-bin target failed before model evaluation, and the bounded 4/8/16-bin family also failed.
8. Generic semantic benchmark performance is distinct from external biological transfer.
9. AHBA is secondary/Extended Data material and does not establish a molecular mechanism.

## NMI reviewer-stage writing rules

1. Keep **target reliability**, **model learnability**, **candidate selection**, **fresh external biological transfer** and **conventional task performance** as distinct empirical stages.
2. Preserve the explicit history that lambda=0.10 was selected in exploratory development and could support a transfer claim only through genuinely fresh external neural targets.
3. Preserve all null/inconclusive external results and the MEG reliability failure.
4. Never describe SMN4Lang MEG as negative model transfer because no model evaluation was performed.
5. Do not imply raw EEG, fMRI and MEG RSA values share a common effect-size scale.
6. Describe the SMN4Lang fMRI effect as a small directional representational shift. +0.00085250 is about 0.7% of the text-only mean RSA; the evidential value lies in prospective independence and 12/12 directional consistency, not magnitude.
7. Treat cross-participant reliability as a necessary **measurement gate**, not evidence of semantic purity, causal relevance or mechanistic specificity.
8. State explicitly that fresh external transfer was evaluated for one frozen multilingual-E5 architecture. Generalization is across neural contexts, not yet model families.
9. Use **neural relational geometry**, **language-related neural geometry** and **external biological transfer** rather than claiming a universal semantic code or general model improvement.
10. Keep AHBA outside the primary transfer narrative.
11. Do not reopen model, lambda, participant, representation, ROI, lag, frequency, sensor, downstream-benchmark or molecular searches to improve the manuscript.

## NMI related-work positioning

The current reference audit includes:

- Moussa, Klakow & Toneva (ICLR 2025), brain-tuning with semantic downstream gains;
- Merlin, Moussa & Toneva (CoNLL 2026), comparison of brain/joint tuning with stimulus-only tuning;
- Hadidi et al. (Nature Communications 2026), robustness and confound risks in brain–LLM alignment;
- Xiao, Du & Lin (Nature Machine Intelligence 2026), brain-guided LLM reasoning improvements.

The submission-facing distinction is deliberate: recent work establishes that neural signals can improve neural fit and/or downstream behavior; NeuroSem asks whether the **biologically induced relational perturbation itself** transfers to neural systems that did not participate in model optimization or selection.

## Figure status

All four main figures have presentation-only reproducible builders:

- `scripts/paper/build_figure1_chineseeeg.py`
- `scripts/paper/build_figure2_zuco.py`
- `scripts/paper/build_figure3_smn4lang.py`
- `scripts/paper/build_figure4_boundaries.py`

The main figures are assembled strictly from locked summaries/participant outputs or locked numerical summaries. They do not refit models, recompute neural RDMs, select representations or create new inferential tests.

Figure 1 should foreground the machine-learning object: text -> embeddings -> pairwise model geometry + neural target -> relational loss -> frozen intervention -> external biological targets. Figure 4 remains an **outcome-status/generalization map**, not a cross-modality effect-size comparison.

## Extended Data organization

- **Extended Data Table 1:** analysis provenance and outcome visibility, including development, sealed holdout, exploratory dose-response, fresh ZuCo validation, prospective SMN4Lang fMRI validation and the MEG reliability boundary.
- **Extended Data Note 1:** secondary AHBA transcriptomic analyses and their frozen null conclusion.

The provenance table is referenced prominently from Methods rather than interrupting the main narrative.

## Reference and Word workflow

The NMI reference audit is stored in `REFERENCE_SOURCE_AUDIT.md`. Literature citations support datasets, models, related work, atlases and methodological context; they do not replace NeuroSem-generated numerical evidence.

The v0.6 Word file preserves Zotero-compatible citation fields and the Zotero bibliography field, including the new Xiao et al. NMI citation. A matching RIS export accompanies the Word master. After authors complete this review round, back-port the accepted wording into a new Markdown manuscript version before the final submission build.

## Remaining author/production items

- final author order, affiliations and corresponding-author information;
- author contributions;
- funding/acknowledgements;
- competing interests;
- final Zotero refresh/reconnection if needed;
- persistent archival DOI for the accepted/submission code snapshot;
- final NMI reporting-summary and formatting compliance pass.

No additional outcome-bearing scientific analysis is required for the reviewer-driven revision.

## Supporting documentation

- `NMI_REVIEW_RESPONSE_V1.md`
- `REFERENCE_SOURCE_AUDIT.md`
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