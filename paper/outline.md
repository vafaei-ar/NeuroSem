# NeuroSem manuscript outline

**Status:** Nature-facing working scaffold, 2026-08-28

This outline follows the strongest scientific evidence hierarchy rather than the chronological order of experiments. The manuscript should be organized around a transferable neural relational constraint, with positive external convergence followed by explicit boundary conditions.

## Central claim

A relational semantic target derived from human EEG can be learned by a language model and can generalize prospectively to independent neural measurements across participants, language, task, and measurement modality.

The strongest evidence chain is:

**ChineseEEG reproducible neural geometry -> neural-guided learning -> ZuCo cross-language EEG transfer -> SMN4Lang cross-modal fMRI transfer -> selective null boundary conditions.**

The paper should not be framed as "brain supervision improves language models" or as a universal semantic enhancement claim.

## Results narrative

### 1. Human language responses contain a reproducible relational neural geometry

Use ChineseEEG Little Prince to establish the target before discussing model optimization.

- The temporal-mean channel representation was selected using neural reliability, not semantic-model performance.
- Residual cross-subject neural geometry remains after nuisance control.
- Pinned Chinese BERT shows small but consistent residual correspondence across six narrative runs.
- This defines a biologically grounded relational target rather than a decoder label or scalar neural objective.

### 2. Neural relational supervision produces a learnable model change

- Present sealed Little Prince run-07 BERT evaluation with base, text-only, neural-guided, and shuffled-neural controls.
- Neural-guided BERT is strongest in two independent seeds.
- Show multilingual E5 as an architecture replication and the frozen source model for external testing.
- Show generic semantic benchmark results here: no stable neural-specific improvement.

Interpretation: neural alignment is learnable, but it is not equivalent to generic semantic quality.

### 3. The learned neural constraint transfers across language in independent EEG

Use ZuCo 2.0 normal reading as the first major external validation.

- New participants, laboratory, texts, acquisition context, and language.
- Strong prospectively inherited EEG reliability.
- Frozen E5 lambda 0.10 versus matched lambda 0 transfer is positive in 17/17 participants.
- No ZuCo tuning or outcome-driven representation/model search.

Interpretation: a neural constraint learned from Chinese reading EEG transfers to independent English natural-reading EEG.

### 4. The learned neural constraint transfers across measurement modality to fMRI

Make SMN4Lang the capstone result.

#### Model-blind fMRI gate

- 12 Mandarin participants listening to 60 naturalistic stories.
- Independently defined LanA language-network mask.
- Frozen TR-level multivoxel geometry and nuisance family.
- Model-blind leave-one-participant-out reliability passes strongly: mean residual reliability 0.65327, 12/12 positive, 95% CI [0.63945, 0.66843], exact one-sided p=0.000244.

#### Single frozen model contrast

- ChineseEEG-trained multilingual-E5 lambda 0.10 neural-guided versus matched lambda 0 text-only.
- Causal within-sentence prefix embeddings at released word onsets.
- Same fixed canonical HRF.
- No SMN4Lang training, layer search, lambda search, checkpoint search, ROI search, lag/HRF search, or semantic-unit search.

Result:

- lambda 0 mean participant residual RSA 0.12092396;
- lambda 0.10 mean 0.12177646;
- mean delta +0.00085250;
- 12/12 participants positive;
- 95% CI [+0.00078966,+0.00091398];
- exact one-sided sign-flip p=0.000244.

Interpretation: a small but highly consistent model change learned from EEG generalizes prospectively to independent cortical fMRI geometry during auditory narrative comprehension.

### 5. Null transfers define the boundary of the phenomenon

Group these results together instead of presenting them as failed replications scattered across the manuscript.

#### TMNRED

- Neural geometry replicates weakly but positively.
- Frozen E5 transfer is null.
- Post-confirmatory alternative representations do not rescue transfer.

#### Garnett Dream

- Same-participant/new-text EEG geometry is reliable.
- Frozen E5 transfer is null/inconclusive.
- This dissociates generalization of neural geometry from generalization of the trained-model advantage.

#### Directional-word dataset

- Out-of-task covert/inner-speech condition.
- Frozen transfer is negative/null.
- Treat as a task boundary, not a task-matched refutation.

Synthesis: the neural-guided shift is not a trivial global RSA increase and is not universally expressed across datasets/tasks.

### 6. Secondary mechanistic constraint: AHBA does not establish a molecular explanation

This section should be compact in the main paper or moved to Extended Data.

- Prespecified GABAergic/serotonergic/pathway tests are null.
- Whole-transcriptome PLS does not survive spatial null inference.
- Published language-gene panels remain primary-null.
- No-mirror dyslexia sensitivity is exploratory and driven mainly by right-hemisphere expression-map changes.

Interpretation: the current data establish representational transfer, not a molecular mechanism.

## Discussion structure

### What is supported

1. Language-related neural relational geometry is reproducible.
2. That relational target can modify a language model under held-out neural evaluation.
3. The learned change can transfer across dataset and language in EEG.
4. The learned change can transfer prospectively from EEG to independent language-network fMRI.
5. Generalization is selective rather than universal.

### What is not supported

1. A broad claim that neural guidance improves generic semantic representations.
2. Universal transfer across all reading/language datasets.
3. A claim that the absolute cross-modal effect is large.
4. A confirmatory GABAergic, serotonergic, or published language-gene molecular mechanism.

### Conceptual interpretation

The conceptual contribution is a shift from using neural data only as a prediction target to using reproducible neural relational structure as a model-training constraint whose portability can be tested prospectively in independent brains.

This creates a general framework:

1. establish reliable biological geometry;
2. train a model toward that geometry;
3. freeze the trained representation;
4. test whether the change generalizes to new neural systems and modalities;
5. use null datasets to identify the scope of transfer.

### Effect-size interpretation

The external model advantages are small in absolute RSA units. This should be explicit.

The argument for importance is not magnitude alone. It is the conjunction of:

- directional consistency;
- prospective design;
- matched controls;
- cross-language transfer;
- cross-modal transfer;
- model-blind reliability gates;
- preserved null boundary conditions.

### Limitations

- Neural-model transfer effects are small in absolute RSA units.
- Dataset/task differences prevent a simple universal-transfer model.
- EEG source specificity is limited.
- SMN4Lang semantic-to-TR mapping depends on a frozen HRF-based encoding convention rather than direct neural timing.
- The current work does not establish molecular causality.
- AHBA has only six donors and sparse right-hemisphere sampling.
- The optional MEG arm is not yet part of the evidence chain.

## Main-paper figure sequence

1. **Figure 1:** concept, ChineseEEG neural target, reliability, held-out neural-guided learning.
2. **Figure 2:** ZuCo cross-language EEG reliability and transfer.
3. **Figure 3:** SMN4Lang fMRI reliability gate and cross-modal transfer, visual centerpiece.
4. **Figure 4:** boundary conditions and generic-semantic dissociation.

AHBA moves to Extended Data unless an editor/reviewer specifically asks for the molecular track in the main narrative.

## Final framing

The strongest paper is about **transferable neural relational constraints**.

A concise statement is:

> Neural geometry learned from human EEG can shape language-model representations in a way that survives prospective transfer to independent brains across language and measurement modality, while null datasets define the limits of that transfer.
