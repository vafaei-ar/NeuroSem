# Current publication master

**Recorded:** 2026-09-18

The current Word masters are maintained outside the Git working tree during final author review. This file records the exact binaries used for submission preparation.

## Main manuscript

### Clean

- File: `NeuroSem_Nature_Manuscript_v1.19.4_clean.docx`
- SHA-256: `c4f2656f164567c03ff051626f47a7ef09e91ff8d1c22956969ee9d467ecb1c0`
- Size: 2,880,219 bytes
- Rendered length: 33 pages

### Tracked changes

- File: `NeuroSem_Nature_Manuscript_v1.19.4_tracked.docx`
- SHA-256: `7f5101ba0633d9c77624036c4fa03da26c14774a670dab63c38c629d27cb213f`
- Size: 2,881,016 bytes
- Rendered length: 34 pages
- Tracked revisions: 27 insertions and 13 deletions

Current title: **Brain-derived relational supervision transfers language-model representations across independent neural datasets**

v1.19.4 is a narrowly scoped presentation, inferential-labeling, documentation, and citation pass over the scientifically locked v1.19.3 package. It introduces no new model training, neural analysis, target definition, dose/model selection, statistical family, or outcome-bearing inference.

The revision removes the Figure 1 participant occlusion and the potentially misleading delta-to-LOO ratio, restores explicit paired connectors and labels the delta marginal, makes Figure 3 uncertainty encoding symmetric without new inference, fills the exact ZuCo RDM/nuisance definition in Extended Data Table 5, marks the lambda=1 high-dose boundary in Extended Data Figure 4, reports the two regional FWER values in the Results, explicitly separates the frozen two-contrast family from the post-confirmatory five-dose family, repairs remaining plotting collisions, and adds seven canonical methods references as Zotero-compatible fields.

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
- The tracked manuscript contains 27 insertions / 13 deletions; the tracked Supplement contains 1 insertion / 0 deletions.
- Accepting all tracked changes yields the same final visible text as the corresponding clean file for both manuscript and Supplement.
- The manuscript retains eight native Word math objects.
- No comments remain.
- Accessibility audit: 0 high and 0 medium findings in all four Word files. The main manuscript has 11 low findings from intentionally displayed raw URLs in Data/Code Availability; the Supplement has 0 findings.
- Final embedded figure bytes match the canonical v1.19.4 RunRelay build exactly.
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

v1.19.4 closes the remaining presentation and documentation items identified in the latest external review without reopening the scientific analysis.

The remaining author-level submission decisions are whether the initial submission is double-anonymized, which determines author/affiliation/contribution/competing-interest metadata in the manuscript file, and whether to shorten the current title.

The repository intentionally does not commit `.docx` masters. Frozen protocol/result documents remain authoritative for analysis chronology, while the Word files recorded here are authoritative for current submission wording and layout.
