# Results

**Working manuscript scaffold, updated 2026-08-28.** Numerical values below are taken from locked NeuroSem result summaries. Before submission, every number should be linked to its final figure/table source and exact RunRelay artifact.

## Human language responses contain a reproducible relational neural geometry

We first asked whether linguistic items evoke reproducible relational structure in neural activity before testing language-model correspondence or model training. In ChineseEEG Little Prince, the primary representation was selected using neural reliability rather than semantic-model performance. Each item epoch was averaged across time within channel, yielding a channel-valued item vector; featurewise-standardized vectors were compared using correlation distance. This temporal-mean representation showed substantially stronger cross-subject reliability than the initial flattened sensor-time representation. Raw leave-one-subject-out reliability was approximately 0.220 and remained approximately 0.121 after nuisance residualization.

Using the same primary representation, residual correspondence between the neural RDM and pinned `bert-base-chinese` final-layer representations was positive in all six Little Prince narrative runs used for the cross-run analysis. Run-level partial-Spearman effects ranged from approximately 0.0034 to 0.0174, with a mean run effect of 0.0085. The primary effect was positive in 6/6 runs, giving an exact one-sided run-level sign-flip p=0.015625. Across the common participant set, 8/9 participants had positive aggregate effects, with exact subject-level sign-flip p=0.0391.

Together, these analyses established a small but reproducible relational neural target before any neural-guided model evaluation.

## Neural relational supervision produces a learnable model change

We next tested whether neural relational supervision could improve model alignment to held-out ChineseEEG geometry. In the sealed Little Prince run-07 evaluation, neural-guided BERT was the strongest arm in two independent seeds. Mean partial-Spearman values for base, text-only, neural-guided, and shuffled-neural arms were 0.0319, 0.0354, 0.0371, and 0.0353 in seed 1, and 0.0319, 0.0341, 0.0375, and 0.0338 in seed 2. Multilingual E5 reproduced the qualitative neural-target alignment phenomenon in an independent architecture and was then frozen for external transfer tests.

This improvement was specific to neural-target alignment rather than a general semantic-performance gain. On the frozen external semantic benchmark, the neural-guided arm did not show a stable neural-specific advantage across seeds. The data therefore separate learnability of a neural relational target from broad improvement in conventional semantic benchmark performance.

## The learned neural constraint transfers across language in independent EEG

ZuCo 2.0 Task 1 Normal Reading provided an independent English-reading test with a structurally frozen 17-participant cohort. Using the prospectively inherited temporal-mean representation, mean nuisance-residualized leave-one-subject-out reliability was 0.06742, bootstrap 95% CI [0.05831, 0.07687], and all 17 participants were positive. Exact one-sided sign-flip p was 7.63e-06.

The single frozen ChineseEEG-to-ZuCo model-transfer contrast was also positive. Neural-guided multilingual-E5 lambda 0.10 minus matched text-only lambda 0 produced mean participant delta +0.0016637, median +0.0014871, bootstrap 95% CI [+0.0012294, +0.0021452], with 17/17 participants positive. Exact one-sided sign-flip p was 7.63e-06 and exact two-sided p was 1.53e-05. No ZuCo tuning, lambda selection, representation selection, participant selection, or item selection was performed from transfer outcomes.

Thus, a neural constraint learned from Chinese natural-reading EEG transferred to independent English natural-reading EEG in different participants and a different dataset.

## The learned neural constraint transfers prospectively from EEG to language-network fMRI

We next tested whether the same frozen neural-guided representation generalized across neural measurement modality. SMN4Lang / OpenNeuro `ds004078` contains 12 native-Mandarin participants listening to 60 naturalistic spoken stories. The fMRI arm was prospectively selected as a cross-modal validation rather than as another EEG replication.

### A model-blind reliability gate established the fMRI target before model loading

The primary fMRI representation was frozen before model comparison. Analyses used an independently published LanA probabilistic language-network mask thresholded at 0.20, retaining 25,137 voxels on the exact SMN4Lang 2-mm MNI grid. Within each participant-story run, retained TRs were featurewise z-scored and represented by correlation-distance RDMs across LanA multivoxel patterns. Nuisance RDMs captured absolute temporal separation, canonical-HRF-convolved word-onset density, and canonical-HRF-convolved acoustic RMS envelope.

Across 12 participants and 60 stories, the model-blind leave-one-participant-out neural geometry was highly reliable. Mean participant residual reliability was 0.65327, median 0.64760, all 12 participants were positive, the bootstrap 95% CI was [0.63945, 0.66843], and the exact one-sided sign-flip p was 0.00024414. The reliability gate was verified before either E5 model arm was loaded.

### A single frozen E5 contrast transferred to fMRI

The confirmatory model comparison reused the exact ChineseEEG-trained multilingual-E5 lambda 0.10 neural-guided adapter and the matched lambda 0 text-only adapter. SMN4Lang was not used for training. Semantic states were defined prospectively as causal within-sentence prefix embeddings at released word onsets, convolved with the same fixed canonical HRF and sampled on the frozen TR grid. No model, layer, lambda, checkpoint, ROI, lag, HRF, semantic-unit, participant, or story search was performed from fMRI outcomes.

Mean participant residual RSA for the text-only lambda 0 arm was 0.12092396. Mean participant residual RSA for the neural-guided lambda 0.10 arm was 0.12177646. The prespecified neural-guided minus text-only contrast was therefore +0.00085250 on average, with median +0.00086365. All 12 participants were positive. The participant-bootstrap 95% CI was [+0.00078966, +0.00091398], and the exact one-sided sign-flip p was 0.00024414.

The absolute effect was small, but its direction was uniform across participants and it survived a prospective change in participants, dataset, language task, and neural measurement modality. These data show that a representational change learned from natural-reading EEG can generalize to independently measured cortical language geometry during auditory narrative comprehension.

## Null transfers define the boundary of the phenomenon

The external transfer effect was not universal. We therefore treat the null datasets as boundary conditions rather than failed attempts to reproduce a universal effect.

### TMNRED replicates weak neural geometry but not the neural-guided transfer advantage

TMNRED provided an independent Chinese sentence-reading test with prospectively frozen participant, session, item, and representation choices. For the primary `row_mean_all` representation, mean nuisance-residualized leave-one-subject-out reliability was 0.00724 with bootstrap 95% CI [0.00356, 0.01079]. The geometry therefore replicated weakly but positively.

The frozen ChineseEEG-trained multilingual-E5 comparison did not transfer detectably. Neural-guided lambda 0.10 minus matched text-only lambda 0 produced mean residual-RSA delta +0.000020, bootstrap 95% CI [-0.000128, +0.000176], with one-sided sign-flip p=0.402. Post-confirmatory analyses using stronger TMNRED amplitude-SD and relative-8-bin sensitivity representations also failed to rescue the transfer contrast.

### Neural geometry generalizes to Garnett Dream, but the trained-model advantage does not clearly transfer

Garnett Dream tested the same acquisition family and overlapping participants on a different narrative. The exact presentation-row to text mapping was frozen across 18 chapters, yielding 9,047 mapped linguistic items. Mean nuisance-residualized participant reliability was 0.01863, all 10 participants were positive, the bootstrap 95% CI was [0.01636, 0.02085], and the exact one-sided sign-flip p was 0.0009766.

The subsequent frozen E5 transfer test produced mean participant delta +0.0003266 and median +0.0003319; 6/10 participants were positive. The bootstrap 95% CI [-0.0001218, +0.0007560] included zero, and the exact one-sided sign-flip p was 0.1015625. We therefore treat the model-transfer result as null/inconclusive despite robust new-narrative neural reliability.

### The directional-word dataset defines an out-of-task boundary

The directional-word analysis used covert/inner speech rather than natural reading and was therefore treated as a secondary out-of-task test. The frozen lambda 0.10 minus text-only lambda 0 mean difference was approximately -0.001786, with no evidence of positive transfer. Because the task differs substantially from the reading and narrative-comprehension datasets, this result is interpreted as a boundary condition rather than a task-matched refutation.

Together, the positive ZuCo and SMN4Lang results and the null TMNRED, Garnett, and directional-word results show that neural-guided transfer is selective rather than a trivial global increase in model-neural RSA.

## Secondary AHBA analyses do not establish a molecular mechanism

We also asked whether the cortical spatial pattern of the established ChineseEEG semantic geometry preferentially aligned with prespecified molecular systems from the Allen Human Brain Atlas. Model-blind preparation froze AHBA preprocessing, donor handling, bilateral treatment, the 128-channel EEG forward/source-sensitivity model, DK68 cortical mapping, and biological gene-set families before outcome testing.

The primary family contained seven GABAergic, serotonergic, and pathway sets. None showed reliable association with the frozen semantic spatial target under the prespecified participant-level and random-gene-set framework. Mean associations ranged from approximately -0.050 to +0.056, with nonsignificant corrected inference throughout.

An explicitly exploratory whole-transcriptome PLS analysis produced in-sample score-phenotype Pearson r=0.4574 and R2=0.2092, but failed hemisphere-constrained spatial-null inference, two-sided p=0.2745. No intrinsic transcriptomic gradient survived FDR.

Two independently frozen published language-gene panels were also primary-null. A no-mirror sensitivity for the fourteen-gene dyslexia panel was stronger than the primary mirrored result, but the primary analysis remained null. Post-hoc diagnostics localized most of this sensitivity to right-hemisphere expression-map changes under sparse AHBA right-hemisphere sampling.

We therefore interpret AHBA as a mechanistic constraint and methodological sensitivity, not as evidence for a specific molecular explanation of the transferable neural geometry.

## Joint interpretation

Across datasets, the evidence supports a specific sequence of claims. First, natural-language neural responses contain reproducible relational geometry. Second, that geometry can serve as a learnable model-training target under sealed neural evaluation. Third, the resulting neural-guided representation can transfer prospectively to independent cross-language EEG and to independent language-network fMRI. Fourth, transfer is selective rather than universal, and it does not imply a stable generic semantic benchmark gain. Finally, the present data do not establish a molecular mechanism for the neural geometry.

The central contribution is therefore not that brain supervision broadly improves a language model. It is that a reproducible biological relational structure can be converted into a model constraint whose portability can be tested across independent brains and neural measurement modalities.
