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

## Frozen DERCo item identity

The authoritative DERCo item key is the retained MNE event label itself, parsed as `<word>_<article>_<stimulus_index>`.

The structural gate passed across all 22 participants and all five articles: every retained label parsed, article identity matched the file folder, stimulus indices were unique and strictly increasing within each participant/article file, and the same `(article, stimulus_index)` key carried one consistent normalized word across participants. Attached FIF feature metadata and behavioural prediction tables are not used to define item identity.

## Frozen EEG reliability estimator

The first attempted reliability implementation required the same item to survive preprocessing in all 22 participants. That structural rule failed before any neural reliability value was computed because article 0 had only 9 all-participant common items. This reflects independent artifact rejection and is not a scientific reliability result.

Before computing any DERCo reliability value, the estimator is therefore frozen as pairwise-available leave-one-participant-out neural-geometry reliability:

- retain all 22 frozen participants and all five articles;
- for each participant/article, use every item retained for that participant;
- represent each item by the temporal mean within every retained EEG channel (`row_mean_all`);
- feature-wise z-standardize items using population standard deviation (`ddof = 0`);
- construct correlation-distance neural RDM entries for all within-participant retained item pairs;
- for each target participant and item pair, construct the leave-one-participant-out reference as the mean correlation distance across other participants who retained both items;
- require at least **11 of the 21** leave-one-out participants to contribute to a tested pair, a strict majority threshold fixed before the estimator is run;
- require at least **1,000 eligible pairs** in every participant/article cell; failure of that rule stops the analysis rather than triggering participant/article selection;
- primary nuisance residualization uses only absolute stimulus-index difference and absolute event-label word-length difference;
- calculate primary reliability as the Pearson correlation between separately nuisance-residualized target and LOO RDM vectors;
- report raw, non-residualized reliability as a sensitivity only;
- aggregate the five article reliabilities within participant by unweighted Fisher-z mean followed by inverse transform;
- use the participant as the inferential unit;
- the reliability gate passes only if the mean participant aggregate is positive and the 10,000-resample participant-bootstrap 95% confidence interval has a lower bound greater than zero;
- report one-sided exact participant sign-flip inference as supportive evidence, not as the gate definition.

This pairwise-available rule handles missing epochs caused by independent artifact rejection without using neural outcomes to select participants, articles, representations, or item subsets.

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
