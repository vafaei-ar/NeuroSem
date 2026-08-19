# Literature Map

This document tracks the literature relevant to NeuroSem. It is intentionally organized by scientific function rather than as a narrative review.

## 1. Brain-language representational alignment

Questions:

- Which language-model layers best align with human neural responses?
- Does alignment reflect lexical, semantic, predictive, syntactic, or temporal structure?
- Which analyses distinguish true representational alignment from shared stimulus structure?

## 2. Representational geometry across people

Questions:

- Is relational geometry more stable across participants than raw neural features?
- Which alignment methods are appropriate for cross-subject neural representations?
- When should RSA, CKA, hyperalignment, Procrustes alignment, or topological methods be used?

## 3. Multilingual neural semantics

Questions:

- Which semantic relationships remain stable across languages?
- Does shared geometry emerge despite language-specific neural implementations?
- Can bilingual or cross-lingual neural data provide a language-invariant supervision signal?

## 4. Neural guidance of machine learning models

Questions:

- Has neural data been used only as an evaluation target, or also as a training signal?
- What evidence exists that brain-guided tuning improves out-of-domain or semantic performance?
- Which controls distinguish biological information from another noisy representation of the stimulus labels?

## 5. EEG-to-language and imagined-speech modeling

Questions:

- Which tasks already have strong baselines for EEG-to-text or EEG-to-semantic retrieval?
- Which contributions would therefore be incremental?
- How much semantic information survives beyond subject, motor, acoustic, and task-specific effects?

## 6. Confounds and statistical validity

Priority topics:

- temporal autocorrelation;
- word/sentence position;
- repeated-stimulus leakage;
- stimulus duration and acoustic/visual structure;
- subject-specific trial structure;
- inflated degrees of freedom in RDM analyses;
- non-independent train/test partitions;
- circular feature selection;
- multiple testing across time windows and model layers.

## 7. Methods relevant to NeuroSem

Methods to review systematically:

- representational similarity analysis (RSA);
- partial RSA;
- variance partitioning;
- centered kernel alignment (CKA);
- cross-validated Mahalanobis distance;
- hyperalignment;
- Procrustes analysis;
- optimal transport;
- topological RSA;
- contrastive representation learning;
- relational knowledge distillation;
- LoRA/adapters for parameter-efficient tuning.

## Evidence table

For each paper added, record:

| Field | Description |
|---|---|
| Citation | Full citation / DOI / PMID |
| Dataset | Neural dataset used |
| Modality | EEG / MEG / ECoG / sEEG / fMRI |
| Participants | Number and population |
| Language task | Reading, listening, production, etc. |
| Model | Language model / embedding model |
| Alignment method | RSA, encoding, CKA, etc. |
| Main result | Concise effect/result |
| Generalization | Subject, stimulus, task, language, dataset |
| Controls | Major nuisance/confound controls |
| Relevance | What it changes for NeuroSem |

## Immediate review priorities

1. Direct brain-guided fine-tuning papers published or posted through 2026.
2. Cross-lingual neural semantic geometry.
3. Critiques showing spurious model-brain alignment from temporal or positional structure.
4. Neural-language datasets suitable for independent replication.
5. Relational/geometry-based distillation methods from machine learning that can be adapted without claiming biological novelty where none exists.
