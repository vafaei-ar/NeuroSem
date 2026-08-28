# NeuroSem figure and table plan

**Status:** Nature-facing working plan, 2026-08-28

The main figures should communicate one compact conceptual story: a reproducible neural relational target can be learned by a language model and can transfer prospectively across language and neural measurement modality. Null transfer datasets should define scope. AHBA should not compete with that central story.

## Main Figure 1. From neural geometry to neural-guided learning

### Panel A. Concept

Natural-language items -> reproducible neural relational geometry -> neural-guided model training -> frozen external validation.

The diagram should emphasize that the neural target is an RDM/geometry, not a class label or decoder output.

### Panel B. ChineseEEG neural target

Show the reliability-led temporal-mean channel representation, nuisance residualization, and cross-subject neural geometry.

### Panel C. Residual semantic correspondence

Run-wise Little Prince residual BERT RSA across runs 01-06, emphasizing 6/6 positive and mean effect 0.0085.

### Panel D. Sealed neural-guided learning

BERT run-07 paired comparison across base, text-only, neural-guided, and shuffled-neural arms for two seeds.

Take-home label: **reliable neural geometry can serve as a learnable relational supervision target.**

## Main Figure 2. Cross-language transfer to independent EEG

ZuCo 2.0 should be the clean external EEG validation.

### Panel A. Independence schematic

ChineseEEG -> ZuCo with icons/labels for:

- new participants;
- new laboratory/dataset;
- new texts;
- Chinese -> English;
- same frozen model contrast.

### Panel B. ZuCo neural reliability

Participant-level residual LOO reliability or forest/paired display:

- mean 0.06742;
- 95% CI [0.05831, 0.07687];
- 17/17 positive.

### Panel C. Frozen E5 transfer

Participant-level delta plot for lambda 0.10 - lambda 0:

- mean +0.0016637;
- 95% CI [+0.0012294,+0.0021452];
- 17/17 positive;
- exact one-sided p=7.63e-06.

Use paired points or slope lines showing text-only and neural-guided RSA within participant.

Take-home label: **the learned neural constraint transfers across language in independent EEG.**

## Main Figure 3. Prospective cross-modal transfer to language-network fMRI

This should be the visual centerpiece.

### Panel A. SMN4Lang design

ChineseEEG-trained frozen E5 -> independent SMN4Lang participants hearing 60 Mandarin stories -> LanA language-network fMRI.

Make explicit:

- no SMN4Lang model training;
- independent participants;
- auditory naturalistic task;
- fMRI rather than EEG.

### Panel B. Model-blind reliability gate

Show LanA mask and participant-level fMRI reliability:

- mean residual LOO 0.65327;
- 95% CI [0.63945,0.66843];
- 12/12 positive;
- exact one-sided p=0.000244.

Label clearly: **reliability established before model loading.**

### Panel C. Frozen semantic-to-fMRI mapping

Compact schematic:

released word onset -> causal within-sentence prefix E5 state -> fixed canonical HRF -> TR-level model geometry -> nuisance-residualized RSA with LanA multivoxel geometry.

Avoid excessive implementation detail in the main panel. Put exact punctuation/reset and timing rules in Methods/Extended Data.

### Panel D. Primary paired participant result

Paired participant points for:

- text-only lambda 0 mean RSA 0.12092396;
- neural-guided lambda 0.10 mean RSA 0.12177646.

Show all 12 participant lines; all should point upward.

### Panel E. Delta inference

- mean +0.00085250;
- median +0.00086365;
- 12/12 positive;
- 95% CI [+0.00078966,+0.00091398];
- exact one-sided p=0.000244.

Take-home label: **an EEG-derived neural constraint survives prospective transfer to independent cortical fMRI geometry.**

## Main Figure 4. Selectivity, boundary conditions, and semantic dissociation

This figure prevents overclaiming and strengthens causal interpretation.

### Panel A. External transfer effects

Aligned forest/effect plot with consistent direction convention for:

- ZuCo: positive;
- SMN4Lang fMRI: positive;
- TMNRED: null;
- Garnett Dream: null/inconclusive;
- directional-word dataset: negative/null boundary.

Because effect scales differ by modality/dataset, either use standardized visual encoding with exact numerical labels or separate axes rather than visually implying direct magnitude comparability.

### Panel B. Independence dimensions

Matrix showing for each external test whether it changes participants, text, language, task, laboratory, and neural modality.

This lets the reader see why SMN4Lang carries special inferential weight even though its absolute delta is small.

### Panel C. Generic semantic benchmark

Show that neural-guided training does not produce a stable neural-specific generic semantic gain.

Take-home label: **transfer is selective and neural-alignment-specific, not a universal semantic uplift.**

## Extended Data

### ED1. ChineseEEG representation selection and nuisance controls

- flattened versus temporal-mean neural reliability;
- run-wise BERT residual RSA;
- participant influence.

### ED2. Neural-guided training controls

- both BERT seeds;
- shuffled-neural control;
- E5 architecture replication;
- Pareto exploration clearly labeled exploratory.

### ED3. TMNRED

- structural/input freeze;
- reliability distributions;
- primary null transfer;
- alternative-representation follow-ups labeled post-confirmatory exploratory.

### ED4. Garnett Dream

- exact text mapping;
- reliability;
- participant and chapter/story transfer heterogeneity;
- null/inconclusive frozen model contrast.

### ED5. SMN4Lang structural and timing QC

- metadata/timebase audit;
- LanA atlas provenance and geometry;
- model-blind reliability details;
- story-level transfer heterogeneity;
- semantic-to-TR mapping checks;
- frozen guardrail checklist.

### ED6. Directional-word boundary condition

- task description;
- fixed model contrast;
- negative/null result.

### ED7-ED9. AHBA mechanistic constraint

If retained in the current paper:

- AHBA spatial mapping and prespecified GABA/serotonin nulls;
- whole-transcriptome spatial-null analysis and published-panel primary nulls;
- mirroring diagnostic explicitly labeled post-hoc methodological sensitivity.

If space or conceptual clarity suffers, move the full AHBA package to Supplementary Information or a separate manuscript.

## Main Table 1. Validation design and independence

Rows:

- ChineseEEG Little Prince;
- ZuCo 2.0 NR;
- SMN4Lang fMRI;
- TMNRED;
- Garnett Dream;
- directional-word condition.

Columns:

- modality;
- task;
- language;
- participant independence;
- text independence;
- laboratory/dataset independence;
- neural representation;
- model trained on target dataset?;
- frozen model contrast;
- confirmatory status;
- role in claim.

## Main Table 2. Neural reliability and frozen transfer

Columns:

- reliability metric;
- reliability mean and CI;
- model arm values where applicable;
- mean lambda 0.10 - lambda 0 delta;
- bootstrap CI;
- fraction positive;
- exact inference;
- interpretation.

## Supplementary Table S1. Full RunRelay provenance

For every outcome-bearing analysis include:

- job id;
- exact NeuroSem commit;
- task;
- status;
- runtime;
- artifact directory;
- confirmatory/exploratory/post-hoc label;
- whether preceding failures altered engineering only or scientific protocol.

## Supplementary Table S2. Frozen analysis choices by dataset

Include:

- participant/item cohort;
- neural representation;
- nuisance family;
- model revision;
- adapter paths/provenance;
- semantic unit;
- temporal mapping;
- inferential unit;
- bootstrap/permutation seed;
- stop rules.

## Figure-generation guardrails

- Plot every participant for the two key positive transfer results where feasible.
- Do not visually inflate the SMN4Lang effect by hiding absolute RSA values.
- Emphasize consistency and independence, not only p-values.
- Keep confirmatory, exploratory, and post-hoc results visually distinct.
- Do not compare raw delta magnitudes across EEG and fMRI as if they were on a common measurement scale.
- Preserve all null external tests.
- Keep AHBA out of the main causal chain from neural geometry to model transfer.
