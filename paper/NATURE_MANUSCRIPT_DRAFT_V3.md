# Human neural geometry provides a transferable constraint on language representations

**Working Nature Article manuscript, v3**  
**Synchronized from author-edited Word working copy:** `NeuroSem_Nature_Manuscript_v0.1.docx`  
**Source DOCX SHA256:** `1f4185dd5266a03d5de04e7e8f2991e3c9796997c146a8ce965bb7634ec5b7b7`  
**Evidence status:** locked analyses only; no new scientific inference introduced by synchronization.  
**Date:** 2026-08-28

*Author list and affiliations: to be finalized by the authors*

## Summary

Language models are usually compared with neural data after training, but whether neural representational structure can itself provide a transferable learning constraint is unknown. We derived a reproducible relational geometry from human electroencephalography during natural reading and used it as an auxiliary target for language-model representations. Neural-guided training produced a small but reproducible change in model geometry that generalized beyond the neural data used for training. The frozen neural-guided model improved alignment to independent English-reading EEG and, prospectively, to language-network functional magnetic resonance imaging measured in different participants during naturalistic auditory comprehension. The model advantage was positive in all participants in both of these external validations. Transfer was not universal: other reading and inner-speech datasets produced null or inconclusive effects, and a prospectively specified sensor-level magnetoencephalography target failed its model-blind reliability prerequisite before model evaluation. Thus, human neural geometry can provide a portable relational constraint on language representations, but its detectable expression depends on the neural and task context and on whether the target neural geometry is itself reproducible.

## Main text

Artificial language representations are commonly evaluated by asking how closely they resemble human neural activity. This treats the brain as an external benchmark. A stronger directional test is whether relational structure extracted from neural data can shape model learning and whether the resulting change remains detectable in independent brains that were never used to define or tune the model.

Such a test requires two safeguards. First, the neural target must itself be reproducible across people rather than dominated by participant- or acquisition-specific variation. Second, model and analysis choices must be insulated from target-dataset outcomes. We therefore organized NeuroSem as a sequence of increasingly independent tests: identify reproducible neural relational geometry during natural reading, establish residual correspondence with language-model geometry, train models with an auxiliary neural relational objective, and then carry a frozen model contrast into independent neural datasets without target-dataset tuning.

This sequence revealed selective but transferable neural guidance. A model change learned from Chinese reading EEG generalized to independent English-reading EEG and, in the strongest prospective test, to language-network fMRI during naturalistic auditory comprehension in different participants. Other datasets defined genuine transfer boundaries, whereas SMN4Lang MEG defined a separate reliability boundary at which model evaluation was not permitted. Together, these results support a transferable neural representational constraint rather than a general improvement in language-model quality.

### Reproducible neural geometry can serve as a learning target

We first analyzed ChineseEEG Little Prince natural reading<sup>1</sup> and selected the primary EEG representation using neural reliability rather than semantic-model performance. The whole-row temporal-mean representation showed raw leave-one-participant-out (LOO) reliability of approximately 0.220 and retained residual LOO reliability of approximately 0.121 after nuisance adjustment (Fig. 1a,b). Thus, the pairwise relations among linguistic items contained a cross-participant neural geometry suitable for model testing.

Final-layer Chinese BERT representations<sup>2</sup> showed small but consistently positive residual correspondence with this neural geometry across six held-out narrative runs. Mean partial-Spearman values were 0.0057, 0.0034, 0.0145, 0.0045, 0.0174 and 0.0056 for runs 01–06, respectively. All six effects were positive; the mean was 0.0085 and the exact one-sided run-level sign-flip probability was 0.015625 (Fig. 1c). The absolute correspondence was modest, but its consistency established overlap between language-model and reproducible neural relational structure beyond the frozen nuisance family.

We next asked whether the neural geometry could act as a learning signal. In the sealed ChineseEEG run-07 evaluation, neural-guided BERT exceeded matched text-only and shuffled-neural controls in both seeds. Residual neural alignment was 0.0371 and 0.0375 for neural-guided training, compared with 0.0354 and 0.0341 for text-only training, 0.0353 and 0.0338 for shuffled-neural training, and 0.0319 for the base model in both seeds (Fig. 1d). Multilingual E5<sup>3</sup> reproduced the qualitative neural-guided alignment effect and was then used for the external transfer program.

The neural objective did not yield a stable neural-specific advantage on a conventional eight-task semantic benchmark. Neural-guided and text-only models were nearly indistinguishable in one seed, whereas neural-guided performance was lower in the other (Fig. 1e). Neural alignment and generic semantic benchmark performance are therefore distinct outcomes.

### The learned constraint transfers across dataset and language

We next tested the frozen multilingual-E5 contrast in ZuCo 2.0 Task 1 Normal Reading<sup>4</sup>, an independent English-reading EEG dataset. The external comparison was fixed as neural-guided λ=0.10 versus matched text-only λ=0, with no ZuCo outcome used to retune the model contrast (Fig. 2a).

The prospectively defined all-retained-channel temporal-mean EEG representation was reproducible across all 17 participants. Mean residual LOO reliability was 0.06742, median 0.06559, and the participant-bootstrap 95% confidence interval was 0.05831 to 0.07687. All 17 participants had positive reliability; the exact one-sided sign-flip probability was 7.63 × 10⁻⁶ (Fig. 2b).

Against this independently measured geometry, the neural-guided model showed a mean participant RSA increment of 0.0016637 relative to text-only, with median 0.0014871 and bootstrap 95% confidence interval 0.0012294 to 0.0021452. The increment was positive in all 17 participants, with exact one-sided sign-flip probability 7.63 × 10⁻⁶ (Fig. 2c,d). A relational constraint learned from Chinese natural-reading EEG therefore remained detectable in independent English-reading EEG without target-dataset model tuning.

### The learned constraint transfers prospectively across measurement modality

We then tested whether the same already-trained model change generalized beyond EEG. SMN4Lang<sup>5</sup> comprised 12 Mandarin-speaking participants who listened to 60 naturalistic spoken Chinese stories during fMRI. This dataset was designated prospectively for cross-modal validation, and its neural target had to pass a model-blind reliability gate before any E5 representation could be evaluated (Fig. 3a).

The primary target used the independently published LanA language-network atlas<sup>6</sup> thresholded at probability 0.20, retaining 25,137 voxels. Story-level multivoxel patterns were converted to correlation-distance RDMs after adjustment for temporal separation, haemodynamic-response-convolved word-onset density and haemodynamic-response-convolved acoustic RMS envelope. Mean residual LOO reliability was 0.65327, median 0.64760, and all 12 participants were positive. The participant-bootstrap 95% confidence interval was 0.63945 to 0.66843, with exact one-sided sign-flip probability 0.00024414 (Fig. 3b). The target therefore passed the prespecified reliability gate before model loading.

Frozen E5 representations were then mapped causally into the fMRI timebase using within-sentence prefix states at released word onsets and the same fixed canonical haemodynamic response (Fig. 3c). No SMN4Lang model training, participant selection, lambda selection, layer selection, checkpoint selection, ROI search, lag search, haemodynamic-response search or semantic-unit search was performed from the fMRI outcome.

Mean participant residual RSA was 0.12092396 for text-only λ=0 and 0.12177646 for neural-guided λ=0.10. The mean participant increment was 0.00085250, median 0.00086365, with bootstrap 95% confidence interval 0.00078966 to 0.00091398. The increment was positive in all 12 participants, with exact one-sided sign-flip probability 0.00024414 (Fig. 3d,e).

The fMRI effect is small in absolute RSA units and should not be interpreted as a large increase in explained neural variance. Its importance lies in the prospective design and convergence of independent constraints: a model intervention learned from reading EEG was carried without SMN4Lang tuning into different participants, a different task context and a different measurement modality, where every participant shifted in the same direction.

### Transfer is selective rather than universal

The positive ZuCo and SMN4Lang results did not extend uniformly across neural datasets (Fig. 4a). In TMNRED<sup>7</sup>, the prospectively frozen temporal-mean EEG representation was weakly but positively reproducible, with mean residual LOO reliability 0.00724 and 95% confidence interval 0.00356 to 0.01079. Yet the frozen E5 neural-guided minus text-only contrast was null: mean participant delta 0.000020, median 0.000053, 95% confidence interval −0.000128 to 0.000176, and one-sided sign-flip probability 0.402. Bounded exploratory alternative EEG summaries did not recover convincing transfer.

ChineseEEG Garnett Dream provided a complementary within-acquisition boundary. The frozen EEG geometry generalized to the new narrative, with residual mean LOO reliability 0.01863, 95% confidence interval 0.01636 to 0.02085, and all 10 participants positive. The corresponding frozen E5 transfer effect was nevertheless inconclusive: mean delta 0.0003266, 95% confidence interval −0.0001218 to 0.0007560, six of ten participants positive, and exact one-sided sign-flip probability 0.1015625.

A directional-word inner-speech dataset<sup>8</sup> provided an out-of-task boundary, with an approximately −0.001786 neural-guided minus text-only contrast and no evidence of positive transfer. Because this task differs substantially from natural reading, it is not a task-matched refutation of the reading results.

These external tests separate two questions that are often conflated: whether neural geometry is reproducible and whether a learned neural-guided model advantage transfers to that geometry. ZuCo supported both, TMNRED and Garnett supported the former but not convincingly the latter, and directional inner speech provided a stronger task-shift boundary. Neural guidance therefore does not create a universally superior language representation.

### A prospectively defined MEG target failed the reliability prerequisite for model testing

SMN4Lang also provided MEG from the same 12 participants and 60 stories. Before model evaluation, we prospectively froze a sensor-level representation using released preprocessed 1–40 Hz data. After excluding samples covered by bad annotations, valid samples were divided into 32 equal normalized-time bins. Root-mean-square field magnitude was summarized separately across retained magnetometers and planar gradiometers, standardized within sensor type across bins, concatenated and converted into story-by-story correlation-distance RDMs.

This representation did not yield sufficiently reproducible cross-participant story geometry. Mean LOO reliability was 0.007713, median 0.011320, with seven of 12 participants positive. The participant-bootstrap 95% confidence interval was −0.007627 to 0.021655 and the exact one-sided sign-flip probability was 0.16870 (Fig. 4b). The representation therefore failed the prespecified model-blind reliability gate, and no E5 alignment analysis was performed.

We then conducted one bounded post-confirmatory model-blind analysis to determine whether simple temporal coarsening could account for the failure. Before observing alternative outcomes, we froze otherwise identical representations using 4, 8 and 16 normalized-time bins. Mean LOO reliability was 0.01534, 0.00548 and 0.00817, respectively; all ordinary 95% confidence intervals crossed zero and none passed the familywise reliability criterion. No exploratory model evaluation was opened.

The MEG result is therefore a reliability boundary, not a negative model-transfer result. Within this sensor-level RMS representation family, neither the prospectively frozen 32-bin target nor the bounded 4/8/16-bin alternatives yielded a sufficiently reproducible cross-participant geometry to support model testing. This does not imply that MEG cannot contain transferable language-related geometry under other prospectively specified representations.

### Neural alignment is distinct from generic semantic quality

Across datasets, the strongest external model effects occurred in ZuCo natural reading and SMN4Lang auditory narratives, but transfer was null or inconclusive elsewhere and generic semantic benchmarks showed no stable neural-specific advantage (Fig. 4c,d). Raw RSA magnitudes are not directly comparable across EEG and fMRI because the neural representations and measurement scales differ.

The combined pattern supports a relational interpretation. Neural-guided training introduces a small change in model geometry that is not reducible to general semantic benchmark improvement, but can remain detectable in independent neural representational spaces. Cross-language EEG and cross-modal fMRI establish portability; the null transfer datasets and the MEG reliability failure define its empirical limits.

## Discussion

This study reverses the usual direction of neural-model comparison. Rather than asking only whether a pretrained model resembles the brain, we asked whether reliable neural relational structure can constrain model learning in a way that remains detectable in independent brains. A target derived from Chinese natural-reading EEG altered language-model geometry, the resulting neural-guided representation improved alignment to independent English-reading EEG in all 17 ZuCo participants, and the same frozen model prospectively improved alignment to language-network fMRI in all 12 SMN4Lang participants during naturalistic auditory comprehension.

The appropriate conclusion is not that brain supervision generally improves language models or that one universal neural semantic geometry has been identified. Human neural geometry can instead act as a transferable relational constraint on language representations. The intervention showed no stable neural-specific advantage on generic semantic benchmarks, and transfer was null or inconclusive in TMNRED, Garnett Dream and directional inner speech. Moreover, the SMN4Lang MEG branch stopped before model evaluation because the prospectively frozen target did not pass its reliability prerequisite. Target reliability, model learnability and external transfer are therefore distinct empirical stages.

The prospective fMRI result provides the strongest evidence because it crosses participants, task context and measurement modality without target-dataset model optimization. Its absolute effect is small, so the claim does not rest on effect size alone. More informative is the combination of a model-blind reliability gate, an independently defined language-network mask, frozen mapping choices, absence of outcome-driven model search, and a positive participant-level direction in all 12 individuals. Under these constraints, the result shows that a model intervention learned from EEG altered relational structure in a direction that remained detectable in independently measured cortical language responses.

The selectivity of transfer also constrains the construct itself. Naturalistic EEG and fMRI reflect correlated lexical, syntactic, discourse, temporal, acoustic and attentional structure; the transferable target should therefore not be equated with pure lexical or semantic coding. We use the broader terms **neural relational geometry** and **language-related neural geometry** to reflect this uncertainty. Future mechanistic work will need experimental designs that dissociate these dimensions rather than infer semantic specificity from naturalistic alignment alone.

Several limitations follow directly from the evidence. Transfer effects are small in absolute RSA units and should be interpreted as representational shifts rather than large gains in neural prediction. External datasets differ in language, acquisition, preprocessing and inferential scale, strengthening independence while preventing simple pooling or direct comparison of raw effects. Positive transfer is accompanied by genuine nulls, demonstrating that the learned constraint is not universally expressed. The MEG conclusion is representation-specific and does not exclude prospectively motivated source-resolved, event-aligned or spectrotemporal alternatives in future work. Finally, secondary transcriptomic analyses do not establish a specific molecular mechanism and should not be used to strengthen the primary representational claim.

The broader methodological implication is that neural supervision should be evaluated as a gated process. A neural geometry must first be shown to be reproducible; a model must then learn a change toward that geometry; and only then can that change be tested in independent neural contexts. The present results show that these stages can align across independent brains, languages and measurement modalities, while also demonstrating that they need not align universally.

## Methods

### Study logic and inferential hierarchy

Analyses were organized as development, sealed validation and prospectively frozen external tests. Neural representations were evaluated for cross-participant reproducibility before external model testing whenever the protocol specified a reliability gate. Model contrasts, target representations and inferential units were carried forward without target-outcome-driven retuning. Post-confirmatory analyses were explicitly labelled and did not revise the status of primary tests.

### ChineseEEG development target

ChineseEEG Little Prince natural-reading EEG<sup>1</sup> was used to establish the development neural geometry. The primary whole-row temporal-mean representation was selected using neural reliability before semantic-model testing. Pairwise distances among linguistic items defined participant-specific representational dissimilarity matrices. Nuisance-adjusted cross-participant reliability was assessed by comparing each participant with the mean geometry of the remaining participants. Residual neural-model correspondence was evaluated across held-out narrative runs using partial Spearman association under the frozen nuisance adjustment.

### Neural-guided model training

Language-model representations were trained with an auxiliary relational objective encouraging model pairwise geometry to align with the reproducible EEG target while retaining the matched text-learning objective. BERT<sup>2</sup> development experiments included text-only and shuffled-neural controls and were evaluated on sealed ChineseEEG run 07. Multilingual E5<sup>3</sup> was then used for the external transfer program. The primary external model contrast was fixed as neural-guided λ=0.10 versus matched text-only λ=0.

### ZuCo EEG validation

ZuCo 2.0 Task 1 Normal Reading<sup>4</sup> served as the independent English-reading EEG validation. The frozen primary representation was the all-retained-channel temporal mean. Cross-participant neural reliability was evaluated before model-transfer interpretation. The participant was the inferential unit. Transfer was summarized by participant-level RSA differences, participant-bootstrap confidence intervals and exact sign-flip inference.

### SMN4Lang fMRI validation

SMN4Lang/OpenNeuro ds004078<sup>5</sup> served as the prospective cross-modal validation. The primary fMRI target used the independently published LanA language-network mask<sup>6</sup> thresholded at probability 0.20. Story-level multivoxel patterns were converted to correlation-distance RDMs after nuisance adjustment for temporal separation, haemodynamic-response-convolved word-onset density and haemodynamic-response-convolved acoustic RMS envelope. A model-blind cross-participant reliability gate was completed before model loading.

For model evaluation, E5 representations were generated causally within sentence using prefix states at released word onsets, mapped into the fMRI timebase with the fixed canonical haemodynamic response, and residualized using the same nuisance family. The only primary model comparison was λ=0.10 versus λ=0. No SMN4Lang model training, layer search, checkpoint search, ROI search, lag search, haemodynamic-response search or semantic-unit search was performed from the fMRI outcome.

### Boundary datasets

TMNRED<sup>7</sup>, ChineseEEG Garnett Dream and the directional-word inner-speech dataset<sup>8</sup> were analyzed under their frozen external protocols. TMNRED and Garnett first established whether the designated neural geometry was reproducible and then evaluated the same fixed E5 contrast. Directional inner speech was treated as an out-of-task boundary rather than a task-matched reading replication.

### SMN4Lang MEG reliability gate

The prospective SMN4Lang MEG analysis used released preprocessed 1–40 Hz sensor-level data from the same 12 participants and 60 stories. Samples covered by annotations beginning with “bad” were excluded. Remaining valid samples were concatenated in temporal order and divided into 32 equal normalized-time bins. Within each bin, one RMS field-magnitude value was calculated across retained magnetometer samples and one across retained planar-gradiometer samples. The 32 magnetometer and 32 gradiometer values were separately standardized across bins and concatenated into a 64-dimensional run vector. Participant-specific 60 × 60 story RDMs were constructed using correlation distance.

Cross-participant reliability was the Spearman correlation between each participant’s upper-triangular RDM edges and the edgewise mean RDM of the other 11 participants. The primary gate required positive mean reliability, a participant-bootstrap 95% confidence interval entirely above zero and an exact one-sided sign-flip probability below 0.05. The gate failed, so no confirmatory model evaluation was performed.

A post-confirmatory model-blind temporal-granularity family was then frozen before alternative outcomes. The only candidate representations used 4, 8 and 16 bins, with all other representation choices unchanged. Familywise reliability was controlled across the three candidates using a Bonferroni-adjusted one-sided alpha of 0.0166667 and a 98.3333% participant-bootstrap confidence interval. No candidate passed, and no exploratory E5 model evaluation was opened.

### Representational analysis and statistical inference

Representational dissimilarity matrices and cross-representation comparisons followed the general RSA framework<sup>9</sup>. Participant-level effects were the primary inferential unit for external neural validation. Confidence intervals were obtained by participant bootstrap according to each frozen protocol. Exact sign-flip tests enumerated all sign assignments where feasible. Raw effect magnitudes were not pooled across EEG, fMRI and MEG because the representational constructions and measurement scales differ.

### Transcriptomic analyses

AHBA analyses were secondary mechanistic extensions rather than part of the primary transfer claim. The Allen Human Brain Atlas<sup>10</sup> was processed with a frozen imaging-transcriptomics workflow using abagen<sup>11</sup>. Prespecified GABAergic, serotonergic and pathway gene-set tests were null under the frozen participant-level and multiplicity-corrected framework. Exploratory whole-transcriptome and hemispheric sensitivity analyses did not revise those primary nulls. Full molecular methods and provenance should remain in Extended Data or Supplementary Information.

## Figures

The composite main-figure artwork is still being assembled. The two current locked rendered panels available from the latest RunRelay figure build are inserted below. Missing composite panels are intentionally marked rather than reconstructed from summary statistics.

> *Figure 1 composite artwork pending: conceptual schematic, ChineseEEG reliability/correspondence, sealed BERT comparison and E5 benchmark dissociation.*

*Current locked reliability overview | Cross-dataset reading-related neural geometry. This panel summarizes participant-level reliability across the locked reading datasets and is retained here as supporting artwork, not as the final Figure 2 composite. The final Figure 2 will contain the ChineseEEG-to-ZuCo validation schematic, ZuCo reliability and paired λ=0 versus λ=0.10 transfer panels.*

> *Figure 3 composite artwork pending: SMN4Lang design/LanA mask, model-blind reliability gate, causal E5-to-fMRI mapping and paired 12-participant transfer display.*

*Figure 4b | SMN4Lang MEG reliability boundary. The prospectively frozen 32-bin sensor-level RMS representation failed the model-blind cross-participant reliability gate. The separately frozen post-confirmatory 4/8/16-bin temporal-granularity family also failed its familywise reliability criteria. No E5 model evaluation was performed for any MEG representation. The final Figure 4 composite will add the external-outcome map, independence/design matrix and generic semantic-benchmark panel.*

## Full figure legends

*Figure 1 | From reproducible neural geometry to a learnable relational constraint. a, Conceptual framework in which linguistic items define a human EEG relational geometry that is used as an auxiliary neural objective during language-model training. b, ChineseEEG Little Prince natural-reading design and reliability-led selection of the whole-row temporal-mean EEG representation. c, Residual neural-model correspondence across held-out Little Prince development runs 01–06; all six run-level effects were positive. d, Sealed run-07 BERT comparison across base, text-only, neural-guided and shuffled-neural conditions in two seeds. e, Multilingual-E5 replication of the neural-guided alignment effect together with the absence of a stable neural-specific gain on the frozen generic semantic benchmark. Development and sealed analyses are shown separately from later external validations.*

*Figure 2 | Cross-language EEG generalization. a, Frozen ChineseEEG-to-ZuCo external validation design. b, Participant-level LOO reliability of the prospectively defined ZuCo 2.0 Task 1 Normal Reading temporal-mean EEG geometry; mean residual reliability 0.06742, 95% participant-bootstrap confidence interval 0.05831–0.07687, 17/17 participants positive. c, Paired participant RSA values for matched text-only λ=0 and neural-guided λ=0.10 multilingual-E5 representations. d, Participant-level neural-guided minus text-only RSA differences; mean +0.0016637, 95% confidence interval +0.0012294 to +0.0021452, 17/17 positive, exact one-sided sign-flip P = 7.63 × 10⁻⁶. Participants are the inferential unit; no ZuCo outcome was used for model retuning.*

*Figure 3 | Prospective cross-modal transfer to language-network fMRI. a, SMN4Lang design: 12 Mandarin-speaking participants, 60 naturalistic spoken stories and an independently defined LanA language-network mask. b, Model-blind participant-level reliability gate for the fMRI story geometry; mean residual LOO reliability 0.65327, 95% confidence interval 0.63945–0.66843, 12/12 participants positive. c, Frozen causal mapping from within-sentence E5 prefix states at released word onsets into the fMRI timebase using the fixed canonical haemodynamic response. d, Paired participant residual RSA for text-only λ=0 and neural-guided λ=0.10. e, Participant-level neural-guided minus text-only differences; mean +0.00085250, 95% confidence interval +0.00078966 to +0.00091398, 12/12 positive, exact one-sided sign-flip P = 0.00024414. Participants are the inferential unit. No SMN4Lang outcome was used for model, layer, checkpoint, ROI, lag, haemodynamic-response or semantic-unit selection.*

*Figure 4 | Generalization map and boundary conditions. a, External transfer outcomes for ZuCo, SMN4Lang fMRI, TMNRED, ChineseEEG Garnett Dream and directional inner speech. Dataset-specific inferential units and scales are preserved; raw RSA differences should not be compared as a common effect-size scale. b, SMN4Lang MEG reliability boundary. The prospectively frozen 32-bin sensor-level RMS representation failed the model-blind cross-participant reliability gate. The separately frozen post-confirmatory 4/8/16-bin temporal-granularity family also failed its familywise reliability criteria. No E5 model evaluation was performed for any MEG representation. c, Independence/design matrix summarizing participant overlap, language, text, task, modality, target-dataset tuning and whether a reliability gate permitted model evaluation. d, Frozen generic semantic benchmark and conceptual summary: neural guidance produces a portable but selective relational constraint rather than a universal improvement in language-model quality.*

## References

1. Mou, X. *et al.* ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding. *Scientific Data* **11**, 550 (2024).

2. Devlin, J., Chang, M.-W., Lee, K. & Toutanova, K. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. in *Proceedings of NAACL-HLT* 4171–4186 (Association for Computational Linguistics, 2019). doi:10.18653/v1/N19-1423.

3. Wang, L. *et al.* *Multilingual E5 Text Embeddings: A Technical Report*. https://arxiv.org/abs/2402.05672 (2024).

4. Hollenstein, N., Troendle, M., Zhang, C. & Langer, N. ZuCo 2.0: A Dataset of Physiological Recordings During Natural Reading and Annotation. in *Proceedings of the Twelfth Language Resources and Evaluation Conference* 138–146 (European Language Resources Association, 2020).

5. Wang, S., Zhang, X., Zhang, J. & Zong, C. A synchronized multimodal neuroimaging dataset for studying brain language processing. *Scientific Data* **9**, 590 (2022).

6. Lipkin, B. *et al.* Probabilistic atlas for the language network based on precision fMRI data from >800 individuals. *Scientific Data* **9**, 529 (2022).

7. Bai, Y. *et al.* TMNRED, A Chinese Language EEG Dataset for Fuzzy Semantic Target Identification in Natural Reading Environments. *Scientific Data* **12**, 701 (2025).

8. Kostulin, D. V. *et al.* EEG-based brain-computer interface (BCI) dataset for directional word recognition. *Scientific Data* **13**, 1195 (2026).

9. Kriegeskorte, N., Mur, M. & Bandettini, P. Representational similarity analysis – connecting the branches of systems neuroscience. *Frontiers in Systems Neuroscience* **2**, 4 (2008).

10. Hawrylycz, M. J., Lein, E. S. & Guillozet-Bongaarts, A. L. An anatomically comprehensive atlas of the adult human brain transcriptome. *Nature* **489**, 391–399 (2012).

11. Markello, R. D. *et al.* Standardizing workflows in imaging transcriptomics with the abagen toolbox. *eLife* **10**, e72129 (2021).

## Submission notes

This is a submission-style working manuscript, not a final Nature upload package. The reference metadata above has been audited against authoritative sources. The current Word file contains real Zotero-compatible citation fields and a Zotero bibliography field. Final author list, affiliations, ethics statements and complete composite Figures 1, 3 and 4a/c/d remain to be supplied before submission.
