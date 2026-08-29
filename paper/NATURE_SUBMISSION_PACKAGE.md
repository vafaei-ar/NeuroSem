# NeuroSem Nature submission package

**Status:** final evidence-locked submission-facing scaffold, 2026-08-28

This document converts the locked NeuroSem evidence into a concise Nature-facing presentation. It is an editorial scaffold, not a replacement for the detailed methods, frozen protocols, experiment ledger, or full Results.

## Preferred title

**Human neural geometry provides a transferable constraint on language representations**

### Alternative titles

1. **Neural relational constraints on language representations generalize across brains and modalities**
2. **Human neural geometry shapes language representations across datasets and modalities**
3. **A transferable neural constraint on language representation**

The preferred title is intentionally claim-limited. It emphasizes the conceptual advance without implying that neural supervision globally improves language-model quality.

## Nature-style summary paragraph

Language models and human brains both encode relations among linguistic inputs, but it remains unclear whether neural representational structure can serve as a transferable constraint on artificial language representations. We derived a reproducible relational geometry from electroencephalographic responses during natural reading and used this geometry as an auxiliary training target for language-model representations. Neural-guided training produced a small but reproducible change in model geometry that generalized beyond the neural data used for training. The frozen neural-guided model showed improved alignment to independent English-reading electroencephalography and, prospectively, to language-network functional magnetic resonance imaging measured in different participants during naturalistic auditory comprehension. These effects were directionally consistent across all participants in the two strongest external validations. Transfer was not universal: other reading and inner-speech datasets produced null or inconclusive effects, and a prospectively specified sensor-level magnetoencephalography target failed its model-blind cross-participant reliability gate before model evaluation. A subsequently frozen exploratory temporal-granularity family likewise yielded no reliable MEG target from 4 to 32 normalized-time bins. Neural relational supervision therefore does not simply make language representations generally better. Instead, it can impose a portable biological constraint whose detectable expression depends on the neural and task geometry being tested and on whether the target neural geometry is itself reproducible.

## One-sentence editor pitch

A relational target learned from human natural-reading EEG altered a language model in a way that prospectively improved alignment to independent cross-language EEG and language-network fMRI, while frozen null tests and a prospectively failed MEG reliability gate defined where that generalization could and could not be evaluated.

## Short editor pitch

Neural data are usually treated as outcomes that models attempt to predict. NeuroSem asks the reverse question: can reliable human neural geometry become a training constraint whose effects remain detectable in independent brains? We derived a relational target from Chinese natural-reading EEG, trained language-model representations against that target, and then carried one frozen neural-guided model into external datasets without target-dataset tuning. The neural-guided representation generalized to independent English-reading EEG and, in the strongest prospective test, to language-network fMRI from different Mandarin-speaking participants listening to naturalistic stories. The fMRI increment is small in absolute RSA units but is positive in all 12 participants under an independently defined language-network mask and a model-blind reliability gate. Transfer is not universal: TMNRED, Garnett Dream, and directional inner-speech tests are null or inconclusive. In the same SMN4Lang cohort, a prospectively specified sensor-level MEG representation did not provide a sufficiently reproducible cross-participant story geometry to permit model evaluation, and this reliability limitation persisted across a separately frozen exploratory 4/8/16-bin family together with the original 32-bin representation. We therefore argue for a selective, portable neural representational constraint whose expression requires a reproducible target geometry rather than a general language-model improvement.

## Cover-letter core argument

Dear Editors,

We submit **Human neural geometry provides a transferable constraint on language representations** for consideration as an Article in *Nature*.

The study addresses whether biological representational structure can be used not only to evaluate artificial language models but to constrain their learning in a way that generalizes to independent neural measurements. We first establish a reproducible relational geometry in human EEG during natural reading and show that this geometry contains residual correspondence with language-model representations. We then use the neural geometry as an auxiliary relational training target and evaluate the resulting models under sealed and prospectively frozen tests.

The main advance is external portability. A neural-guided multilingual representation learned from Chinese reading EEG improves alignment to independent English-reading EEG in all 17 tested participants. More importantly, the same already-trained model prospectively improves alignment to an independently defined language-network fMRI geometry in all 12 participants of SMN4Lang during naturalistic auditory comprehension. No SMN4Lang model training, participant selection, lambda selection, layer selection, checkpoint selection, ROI search, temporal-lag search, or semantic-unit search was performed from the fMRI outcome.

The effect is small in absolute magnitude, and we make that explicit. Its significance is instead the convergence across independent datasets, languages, participants, and measurement modalities under frozen analysis choices. Equally important, several external transfer tests are null or inconclusive. A separately prospectively specified sensor-level MEG representation in SMN4Lang failed its model-blind reliability prerequisite before any model evaluation; a subsequently frozen exploratory temporal-granularity family also failed to establish a reliable target. These boundary conditions rule out the stronger but less credible claim that neural guidance simply improves language representations in general, while demonstrating that transfer should only be tested where neural geometry is itself reproducible.

We believe the work will interest readers across cognitive and computational neuroscience, language science, representation learning, and artificial intelligence because it demonstrates that relational information derived from one form of human neural measurement can become a portable constraint whose consequences are detectable in independent brains measured with another modality, while prospectively defined failures delimit the conditions under which such transfer can be meaningfully evaluated.

Sincerely,

The authors

## Results hierarchy for the main text

### Result 1. Human language processing contains reproducible relational neural geometry

Establish ChineseEEG reliability first, before model optimization. Show that the selected temporal-mean channel representation was chosen by neural reliability rather than semantic-model performance, and that residual neural-model correspondence is positive across held-out narrative runs.

### Result 2. Neural relational supervision is learnable

Present the sealed BERT neural-guided experiment with text-only and shuffled-neural controls, followed by the independent E5 architecture replication. Separate neural-target alignment from generic semantic benchmark performance.

### Result 3. The learned constraint transfers across dataset and language

Use ZuCo as the strongest EEG validation. Highlight the prospectively carried representation and model contrast, 17/17 positive participant deltas, and the absence of ZuCo model tuning.

### Result 4. The learned constraint transfers across measurement modality

Use SMN4Lang fMRI as the capstone. Present the model-blind fMRI reliability gate, independent LanA language-network definition, frozen causal text-to-TR mapping, and sole lambda 0.10 versus lambda 0 contrast. Report both the small absolute increment and the 12/12 directional consistency.

### Result 5. Transfer is selective and requires a reproducible neural target

Integrate TMNRED, Garnett Dream, and directional inner-speech results as transfer boundary conditions. Then distinguish the SMN4Lang MEG result conceptually: the prospectively frozen sensor-level MEG representation failed the model-blind cross-participant reliability prerequisite, so no E5 transfer test was performed. Report the post-confirmatory exploratory 4/8/16-bin family only as evidence that simple temporal coarsening did not recover a familywise-reliable target. Do not call the MEG result a negative model-transfer test.

### Result 6. Neural alignment is distinct from generic semantic quality

Use the frozen semantic benchmark to show that the neural-specific representational change does not translate into a stable conventional semantic advantage.

## Main-figure architecture

### Figure 1. From reproducible neural geometry to a learnable relational constraint

- **A:** Conceptual schematic: linguistic items -> human EEG relational geometry -> neural relational loss -> model geometry.
- **B:** ChineseEEG natural-reading design and model-blind reliability-led representation selection.
- **C:** Residual neural-model RSA across Little Prince development runs.
- **D:** Sealed BERT run-07 comparison: base, text-only, neural-guided, shuffled-neural, two seeds.
- **E:** E5 architecture replication and explicit separation from generic semantic benchmark performance.

Primary message: the biological target exists, is reproducible, and can be learned.

### Figure 2. Cross-language EEG generalization

- **A:** ChineseEEG training to ZuCo English natural-reading validation schematic.
- **B:** ZuCo neural reliability across participants.
- **C:** Paired lambda 0 versus lambda 0.10 participant RSA values or delta plot.
- **D:** 17/17 participant deltas with bootstrap interval and exact sign-flip inference.

Primary message: a ChineseEEG-derived neural constraint survives dataset, participant, language, and acquisition changes within EEG.

### Figure 3. Prospective cross-modal transfer to language-network fMRI

- **A:** SMN4Lang design: 12 participants x 60 naturalistic auditory stories, fMRI, independent LanA language-network mask.
- **B:** Model-blind fMRI reliability gate with participant estimates and interval.
- **C:** Frozen causal within-sentence prefix-to-word-onset-to-HRF mapping into the fMRI timebase.
- **D:** Paired participant lambda 0 versus lambda 0.10 residual RSA.
- **E:** Participant deltas, 12/12 positive, bootstrap interval, exact sign-flip inference.

Primary message: the already learned constraint is detectable in a different neural modality and task context without target-dataset model optimization.

### Figure 4. Generalization map and boundary conditions

- **A:** Harmonized outcome display for ZuCo, SMN4Lang fMRI, TMNRED, Garnett Dream, and directional inner speech. Preserve dataset-specific inferential units and do not imply directly comparable raw RSA scales.
- **B:** SMN4Lang MEG reliability boundary: prospectively frozen 32-bin result plus explicitly post-confirmatory 4/8/16-bin temporal-granularity family. Plot cross-participant reliability with confidence intervals and show that no candidate passed the reliability criterion. Label clearly that no model evaluation was performed.
- **C:** Independence/design matrix: participant overlap, language, text, task, modality, target-dataset tuning, and whether a reliability gate permitted model evaluation.
- **D:** Generic semantic benchmark showing no stable neural-specific advantage, followed by the conceptual conclusion: portable neural constraint with selective expression, not universal model improvement.

Primary message: successful transfer is real but bounded, and evaluation itself is conditional on a reproducible neural target.

## Extended Data priority

1. ChineseEEG representation-selection benchmark and nuisance controls.
2. ChineseEEG run-wise/participant-wise neural-model correspondence.
3. E5 lambda-development history clearly separated from external validation.
4. ZuCo structural and stimulus-alignment QC.
5. SMN4Lang fMRI metadata/timebase QC and independent LanA atlas provenance.
6. SMN4Lang fMRI story-level transfer distribution, shown descriptively rather than used as the inferential unit.
7. SMN4Lang MEG prospective protocol, structural probe, primary 32-bin reliability gate, and post-confirmatory 4/8/16-bin exploratory family. Explicitly state that model evaluation was never opened.
8. TMNRED null transfer and post-confirmatory non-rescue analyses.
9. Garnett reliability plus null/inconclusive transfer.
10. Directional inner-speech boundary condition.
11. AHBA mechanistic analyses, if retained with this paper, explicitly labelled confirmatory null / exploratory / post-hoc diagnostic and kept out of the main Figure 4 unless required editorially.

## Claims to avoid

Do not write that:

- brain supervision generally improves language models;
- the fMRI effect is large;
- SMN4Lang proves pure semantic coding independent of all other language structure;
- neural-guided transfer is universal;
- MEG showed a negative transfer effect, because model evaluation was not permitted after reliability failure;
- temporal coarsening rescued MEG reliability;
- the positive results validate a GABAergic, serotonergic, dyslexia-related, or transcriptomic mechanism;
- null external datasets are failed replications that should be rescued by alternative analysis choices.

## Wording to prefer

Prefer:

- **neural relational geometry** or **language-related neural geometry** when the construct is broader than pure semantics;
- **neural-guided representational alignment** rather than generic model improvement;
- **portable / transferable neural representational constraint** for the central concept;
- **small but directionally consistent effect** for SMN4Lang fMRI;
- **prospectively frozen external validation** only where the exact protocol supports that label;
- **boundary condition** for task/dataset contexts where reliable neural geometry exists but the trained-model advantage does not transfer;
- **reliability boundary** for SMN4Lang MEG, where the neural target itself was not sufficiently reproducible to permit model evaluation;
- **post-confirmatory exploratory temporal-granularity analysis** for the 4/8/16-bin MEG family.

## Editorial test

The paper should be understandable to a scientist outside EEG, fMRI, or language-model methodology as a simple sequence:

1. identify reliable relational structure in human neural responses;
2. make a model learn that relational structure;
3. ask whether the learned change appears in independent brains;
4. show that it crosses language and then measurement modality;
5. show where transfer does not generalize and where the neural target itself is too unreliable to support the test.

If a main-text analysis does not strengthen one of those five steps, it should normally move to Extended Data, Supplementary Information, or a separate paper.
