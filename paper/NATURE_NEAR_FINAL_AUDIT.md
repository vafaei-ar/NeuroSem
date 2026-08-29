# Nature near-final manuscript audit

**Status:** near-final scientific manuscript for author review  
**Date:** 2026-08-28

This audit records the submission-facing checks completed after the evidence and main figures were locked. It does not introduce new scientific analyses or alter the inferential hierarchy.

## Completed scientific packaging

- Main title and central claim are aligned to the locked evidence: human neural geometry can act as a transferable relational constraint on language representations, with selective rather than universal generalization.
- Figures 1–4 are assembled from locked outputs only.
- ZuCo remains the independent cross-language EEG validation and SMN4Lang fMRI remains the prospective cross-modal capstone.
- TMNRED, Garnett Dream and directional inner speech remain explicit transfer boundaries.
- SMN4Lang MEG remains a model-blind reliability boundary. No model evaluation was performed after the frozen reliability gate failed.
- AHBA remains secondary/Extended Data mechanistic material and does not strengthen the primary transfer claim.

## Ethics and secondary-data use

NeuroSem recruited no new participants and performed secondary analyses of de-identified or publicly released data. The manuscript ethics statement records the original oversight and consent basis for each participant-level source used in the paper:

- **ChineseEEG:** University of Macau Institutional Review Board approval `BSERE20-APP011-ICI`; written informed consent; Declaration of Helsinki.
- **ZuCo 2.0:** Ethics Commission of the University of Zurich; written consent for participation and reuse of data.
- **SMN4Lang fMRI/MEG:** Institutional Review Board of Peking University; written informed consent.
- **TMNRED:** Ethics Committee of Tianjin University approval `TJUE-2024-402`; written informed consent and permission for de-identified open-data sharing.
- **Directional-word EEG:** Bioethics Commission of Southern Federal University, Bioethics Committee Report No. 3, 9 September 2022; written informed consent including anonymized public release.
- **Allen Human Brain Atlas:** post-mortem tissue obtained under the ethical procedures of the contributing tissue banks, with next-of-kin consent as described by the Allen Institute and source publications.
- **LanA:** used only as a previously published derived probabilistic language-network atlas; no participant-level LanA data were newly analyzed by NeuroSem.

The manuscript should not imply that NeuroSem obtained a single new IRB approval covering these independent source datasets.

## Data availability

The near-final manuscript identifies the principal public data sources used for the reported analyses:

- ChineseEEG: OpenNeuro `ds004952` and ScienceDB DOI `10.57760/sciencedb.CHNNeuro.00007`.
- ZuCo 2.0: OSF `https://osf.io/2urht/`.
- SMN4Lang: OpenNeuro `ds004078`, DOI `10.18112/openneuro.ds004078.v1.0.4`.
- TMNRED: OpenNeuro `ds005383`, DOI `10.18112/openneuro.ds005383.v1.0.0`.
- Directional-word EEG: Zenodo DOI `10.5281/zenodo.20374418`.
- LanA atlas: figshare DOI `10.6084/m9.figshare.20425209`.
- Allen Human Brain Atlas: Allen Institute human brain-map portal.

The statement explicitly says that NeuroSem does not redistribute restricted or identifiable participant-level data.

## Code availability and provenance

- Custom analysis and figure-generation code is available in `https://github.com/vafaei-ar/NeuroSem`.
- Frozen protocols, exact-commit provenance and analysis-status documentation are retained in the repository.
- The multilingual-E5 model is identified as `intfloat/multilingual-e5-large` with the pinned revision used in the frozen external analyses.
- A persistent archival release/DOI should be minted from the submission commit before publication. This is a publication-packaging step, not a missing scientific analysis.

## Nature-facing formatting and editorial checks

- Standard 12-point Times New Roman manuscript typography is used.
- A concise summary paragraph, main text, Methods, four main figures, complete figure legends and references are present.
- Data Availability and Code Availability sections are included in Methods.
- The manuscript has been rendered after the final editorial/ethics edits and all pages visually inspected for clipping, overlap, missing glyphs and figure-placement defects.
- Raw RSA effects across EEG, fMRI and MEG are not pooled or presented as a common effect-size scale.
- The small absolute SMN4Lang fMRI effect is explicitly described as small and is interpreted through prospective independence and participant-level directional consistency rather than magnitude.
- Language such as “pure semantic geometry”, “brain-like model”, “negative MEG transfer” and universal-improvement claims is avoided.

## Reference audit

The current bibliography covers the principal dataset, model, atlas, RSA and imaging-transcriptomics provenance sources used in the main text and Methods. Repository identifiers and data DOIs are additionally provided in Data Availability so that dataset access does not depend on bibliography formatting alone. Zotero-compatible citation/bibliography fields are preserved in the Word working manuscript.

## Items intentionally left for authors

The scientific manuscript can now be reviewed without the final author block. Before submission, the authors should supply or confirm only the author-dependent administrative material:

1. final author names, order and affiliations;
2. corresponding-author details;
3. author-contribution statement;
4. funding and acknowledgements;
5. competing-interest declaration;
6. any journal-required reporting-summary responses and the final archival code/data release metadata.

No additional outcome-bearing analysis is required for the current manuscript story.
