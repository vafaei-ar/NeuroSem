# NeuroSem manuscript reference and source audit

**Date:** 2026-08-28  
**Scope:** `paper/NATURE_MANUSCRIPT_DRAFT_V2.md`  
**Purpose:** verify the external sources needed to support dataset, model-family, atlas, RSA and transcriptomic-method statements. NeuroSem numerical results remain project-generated evidence and should be cited to the manuscript itself, not retrofitted to external papers.

## Verified core references

| # | Manuscript role | Verified reference | Persistent identifier | Status |
|---|---|---|---|---|
| 1 | ChineseEEG / Little Prince and Garnett Dream dataset | Mou, X. et al. *ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding.* Scientific Data 11, 550 (2024). | DOI `10.1038/s41597-024-03398-7`; PMID `38811613` | Verified against PubMed and Scientific Data |
| 2 | BERT model family | Devlin, J., Chang, M.-W., Lee, K. & Toutanova, K. *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.* NAACL-HLT, 4171–4186 (2019). | DOI `10.18653/v1/N19-1423` | Verified against ACL Anthology |
| 3 | multilingual-E5 model family | Wang, L., Yang, N., Huang, X., Yang, L., Majumder, R. & Wei, F. *Multilingual E5 Text Embeddings: A Technical Report* (2024). | arXiv `2402.05672` | Verified against arXiv metadata; no journal DOI used |
| 4 | ZuCo 2.0 dataset | Hollenstein, N., Troendle, M., Zhang, C. & Langer, N. *ZuCo 2.0: A Dataset of Physiological Recordings During Natural Reading and Annotation.* LREC, 138–146 (2020). | ACL Anthology `2020.lrec-1.18` | Verified against ACL Anthology |
| 5 | SMN4Lang dataset | Wang, S., Zhang, X., Zhang, J. & Zong, C. *A synchronized multimodal neuroimaging dataset for studying brain language processing.* Scientific Data 9, 590 (2022). | DOI `10.1038/s41597-022-01708-5`; PMID `36180444` | Verified against PubMed and Scientific Data |
| 6 | LanA language-network atlas | Lipkin, B. et al. *Probabilistic atlas for the language network based on precision fMRI data from >800 individuals.* Scientific Data 9, 529 (2022). | DOI `10.1038/s41597-022-01645-3`; PMID `36038572` | Verified against PubMed and Scientific Data |
| 7 | TMNRED dataset | Bai, Y. et al. *TMNRED, A Chinese Language EEG Dataset for Fuzzy Semantic Target Identification in Natural Reading Environments.* Scientific Data 12, 701 (2025). | DOI `10.1038/s41597-025-05036-2`; PMID `40280929` | Verified against PubMed and Scientific Data |
| 8 | directional-word / inner-speech EEG dataset | Kostulin, D. V. et al. *EEG-based brain-computer interface (BCI) dataset for directional word recognition.* Scientific Data 13, 1195 (2026). | DOI `10.1038/s41597-026-07809-9`; dataset DOI `10.5281/zenodo.20374418` | Verified against Scientific Data |
| 9 | representational similarity analysis | Kriegeskorte, N., Mur, M. & Bandettini, P. *Representational similarity analysis – connecting the branches of systems neuroscience.* Frontiers in Systems Neuroscience 2, 4 (2008). | DOI `10.3389/neuro.06.004.2008`; PMID `19104670` | Verified against PubMed/Frontiers |
| 10 | Allen Human Brain Atlas | Hawrylycz, M. J. et al. *An anatomically comprehensive atlas of the adult human brain transcriptome.* Nature 489, 391–399 (2012). | DOI `10.1038/nature11405` | Verified against Nature |
| 11 | abagen | Markello, R. D. et al. *Standardizing workflows in imaging transcriptomics with the abagen toolbox.* eLife 10, e72129 (2021). | DOI `10.7554/eLife.72129`; PMID `34783653` | Verified against PubMed/eLife |

## Source-to-claim audit

- **Project numerical results:** ChineseEEG reliability/correspondence/tuning results, ZuCo transfer statistics, SMN4Lang fMRI reliability and transfer statistics, TMNRED/Garnett/directional results, and SMN4Lang MEG reliability results are produced by the frozen NeuroSem analyses. External dataset papers support dataset provenance and acquisition context, not these NeuroSem effect estimates.
- **ChineseEEG:** the Scientific Data descriptor supports the natural-reading paradigm, two Chinese novels, high-density EEG, and dataset provenance. The manuscript should not imply that Mou et al. reported the NeuroSem reliability or neural-guided training results.
- **ZuCo 2.0:** the LREC paper supports the English natural-reading EEG/eye-tracking dataset and task structure. The 17/17 transfer result is NeuroSem-generated.
- **SMN4Lang:** the Scientific Data descriptor supports the same-participant fMRI+MEG cohort, 12 participants and naturalistic story listening. The prospective reliability gate and E5 transfer are NeuroSem-generated.
- **LanA:** Lipkin et al. supports the probabilistic language-network atlas based on 806 individuals. The manuscript's use of probability threshold 0.20 and retained voxel count are analysis-specific NeuroSem choices.
- **TMNRED:** Bai et al. supports the public Chinese natural-reading EEG dataset. The frozen transfer null is NeuroSem-generated.
- **Directional dataset:** Kostulin et al. supports the overt/covert directional-word EEG dataset. The lambda 0.10 versus 0 result is NeuroSem-generated.
- **RSA:** Kriegeskorte et al. supports the RDM/RSA framework. Dataset-specific correlation-distance construction and nuisance residualization remain manuscript methods.
- **AHBA/abagen:** retain these references only if the transcriptomic Extended Data remain in the submitted paper.

## Items intentionally not treated as external references

- RunRelay job IDs, exact commits, freeze documents and internal protocol files are provenance records, not literature references. They belong in Code/Data Availability, Methods provenance or Supplementary audit material if needed.
- The neural-guided objective and its λ=.10 external contrast are NeuroSem methods and should be described directly rather than attributed to an external paper.
- No external citation can support the claim that the NeuroSem fMRI effect is 12/12 positive or that the ZuCo effect is 17/17 positive; those statements must trace to the locked analysis outputs.

## Outstanding before final journal submission

1. Replace the working author list and affiliations with the final author-approved version.
2. Add any mandatory ethics/consent citations or institutional statements from the source datasets exactly as required by Nature.
3. Add model repository/version citations only if the journal requests software/model accession details beyond the model-family papers.
4. If AHBA is removed from the final paper, remove references 10–11 from the manuscript bibliography.
5. Finalize composite Figures 1, 3 and 4a/c/d. The current locked figure build contains Figure 2 reliability material and the SMN4Lang MEG reliability-boundary panel, but not all planned composite main figures.
