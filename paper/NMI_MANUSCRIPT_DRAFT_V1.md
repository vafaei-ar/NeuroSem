# Human neural geometry provides a transferable constraint on language representations

**Nature Machine Intelligence working manuscript, NMI draft v1**  
**Evidence status:** primary analyses locked; bidirectional, dose-response and model-family analyses explicitly post-confirmatory.  
**Figure status:** main Figures 1-4 frozen from the v3.4 publication figure system.  
**Assembly date:** 2026-08-30

*Author list, affiliations, author contributions, funding and corresponding-author information remain to be finalized by the authors.*

## Abstract

Language models are usually compared with neural data after training, leaving open whether neural representational structure can itself provide a learning constraint that generalizes beyond the brain data used for optimization. We derived a reproducible relational geometry from human electroencephalography (EEG) during natural reading and used it as an auxiliary target for language-model representations. Neural-guided learning produced a small perturbation of model geometry that generalized to independent neural measurements. A frozen multilingual-E5 contrast improved alignment to independent English-reading EEG in all 17 ZuCo participants and, prospectively, to language-network functional magnetic resonance imaging (fMRI) in all 12 SMN4Lang participants during Mandarin auditory narratives. A separately frozen post-confirmatory analysis reversed the source modality: an fMRI-derived relational constraint transferred to independent ZuCo EEG, with a graded response across already-trained neural-loss weights. Under a common six-model, three-seed protocol, bidirectional external transfer reproduced across multilingual E5-large and E5-base but not uniformly across MPNet, MiniLM, XLM-R or multilingual BERT. Transfer was also null or inconclusive in several neural boundary datasets, and a prospectively specified SMN4Lang MEG representation failed its model-blind reliability gate before model evaluation. These results show that human neural geometry can provide a portable relational constraint on language representations, while also demonstrating that portability depends on neural context, direction and model family.

## Main text

Artificial language representations are commonly evaluated by asking how closely a trained model resembles human neural activity. This treats the brain as an external benchmark. A stronger intervention test asks whether reproducible relational structure extracted from neural data can shape model learning and whether the resulting representational change remains detectable in independent brains that did not participate in model optimization or selection.

This distinction matters because improved fit to the training brain is not sufficient evidence that biological supervision has induced a biologically portable representation. A model can overfit participant-specific, acquisition-specific or stimulus-specific structure. Conversely, a small learned perturbation may be scientifically informative if it transfers under frozen analysis choices across different people, languages, tasks or measurement modalities. We therefore organized NeuroSem as a gated sequence: establish reproducible neural relational geometry, show that model geometry can learn toward that target, freeze the induced model contrast, and test whether the contrast transfers to independent neural systems.

The primary evidence chain moves from Chinese natural-reading EEG to independent English-reading EEG and then prospectively to Mandarin language-network fMRI. Later analyses were deliberately separated from this primary chain. They ask whether transfer can also occur in the reverse source-modality direction and whether such bidirectional portability generalizes across optimization seeds and model families. This separation preserves the evidential hierarchy: the original external tests remain the confirmatory core, whereas reverse transfer, dose-response and architecture analyses are explanatory post-confirmatory evidence.

### Reproducible neural geometry can serve as a learning target

We first analyzed ChineseEEG Little Prince natural-reading EEG and selected the primary representation using neural reliability rather than semantic-model performance. The whole-row temporal-mean representation showed raw leave-one-participant-out (LOO) reliability of approximately 0.220 and retained nuisance-residualized LOO reliability of approximately 0.121 (Fig. 1a,b). Thus, pairwise relations among linguistic items contained reproducible cross-participant neural structure suitable for model testing.

Final-layer Chinese BERT representations showed small but consistently positive residual correspondence with this neural geometry across six held-out narrative runs. Run-level partial-Spearman values were 0.0057, 0.0034, 0.0145, 0.0045, 0.0174 and 0.0056. All six were positive, with mean 0.0085 and exact one-sided run-level sign-flip P = 0.015625 (Fig. 1c). The absolute correspondence was modest, but its consistency established overlap between language-model geometry and reproducible neural relational structure beyond the frozen nuisance family.

We next asked whether the neural geometry could act as a learning signal. In sealed ChineseEEG run-07 evaluation, neural-guided BERT exceeded matched text-only and shuffled-neural controls in both development seeds. Residual neural alignment was 0.0371 and 0.0375 for neural-guided training, compared with 0.0354 and 0.0341 for text-only training, 0.0353 and 0.0338 for shuffled-neural training, and 0.0319 for the base model in both seeds (Fig. 1d). Multilingual E5 reproduced the qualitative neural-guided alignment effect and became the model used for the frozen external-transfer program.

The intervention should not be interpreted as general downstream improvement. The neural objective did not produce a stable neural-specific advantage on the frozen conventional semantic benchmark: neural-guided and text-only models were nearly indistinguishable in one seed, whereas neural-guided performance was lower in another. Neural alignment and conventional semantic-task quality are therefore distinct outcomes.

### The learned constraint transfers across dataset and language

We next evaluated the frozen multilingual-E5 contrast in ZuCo 2.0 Task 1 Normal Reading, an independent English-reading EEG dataset. The external comparison was neural-guided lambda = 0.10 versus matched text-only lambda = 0, with no ZuCo outcome used to retune the model contrast (Fig. 2a).

The prospectively defined all-retained-channel temporal-mean EEG representation was reproducible across all 17 participants. Mean residual LOO reliability was 0.06742, with 95% participant-bootstrap confidence interval 0.05831 to 0.07687. All 17 participants had positive reliability, and the exact one-sided sign-flip probability was 7.63 x 10^-6 (Fig. 2b).

Against this independently measured geometry, the neural-guided model showed a mean participant RSA increment of +0.0016637 relative to text-only, with median +0.0014871 and bootstrap 95% confidence interval +0.0012294 to +0.0021452. The increment was positive in all 17 participants, with exact one-sided sign-flip P = 7.63 x 10^-6 (Fig. 2c,d). A relational constraint learned from Chinese natural-reading EEG therefore remained detectable in independent English-reading EEG without target-dataset model tuning.

### The learned constraint transfers prospectively across measurement modality

We then tested whether the same already-trained model change generalized beyond EEG. SMN4Lang comprised 12 Mandarin-speaking participants who listened to 60 naturalistic spoken Chinese stories during fMRI. This dataset was designated prospectively for cross-modal validation, and its neural target had to pass a model-blind reliability gate before any E5 representation could be evaluated (Fig. 3a).

The primary target used the independently published LanA language-network atlas thresholded at probability 0.20, retaining 25,137 voxels. Story-level multivoxel patterns were converted to correlation-distance representational dissimilarity matrices after adjustment for temporal separation, haemodynamic-response-convolved word-onset density and haemodynamic-response-convolved acoustic RMS envelope. Mean residual LOO reliability was 0.65327, with all 12 participants positive and bootstrap 95% confidence interval 0.63945 to 0.66843. The exact one-sided sign-flip probability was 0.00024414 (Fig. 3b). The target therefore passed the prespecified reliability gate before model loading.

Frozen E5 representations were then mapped causally into the fMRI timebase using within-sentence prefix states at released word onsets and the same fixed canonical haemodynamic response. No SMN4Lang model training, participant selection, lambda selection, layer selection, checkpoint selection, ROI search, lag search, haemodynamic-response search or semantic-unit search was performed from the fMRI outcome.

Mean participant residual RSA was 0.12092396 for text-only lambda = 0 and 0.12177646 for neural-guided lambda = 0.10. The mean participant increment was +0.00085250, median +0.00086365, with bootstrap 95% confidence interval +0.00078966 to +0.00091398. The increment was positive in all 12 participants, with exact one-sided sign-flip P = 0.00024414 (Fig. 3c,d).

The fMRI effect is small in absolute RSA units, approximately 0.7% of the text-only mean RSA, and should not be interpreted as a large increase in explained neural variance. Its evidential value lies in the prospective design and convergence of independent constraints: a model intervention learned from reading EEG was carried without SMN4Lang outcome-driven tuning into different participants, a different task context and a different measurement modality, where every participant shifted in the same direction.

### Reverse transfer and model-family tests define the scope of portability

The primary chain establishes transfer from an EEG-derived source constraint to independent EEG and fMRI targets. We next asked, post-confirmatorily, whether portability could also be observed when the source modality was reversed. A source-only SMN4Lang fMRI calibration used the fixed multilingual-E5 lambda grid {0, 0.01, 0.03, 0.10, 0.30, 1.0}. The prespecified one-standard-error rule selected the smallest positive lambda within one standard error of the best source-validation mean, yielding lambda = 0.01 before external EEG was read.

The frozen fMRI-guided lambda = 0.01 model showed positive transfer to independent ZuCo EEG. Mean participant delta RSA was +0.00001671, median approximately +0.00002095, with 14/17 participants positive and bootstrap 95% confidence interval approximately +0.00001108 to +0.00002200. Exact one-sided sign-flip P was 0.0001068. This result establishes post-confirmatory source-modality bidirectionality within multilingual E5: an EEG-derived intervention transferred to fMRI in the primary chain, and an independently trained fMRI-derived intervention transferred back to EEG.

Because all other fMRI-guided E5 lambda arms had already been trained, we then characterized their external ZuCo behavior without adding new doses or selecting a new confirmatory optimum. Transfer increased with neural-loss weight: mean ZuCo delta RSA was +0.0000167 at lambda = 0.01, +0.0000557 at 0.03, +0.0002016 at 0.10, +0.0006163 at 0.30 and +0.0017453 at 1.0 (Fig. 4a). Participant-level ordered slopes were positive in 16/17 participants, with mean slope approximately +0.000807, bootstrap 95% confidence interval +0.000617 to +0.000993 and exact one-sided P = 1.53 x 10^-5. This dose-response is a post-confirmatory characterization and does not replace lambda = 0.01 as the source-selected reverse-transfer candidate.

A secondary ChineseEEG run-07 analysis was directionally concordant at lambda = 0.01 but inconclusive. In a separate three-seed post-confirmatory robustness experiment, lower and intermediate fMRI-guidance weights were heterogeneous across optimization trajectories. Only lambda = 1.0 produced a positive seed-level mean in all three added seeds, with seed means +7.7478 x 10^-5, +6.2966 x 10^-5 and +5.4571 x 10^-5. Participant-level intervals crossed zero in each 10-participant seed evaluation. ChineseEEG therefore provides suggestive high-dose consistency rather than a separately established reverse dose-response.

We then evaluated whether bidirectional portability was specific to one E5 checkpoint or generalized across multilingual encoder families. A frozen common-protocol panel tested six models, three optimization seeds and two source directions, completing all 36 planned model x seed x direction units with no omitted outcomes (Fig. 4b-d). The shared adaptation used final hidden-state mean pooling, L2 normalization, cosine relational geometry, LoRA on attention query/value projections, a symmetric dropout-view InfoNCE text objective, fixed neural weight lambda = 0.10 and five source-training epochs. No model-specific lambda, layer, pooling or checkpoint rescue was allowed.

For ChineseEEG-derived constraints evaluated on SMN4Lang fMRI, transfer was relatively broad. Mean seed-level external deltas were +0.00111179 for E5-large, +0.00027136 for E5-base, +0.00119328 for multilingual MPNet, +0.00064239 for multilingual MiniLM, +0.00052302 for XLM-R and +0.00024877 for mBERT. E5-large, E5-base, MPNet, MiniLM and mBERT had positive seed-level means in all three seeds, whereas XLM-R was heterogeneous.

The reverse fMRI-to-ZuCo direction was more selective. E5-large showed mean seed-level delta +0.00020314 and E5-base +0.00003368, with all three seeds positive for both models. In contrast, multilingual MPNet was approximately centered on zero (mean -0.00000122), MiniLM was negative in all three seeds (mean -0.00003740), XLM-R was seed-heterogeneous (mean +0.00003108) and mBERT was negative in all three seeds (mean -0.00044102). Thus, the panel does not support a simple sentence-embedding versus masked-language-model dichotomy. EEG-derived constraints can transfer across several multilingual encoders, but stable reverse fMRI-to-EEG transfer was reproduced only in the two tested E5 variants under the common protocol.

This model-family result is explanatory, not prospective confirmation of an architecture effect. It does not establish that E5 is uniquely capable among all language models, nor that non-E5 models could never transfer after model-specific optimization. It does show that the bidirectional result is not an idiosyncrasy of a single E5 checkpoint or one optimization trajectory, and that biological transfer cannot be assumed to be architecture-invariant.

### Transfer remains selective across neural contexts

The positive primary transfer and post-confirmatory bidirectionality do not imply universal biological transfer. TMNRED had weak but positive residual neural reliability (mean 0.00724, 95% confidence interval 0.00356 to 0.01079), yet the frozen E5 neural-guided minus text-only transfer contrast was null: mean participant delta +0.000020, 95% confidence interval -0.000128 to +0.000176 and one-sided P = 0.402.

ChineseEEG Garnett Dream provided a complementary same-acquisition/new-text boundary. Neural geometry remained reproducible, with residual mean LOO reliability 0.01863 and 10/10 positive participants, but the frozen E5 transfer effect was inconclusive: mean delta +0.0003266, bootstrap 95% confidence interval -0.0001218 to +0.0007560, six of ten participants positive and exact one-sided P = 0.1016. A directional-word inner-speech dataset provided a stronger task-shift boundary, with an approximately -0.001786 neural-guided minus text-only contrast and no evidence of positive transfer.

SMN4Lang MEG defines a different type of boundary. A prospectively frozen sensor-level representation yielded mean LOO reliability 0.007713, median 0.011320, seven of 12 participants positive, bootstrap 95% confidence interval -0.007627 to +0.021655 and exact one-sided P = 0.16870. Because the model-blind reliability gate failed, no E5 alignment analysis was performed. A separately frozen 4/8/16-bin temporal-granularity family also failed its familywise reliability criterion. The MEG result is therefore a measurement-reliability boundary, not negative model transfer.

Together, these outcomes separate at least three empirical questions: whether a neural geometry is reproducible, whether a model can learn a perturbation toward a source geometry, and whether the perturbation transfers to a distinct target geometry. These stages can align, as in ZuCo and SMN4Lang fMRI, but they need not align universally.

## Discussion

This study reverses the usual direction of brain-model comparison. Rather than asking only whether a pretrained model resembles neural activity, we asked whether reliable neural relational structure can constrain model learning in a way that remains detectable in independent brains. A target derived from Chinese natural-reading EEG altered language-model geometry, the resulting neural-guided representation improved alignment to independent English-reading EEG in all 17 ZuCo participants, and the same frozen intervention prospectively improved alignment to language-network fMRI in all 12 SMN4Lang participants during naturalistic auditory comprehension.

The strongest evidence remains the prospective fMRI test because it crosses participants, task context and measurement modality without target-dataset model optimization. The absolute effect is small, so the claim does not rest on magnitude alone. More informative is the combination of a model-blind reliability gate, an independently defined language-network mask, frozen causal mapping choices, absence of outcome-driven model search and positive participant-level direction in all 12 individuals. Under these constraints, the result shows that an EEG-derived model perturbation altered relational structure in a direction that remained detectable in independently measured cortical language responses.

The later bidirectional experiments sharpen the interpretation without changing the status of the original evidence chain. A source-only fMRI calibration selected lambda = 0.01 before external EEG evaluation, and the resulting fMRI-guided E5 model transferred positively to ZuCo. Already-trained stronger fMRI-guided E5 doses produced an ordered external response, showing that target transfer varied systematically with the strength of the source relational objective. The six-model panel then showed that bidirectional transfer was reproducible across both tested E5 sizes and all three optimization seeds, but was not shared uniformly by the other multilingual encoders. These results argue against two trivial explanations: that bidirectionality was a single lucky E5-large trajectory, or that any multilingual encoder trained with the relational objective would necessarily show the same external behavior.

The appropriate conclusion is nevertheless narrower than a claim of universal brain supervision. The intervention showed no stable neural-specific advantage on generic semantic benchmarks; transfer was null or inconclusive in TMNRED, Garnett Dream and directional inner speech; reverse transfer was weak or negative in several non-E5 models; and the prospectively defined MEG representation did not even pass the measurement prerequisite required for model testing. Human neural geometry can therefore act as a transferable relational constraint on language representations, but transfer is conditional on the source-target pairing, measurement quality, training context and architecture.

The construct itself should also remain broad. Naturalistic EEG and fMRI reflect correlated lexical, syntactic, discourse, temporal, acoustic, attentional and task-related structure. The transferable target should not be equated with a pure lexical-semantic code. We therefore use *neural relational geometry* and *language-related neural geometry*. Future mechanistic work will require experimental designs that dissociate these dimensions rather than infer semantic specificity from naturalistic representational alignment alone.

Several limitations follow directly from the evidence. First, external RSA shifts are small and should be interpreted as reproducible representational changes rather than large increases in explained neural variance. Second, participant-level inference conditions on each dataset's fixed stimulus set; stimulus-resampling sensitivities were conducted only where separately specified. Third, EEG and fMRI outcomes use different representational constructions and cannot be pooled as a common effect-size scale. Fourth, the model-family panel is post-confirmatory and contains a fixed, small set of multilingual encoders, so it supports scope restriction rather than population-level claims about architecture classes. Fifth, the MEG conclusion is representation-specific and does not exclude other prospectively specified source-resolved, event-aligned or spectrotemporal MEG representations in future work. Finally, secondary AHBA analyses remain mechanistically null under the frozen primary tests and do not identify a molecular substrate for the transfer effect.

The broader methodological implication is that biological supervision should be evaluated through external biological transfer rather than training-target fit alone. A neural target must first be reproducible; a model must then learn a perturbation toward that target; and the induced perturbation must survive evaluation in neural systems that did not participate in its optimization or selection. NeuroSem shows that this sequence can succeed across independent brains, languages and modalities, while the boundary analyses show why each gate is necessary.

## Methods

### Study logic and inferential hierarchy

Analyses were organized into development, sealed validation, prospectively frozen external tests and explicitly labelled post-confirmatory analyses. Neural representations were evaluated for cross-participant reproducibility before model testing whenever the protocol specified a reliability gate. Model contrasts, target representations and inferential units were carried forward without target-outcome-driven retuning. The original ChineseEEG-to-ZuCo-to-SMN4Lang sequence defines the primary external evidence chain. Reverse-source, dose-response, optimization-seed and model-family experiments were designed after primary external results were known and are treated as explanatory post-confirmatory evidence.

### ChineseEEG development target

ChineseEEG Little Prince natural-reading EEG was used to establish the development neural geometry. The primary whole-row temporal-mean representation was selected using neural reliability before semantic-model testing. Pairwise distances among linguistic items defined participant-specific representational dissimilarity matrices. Nuisance-adjusted cross-participant reliability compared each participant with the mean geometry of the remaining participants. Residual neural-model correspondence was evaluated across held-out narrative runs using partial Spearman association under the frozen nuisance adjustment.

### Neural-guided model training

Language-model representations were trained with an auxiliary relational objective encouraging model pairwise geometry to align with a frozen neural relational target while retaining a matched text-learning objective. BERT development experiments included text-only and shuffled-neural controls and were evaluated on sealed ChineseEEG run 07. Multilingual E5 was then used for the primary external-transfer program. The primary external model contrast was fixed as neural-guided lambda = 0.10 versus matched text-only lambda = 0. Lambda = 0.10 arose during exploratory development and is not described as a prospectively selected universal optimum.

### ZuCo EEG validation

ZuCo 2.0 Task 1 Normal Reading served as independent English-reading EEG validation. The frozen primary representation was the all-retained-channel temporal mean. Cross-participant neural reliability was evaluated before model-transfer interpretation. The participant was the primary inferential unit. Transfer was summarized by participant-level RSA differences, participant-bootstrap confidence intervals and exact sign-flip inference.

### SMN4Lang fMRI validation

SMN4Lang/OpenNeuro ds004078 served as the prospective cross-modal validation. The primary fMRI target used the independently published LanA language-network mask thresholded at probability 0.20. Story-level multivoxel patterns were converted to correlation-distance RDMs after nuisance adjustment for temporal separation, haemodynamic-response-convolved word-onset density and haemodynamic-response-convolved acoustic RMS envelope. A model-blind cross-participant reliability gate was completed before model loading.

For model evaluation, E5 representations were generated causally within sentence using prefix states at released word onsets, mapped into the fMRI timebase with the fixed canonical haemodynamic response and residualized using the same nuisance family. The only primary model comparison was lambda = 0.10 versus lambda = 0. No SMN4Lang model training, layer search, checkpoint search, ROI search, lag search, haemodynamic-response search or semantic-unit search was performed from the fMRI outcome.

### Post-confirmatory reverse fMRI-to-EEG transfer

A source-only SMN4Lang fMRI calibration used the frozen E5 lambda grid {0, 0.01, 0.03, 0.10, 0.30, 1.0}. Selection was performed without reading external EEG outcomes. The prespecified one-standard-error rule selected the smallest positive lambda within one standard error of the best held-out source-validation mean, yielding lambda = 0.01. The matched lambda = 0 arm came from the same calibration run and seed. The frozen primary reverse target was the existing 17-participant ZuCo temporal-mean EEG pipeline; no alternative lambda, checkpoint, model, layer, pooling rule or source story subset was selected after ZuCo evaluation.

### Post-confirmatory E5 dose-response characterization

After the reverse primary result was evaluated, already-trained fMRI-guided E5 arms across the fixed lambda grid were tested on ZuCo and ChineseEEG run-07 without retraining, adding new lambda values or target-side selection. Dose-response analyses are descriptive/post-confirmatory and do not redefine the source-selected lambda = 0.01 result. A separate three-seed ChineseEEG robustness analysis used fixed added seeds 20260829, 20260830 and 20260831 and the unchanged lambda grid.

### Post-confirmatory model-family panel

The frozen model-family panel evaluated six multilingual models: multilingual E5-large, multilingual E5-base, paraphrase-multilingual-MPNet-base-v2, paraphrase-multilingual-MiniLM-L12-v2, XLM-R base and multilingual BERT. Each model was evaluated under seeds 20260829, 20260830 and 20260831 in both ChineseEEG-to-fMRI and fMRI-to-ZuCo directions.

All models used a common adaptation protocol: final hidden-state representation, attention-mask mean pooling, L2 normalization, cosine-distance geometry, LoRA on attention query/value projections with rank 8, alpha 16 and dropout 0.05, AdamW learning rate 2 x 10^-4 and weight decay 0.01, five fixed source epochs, symmetric dropout-view InfoNCE text objective with temperature 0.05, and neural relational loss weight lambda = 0.10 versus matched lambda = 0. E5 inputs used the `query: ` prefix and other models used no task prefix. No early stopping, checkpoint selection, model-specific lambda search, layer search, pooling search or target-side rescue was permitted. All 36 planned model x seed x direction units completed.

### Boundary datasets

TMNRED, ChineseEEG Garnett Dream and the directional-word inner-speech dataset were analyzed under their frozen external protocols. TMNRED and Garnett first established whether the designated neural geometry was reproducible and then evaluated the same fixed E5 contrast. Directional inner speech was treated as an out-of-task boundary rather than a task-matched reading replication.

### SMN4Lang MEG reliability gate

The prospective SMN4Lang MEG analysis used released preprocessed 1-40 Hz sensor-level data from the same 12 participants and 60 stories. Samples covered by annotations beginning with `bad` were excluded. Remaining valid samples were concatenated in temporal order and divided into 32 equal normalized-time bins. Within each bin, one RMS field-magnitude value was calculated across retained magnetometer samples and one across retained planar-gradiometer samples. The 32 magnetometer and 32 gradiometer values were separately standardized across bins and concatenated into a 64-dimensional run vector. Participant-specific 60 x 60 story RDMs were constructed using correlation distance.

Cross-participant reliability was the Spearman correlation between each participant's upper-triangular RDM edges and the edgewise mean RDM of the other 11 participants. The primary gate required positive mean reliability, a participant-bootstrap 95% confidence interval entirely above zero and an exact one-sided sign-flip probability below 0.05. The gate failed, so no model evaluation was performed. A post-confirmatory model-blind 4/8/16-bin temporal-granularity family also failed its familywise reliability criterion, and no exploratory E5 model evaluation was opened.

### Representational analysis and statistical inference

Representational dissimilarity matrices and cross-representation comparisons followed the general RSA framework. Participant-level effects were the primary inferential unit for external neural validation. Confidence intervals were obtained by participant bootstrap according to each frozen protocol. Exact sign-flip tests enumerated sign assignments where feasible. Raw effect magnitudes were not pooled across EEG, fMRI and MEG because the representational constructions and measurement scales differ.

### Transcriptomic analyses

AHBA analyses were secondary mechanistic extensions rather than part of the primary transfer claim. The Allen Human Brain Atlas was processed with a frozen imaging-transcriptomics workflow using abagen. Prespecified molecular-panel and pathway analyses were null under the frozen primary framework. Exploratory sensitivities did not revise those null conclusions. Molecular analyses should remain in Extended Data or Supplementary Information and should not be used to strengthen the primary representational claim.

## Main figure legends

**Figure 1 | Reproducible neural geometry provides a learnable relational training signal.** a, Conceptual framework: reproducible human EEG geometry supplies an auxiliary relational constraint to a language model, and the induced perturbation is evaluated in external brains. b, ChineseEEG target reliability before and after nuisance residualization. c, Residual neural-model correspondence across six held-out narrative runs; all six run-level values are positive, mean 0.0085, exact one-sided P = 0.0156. d, Sealed ChineseEEG run-07 comparison showing neural-guided BERT strongest in both development seeds. Development results establish reliability and learnability but are kept distinct from later external validation.

**Figure 2 | A ChineseEEG-derived constraint transfers to independent English-reading EEG.** a, Frozen cross-language transfer design from ChineseEEG through the fixed multilingual-E5 neural-guided versus text-only contrast to ZuCo EEG. b, Participant-level residual LOO reliability of the frozen ZuCo temporal-mean EEG geometry; mean 0.06742 and 17/17 positive. c, Paired participant residual RSA for text-only lambda = 0 and neural-guided lambda = 0.10. d, Participant neural-guided minus text-only differences; mean +0.0016637, 95% confidence interval +0.0012294 to +0.0021452, 17/17 positive, exact one-sided P = 7.63 x 10^-6. No ZuCo outcome was used for model retuning.

**Figure 3 | The same frozen EEG-derived intervention transfers prospectively to language-network fMRI.** a, Prospective cross-modal design from the frozen ChineseEEG-derived E5 contrast to SMN4Lang fMRI in 12 Mandarin-speaking participants. b, Model-blind fMRI reliability gate; mean residual LOO reliability 0.65327, 95% confidence interval 0.63945 to 0.66843, 12/12 positive. c, Paired participant residual RSA values for text-only lambda = 0 and neural-guided lambda = 0.10. d, Participant differences; mean +0.00085250, 95% confidence interval +0.00078966 to +0.00091398, 12/12 positive, exact one-sided P = 0.000244. No SMN4Lang model, layer, checkpoint, ROI, lag, haemodynamic-response or semantic-unit selection was performed from the target outcome.

**Figure 4 | Bidirectionality and model-family scope of external neural transfer.** a, Post-confirmatory reverse transfer within multilingual E5 is graded across the already-trained fMRI relational-loss weights when evaluated on independent ZuCo EEG. The source-selected primary reverse candidate remains lambda = 0.01; the larger-dose pattern is characterization, not retrospective reselection. b, Conceptual bidirectional transfer within E5 and replication across model size: E5-large and E5-base are positive in all three optimization seeds in both source directions. c, Six-model common-protocol panel for ChineseEEG-derived constraint to SMN4Lang fMRI. Filled circles show individual optimization seeds and open circles show the three-seed mean. d, The corresponding fMRI-derived constraint to ZuCo EEG. Reverse transfer is stable in both E5 variants but not in MPNet, MiniLM, XLM-R or mBERT. The panel is post-confirmatory and supports architecture- and direction-dependent scope, not E5 uniqueness across all possible language models.

## References

1. Mou, X. et al. ChineseEEG: A Chinese Linguistic Corpora EEG Dataset for Semantic Alignment and Neural Decoding. *Scientific Data* **11**, 550 (2024).

2. Devlin, J., Chang, M.-W., Lee, K. & Toutanova, K. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In *Proceedings of NAACL-HLT* 4171-4186 (Association for Computational Linguistics, 2019). doi:10.18653/v1/N19-1423.

3. Wang, L. et al. *Multilingual E5 Text Embeddings: A Technical Report*. arXiv:2402.05672 (2024).

4. Hollenstein, N., Troendle, M., Zhang, C. & Langer, N. ZuCo 2.0: A Dataset of Physiological Recordings During Natural Reading and Annotation. In *Proceedings of the Twelfth Language Resources and Evaluation Conference* 138-146 (European Language Resources Association, 2020).

5. Wang, S., Zhang, X., Zhang, J. & Zong, C. A synchronized multimodal neuroimaging dataset for studying brain language processing. *Scientific Data* **9**, 590 (2022).

6. Lipkin, B. et al. Probabilistic atlas for the language network based on precision fMRI data from >800 individuals. *Scientific Data* **9**, 529 (2022).

7. Bai, Y. et al. TMNRED, A Chinese Language EEG Dataset for Fuzzy Semantic Target Identification in Natural Reading Environments. *Scientific Data* **12**, 701 (2025).

8. Kostulin, D. V. et al. EEG-based brain-computer interface dataset for directional word recognition. *Scientific Data* **13**, 1195 (2026).

9. Kriegeskorte, N., Mur, M. & Bandettini, P. Representational similarity analysis - connecting the branches of systems neuroscience. *Frontiers in Systems Neuroscience* **2**, 4 (2008).

10. Hawrylycz, M. J., Lein, E. S. & Guillozet-Bongaarts, A. L. An anatomically comprehensive atlas of the adult human brain transcriptome. *Nature* **489**, 391-399 (2012).

11. Markello, R. D. et al. Standardizing workflows in imaging transcriptomics with the abagen toolbox. *eLife* **10**, e72129 (2021).

## Assembly notes

This Markdown draft is the first repository back-port that incorporates the completed post-confirmatory reverse-transfer, dose-response and six-model bidirectional panel together with the frozen v3.4 main figures. It supersedes `NATURE_MANUSCRIPT_DRAFT_V3.md` for current Markdown scientific wording, while preserving the original ChineseEEG -> ZuCo -> SMN4Lang primary evidential hierarchy. The prior v0.6 NMI Word review master remains a historical author-edited source but was not accessible through the connected Drive during this assembly pass.

Before submission, authors still need to finalize author order and affiliations, author contributions, ethics wording, funding and acknowledgements, competing interests, data/code availability production details, journal reporting-summary compliance, and Zotero-linked references in the final Word submission file.