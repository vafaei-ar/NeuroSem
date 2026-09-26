# Current publication master

**Recorded:** 2026-09-18

The current Word masters are maintained outside the Git working tree during final author review. This file records the exact binaries used for submission preparation.

## Main manuscript

### Clean

- File: `NeuroSem_Nature_Manuscript_v1.19.5_clean.docx`
- SHA-256: `ff2e2ba5582f47329c1ba9395e06366e97ae1f4960454be69d1d81c410857008`
- Size: 2,880,129 bytes
- Rendered length: 33 pages

### Tracked changes

- File: `NeuroSem_Nature_Manuscript_v1.19.5_tracked.docx`
- SHA-256: `cae51481630619605d09dc1a0a1f465fb3f06577dc7347948c21b7f183d70e72`
- Size: 2,881,333 bytes
- Rendered length: 35 pages
- Tracked revisions: 26 insertions and 26 deletions

Current title: **Brain-derived relational supervision transfers language-model representations across EEG and fMRI**

v1.19.5 is a language-only readability pass over the scientifically locked v1.19.4 package. It introduces no new model training, neural analysis, target definition, dose/model selection, statistical family, figure change, or outcome-bearing inference.

## Post-v1.19.5 result awaiting integration

Since v1.19.5 was produced, the previously frozen displacement-matched MPNet specificity experiment completed. The selected structured surrogate dose was `lambda=0.03`, matched to the genuine-neural arm on source-side `1-CKA` before external outcomes were opened.

The prespecified participant-level genuine-neural minus matched-surrogate contrast was positive on both external targets:

- ZuCo: mean **+0.00138471**, 15/17 positive, 95% CI **[+0.00087856,+0.00190007]**, Holm-adjusted two-sided sign-flip **P=0.00012207**.
- SMN4Lang fMRI: mean **+0.00189761**, 12/12 positive, 95% CI **[+0.00172727,+0.00204934]**, Holm-adjusted two-sided sign-flip **P=0.00048828**.

The matched surrogate itself was near-zero/inconsistent on ZuCo and negative on fMRI. The defensible interpretation is specificity relative to this structured non-neural control at comparable displacement, not neural uniqueness.

**Planned next Word revision:** v1.19.6 should integrate this result into the specificity figure/text, Results, Methods, Discussion and Supplement. The separate target-compatibility mechanism project is not a prerequisite for v1.19.6 and should not be imported wholesale into the NMI paper. Live status is recorded in `docs/CURRENT_NMI_AND_MECHANISM_STATUS.md`.

The revision shortens and clarifies the title, reduces repetitive framing in the Abstract and Introduction, defines lambda before the primary Results, removes low-value development-stage number lists from the narrative, makes the reverse-transfer transition explicit, simplifies regional and boundary wording, and tightens the Discussion. The Supplement and all scientific figures are unchanged.

## Supplementary Information

### Clean Word master

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.4_clean.docx`
- SHA-256: `de62fd9f53b7d5fed52ebd1894bce6311f968f464fce30c44d7de603f96e69fa`
- Size: 65,931 bytes
- Rendered length: 13 pages

### Tracked changes

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.4_tracked.docx`
- SHA-256: `2b194e3de1774fbcdb2585e68bf4e1fe348abee2d736044aa79f7ba1fdb77337`
- Size: 65,990 bytes
- Rendered length: 13 pages
- Tracked revisions: 1 insertion and 0 deletions

### Submission PDF

- File: `NeuroSem_NMI_Supplementary_Technical_Tables_v1.19.4.pdf`
- SHA-256: `65356d77249897944aca8b254c33e2a6d892403d3d0cb83bfeaa8824299a4945`
- Size: 712,316 bytes
- Rendered length: 13 pages

The Supplement now states explicitly that Supplementary Table 11 uses the frozen two-contrast regional max-stat family, whereas Supplementary Table 13 uses a separate post-confirmatory five-dose specificity family.

## Portable reference additions

Seven canonical method references were added as Zotero-compatible Word citation fields and supplied as portable library exports:

- `NeuroSem_v1.19.4_new_references.ris`, SHA-256 `2cc64051579323a078456966ff1f5eefcc08396b19b13f0b845b57ba8cb045cf`
- `NeuroSem_v1.19.4_new_references.bib`, SHA-256 `43fbccb582c6087cae1fe26f1af5273e8cb1c4645efc8046f18ba06250a5ef94`
- `NeuroSem_v1.19.4_new_references.json`, SHA-256 `73e846dcab88a1da334c5cbbeace3ca5a9822bbc3e36a6e5f93eafbf575d5605`

The file-based workflow preserves existing Zotero fields but cannot know the item keys assigned by the author's local Zotero library after import. The seven new citations should therefore be imported via RIS and reconnected/refreshed with Zotero Add/Edit Citation before relying on cross-machine library synchronization.

## Quality checks

- Every page of the clean and tracked manuscript and Supplement was rendered after the final figure and citation patch and visually inspected.
- DOCX ZIP/package integrity passes for all four Word files.
- The main manuscript retains 29 `ZOTERO_ITEM` citation fields plus one `ZOTERO_BIBL` bibliography field.
- Clean files contain no tracked revisions and have Track Changes disabled.
- The tracked manuscript contains 26 insertions / 26 deletions; the tracked Supplement remains the unchanged v1.19.4 file with 1 insertion / 0 deletions.
- Accepting all tracked changes yields the same final visible text as the corresponding clean file for both manuscript and Supplement.
- The manuscript retains eight native Word math objects.
- No comments remain.
- Accessibility audit: 0 high and 0 medium findings in all four Word files. The main manuscript has 11 low findings from intentionally displayed raw URLs in Data/Code Availability; the Supplement has 0 findings.
- Final embedded figure bytes are byte-identical to v1.19.4 and match the canonical RunRelay build exactly.
- References total 27.

## Figure code snapshot

The immutable v1.19.4 submission figure-code snapshot cited by the manuscript is commit:

`205bf89582cdba68ab48178c78cb69d32e2485ef`

The canonical submission-facing figure entry point remains:

```text
scripts/paper/final_figures/build_all_figures.py
```

Exact-commit RunRelay job `X7M3K9V2` rebuilt, validated, and exported the final 4-main plus 4-Extended-Data figure package with exit code 0. The submission manifest records `status: ok` and `scientific_values_changed: false`.

Embedded PNG SHA-256 fingerprints:

- Main Figure 1: `2110c48c472df438646de451c9f46537ddde7c82cd4122b106b688811615e4ae`
- Main Figure 2: `eab6bd65722b62d08624af69ebb4fcbc33479d7ca6173b1a897bf13611379366`
- Main Figure 3: `84194d006bd99d5be9a762ea778c73c0cb391a55b785417a19f8dbf28e9b3b03`
- Main Figure 4: `282d6b3eda849c7ad13eda3cec05dc768c46c9f692ed226616787bf4e25c1dd6`
- Extended Data Figure 1: `2248958b348c55e9f86f3822a75dc621984ee650d9e3236ef407d4da0731a873`
- Extended Data Figure 2: `df0030a6c0efb98effb549bd582adf2fea8d56c089fe2bde6a1dccd882216f82`
- Extended Data Figure 3: `3a9df74ab1932609812e9df32768e0c67f72a0848d496482f4276f0bb73626c0`
- Extended Data Figure 4: `ff57a3cb46a46883f79286f8b87abb37ddd02f59f489a1b51d48bb7f00b5b7d5`

## Status

v1.19.5 remains the current external Word master and the completed reader-friction baseline. It is no longer the intended final scientific package because the frozen displacement-matched MPNet specificity result completed afterward. The next intended manuscript package is v1.19.6, limited to integrating that specificity result while keeping the separate mechanism analyses outside the submission unless explicitly decided otherwise.

The remaining author-level submission decision is whether the initial submission is double-anonymized, which determines author/affiliation/contribution/competing-interest metadata in the manuscript file.

The repository intentionally does not commit `.docx` masters. Frozen protocol/result documents remain authoritative for analysis chronology, while the Word files recorded here are authoritative for current submission wording and layout.
