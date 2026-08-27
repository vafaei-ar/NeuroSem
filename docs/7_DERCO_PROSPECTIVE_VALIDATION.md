# DERCo prospective external validation

**Status:** prospectively designated, before any DERCo NeuroSem outcome

## Rationale

DERCo (Dublin EEG-based Reading Experiment Corpus; Quach, Gurrin & Healy, Scientific Data 2024; OSF DOI 10.17605/OSF.IO/RKQBU) is the next independent external validation target for NeuroSem.

It was selected because it provides a stronger independence test than another dataset from the ZuCo acquisition family:

- 22 healthy adult native English speakers;
- narrative reading over five articles;
- 32-channel ActiCHamp EEG;
- word-presentation triggers obtained with a photodiode;
- public raw and preprocessed EEG on OSF;
- participant/article preprocessed epochs in FIF format;
- independent lab, hardware, participants, stimuli, and acquisition pipeline relative to ChineseEEG and ZuCo.

## Frozen scientific question

Does the ChineseEEG-trained multilingual-E5 neural-guided model (`lambda = 0.10`) show stronger alignment than the matched text-only model (`lambda = 0`) to independently measured DERCo reading-related EEG geometry, without any DERCo tuning?

## Prospective sequence

1. Metadata-only OSF inventory. Do not download EEG or compute any neural/model outcome.
2. Structural/materialization audit of participant, article, text, event/epoch, channel, and sampling metadata.
3. Freeze the exact DERCo semantic analysis unit and text mapping.
4. Run an EEG-only reliability test using the already-selected all-retained-channel temporal mean (`row_mean_all`) as the primary representation. Sensitivity representations may only reuse already-defined `row_std_all` and `relative_8bin_all` conventions.
5. Only if the primary DERCo neural geometry passes a prospectively specified positive reliability gate, run the single frozen model contrast: ChineseEEG-trained E5 `lambda = 0.10` neural-guided minus `lambda = 0` text-only.
6. Participant-level inference is primary. No DERCo model tuning, representation search, time-window search, participant exclusion from transfer outcomes, or alternative model search is allowed.

## Analysis principles

The target should match the existing NeuroSem geometry as closely as DERCo permits:

- temporal average within every retained EEG channel for each frozen linguistic item;
- never average channels before constructing the item feature vector;
- feature-wise standardization across items;
- correlation-distance neural RDM;
- nuisance-residualized RSA using only nuisance terms that can be frozen from DERCo timing/text metadata before model outcomes;
- participant is the inferential unit;
- report the full participant distribution, mean/median transfer delta, bootstrap interval, fraction positive, and sign-flip inference.

If DERCo's released epoch structure cannot support an item definition comparable enough to the established NeuroSem target, stop at the structural audit and record DERCo as infeasible rather than adapting the scientific question post hoc.

## Interpretation

A positive frozen DERCo transfer result would provide a second independent English-language replication of transferable neural-guided semantic alignment, under an acquisition family independent of ZuCo. A null result remains informative and must not trigger feature/model searches.
