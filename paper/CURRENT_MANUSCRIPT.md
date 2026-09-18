# Current publication master

**Recorded:** 2026-09-18

The current Word masters are maintained outside the Git working tree during final author review. This file records the exact binaries used for submission preparation.

## Main manuscript

### Clean

- File: `NeuroSem_Nature_Manuscript_v1.19.3_clean.docx`
- SHA-256: `aea651a20f653c29ac28de61792864cda7d81293d2b7bc6f689f40c958587061`
- Size: 2,848,688 bytes
- Rendered length: 33 pages

### Tracked changes

- File: `NeuroSem_Nature_Manuscript_v1.19.3_tracked.docx`
- SHA-256: `a3379306a94e9eccb48f109a13a5beb6407193cef58fdade2b3b542bbc61ddd1`
- Size: 3,274,638 bytes
- Rendered length: 35 pages
- Tracked revisions: 54 insertions and 23 deletions

Current title: **Brain-derived relational supervision transfers language-model representations across independent neural datasets**

v1.19.3 is a reviewer-response and presentation-clarification pass over the scientifically locked v1.19.2 package. It adds no model training, target definition, dose/model selection, statistical family, or outcome-bearing inference.

The revision makes the reliability/RSA distinction explicit, shows actual text-only and neural-guided residual RSA in Figure 1, clarifies that negative absolute ZuCo RSA is compatible with a positive paired displacement, distinguishes the structured non-neural surrogate from the MPNet backbone experiment, explicitly addresses a cortex-wide/global-offset alternative, interprets the high-dose spatial pattern as redistribution rather than language-selective sharpening, corrects the Extended Data versus Supplementary chronology cross-reference, and adds an Extended Data table summarizing dataset-specific RDM construction and nuisance families.

## Supplementary Information

### Clean Word master

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.3_clean.docx`
- SHA-256: `dc231f80a2390686b82efda00ffee6c039e507d13a61ef74a3c987b40e208830`
- Size: 65,784 bytes
- Rendered length: 13 pages

### Tracked changes

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.3_tracked.docx`
- SHA-256: `c0fd25bbf41ced34e0de0b951585319575abc2751d23becb9232ba7e26e2505a`
- Size: 66,586 bytes
- Rendered length: 13 pages
- Tracked revisions: 20 insertions and 20 deletions

### Submission PDF

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.3.pdf`
- SHA-256: `7aa68654c70633c2f9529a2166bc389d0ccf3d9ad0d99cd104d94997a23dba54`
- Size: 711,596 bytes
- Rendered length: 13 pages

The Supplement now uses the same structured-surrogate terminology as the manuscript and explicitly states the high-dose spatial-redistribution caveat. Scientific values are unchanged.

## Quality checks

- Every page of the clean and tracked manuscript and Supplement was rendered and visually inspected after the final layout patch.
- DOCX ZIP/package integrity passes for all four Word files.
- Main manuscript retains 22 `ZOTERO_ITEM` citation fields plus one `ZOTERO_BIBL` bibliography field.
- Clean files contain no tracked revisions and have Track Changes disabled.
- The tracked manuscript contains 54 insertions / 23 deletions; the tracked Supplement contains 20 insertions / 20 deletions.
- Accepting all tracked changes yields the same final visible text as the corresponding clean file for both manuscript and Supplement.
- The manuscript retains the native Word math objects used for the relational objective and estimand.
- No comments remain.
- Accessibility audit: 0 high and 0 medium findings in all four Word files. The main manuscript has 11 low findings from intentionally displayed raw URLs in Data/Code Availability; the Supplement has 0 findings.
- Final embedded figure bytes match the canonical v1.19.3 figure-build artifacts exactly.

## Figure code snapshot

The immutable submission figure-code snapshot cited by the v1.19.3 manuscript is commit:

`b122fdeea10b613188aec3a49884133ce3c2eb6b`

The canonical submission-facing figure entry point remains:

```text
scripts/paper/final_figures/build_all_figures.py
```

Exact-commit RunRelay job `T8M3V6K2` rebuilt and validated the 4-main plus 4-Extended-Data v1.19.3 figure package with exit code 0. The rebuild was presentation-only and recorded `scientific_values_changed: false`.

Embedded PNG SHA-256 fingerprints:

- Main Figure 1: `6dbeb36e49377c16e5b090e657b3c3da77a55e66b1eacc8959d388b35ad714da`
- Main Figure 2: `833a1205f8d9e859059d0e9cf04f00961aff866c79bd37984ee00d033d3b228e`
- Main Figure 3: `287cd0c72c604dc1f604f9049d31b1e5f26145462090d68c1b68d9d6b2f5dea7`
- Main Figure 4: `282d6b3eda849c7ad13eda3cec05dc768c46c9f692ed226616787bf4e25c1dd6`
- Extended Data Figure 1: `2248958b348c55e9f86f3822a75dc621984ee650d9e3236ef407d4da0731a873` (unchanged)
- Extended Data Figure 2: `b09cd003652b9425433412439696cad8cf5c687c19e60d1c022c316868630f90`
- Extended Data Figure 3: `3a9df74ab1932609812e9df32768e0c67f72a0848d496482f4276f0bb73626c0`
- Extended Data Figure 4: `1e704f232b22f07b6fa68c085509ff57c2425e2da3323587d94a9c3b23bd6708`

## Citation-management note

No new bibliography entries were introduced in v1.19.3. The existing live Zotero fields were preserved unchanged. A reviewer suggestion to broaden citations for generic methodological components (for example LoRA/CKA/contrastive-learning background) remains an author-side Zotero-library update because the current ChatGPT workspace does not expose a Zotero connector. No unmanaged citation was inserted into the Word master.

## Status

v1.19.3 closes the substantive scientific/presentation issues identified in the latest review without reopening the scientific analysis. The only remaining manuscript-content task from that review is the optional Zotero-managed expansion of generic methods citations noted above.

Author-level submission decisions remain external to this document record: whether the initial submission is double-anonymized, which determines author/affiliation/contribution/competing-interest metadata in the manuscript file; and whether to shorten the 112-character title.

The repository intentionally does not commit `.docx` masters. Frozen protocol/result documents remain authoritative for analysis chronology, while the Word files recorded here are authoritative for current submission wording and layout.
