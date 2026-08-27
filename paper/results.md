# Results

**Working manuscript scaffold.** Numerical values below are taken from the current locked NeuroSem result summaries. Before submission, every number should be linked to its final figure/table source and exact RunRelay artifact.

## Reproducible relational EEG geometry during natural reading

We first asked whether linguistic items evoke reproducible relational structure in EEG before testing language-model correspondence. In ChineseEEG Little Prince, the primary representation was selected using neural reliability rather than semantic-model performance. Each item epoch was averaged across time within channel, yielding a channel-valued item vector; featurewise-standardized vectors were compared using correlation distance. This temporal-mean representation showed substantially stronger cross-subject reliability than the initial flattened sensor-time representation. Raw leave-one-subject-out reliability was approximately 0.220 and remained approximately 0.121 after nuisance residualization.

Using the same primary representation, residual correspondence between the neural RDM and pinned `bert-base-chinese` final-layer representations was positive in all six Little Prince narrative runs used for the cross-run analysis. Run-level partial-Spearman effects ranged from approximately 0.0034 to 0.0174, with a mean run effect of 0.0085. The primary effect was positive in 6/6 runs, giving an exact one-sided run-level sign-flip p=0.015625. Across the common participant set, 8/9 participants had positive aggregate effects, with exact subject-level sign-flip p=0.0391.

Together, these results establish a small but reproducible neural relational geometry associated with language-model semantic structure after nuisance control.

## Neural-guided training improves held-out alignment within ChineseEEG

We next tested whether neural relational supervision could improve model alignment to held-out ChineseEEG geometry. In the sealed Little Prince run-07 evaluation, neural-guided BERT was the strongest arm in two independent seeds. Mean partial-Spearman values for base, text-only, neural-guided, and shuffled-neural arms were 0.0319, 0.0354, 0.0371, and 0.0353 in seed 1, and 0.0319, 0.0341, 0.0375, and 0.0338 in seed 2. Multilingual E5 reproduced the qualitative neural-target alignment phenomenon in an independent architecture.

This improvement was specific to neural-target alignment rather than a general semantic-performance gain. On the frozen external semantic benchmark, the neural-guided arm did not show a stable neural-specific advantage across seeds. The data therefore separate learnability of the neural relational target from broad improvement in generic semantic representations.

## Independent reading datasets reveal robust neural geometry but non-universal model transfer

### TMNRED replicates weak neural geometry but not the neural-guided transfer advantage

TMNRED provided an independent Chinese sentence-reading test with prospectively frozen participant, session, item, and representation choices. For the primary `row_mean_all` representation, mean nuisance-residualized leave-one-subject-out reliability was 0.00724 with bootstrap 95% CI [0.00356, 0.01079]. The geometry therefore replicated weakly but positively.

The frozen ChineseEEG-trained multilingual-E5 comparison did not transfer detectably to TMNRED. Neural-guided lambda 0.10 minus matched text-only lambda 0 produced mean residual-RSA delta +0.000020, bootstrap 95% CI [-0.000128, +0.000176], with 55.2% of participants positive and one-sided sign-flip p=0.402. Post-confirmatory analyses using the stronger TMNRED amplitude-SD and relative-8-bin sensitivity representations also failed to rescue the transfer contrast.

### ZuCo shows strong cross-language neural replication and positive frozen transfer

ZuCo 2.0 Task 1 Normal Reading provided an independent English-reading test with a structurally frozen 17-participant cohort. Using the prospectively inherited temporal-mean representation, mean nuisance-residualized leave-one-subject-out reliability was 0.06742, bootstrap 95% CI [0.05831, 0.07687], and all 17 participants were positive. Exact one-sided sign-flip p was 7.63e-06.

The single frozen ChineseEEG-to-ZuCo model-transfer contrast was also positive. Neural-guided multilingual-E5 lambda 0.10 minus matched text-only lambda 0 produced mean participant delta +0.0016637, median +0.0014871, bootstrap 95% CI [+0.0012294, +0.0021452], with 17/17 participants positive. Exact one-sided sign-flip p was 7.63e-06 and exact two-sided p was 1.53e-05. No ZuCo tuning, lambda selection, representation selection, participant selection, or item selection was performed from transfer outcomes.

Thus, a modest neural-guided advantage learned from ChineseEEG transferred to an independent English natural-reading EEG dataset, although the TMNRED result shows that this transfer is not universal.

## Neural geometry generalizes across narratives within ChineseEEG, but the trained-model advantage does not clearly transfer

Garnett Dream tested the same acquisition family and overlapping participants on a different narrative. The exact presentation-row to text mapping was frozen across 18 chapters, yielding 9,047 mapped linguistic items. Using the prospectively designated `row_mean_all` representation, mean raw leave-one-subject-out reliability was 0.03545 and mean nuisance-residualized participant reliability was 0.01863. The median residualized value was 0.01895, all 10 participants were positive, the participant-bootstrap 95% CI was [0.01636, 0.02085], and the exact one-sided sign-flip p was 0.0009766.

The subsequent frozen E5 transfer test compared the already-trained ChineseEEG neural-guided lambda 0.10 model with matched text-only lambda 0 using chapter-wise RSA, full text-derived nuisance control, and participant-level inference. The mean participant delta was +0.0003266 and median +0.0003319; 6/10 participants were positive. The bootstrap 95% CI [-0.0001218, +0.0007560] included zero, and the exact one-sided sign-flip p was 0.1015625. We therefore treat the model-transfer result as null/inconclusive despite robust new-narrative neural reliability.

This dissociation shows that generalization of the neural geometry itself is stronger than generalization of the trained-model advantage.

## The Nature directional-word dataset defines an out-of-task boundary condition

The Nature directional-word analysis used covert/inner speech rather than natural reading and was therefore treated as a secondary out-of-task test. The frozen lambda 0.10 minus text-only lambda 0 mean difference was approximately -0.001786, with no evidence of positive transfer. Because the task differs substantially from the reading datasets, this result is interpreted as a boundary condition rather than a task-matched refutation of reading-related neural geometry.

## A frozen AHBA analysis does not support prespecified GABAergic or serotonergic mechanisms

We next asked whether the cortical spatial pattern of the established ChineseEEG semantic geometry preferentially aligned with prespecified molecular systems from the Allen Human Brain Atlas. Model-blind preparation froze AHBA preprocessing, donor handling, bilateral treatment, the 128-channel EEG forward/source-sensitivity model, DK68 cortical mapping, and the biological gene-set families before outcome testing.

The primary family contained seven GABAergic, serotonergic, and pathway sets. None showed reliable association with the frozen semantic spatial target under the prespecified participant-level and random-gene-set framework. Mean Spearman associations and exact sign-flip p values were: GABA-A rho=0.0398, p=0.6953; GABA-B rho=0.0560, p=0.5938; GABA machinery rho=-0.0497, p=0.6211; serotonin receptors rho=0.0370, p=0.6133; serotonin machinery rho=0.0542, p=0.5234; Reactome GABA activation rho=0.0456, p=0.6836; and Reactome serotonin receptors rho=0.0372, p=0.5000. BH-corrected q values were nonsignificant throughout. Broad cell-type controls were also nonsignificant by the primary participant-level inference.

Accordingly, population cortical transcriptomic variation in these prespecified GABAergic and serotonergic systems did not reliably explain the spatial channel-contribution pattern of established ChineseEEG semantic neural geometry.

## Exploratory whole-transcriptome analysis does not survive spatial null inference

To ask whether a broader transcriptomic pattern might relate to the cortical phenotype, we performed an explicitly exploratory whole-transcriptome PLS analysis using the frozen AHBA-blind DK68 semantic target. PLS1 showed moderate in-sample alignment between its score and the semantic phenotype, Pearson r=0.4574 and R2=0.2092. However, under 5,000 hemisphere-constrained spherical rotations with within-hemisphere one-to-one reassignment, the two-sided spatial-null p value was 0.2745. The global PLS result therefore did not survive spatial inference.

The first ten intrinsic transcriptomic gradients likewise showed no FDR-significant association with the semantic phenotype. Gradient 10 was the closest nominal trend, Spearman rho=0.2256, spin p=0.0566, but q=0.4747. Leave-one-donor-out PLS gene-weight rankings were highly stable for five valid donor exclusions, but stable rankings do not establish phenotype association when the global spatial test is null.

## Published language-gene panels remain primary-null under spatial and coexpression-aware controls

We independently froze two exact Wong et al. 2024 main-article subsets before outcome testing: a six-gene structural-connectivity panel and a fourteen-gene dyslexia-related panel. All genes were represented in the primary AHBA universe.

For the six-gene connectivity panel, the observed cortical association was Spearman rho=-0.1515. The spatial-spin p value was 0.463 and the coexpression-profile-matched gene-set p value was 0.389, providing no evidence of support.

For the fourteen-gene dyslexia panel, the observed association was rho=-0.2733. The raw spatial-spin p value was 0.0516, with BH q=0.103 across the two published panels. The coexpression-profile-matched gene-set p value was 0.0990, q=0.198. The panel therefore failed the frozen criterion requiring support under both spatial and coexpression-aware inference.

## Post-hoc mirroring diagnostics reveal a right-hemisphere preprocessing sensitivity

A prespecified no-mirror sensitivity of the dyslexia panel was substantially stronger than the primary left-to-right mirrored result, with rho=-0.4776 and nominally strong spatial and coexpression-aware p values. Because this was a sensitivity analysis following a failed primary result, it was not treated as confirmatory evidence. We instead performed a post-hoc diagnostic to determine why the bilateral handling choice changed the association.

The diagnostic ruled out parcel-support loss: both mirrored and no-mirror dyslexia maps had 68 common parcels, and restricting the mirrored analysis to matched support left its whole-cortex association unchanged at rho=-0.2733. The left-hemisphere association was already strong and nearly invariant to mirroring, with mirrored rho=-0.5670 and no-mirror rho=-0.5804. In contrast, the right-hemisphere mirrored association was approximately zero, rho=+0.0038, whereas the no-mirror right-hemisphere map was strongly negative, rho=-0.4310. Mirrored and no-mirror dyslexia maps were highly similar in the left hemisphere, rho=0.9884, but only moderately similar in the right hemisphere, rho=0.5047.

The no-mirror shift was not attributable to one gene alone. Among the larger gene-level changes toward more negative semantic association were OXR1, GABRD, SLIT2, CDH10, and GPR26. Leave-one-donor-out matched-support analyses preserved the same direction: for every donor exclusion, the no-mirror dyslexia-panel association remained more negative than the mirrored association.

We interpret this as a methodological sensitivity of AHBA bilateral preprocessing under asymmetric donor sampling, not as a validated dyslexia-related molecular mechanism.

## Joint interpretation

Across datasets, the evidence supports reproducible reading-related neural geometry and demonstrates that neural-guided training can produce transferable neural-alignment benefits under some conditions, most clearly in independent English natural reading. The transfer advantage is not universal and does not provide a stable generic semantic benefit. The AHBA extension further constrains the mechanistic interpretation: prespecified neurotransmitter systems and independent published language-gene panels are not confirmatorily supported, while the post-hoc mirroring analysis identifies an important hemispheric preprocessing sensitivity that requires independent bilateral transcriptomic validation.
