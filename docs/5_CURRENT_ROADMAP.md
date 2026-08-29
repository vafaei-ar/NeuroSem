# 5. Current Roadmap

**Last updated:** 2026-08-29

NeuroSem is now in an **evidence-locked manuscript-consolidation phase** for the primary paper, with a separate **deferred post-confirmatory generalization queue** documented below. The immediate goal remains to finish the submission package and preserve the current prospective evidential chain. Any newly proposed outcome-bearing experiment must remain explicitly secondary/post-confirmatory and must be frozen before execution.

## Final scientific position for the present paper

The project has six core evidence blocks:

1. **ChineseEEG Little Prince:** reproducible neural relational geometry and neural-guided model learning under held-out evaluation.
2. **ZuCo 2.0 normal reading:** independent cross-language EEG reliability and positive frozen transfer, **17/17** participants positive.
3. **SMN4Lang fMRI:** model-blind language-network reliability followed by positive frozen cross-modal E5 transfer, **12/12** participants positive. This is the prospective capstone.
4. **Transfer boundaries:** TMNRED null transfer, Garnett Dream null/inconclusive transfer despite reliable neural geometry, and directional inner-speech out-of-task null/negative transfer.
5. **SMN4Lang MEG reliability boundary:** the prospectively frozen 32-bin sensor-level target failed its model-blind reliability gate; a separately frozen 4/8/16-bin family also failed. No model evaluation was performed. The MEG branch is closed for this paper.
6. **AHBA transcriptomics:** completed primary mechanistic nulls and an exploratory bilateral-processing sensitivity. This remains secondary/Extended Data material.

## Central manuscript claim

> Human neural geometry can provide a transferable relational constraint on language representations, with effects that generalize across independent brains, languages and measurement modalities, but not universally across neural contexts.

Do not frame the work as showing a generally better language model, a universal semantic geometry, a negative MEG transfer effect, or a specific transcriptomic mechanism.

## Evidence hierarchy

```mermaid
flowchart TD
    A[ChineseEEG reproducible geometry] --> B[Neural-guided learning]
    B --> C[ZuCo cross-language EEG transfer]
    C --> D[SMN4Lang prospective fMRI transfer]
    D --> E[Transfer boundaries: TMNRED / Garnett / directional]
    D --> F[MEG reliability boundary: no model test]
    A --> G[Secondary AHBA mechanistic nulls]
```

## SMN4Lang final decisions

### fMRI

The primary fMRI analysis is complete and positive:

- reliability mean residual LOO **0.65327**, 95% CI **[0.63945,0.66843]**, **12/12** positive, exact one-sided **p = 0.000244**;
- frozen E5 transfer mean delta **+0.00085250**, 95% CI **[+0.00078966,+0.00091398]**, **12/12** positive, exact one-sided **p = 0.000244**.

No fMRI target-side model/representation search should be reopened for the primary analysis.

### MEG

The MEG branch is also complete:

- prospective 32-bin sensor-level RMS mean LOO reliability **0.007713**;
- 95% CI **[-0.007627,+0.021655]**;
- exact one-sided **p = 0.16870**;
- gate failed; no E5 evaluation.

The bounded post-confirmatory 4/8/16-bin family produced no familywise-reliable target. This demonstrates that the failed 32-bin target was not simply rescued by straightforward temporal coarsening within the same representation family. It does **not** establish that MEG generally lacks transferable language-related structure.

No further MEG alternatives should be run for the present manuscript.

## Main-paper architecture

### Figure 1
Conceptual framework, ChineseEEG reliability-led target, residual model correspondence, sealed BERT neural-guided learning, and E5/generic-semantic dissociation.

### Figure 2
ZuCo cross-language EEG reliability and paired frozen E5 transfer.

### Figure 3
SMN4Lang prospective fMRI reliability gate, frozen causal semantic-to-fMRI mapping, and paired participant transfer. This is the visual centerpiece.

### Figure 4
Generalization/boundary map: harmonized external outcomes, SMN4Lang MEG reliability boundary, independence/design matrix, and generic semantic benchmark/conceptual conclusion. Raw EEG/fMRI/MEG RSA values must not be presented as a common effect-size scale.

AHBA remains Extended Data / Supplementary unless requested editorially.

## Manuscript state

Authoritative submission-facing files:

- `paper/NATURE_SUBMISSION_PACKAGE.md`
- `paper/NATURE_MANUSCRIPT_DRAFT_V2.md`
- `paper/REFERENCE_SOURCE_AUDIT.md`

`NATURE_MANUSCRIPT_DRAFT_V1.md`, `outline.md`, `results.md`, and `methods.md` are retained as development history/scaffolds and should not override v2.

The current Word submission working copy was produced from v2 with Zotero-compatible fields outside the repository build flow; the repository source of truth remains the Markdown manuscript plus verified reference audit until a binary manuscript packaging policy is deliberately adopted.

## Immediate operational order

1. Complete and interpret the currently running post-confirmatory robustness suite without changing its frozen design.
2. Keep canonical documentation synchronized with the final fMRI and MEG decisions.
3. Complete submission-facing manuscript/figure consistency work from locked outputs.
4. Keep the reference/source audit synchronized with citation edits.
5. Recheck exact job/commit/artifact provenance for every main-text numerical result and figure source.
6. Perform final repository hygiene and submission-readiness checks.

## Deferred post-confirmatory generalization queue

These are **not required to preserve the validity of the current primary claim**. They are designed to address stronger generalization questions and must remain secondary/post-confirmatory because the current external outcomes are already known.

1. **Second-model-family robustness.** Test the same neural-relational training principle in one prespecified substantially different multilingual sentence-representation model, with no external-target-driven model/lambda search. Highest priority for the remaining NMI model-generality concern.
2. **Bidirectional cross-modal transfer analysis.** Use the already-frozen SMN4Lang fMRI representation as a source relational constraint, select/freeze the fMRI-guided candidate using source-only validation, then test transfer to independent EEG, with ZuCo as the primary EEG target. Highest conceptual priority.
3. **Full model-family x source-modality factorial extension.** Defer unless the first two experiments are informative and a genuinely independent fMRI target is available; otherwise the design is asymmetric because SMN4Lang cannot be both the fMRI training source and an independent fMRI target.

The detailed design and guardrails are frozen at the planning level in `15_POSTCONFIRMATORY_GENERALIZATION_TODO.md`. Execution requires a separate committed protocol and named RunRelay task for each experiment.

## Stopping rules

- No new dataset search for positive transfer within the current primary analysis.
- No reopening of ZuCo or SMN4Lang fMRI target-side model/representation choices.
- No rescue search for TMNRED or Garnett.
- No E5 evaluation on failed MEG targets.
- No further MEG bands, sensors, sources, latencies or temporal alternatives.
- No additional AHBA significance search or molecular-panel screening.
- Preserve all confirmatory nulls and reliability failures.
- Any Experiment A/B/C execution must use a separately frozen protocol, report all prespecified outcomes, and stop after the prespecified analysis rather than launching outcome-driven rescue searches.

## Related documents

- `1_PROJECT_OVERVIEW.md`
- `3_RESULTS_AND_COMPARISONS.md`
- `4_EXPERIMENT_LEDGER.md`
- `8_SMN4LANG_PROSPECTIVE_VALIDATION.md`
- `9_SMN4LANG_FMRI_RELIABILITY_FREEZE.md`
- `10_SMN4LANG_FMRI_E5_TRANSFER_RESULT.md`
- `12_SMN4LANG_MEG_MODEL_BLIND_PROBE_PROTOCOL.md`
- `13_SMN4LANG_MEG_REPRESENTATION_FREEZE.md`
- `14_SMN4LANG_MEG_EXPLORATORY_GRANULARITY_FREEZE.md`
- `15_POSTCONFIRMATORY_GENERALIZATION_TODO.md`
- `paper/NATURE_SUBMISSION_PACKAGE.md`
- `paper/NATURE_MANUSCRIPT_DRAFT_V2.md`
- `paper/REFERENCE_SOURCE_AUDIT.md`
