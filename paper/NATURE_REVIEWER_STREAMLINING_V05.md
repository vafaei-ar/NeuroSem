# Nature reviewer streamlining v0.5

**Date:** 2026-08-28

This note records the reviewer-facing editorial changes applied to the Word review master `NeuroSem_Nature_Manuscript_v0.5_nature_streamlined.docx`. No new outcome-bearing analysis was introduced.

## Decisions applied

1. **Retain explicit fMRI magnitude context.** The manuscript keeps the statement that the SMN4Lang mean increment (+0.00085250) is approximately 0.7% of the text-only mean RSA and explicitly interprets it as a small directional representational shift rather than a large gain in neural prediction or model capability.
2. **Move analysis provenance to Extended Data.** The full chronology/status table is now `Extended Data Table 1 | Analysis provenance and outcome visibility`. Main Methods contains a prominent pointer to this table.
3. **Make lambda selection history explicit.** The manuscript states that the lambda=0.10 candidate arose from an explicitly exploratory, prespecified E5 dose-response after ChineseEEG run-07 and generic semantic outcomes were already known. ZuCo and SMN4Lang are therefore the genuinely fresh external tests of this development-stage candidate.
4. **Compress the MEG Results.** Main Results now reports the failed prospective reliability gate, the bounded 4/8/16-bin model-blind sensitivity family, and the decision not to evaluate E5. Sensor-level representation details remain in Methods. The result is described only as a representation-specific reliability boundary.
5. **Move AHBA out of the primary manuscript narrative.** The transcriptomic Methods paragraph is now an Extended Data note. The main Discussion retains only the limitation that secondary transcriptomic analyses do not establish a specific molecular mechanism.
6. **Preserve heterogeneous external outcomes categorically.** Figure 4 and the text continue to avoid treating raw EEG/fMRI RSA differences as a common effect-size scale.

## Word QA

The v0.5 DOCX was rendered after the edits and visually inspected page by page. Extended Data now begins on a separate page so the provenance table is not split awkwardly from its heading. Zotero-compatible fields and the bibliography field remain present.

## Source synchronization status

`NATURE_MANUSCRIPT_DRAFT_V3.md` remains the last fully synchronized Markdown source before the reviewer-stage Word revisions. The v0.5 Word document is the current author-review master. A full Markdown synchronization should be performed after the present author review so substantive review edits are not duplicated across two simultaneous masters.