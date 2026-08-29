# NeuroSem manuscript reference and source audit

**Date:** 2026-08-28  
**Scope:** current Nature Machine Intelligence-focused manuscript revision (`NeuroSem_Nature_Manuscript_v0.6_NMI_revised.docx`) and repository manuscript sources.  
**Purpose:** verify external sources supporting dataset, model-family, related-work, atlas, RSA and transcriptomic-method statements. NeuroSem numerical results remain project-generated evidence and should not be retrofitted to external papers.

## Verified core references

| # | Manuscript role | Verified reference | Persistent identifier | Status |
|---|---|---|---|---|
| 1 | ChineseEEG / Little Prince and Garnett Dream dataset | Mou, X. et al. *ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding.* Scientific Data 11, 550 (2024). | DOI `10.1038/s41597-024-03398-7`; PMID `38811613` | Verified against PubMed and Scientific Data |
| 2 | BERT model family | Devlin, J., Chang, M.-W., Lee, K. & Toutanova, K. *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.* NAACL-HLT, 4171–4186 (2019). | DOI `10.18653/v1/N19-1423` | Verified against ACL Anthology |
| 3 | multilingual-E5 model family | Wang, L. et al. *Multilingual E5 Text Embeddings: A Technical Report* (2024). | arXiv `2402.05672` | Verified against arXiv metadata |
| 4 | ZuCo 2.0 dataset | Hollenstein, N., Troendle, M., Zhang, C. & Langer, N. *ZuCo 2.0: A Dataset of Physiological Recordings During Natural Reading and Annotation.* LREC, 138–146 (2020). | ACL Anthology `2020.lrec-1.18` | Verified against ACL Anthology |
| 5 | SMN4Lang dataset | Wang, S., Zhang, X., Zhang, J. & Zong, C. *A synchronized multimodal neuroimaging dataset for studying brain language processing.* Scientific Data 9, 590 (2022). | DOI `10.1038/s41597-022-01708-5`; PMID `36180444` | Verified against PubMed and Scientific Data |
| 6 | LanA language-network atlas | Lipkin, B. et al. *Probabilistic atlas for the language network based on precision fMRI data from >800 individuals.* Scientific Data 9, 529 (2022). | DOI `10.1038/s41597-022-01645-3`; PMID `36038572` | Verified against PubMed and Scientific Data |
| 7 | TMNRED dataset | Bai, Y. et al. *TMNRED, A Chinese Language EEG Dataset for Fuzzy Semantic Target Identification in Natural Reading Environments.* Scientific Data 12, 701 (2025). | DOI `10.1038/s41597-025-05036-2`; PMID `40280929` | Verified against PubMed and Scientific Data |
| 8 | directional-word / inner-speech EEG dataset | Kostulin, D. V. et al. *EEG-based brain-computer interface (BCI) dataset for directional word recognition.* Scientific Data 13, 1195 (2026). | DOI `10.1038/s41597-026-07809-9`; dataset DOI `10.5281/zenodo.20374418` | Verified against Scientific Data |
| 9 | representational similarity analysis | Kriegeskorte, N., Mur, M. & Bandettini, P. *Representational similarity analysis – connecting the branches of systems neuroscience.* Frontiers in Systems Neuroscience 2, 4 (2008). | DOI `10.3389/neuro.06.004.2008`; PMID `19104670` | Verified against PubMed/Frontiers |
| 10 | Allen Human Brain Atlas | Hawrylycz, M. J. et al. *An anatomically comprehensive atlas of the adult human brain transcriptome.* Nature 489, 391–399 (2012). | DOI `10.1038/nature11405` | Verified against Nature |
| 11 | abagen | Markello, R. D. et al. *Standardizing workflows in imaging transcriptomics with the abagen toolbox.* eLife 10, e72129 (2021). | DOI `10.7554/eLife.72129`; PMID `34783653` | Verified against PubMed/eLife |
| 12 | prior brain-tuning / semantic downstream performance | Moussa, O., Klakow, D. & Toneva, M. *Improving Semantic Understanding in Speech Language Models via Brain-Tuning.* ICLR (2025). | OpenReview `KL8Sm4xRn7`; arXiv `2410.09230` | Verified against OpenReview conference paper |
| 13 | brain data versus stimulus-only tuning | Merlin, G., Moussa, O. & Toneva, M. *What Brain Data Adds to Language Model Training.* CoNLL, 178–212 (2026). | DOI `10.18653/v1/2026.conll-main.12` | Verified against ACL Anthology |
| 14 | robustness/confounds in brain–LLM alignment | Hadidi, N. et al. *Spurious alignment between large language models and brains can emerge from non-robust methods and overlooked confounds.* Nature Communications 17, 5769 (2026). | DOI `10.1038/s41467-026-72253-7` | Verified against Nature Communications |
| 15 | recent NMI brain-guided reasoning comparison | Xiao, M., Du, K. & Lin, Z. *Beyond representational alignment with brain-guided language models for robust reasoning.* Nature Machine Intelligence 8, 1275–1289 (2026). | DOI `10.1038/s42256-026-01278-w` | Verified against Nature Machine Intelligence; published 3 August 2026 |

## Source-to-claim audit

- **Project numerical results:** ChineseEEG reliability/correspondence/tuning results, ZuCo transfer statistics, SMN4Lang fMRI reliability and transfer statistics, TMNRED/Garnett/directional results, and SMN4Lang MEG reliability results are produced by frozen NeuroSem analyses. External papers support provenance/context, not NeuroSem effect estimates.
- **ChineseEEG:** the Scientific Data descriptor supports the natural-reading paradigm, two Chinese novels, high-density EEG and dataset provenance. Mou et al. did not report NeuroSem reliability or neural-guided training results.
- **ZuCo 2.0:** the LREC paper supports the English natural-reading EEG/eye-tracking dataset and task structure. The 17/17 transfer result is NeuroSem-generated.
- **SMN4Lang:** the Scientific Data descriptor supports the same-participant fMRI+MEG cohort, 12 participants and naturalistic story listening. The prospective reliability gate and E5 transfer are NeuroSem-generated.
- **LanA:** Lipkin et al. supports the probabilistic language-network atlas. The probability threshold 0.20 and retained voxel count are NeuroSem choices.
- **TMNRED:** Bai et al. supports the public Chinese natural-reading EEG dataset. The frozen transfer null is NeuroSem-generated.
- **Directional dataset:** Kostulin et al. supports the directional-word EEG dataset. The lambda 0.10 versus 0 result is NeuroSem-generated.
- **RSA:** Kriegeskorte et al. supports the RDM/RSA framework. Dataset-specific correlation-distance construction and nuisance residualization remain manuscript methods.
- **Moussa/Merlin:** support the statement that neural/brain tuning can improve neural alignment and/or downstream linguistic performance relative to model-only or stimulus-only comparators. They do not establish external biological transfer as defined by NeuroSem.
- **Hadidi:** supports the motivation for robust split design, activation extraction care and control of simple temporal/word-rate confounds in brain–LLM mapping. It does not validate NeuroSem analyses directly.
- **Xiao et al.:** supports the contemporary NMI context that task-evoked brain activity can guide LLM representations and improve deductive-reasoning performance across model scales. NeuroSem is positioned as complementary: independent biological transfer of the induced relational perturbation rather than downstream-performance improvement.
- **AHBA/abagen:** remain secondary Extended Data references only; they must not strengthen the primary transfer claim.

## NeuroSem-specific methods that must remain directly described

- RunRelay job IDs, exact commits, freeze documents and internal protocol files are provenance records, not literature references.
- The relational neural objective, its E5 dose-response, and the lambda=0.10 external contrast are NeuroSem methods.
- The E5 dose-response reused already-observed ChineseEEG run-07 and semantic-benchmark outcomes and is exploratory. Lambda=0.10 can support transfer claims only through genuinely fresh neural targets.
- Cross-participant reliability is a measurement prerequisite, not evidence of semantic purity or mechanistic validity.
- No external citation can support the claim that the NeuroSem fMRI effect is 12/12 positive or that the ZuCo effect is 17/17 positive; these statements must trace to locked analysis outputs.

## Remaining before final journal submission / acceptance

1. Insert the final author list, affiliations and corresponding-author information.
2. Finalize author contributions, acknowledgements/funding and competing-interest statements.
3. Refresh/reconnect Zotero fields as needed after the final author-approved reference import.
4. Archive the exact accepted/submission code snapshot with a persistent DOI, environment specification and reproducibility entry points before publication.
5. Run one final NMI-format and reporting-summary compliance pass after authorship information is complete.

Figures 1–4, ethics/secondary-data language, Data Availability and Code Availability are now present in the NMI-focused working manuscript. No new outcome-bearing analysis is required for the reviewer-driven revision.