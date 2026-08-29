# Nature Machine Intelligence reviewer-response strategy

**Status:** manuscript-level revision completed on 2026-08-28 without new outcome-bearing analysis.

This document records how the NMI-focused manuscript addresses the independent multi-reviewer critique. It is an editorial/provenance record, not a retrospective claim of preregistration.

| Reviewer concern | Revision implemented | Scientific status |
|---|---|---|
| NMI relevance and novelty relative to recent brain-guided LLM work | Reframed the central contribution as **external biological transfer of an induced representation** rather than task-performance improvement; added direct comparison with Xiao, Du & Lin (Nature Machine Intelligence, 2026). | Interpretation only; no new analysis. |
| Prior brain-tuning literature | Added Moussa et al. (ICLR 2025), Merlin et al. (CoNLL 2026), Hadidi et al. (Nature Communications 2026), and Xiao et al. (Nature Machine Intelligence 2026) to distinguish performance-oriented brain guidance from independent-neural transfer and to motivate robustness safeguards. | Literature positioning only. |
| No stable downstream semantic-performance gain | Made this an explicit boundary of the claim: NeuroSem tests portability of a biologically induced representational change, not general language-model capability improvement. | Existing locked benchmark result retained. |
| Very small external RSA increments | Retained the absolute values and added the fMRI context that +0.00085250 is about 0.7% of the text-only mean RSA. Explicitly distinguish **evidence for transfer** from **magnitude of transfer**. | Existing locked results only. |
| External transfer demonstrated in one model family | Added explicit limitation: BERT and multilingual E5 establish learnability during development, but all genuinely fresh external transfer tests used one frozen multilingual-E5 candidate. Generalization is therefore across neural contexts, not model architectures. | Scope clarification only. |
| Reliability could be mistaken for semantic or biological validity | Added explicit statement that cross-participant reliability is a necessary measurement prerequisite, not evidence of semantic purity, causal relevance or mechanistic specificity. | Conceptual clarification only. |
| lambda=0.10 development selection | Preserved the full chronology: the E5 dose-response reused already-observed ChineseEEG run-07 and generic semantic outcomes and was exploratory; lambda=0.10 became a development-stage candidate that could support a transfer claim only on genuinely fresh neural targets. ZuCo and SMN4Lang outcomes were not used to select lambda. | Provenance clarification; no relabeling of exploratory outcomes as confirmatory. |
| One-sided inference | Methods now state that directional alternatives were fixed before the corresponding fresh external outcomes, motivating one-sided exact sign-flip tests. | Matches frozen external protocols. |
| Bootstrap specification | Methods now identify participants as the resampling unit, 10,000 resamples where specified, and percentile 95% intervals. | Verified from frozen analysis code; no recomputation. |
| Researcher degrees of freedom / multiplicity | Extended Data provenance separates development, sealed, exploratory, fresh-external and post-confirmatory analyses. The manuscript explicitly makes no omnibus significance claim over the full research program. | Reporting clarification only. |
| Heterogeneous external datasets could look like a meta-analysis | Figure 4 and text describe **outcome status**, not a common effect-size scale, and explicitly prohibit direct comparison/pooling of raw EEG/fMRI RSA deltas. | Presentation only. |
| MEG could be misread as negative model transfer | Main text is compressed to the reliability-gate logic. The manuscript states that no model evaluation was performed because the target failed the prespecified model-blind gate. | Existing locked null boundary retained. |
| AHBA distracts from the main NMI claim | Transcriptomics remains secondary Extended Data material and does not support the main representational-transfer claim. | Presentation only. |
| Reproducibility / permanent archive | Code Availability now commits to archiving the exact accepted/submission snapshot with a persistent DOI, environment specification and reproducibility entry points before publication. | Production task, not scientific analysis. |
| Figure 1 should foreground the ML object | Legend and manuscript framing now describe the pipeline as text -> embeddings -> pairwise model geometry + neural target -> relational loss -> frozen intervention -> external biological transfer. Scientific plots remain locked. | Presentation only. |

## NMI-specific central claim

The manuscript should be judged on the following claim, not on a claim of improved generic language-model capability:

> Biological supervision should be evaluated by whether the representation it induces transfers to independent biological targets, not merely by improved fit to the training brain or conventional downstream benchmarks. NeuroSem provides evidence that a neural relational intervention learned in development can produce a small but reproducible directional perturbation that transfers to genuinely independent human neural systems.

## Scope limits retained

- The external effects are small in absolute RSA units.
- External transfer is demonstrated for one frozen multilingual-E5 architecture.
- Naturalistic neural geometry is biologically composite and is not equated with a pure semantic code.
- TMNRED, Garnett Dream and directional inner speech remain null/inconclusive boundary results.
- SMN4Lang MEG is a reliability boundary, not negative model transfer.
- No new lambda, layer, model, ROI, HRF/lag, MEG representation, downstream benchmark or external dataset is to be searched as a manuscript-rescue analysis.

## Submission-facing distinction from recent work

Recent brain-guided model studies establish that neural signals can improve neural alignment and/or conventional downstream performance. NeuroSem asks a complementary question: whether the **induced biological relational constraint itself** survives transfer to neural representational spaces that did not participate in optimization or model selection. The manuscript therefore treats independent biological transfer as a separate evaluation axis from task-performance gain.
