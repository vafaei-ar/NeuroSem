# Human neural geometry provides a transferable constraint on language representations

**Working Nature Article draft, v1**  
**Evidence status:** locked analyses only; no new inference introduced in this manuscript draft.  
**Date:** 2026-08-28

## Summary

Language models and human brains both encode relations among linguistic inputs, but it remains unclear whether neural representational structure can serve as a transferable constraint on artificial language representations. We derived a reproducible relational geometry from electroencephalographic responses during natural reading and used this geometry as an auxiliary training target for language-model representations. Neural-guided training produced a small but reproducible change in model geometry that generalized beyond the neural data used for training. The frozen neural-guided model showed improved alignment to independent English-reading electroencephalography and, prospectively, to language-network functional magnetic resonance imaging measured in different participants during naturalistic auditory comprehension. These effects were directionally consistent across all participants in the two strongest external validations. Transfer was not universal: other reading and inner-speech datasets produced null or inconclusive effects, and a prospectively specified sensor-level magnetoencephalography target failed its model-blind cross-participant reliability gate before model evaluation. A subsequently frozen exploratory temporal-granularity family likewise yielded no reliable MEG target from 4 to 32 normalized-time bins. Neural relational supervision therefore does not simply make language representations generally better. Instead, it can impose a portable biological constraint whose detectable expression depends on the neural and task geometry being tested and on whether the target neural geometry is itself reproducible.

## Main text

Language models are commonly compared with human neural responses after training, with the brain treated as an external benchmark for representational similarity. This approach asks whether an artificial representation resembles neural activity, but not whether the relational structure contained in neural data can itself shape model learning. A stronger test of biological relevance is therefore directional: if neural representational geometry is used as a learning constraint, does the resulting change remain detectable in independent brains that were never used to define or tune the model?

This question is difficult for two reasons. First, neural measurements contain large amounts of participant-specific, acquisition-specific and task-specific variation, so a useful target must be demonstrably reproducible before it is used for model supervision. Second, apparent neural-model correspondence can be inflated by analytical flexibility, especially when choices of representation, model, layer, regularization strength, participant subset or region of interest are adjusted after observing target-dataset outcomes. We therefore structured NeuroSem around a sequence of increasingly independent tests. We first identified a reproducible relational geometry in electroencephalography (EEG) during natural reading, then asked whether language-model representations contained residual correspondence with that geometry, then trained models with an auxiliary neural relational objective, and finally carried a frozen model contrast into independent neural datasets without target-dataset tuning.

The resulting evidence supports a selective rather than universal form of transfer. Neural-guided training improved alignment to the development EEG target and transferred to independent English-reading EEG. More importantly, the same already-trained model prospectively improved alignment to language-network functional magnetic resonance imaging (fMRI) during naturalistic auditory comprehension in different participants. Other datasets provided null or inconclusive transfer results, and a prospectively defined sensor-level magnetoencephalography (MEG) representation failed its model-blind reliability prerequisite before model evaluation. Together, these findings indicate that human neural geometry can provide a transferable relational constraint on language representations, but that the detectability of this constraint depends on the neural and task geometry being tested.

## Reproducible language-related neural geometry provides a training target

We began with ChineseEEG Little Prince natural reading and selected the primary EEG representation on neural reliability rather than on semantic-model performance. The selected whole-row temporal-mean representation showed substantial cross-participant reproducibility before nuisance control and retained positive reliability after nuisance residualization, with raw leave-one-participant-out (LOO) reliability of approximately 0.220 and residual LOO reliability of approximately 0.121 (Fig. 1a,b). Thus, linguistic items could be represented by a relational neural geometry that was shared across participants rather than being dominated by idiosyncratic response structure.

We next asked whether this neural geometry contained correspondence with language-model representations beyond nuisance structure. Across six held-out Little Prince narrative runs, final-layer Chinese BERT representations showed small but consistently positive residual neural-model correspondence. Mean partial-Spearman values were 0.0057, 0.0034, 0.0145, 0.0045, 0.0174 and 0.0056 across runs 01-06, respectively. All six run-level effects were positive, with a mean of 0.0085 and an exact one-sided run-level sign-flip probability of 0.015625 (Fig. 1c). These effects were modest in magnitude, but their consistency established that the reproducible EEG geometry contained relational structure that overlapped with language-model geometry after nuisance adjustment.

To test whether this neural structure could act as a learning signal rather than only as an evaluation target, we added a neural relational objective to model training. In the sealed ChineseEEG run-07 evaluation, neural-guided BERT exceeded matched text-only and shuffled-neural controls in both seeds. Residual neural alignment for the neural-guided model was 0.0371 and 0.0375 across the two seeds, compared with 0.0354 and 0.0341 for text-only training, 0.0353 and 0.0338 for shuffled-neural training, and 0.0319 for the base model in both seeds (Fig. 1d). Multilingual E5 reproduced the qualitative neural-guided alignment effect, providing an architecture and multilingual model family suitable for frozen external testing.

The neural objective did not produce a stable general improvement on conventional semantic benchmarks. Across an eight-task semantic benchmark, neural-guided and text-only models were nearly indistinguishable in one seed and neural-guided performance was lower in the other. This dissociation argues against interpreting the intervention as generic semantic improvement. Instead, the training objective changed model representations in a way that was specifically detectable relative to neural geometry (Fig. 1e).

## Neural-guided geometry transfers across dataset and language

We next tested whether the learned neural constraint generalized to an independent English-reading EEG dataset, ZuCo 2.0 Task 1 Normal Reading. The neural representation was defined prospectively from the previously established analysis family, and model evaluation used the frozen multilingual-E5 contrast between neural-guided lambda 0.10 and matched text-only lambda 0. No ZuCo outcome was used to retune the model contrast.

The prospectively frozen all-retained-channel temporal-mean EEG representation was itself reproducible across the 17 ZuCo participants. Mean residual LOO reliability was 0.06742, with median 0.06559 and a participant-bootstrap 95% confidence interval of 0.05831 to 0.07687. All 17 participants had positive reliability, and the exact one-sided sign-flip probability was 7.63 × 10^-6 (Fig. 2b). This established that the target neural geometry generalized across dataset, acquisition context, participants and language.

We then compared neural-guided and text-only E5 representations against the frozen ZuCo neural geometry. The neural-guided model showed a mean participant RSA increment of 0.0016637 relative to text-only, with median increment 0.0014871 and a bootstrap 95% confidence interval of 0.0012294 to 0.0021452. The difference was positive in all 17 participants, with exact one-sided sign-flip probability 7.63 × 10^-6 (Fig. 2c,d). Thus, a relational constraint learned from Chinese natural-reading EEG remained detectable in independent English-reading EEG without target-dataset model tuning.

This result is important because it separates the existence of reproducible neural geometry from the transfer of a neural-guided model advantage. ZuCo supported both. The shared relational structure was reproducible across participants, and the model change produced by ChineseEEG neural guidance shifted the model in a direction that improved alignment to that independently measured geometry.

## The learned constraint transfers prospectively across measurement modality

We next asked whether the same learned constraint could generalize beyond EEG. SMN4Lang (OpenNeuro ds004078) provided an independent cohort of 12 Mandarin-speaking participants who listened to 60 naturalistic spoken Chinese stories during fMRI. This dataset was designated prospectively for cross-modal validation. Critically, the fMRI neural target was required to pass a model-blind reliability gate before any E5 representation was evaluated.

We defined the primary fMRI representation in an independently published LanA language-network mask thresholded at probability 0.20, retaining 25,137 voxels. For each participant and story, multivoxel response geometry was summarized using correlation distance after nuisance adjustment for temporal separation, haemodynamic-response-function-convolved word-onset density and haemodynamic-response-function-convolved acoustic RMS envelope. Across the 12 participants, mean residual LOO reliability was 0.65327, median 0.64760, and all 12 participants were positive. The participant-bootstrap 95% confidence interval was 0.63945 to 0.66843 and the exact one-sided sign-flip probability was 0.00024414 (Fig. 3a,b). The neural target therefore passed the prespecified reliability gate before model evaluation.

We then mapped frozen E5 representations into the fMRI timebase using causal within-sentence prefix states sampled at released word onsets, convolved with the same fixed canonical haemodynamic response. No SMN4Lang model training, participant selection, lambda selection, layer selection, checkpoint selection, region-of-interest search, lag search, haemodynamic-response search or semantic-unit search was performed from the fMRI outcome (Fig. 3c).

Mean participant residual RSA was 0.12092396 for the text-only lambda 0 model and 0.12177646 for the neural-guided lambda 0.10 model. The mean participant increment was therefore 0.00085250, with median 0.00086365 and bootstrap 95% confidence interval 0.00078966 to 0.00091398. The increment was positive in all 12 participants, with exact one-sided sign-flip probability 0.00024414 (Fig. 3d,e).

The absolute effect was small, and we do not interpret it as a large increase in explained neural variance. Its importance instead lies in the independence of the validation and the directional consistency of the participant-level effect. A model intervention learned from Chinese reading EEG was carried without SMN4Lang tuning into different participants, a different task context, and a different measurement modality, where it produced a positive shift in alignment to independently defined language-network fMRI geometry.

## Transfer is selective rather than universal

The positive ZuCo and SMN4Lang results did not extend uniformly across all neural datasets. This heterogeneity was retained as part of the inferential structure rather than treated as a reason to retune the model or neural representation.

In TMNRED, the prospectively frozen temporal-mean EEG representation showed weak but positive reproducibility, with mean residual LOO reliability 0.00724 and bootstrap 95% confidence interval 0.00356 to 0.01079. However, the frozen E5 neural-guided minus text-only contrast was effectively null: mean participant delta 0.000020, median 0.000053, bootstrap 95% confidence interval -0.000128 to 0.000176, and one-sided sign-flip probability 0.402. Exploratory alternative EEG summaries did not recover convincing transfer. TMNRED therefore shows that a reproducible neural geometry does not guarantee that the learned neural-guided model advantage will transfer to that geometry.

ChineseEEG Garnett Dream provided a complementary within-acquisition boundary condition. The frozen EEG geometry generalized to a new narrative in the same participant family: residual mean LOO reliability was 0.01863, the 95% confidence interval was 0.01636 to 0.02085, and all 10 participants were positive. Yet the frozen E5 transfer effect was inconclusive, with mean delta 0.0003266, bootstrap 95% confidence interval -0.0001218 to 0.0007560, six of ten participants positive, and exact one-sided sign-flip probability 0.1015625. Thus, neural-geometry generalization and model-transfer generalization are separable properties.

A directional-word inner-speech dataset provided a stronger task-shift boundary. The frozen covert/inner-speech neural-guided minus text-only contrast was approximately -0.001786, with no evidence of positive transfer. Because this task differs substantially from natural reading, we interpret it as an out-of-task boundary condition rather than as a task-matched refutation of the reading results.

Together, these datasets show that neural guidance does not create a universally superior language representation. The same model contrast that transferred consistently in ZuCo and SMN4Lang was null or inconclusive in other contexts. This selectivity narrows the interpretation toward a portable but context-dependent relational constraint rather than a general-purpose improvement.

## A prospectively defined MEG target failed the reliability prerequisite for model testing

SMN4Lang also released MEG from the same 12 participants and 60 stories, providing an opportunity to ask whether the transfer framework could be extended to a second electrophysiological modality. We prospectively froze a sensor-level MEG representation before model evaluation. For each participant-story run, valid preprocessed 1-40 Hz samples were divided into 32 equal normalized-time bins after exclusion of bad samples. Root-mean-square field magnitude was summarized separately across retained magnetometers and planar gradiometers, standardized within sensor type across bins, concatenated, and converted into a story-by-story correlation-distance representational dissimilarity matrix.

The resulting 32-bin representation did not yield sufficiently reproducible cross-participant story geometry. Mean LOO reliability was 0.007713, median 0.011320, with seven of twelve participants positive. The participant-bootstrap 95% confidence interval ranged from -0.007627 to 0.021655 and the exact one-sided sign-flip probability was 0.16870 (Fig. 4b). The representation therefore failed the prespecified model-blind reliability gate. Consistent with the frozen protocol, no E5 model-alignment analysis was performed.

After this confirmatory failure, we conducted one bounded post-confirmatory sensitivity analysis to test whether temporal aggregation alone could explain the absence of a reliable target. Before observing alternative outcomes, we froze three coarser temporal granularities of 4, 8 and 16 bins while retaining the same sensor families, preprocessing, standardization and RDM construction. None passed the familywise reliability criterion. Mean LOO reliability was 0.01534 for 4 bins, 0.00548 for 8 bins and 0.00817 for 16 bins; their ordinary 95% confidence intervals all crossed zero, and none met the Bonferroni-adjusted familywise rule. Because no exploratory candidate passed, no model evaluation was opened for any MEG representation.

The MEG result is therefore a reliability boundary, not a negative model-transfer result. It shows that the present sensor-level RMS representation family did not provide a sufficiently reproducible cross-participant target to support the transfer test. It does not establish that MEG cannot contain transferable language-related geometry under other prospectively specified representations.

## Neural alignment is distinct from generic semantic quality

The full pattern of positive and null results argues against a simple account in which neural guidance improves language representations globally. Generic semantic benchmarks did not show a stable neural-specific benefit, and independent neural transfer was selective across datasets. The strongest effects appeared when the neural target itself was reproducible and when the external task retained substantial natural-language structure, as in ZuCo natural reading and SMN4Lang auditory narratives. Even then, effect magnitude varied substantially across measurement contexts and should not be compared directly across EEG and fMRI RSA scales.

These findings instead support a relational interpretation. Neural-guided training imposes a small change in model geometry that is not reducible to generic benchmark improvement, but that can remain detectable in independent neural representational spaces. The cross-language EEG and cross-modal fMRI results demonstrate portability, whereas TMNRED, Garnett Dream, directional inner speech and the SMN4Lang MEG reliability boundary define the limits of that portability and of the conditions under which it can be evaluated.

## Discussion

Neural-model alignment studies usually ask whether a pretrained model resembles the brain. Here we asked whether reliable neural relational structure can influence model learning in a way that remains detectable beyond the neural data used for training. The answer is qualified but positive. A relational target derived from Chinese natural-reading EEG altered language-model geometry, the resulting neural-guided representation improved alignment to independent English-reading EEG in all 17 ZuCo participants, and the same frozen model prospectively improved alignment to independently defined language-network fMRI in all 12 SMN4Lang participants during naturalistic auditory comprehension.

The strongest conclusion is therefore not that brain supervision generally improves language models, nor that a single universal neural semantic geometry has been identified. Rather, human neural geometry can act as a transferable relational constraint on language representations. This distinction matters. The intervention did not produce a stable neural-specific advantage on generic semantic benchmarks, and transfer was null or inconclusive in TMNRED, Garnett Dream and directional inner speech. Neural geometry itself could be reproducible without carrying a detectable model-transfer advantage, as in TMNRED and Garnett Dream. Conversely, in SMN4Lang MEG the analysis stopped before model evaluation because the prospectively frozen neural target was not sufficiently reproducible. These outcomes demonstrate that reliability of the target and transfer of the learned constraint are distinct empirical questions.

The cross-modal SMN4Lang result provides the most stringent validation because it crosses participants, task context and measurement modality without target-dataset model optimization. The increment in fMRI RSA is numerically small. We therefore place little weight on its absolute magnitude in isolation. More informative is the combination of prospective design, model-blind neural reliability assessment, independent language-network definition, absence of outcome-driven model or mapping search, and positive participant-level direction in all 12 individuals. Under these constraints, a small consistent shift is evidence that the model intervention learned from EEG altered representational relations in a direction that remained detectable in independently measured cortical language responses.

The selectivity of transfer also constrains interpretation of what the neural target represents. The relevant geometry should not be equated with pure lexical or semantic coding. Naturalistic EEG and fMRI reflect multiple correlated dimensions, including lexical, syntactic, discourse, temporal, acoustic and attentional structure. We therefore use the terms neural relational geometry or language-related neural geometry rather than claiming isolation of a purely semantic code. The central result concerns transferable relational structure, not the exclusivity of its cognitive content.

A further implication is methodological. Reliability should precede neural-model comparison whenever the scientific claim depends on shared representational geometry. In SMN4Lang fMRI, the model-blind reliability gate established that a common neural target existed before model evaluation. In MEG, the same logic prevented an uninterpretable transfer test after the prespecified target failed. The subsequent bounded temporal-granularity analysis did not recover a familywise-reliable MEG target, reinforcing the decision not to proceed. This design separates failure of a neural representation from failure of a model and reduces incentives for post-outcome target search.

The study has several limitations. First, the transfer effects are small in absolute RSA units and should be interpreted as representational shifts rather than large improvements in neural prediction. Second, the development target and external datasets differ in acquisition, linguistic material, preprocessing and inferential scale, which strengthens independence but complicates direct effect-size comparison. Third, the positive external tests are accompanied by genuine nulls, indicating that the learned constraint is not universally expressed. Fourth, the present MEG conclusion is representation-specific: failure of the frozen sensor-level RMS geometry does not exclude transferable structure in prospectively motivated source-resolved, spectrotemporal or event-aligned MEG representations. Finally, secondary transcriptomic analyses do not establish a specific molecular mechanism for the neural geometry and should not be used to strengthen the primary representational claim.

These limits define a tractable next step. If neural relational constraints are biologically meaningful, future work should test prospectively specified targets across broader languages, tasks, developmental groups and clinical populations, while separating three stages that are often conflated: whether a neural geometry is reproducible, whether a model can learn it, and whether the learned change transfers to independent neural contexts. The present results establish that all three stages can align across independent brains, languages and measurement modalities, but also that they need not do so universally.

## Methods

### Study logic and inferential hierarchy

Analyses were organized as a sequence of development, sealed validation and prospectively frozen external tests. Neural representations were evaluated for cross-participant reproducibility before they were used as external model targets whenever the protocol specified a reliability gate. Model contrasts, target representations and inferential units were carried forward without target-outcome-driven retuning. Post-confirmatory analyses were explicitly labelled and did not revise the status of failed primary tests.

### ChineseEEG development target

ChineseEEG Little Prince natural-reading EEG was used to establish the development neural geometry. The primary whole-row temporal-mean representation was selected using neural reliability before semantic-model testing. Pairwise distances among linguistic items defined participant-specific representational dissimilarity matrices. Nuisance-adjusted cross-participant reliability was assessed using leave-one-participant-out comparison against the mean geometry of the remaining participants. Residual neural-model correspondence was evaluated across held-out narrative runs using partial Spearman association after the frozen nuisance adjustment.

### Neural-guided model training

Language-model representations were trained with an auxiliary relational objective that encouraged model pairwise geometry to align with the reproducible EEG target while retaining the matched text-learning objective. BERT development experiments included text-only and shuffled-neural controls and were evaluated on sealed ChineseEEG run 07. Multilingual E5 was then used for the external transfer program. The primary external contrast was fixed as neural-guided lambda 0.10 versus matched text-only lambda 0.

### ZuCo EEG validation

ZuCo 2.0 Task 1 Normal Reading served as the independent English-reading EEG validation. The frozen primary representation was the all-retained-channel temporal mean. Cross-participant neural reliability was evaluated before interpreting model-transfer results. The inferential unit was the participant. Neural-guided versus text-only transfer was summarized by participant-level RSA differences, participant bootstrap confidence intervals and exact sign-flip inference.

### SMN4Lang fMRI validation

SMN4Lang/OpenNeuro ds004078 served as the prospective cross-modal validation. The primary fMRI target used the independently published LanA language-network mask thresholded at probability 0.20. Story-level multivoxel patterns were converted to correlation-distance RDMs after nuisance adjustment for temporal separation, haemodynamic-response-convolved word-onset density and haemodynamic-response-convolved acoustic RMS envelope. A model-blind cross-participant reliability gate was completed before model loading.

For model evaluation, E5 representations were generated causally within sentence using prefix states at released word onsets, mapped into the fMRI timebase using the fixed canonical haemodynamic response, and residualized using the same nuisance family. The only primary model comparison was lambda 0.10 versus lambda 0. No SMN4Lang model training, layer search, checkpoint search, ROI search, lag search, haemodynamic-response search or semantic-unit search was performed from the fMRI outcome.

### Boundary datasets

TMNRED, ChineseEEG Garnett Dream and the directional-word inner-speech dataset were analyzed as external boundary conditions using their frozen protocols. TMNRED and Garnett first established whether the designated neural geometry was reproducible, then evaluated the same fixed E5 contrast. Directional inner speech was treated as an out-of-task boundary rather than a task-matched reading replication.

### SMN4Lang MEG reliability gate

The prospective SMN4Lang MEG analysis used released preprocessed 1-40 Hz sensor-level data from the same 12 participants and 60 stories. Samples covered by annotations beginning with `bad` were excluded. Remaining valid samples were concatenated in temporal order and divided into 32 equal normalized-time bins. Within each bin, one RMS field-magnitude value was calculated across all retained magnetometer samples and one across all retained planar-gradiometer samples. The 32 magnetometer and 32 gradiometer values were separately standardized across bins and concatenated into a 64-dimensional run vector. Participant-specific 60 × 60 story RDMs were then constructed using correlation distance.

Cross-participant reliability was defined as the Spearman correlation between each participant's upper-triangular RDM edges and the edgewise mean RDM of the other 11 participants. The primary gate required positive mean reliability, a participant-bootstrap 95% confidence interval entirely above zero and an exact one-sided sign-flip probability below 0.05. The gate failed, so no confirmatory model evaluation was performed.

A post-confirmatory model-blind temporal-granularity analysis was subsequently frozen before alternative outcomes. The only candidate representations used 4, 8 and 16 bins, with all other representation choices unchanged. Familywise reliability was controlled across the three candidates using a Bonferroni-adjusted one-sided alpha of 0.0166667 and a 98.3333% participant-bootstrap confidence interval. No candidate passed, and no exploratory E5 model evaluation was opened.

### Statistical inference

Participant-level effects were treated as the primary inferential unit for external neural validation. Confidence intervals were obtained by participant bootstrap according to the frozen protocol for each dataset. Exact sign-flip tests enumerated all sign assignments where feasible. Raw effect magnitudes were not pooled across EEG, fMRI and MEG because the representational constructions and measurement scales differ.

### Transcriptomic analyses

AHBA analyses were secondary mechanistic extensions rather than part of the primary transfer claim. Prespecified GABAergic, serotonergic and pathway gene-set tests were null under the frozen participant-level and multiplicity-corrected framework. Exploratory whole-transcriptome and hemispheric sensitivity analyses did not revise those primary null results. Full molecular methods and provenance are retained in the project documentation and should be presented in Extended Data or Supplementary Information rather than used to support the primary neural-transfer conclusion.

## Figure plan

**Figure 1 | From reproducible neural geometry to a learnable relational constraint.** ChineseEEG natural-reading design; reliability-led representation selection; residual neural-model correspondence across development runs; sealed BERT run-07 control comparison; E5 replication and generic semantic-benchmark dissociation.

**Figure 2 | Cross-language EEG generalization.** ChineseEEG-to-ZuCo validation design; ZuCo reliability; paired lambda 0 versus lambda 0.10 participant values; 17/17 participant transfer deltas.

**Figure 3 | Prospective cross-modal transfer to language-network fMRI.** SMN4Lang design and LanA mask; model-blind reliability gate; frozen causal E5-to-fMRI mapping; paired participant RSA; 12/12 positive deltas.

**Figure 4 | Generalization map and boundary conditions.** Harmonized external outcome map for ZuCo, SMN4Lang fMRI, TMNRED, Garnett Dream and directional inner speech; SMN4Lang MEG reliability boundary across 4, 8, 16 and 32 bins; independence/design matrix; generic semantic benchmark and conceptual conclusion.

## Extended Data priorities

1. ChineseEEG representation-selection benchmark and nuisance controls.
2. ChineseEEG run-wise and participant-wise neural-model correspondence.
3. E5 lambda-development history separated from external validation.
4. ZuCo structural and stimulus-alignment quality control.
5. SMN4Lang fMRI metadata/timebase quality control and LanA atlas provenance.
6. SMN4Lang fMRI story-level transfer distribution as descriptive evidence only.
7. SMN4Lang MEG prospective protocol, structural probe, primary 32-bin reliability gate and post-confirmatory 4/8/16-bin family.
8. TMNRED null transfer and bounded post-confirmatory analyses.
9. Garnett reliability and null/inconclusive transfer.
10. Directional inner-speech boundary condition.
11. AHBA confirmatory nulls and exploratory hemispheric sensitivity.

## Claims explicitly excluded from this draft

This manuscript does not claim that neural guidance generally improves language models, that the fMRI effect is large, that SMN4Lang isolates pure semantic coding, that transfer is universal, that MEG showed negative model transfer, that temporal coarsening rescued MEG reliability, or that a specific transcriptomic mechanism explains the transferable geometry.
