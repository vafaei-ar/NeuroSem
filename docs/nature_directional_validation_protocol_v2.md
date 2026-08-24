# Nature directional-word EEG external validation protocol v2

Status: frozen after model-blind structural/documentation audit and before any Nature neural-model RSA.

## Scientific question

Does the prospectively chosen low-dose NeuroSem E5 model (lambda = 0.10) align better than the matched text-only E5 model (lambda = 0.00) with independent inner-speech EEG concept geometry in the Scientific Data 2026 directional-word dataset?

Primary publication: Kostulin DV, Shaposhnikov PD, Ekizyan AKh, et al. *EEG-based brain-computer interface (BCI) dataset for directional word recognition.* Scientific Data. 2026;13:1195. DOI: 10.1038/s41597-026-07809-9.

Data DOI: 10.5281/zenodo.20374418.

This dataset was not used for NeuroSem training or lambda selection.

## Audit facts used to freeze this protocol

The model-blind audit confirmed:
- 22 participants total: 12 Russian and 10 Spanish;
- 8 Russian standard-marker participants and 10 Spanish standard-marker participants, giving 18 primary participants;
- the four modified Russian participants are sub1, sub3, sub5, and sub10 and are excluded from the primary analysis;
- standard epochs are approximately -0.5 to +1.0 s around the self-initiated marker, generally at 500 Hz;
- event labels occur as paired concept labels ending in 1 and 2 (for example UP1/UP2);
- no NeuroSem model was loaded and no neural-model RSA was computed during the audit/probe stages.

The publication specifies that within each concept block overt articulation occurred first and covert/inner articulation second. Therefore the primary code will treat suffix 2 as covert only after verifying, for every primary participant and concept, that suffix-1 events precede suffix-2 events in the epoched event sequence. If this structural assertion fails, the confirmatory analysis must stop rather than guess the condition mapping.

## Primary population

Primary participants:
- Russian: sub2, sub4, sub6, sub7, sub8, sub9, sub11, sub12;
- Spanish: sub0 through sub9;
- total n = 18.

No participant will be removed based on neural-model alignment or neural split-half reliability.

The four modified-marker Russian participants are excluded from the primary analysis because their marker/epoch structure differs by design. They may be examined only as a labeled sensitivity analysis later.

## Concepts and model stimuli

Canonical concept order:
1. up
2. down
3. left
4. right
5. forward
6. backward

Russian words:
- вверх
- вниз
- влево
- вправо
- вперёд
- назад

Spanish words:
- arriba
- abajo
- izquierda
- derecha
- adelante
- atrás

The Russian-only extra command NEXT is not used.

## Primary EEG condition

Primary condition: covert / inner articulation (suffix 2 after the structural order assertion described above).

Overt articulation is not part of the primary endpoint because of stronger speech-muscle contamination.

## Primary EEG representation

For each primary participant:
1. load the distributed preprocessed MNE Epochs FIF file;
2. select scalp EEG channels and exclude auricular reference channels A1/A2 if present;
3. apply per-channel baseline correction using -0.20 to 0.00 s;
4. exclude the known early keypress-contaminated interval by using only 0.20 to 0.80 s after the marker;
5. for each of the six covert concept conditions, average all available trials to obtain one concept ERP matrix (channels x time);
6. flatten each concept ERP matrix into one feature vector;
7. stack the six concept vectors into a 6 x features matrix;
8. z-score each feature across the six concepts (zero-variance features are set to zero after centering);
9. calculate the six-concept neural RDM with correlation distance, giving 15 unique concept-pair distances.

The 0.20 to 0.80 s window is fixed before any model comparison. It removes the published 0-200 ms keypress-contamination interval while retaining a broad post-marker inner-speech interval. No alternate window will replace it based on the result.

## EEG-only reliability diagnostic

For each participant and concept, covert trials will also be split deterministically into alternating odd/even trials. The same concept-RDM procedure will be applied to both halves, and their 15-edge RDMs will be compared with Spearman correlation.

This split-half value is diagnostic only. It will be reported but will not be used to select participants, time windows, channels, or models.

## Model representations

Frozen base model:
- intfloat/multilingual-e5-large
- revision 3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3

Input format and pooling must match prior E5 NeuroSem evaluations:
- prefix: `query: `
- attention-mask mean pooling of final hidden states;
- L2 normalization of pooled embeddings.

For each language separately, embed the six exact native-language words and compute a six-concept model RDM using cosine distance.

## Frozen model contrasts

Primary contrast:
- lambda = 0.10 NeuroSem adapter versus lambda = 0.00 text-only adapter.

Frozen adapter sources:
- lambda = 0.00: `outputs/e5_neural_tuning_v1/text_only/20260823_181507/adapter`
- lambda = 0.10: latest completed adapter under `outputs/e5_neural_tuning_pareto_v1/lambda_0p10/neural/*/adapter`, requiring an adjacent completed `summary.json`.

Secondary descriptive contrasts, already prespecified in v1:
- lambda = 1.00 genuine-neural adapter versus lambda = 0.00;
- untuned frozen E5 base where technically available.

No new lambda values will be introduced after Nature results are observed.

## Primary RSA statistic

For participant i:
- compute Spearman correlation between that participant's 15-edge neural RDM and the language-matched lambda = 0.10 model RDM: rho_i(0.10);
- compute the analogous correlation for lambda = 0.00: rho_i(0.00);
- define delta_i = rho_i(0.10) - rho_i(0.00).

Primary effect = mean(delta_i) across all 18 primary participants.

Primary hypothesis is directional: mean(delta_i) > 0.

## Primary inference

Use an exact one-sided subject-level sign-flip test on the 18 participant deltas.

All 2^18 sign configurations will be enumerated. The p-value is the fraction of sign-flipped mean deltas greater than or equal to the observed mean delta.

This keeps the participant as the unit of inference and does not treat the 15 RDM edges as independent observations.

## Cross-language consistency

Report separately:
- mean delta in the 8 Russian primary participants;
- exact one-sided sign-flip p-value in Russian participants;
- mean delta in the 10 Spanish participants;
- exact one-sided sign-flip p-value in Spanish participants.

The overall test remains primary. A scientifically strong transfer result should have positive mean deltas in both language groups. If the overall effect is driven by only one language, that limitation must be stated explicitly.

## Secondary outputs

Report:
- participant-level rho for lambda 0, lambda 0.10, lambda 1, and untuned base;
- participant-level deltas;
- split-half neural RDM reliability;
- trial counts per participant and concept;
- language-specific model RDMs;
- primary and language-stratified exact sign-flip results.

Secondary outcomes do not replace the primary endpoint.

## Interpretation

Positive primary result:
The prospectively selected low-dose NeuroSem model transfers to an independent EEG dataset and aligns better with inner-speech concept geometry than matched text-only tuning. This supports cross-dataset neural-geometry generalization.

Null primary result:
The low-dose ChineseEEG steering effect does not clearly transfer to this small six-concept inner-speech dataset under the frozen analysis.

Negative primary result:
The low-dose NeuroSem model aligns worse than text-only with this independent neural target, arguing against broad transfer of the current neural objective.

Because there are only six concepts (15 RDM edges), even a positive result is evidence for independent neural transfer, not a broad proof of semantic superiority.

## No post-hoc rescue

After this protocol is committed, do not change the primary result by:
- searching alternate lambdas;
- moving the primary EEG window;
- selecting channels based on model alignment;
- excluding low-alignment participants;
- changing covert to overt as the primary condition;
- choosing a different RDM metric because it improves the result;
- replacing native-language stimuli with translations because they perform better.

Any such follow-up must be labeled exploratory and require another fresh target for confirmation.
