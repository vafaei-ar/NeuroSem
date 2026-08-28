# NeuroSem Nature-level positioning

**Working editorial strategy, updated 2026-08-28 after completion of SMN4Lang fMRI.**

## The central conceptual advance

The strongest paper is not a chronology of EEG analyses, model tuning experiments, and transcriptomic follow-ups. The strongest paper is a test of whether a relational structure learned from human neural responses can become a transferable representational constraint on a language model.

The central claim should be:

> A semantic relational target derived from human EEG can be learned by a language model and can generalize prospectively to independent neural measurements across language, participants, tasks, and measurement modality.

The most important evidence is the conjunction of:

1. a reproducible neural relational geometry in the development EEG data;
2. successful neural-guided learning under sealed held-out evaluation;
3. independent cross-language EEG transfer in ZuCo;
4. prospective cross-modal transfer to naturalistic language-network fMRI in SMN4Lang;
5. explicit null and inconclusive transfer tests that define boundaries and rule out a universal or generic-semantic interpretation.

The SMN4Lang fMRI result changes the manuscript hierarchy. ZuCo is no longer the terminal validation. SMN4Lang is the capstone because it changes measurement modality and language task while preserving the frozen neural-guided advantage.

## What is surprising and broadly interesting

The surprising result is not the absolute size of the RSA increment. It is that a representation modified using EEG relational supervision from one natural-reading dataset is detectably closer to independent fMRI language-network geometry in different people listening to different naturalistic narratives.

This connects questions that are usually studied separately:

- cognitive neuroscience: whether semantic neural geometry is reproducible;
- representation learning: whether relational neural supervision can alter a language model;
- generalization: whether the learned constraint transfers out of sample;
- multimodal neuroscience: whether the learned relationship survives a change from scalp EEG to cortical fMRI.

The result should therefore be framed as evidence for **portable neural representational constraints**, not as evidence that EEG creates a generally better language model.

## Main claims, ordered by importance

### Claim 1. Neural semantic geometry can function as a transferable relational constraint

**Strongly supported.**

ChineseEEG establishes the target; sealed neural-guided training demonstrates learnability; ZuCo and SMN4Lang demonstrate external transfer.

### Claim 2. Cross-modal transfer is real but small

**Strongly supported for the frozen SMN4Lang test.**

The neural-guided E5 adapter improves residual fMRI RSA over the matched text-only adapter by `+0.0008525`, with 12/12 participants positive, bootstrap 95% CI `[+0.0007897, +0.0009140]`, and exact one-sided sign-flip `p=0.000244`.

The manuscript must describe this as a small absolute representational shift with unusually strong directional consistency, not as a large predictive gain.

### Claim 3. Generalization is selective rather than universal

**Strongly supported.**

- ZuCo: positive cross-language reading-EEG transfer.
- SMN4Lang: positive cross-modal fMRI transfer.
- TMNRED: null transfer.
- Garnett Dream: null/inconclusive transfer despite reliable neural geometry.
- directional-word dataset: out-of-task negative/null boundary condition.

These nulls should not be hidden. They make the scientific claim narrower and more credible: the learned neural constraint can transfer, but task/data structure determines whether it is expressed.

### Claim 4. Neural alignment and generic semantic quality are different objectives

**Supported.**

Generic semantic benchmarks do not show a stable neural-specific gain. This should be presented as a mechanistic dissociation rather than a failure: neural guidance changes representational alignment with brain data without simply increasing conventional semantic benchmark scores.

## What should not be the central claim

Do not lead with:

- "brain supervision improves language models";
- "EEG makes E5 better";
- a universal semantic enhancement claim;
- a molecular GABA/serotonin mechanism;
- the AHBA no-mirror dyslexia sensitivity;
- the chronological sequence in which datasets happened to be analyzed.

These framings either overclaim the evidence or bury the strongest conceptual advance.

## Recommended main-paper Results order

### Result 1. A reproducible neural relational target exists

Use ChineseEEG to introduce the reliability-led neural representation and residual semantic geometry. The purpose is to establish that there is a real neural target before any model optimization is discussed.

### Result 2. Neural relational supervision changes the model in a learnable, held-out way

Present sealed BERT run-07 first as the causal training demonstration, then multilingual E5 as architecture replication and the source model for external tests. Show the generic semantic benchmark dissociation here or at the end of this section.

### Result 3. The learned neural constraint transfers across language in EEG

Use ZuCo as the cleanest independent EEG transfer because it changes dataset, participants, text, and language. Pair its strong neural reliability with the 17/17 positive frozen E5 transfer result.

### Result 4. The learned neural constraint transfers across measurement modality to fMRI

Make SMN4Lang the capstone figure/result.

Key design features should be visually explicit:

- ChineseEEG-trained model only;
- independent SMN4Lang participants;
- naturalistic auditory narratives;
- independently defined LanA language-network mask;
- model-blind reliability gate first;
- one frozen `lambda=0.10 - lambda=0` contrast;
- 12/12 participants positive.

This is the result most likely to justify broad interdisciplinary interest.

### Result 5. Null transfers define the boundary of the phenomenon

Bring TMNRED, Garnett Dream, and the directional-word dataset together in one compact boundary-condition section/figure. Their role is not to compete with ZuCo/SMN4Lang. Their role is to show that the effect is not a trivial property of the adapter or a universal upward shift in RSA.

This section should motivate the scientific question: which neural/task structures permit transfer of the learned constraint?

## AHBA recommendation

The AHBA work is rigorous and worth preserving, but it should not currently carry the main Nature narrative.

Reasons:

1. the prespecified molecular tests are null;
2. the most visually striking result is a post-hoc bilateral-processing sensitivity;
3. integrating this track forces the manuscript to explain EEG forward sensitivity, AHBA donor asymmetry, transcriptomic null models, and mirroring choices after the main neural-model story is already complete;
4. this creates a second conceptual center without strengthening the principal causal/generalization claim.

Recommended placement:

- move the core AHBA primary-null summary to Extended Data or Supplementary Information as a mechanistic constraint; or
- develop AHBA as a separate paper centered on the methodological consequences of bilateral transcriptomic preprocessing, after independent validation.

Do not use the AHBA sensitivity as a Nature-level hook for the current NeuroSem paper.

## Recommended main figures

### Figure 1. From neural geometry to transferable relational supervision

Conceptual framework plus ChineseEEG target construction and reliability. End the figure with sealed held-out neural-guided improvement.

### Figure 2. Cross-language transfer to independent EEG

ZuCo reliability and participant-level `lambda=0.10 - lambda=0` transfer. Include the independence dimensions graphically: new people, laboratory, texts, and language.

### Figure 3. Prospective cross-modal transfer to language-network fMRI

This should be the visual centerpiece.

Panels:

- SMN4Lang design and model-blind reliability gate;
- causal prefix-to-HRF semantic mapping and LanA fMRI geometry;
- participant paired points for text-only versus neural-guided RSA;
- participant delta plot, 12/12 positive;
- compact statement of frozen guardrails.

### Figure 4. Selectivity and boundary conditions

One aligned effect-size panel for ZuCo, SMN4Lang, TMNRED, Garnett, and the directional-word condition, with clear labels for task/modality and confirmatory status.

A small panel can show that generic semantic benchmark performance is not systematically improved by neural guidance.

## Extended Data priorities

1. ChineseEEG representation-selection and nuisance robustness.
2. BERT seed replication and shuffled-neural controls.
3. E5 Pareto/generic semantic benchmark analyses.
4. TMNRED reliability and null transfer.
5. Garnett reliability, exact text mapping, and null/inconclusive transfer.
6. SMN4Lang metadata/timebase/LanA QC and story-level heterogeneity.
7. directional-word boundary condition.
8. AHBA primary mechanistic nulls and, if retained, bilateral-handling diagnostic.
9. full RunRelay/provenance table.

## Nature editorial test

Nature states that papers should be technically sound, provide strong evidence, be novel, matter within their field, interest a general scientific audience, and represent an advance likely to influence thinking. It also emphasizes originality, importance, interdisciplinary interest, accessibility, elegance, and surprising conclusions.

The manuscript should therefore answer these editorial questions directly:

### What changes how people think?

Neural data need not only be decoded or predicted. A relational geometry extracted from neural measurements can serve as a training constraint whose consequences are testable in independent brains and even another measurement modality.

### Why should scientists outside EEG/LLM research care?

The study provides a general strategy for converting biological representational structure into a portable model constraint and then testing whether the constraint generalizes across biological measurements.

### What is the strongest evidence?

Prospectively frozen transfer from ChineseEEG-guided E5 to independent naturalistic-language fMRI, together with cross-language EEG convergence and explicit null boundary conditions.

### What is the restraint that makes the claim credible?

No post-hoc model search in the positive external datasets, model-blind reliability gates, matched text-only controls, participant-level inference, and preservation of null transfers and generic-semantic nulls.

## Suggested title directions

Prefer titles about transferable neural constraints rather than model improvement. Examples:

- **Neural semantic geometry provides a transferable constraint on language representations**
- **Human neural geometry shapes language representations that generalize across brains and modalities**
- **Neural relational supervision transfers from EEG to language-network fMRI**
- **A transferable neural constraint on language-model semantic geometry**

The first two have the broadest Nature-style conceptual reach. The third is the cleanest empirical description but may read as more specialist.

## Suggested one-sentence editor pitch

> We show that a relational semantic target learned from human natural-reading EEG can alter a language model in a way that prospectively improves alignment not only to independent cross-language EEG but also to language-network fMRI in different participants during naturalistic auditory comprehension, while preregistered null transfers define the limits of that generalization.

## Decision

For the current paper, prioritize a compact four-part story:

**reproducible neural geometry -> neural-guided learning -> cross-language EEG transfer -> cross-modal fMRI transfer**, followed by a concise boundary-condition section.

Do not let AHBA, engineering chronology, or dataset-by-dataset history determine the manuscript architecture.
