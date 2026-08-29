# Nature reporting summary draft

**Manuscript:** *Human neural geometry provides a transferable constraint on language representations*  
**Status:** prepared from the locked NeuroSem protocols and results for author review. This document is intended to support completion of the journal's current Reporting Summary form; field names should be transcribed into the form available at submission.

## Research design

This work is a secondary analysis and computational modelling study using previously collected and released human EEG, MEG and fMRI datasets plus a published post-mortem transcriptomic resource. NeuroSem recruited no new participants and performed no intervention or prospective data collection.

The inferential hierarchy separated: (1) development of a reproducible neural relational target in ChineseEEG; (2) sealed within-dataset model evaluation; (3) frozen external neural validation; and (4) explicitly labelled post-confirmatory or exploratory analyses. External target representations and model contrasts were frozen before the relevant target outcomes wherever specified by the protocol.

## Human participants and datasets

- **ChineseEEG:** development natural-reading EEG and same-acquisition Garnett Dream boundary analysis.
- **ZuCo 2.0 Task 1 Normal Reading:** independent English-reading EEG validation; 17 structurally eligible participants in the frozen analysis cohort.
- **SMN4Lang:** prospective cross-modal validation; 12 Mandarin-speaking participants, 60 stories, fMRI primary validation and a separately gated MEG reliability analysis.
- **TMNRED:** independent Chinese natural-reading EEG boundary validation; frozen cohort and item inclusion were determined before model-transfer testing.
- **Directional-word EEG:** out-of-task inner-speech boundary analysis.
- **Allen Human Brain Atlas:** secondary post-mortem imaging-transcriptomics analyses.

Participant inclusion/exclusion rules are dataset-specific and documented in the frozen protocols and experiment ledger. No participant was removed on the basis of a NeuroSem model-transfer outcome.

## Sample-size determination

NeuroSem did not prospectively recruit participants or set sample sizes. Analyses used the available eligible participants from the source datasets after prespecified structural/data-quality criteria. Statistical inference therefore reflects the fixed available cohorts rather than a newly powered experiment. The manuscript reports the participant as the primary inferential unit for external neural validations.

## Data exclusions

Structural or data-quality exclusions were applied according to dataset-specific frozen protocols before outcome interpretation. For example, the ZuCo cohort excluded one subject before outcome analysis because required Normal Reading runs failed structural event quality control. SMN4Lang fMRI used the complete frozen 12-participant, 60-story cohort. The SMN4Lang MEG branch was stopped at its prespecified reliability gate rather than excluding participants or searching alternative model outcomes.

## Replication

The central claim is evaluated through independent forms of replication rather than repeated sampling within one dataset. The learned relational constraint was developed in ChineseEEG, transferred to independent English-reading EEG in ZuCo, and was then tested prospectively in SMN4Lang language-network fMRI in different participants and a different measurement modality. TMNRED, Garnett Dream and directional inner speech were retained as null/inconclusive boundary conditions.

## Randomization and blinding

No participant randomization was performed by NeuroSem because all human data were pre-existing. Model-blind procedures were used where outcome protection was scientifically relevant. The SMN4Lang fMRI neural-geometry reliability gate was completed before E5 model loading. The SMN4Lang MEG primary reliability analysis and bounded temporal-granularity follow-up were model-blind; because the reliability criterion failed, no MEG model evaluation was performed. Frozen model contrasts were carried into external datasets without target-outcome-driven model retuning.

## Statistical methods

Representational dissimilarity matrices were compared using correlation-based representational similarity analysis under the dataset-specific frozen nuisance-control procedures. Participant-level effects were the primary inferential unit in external validations. Confidence intervals were obtained by participant bootstrap according to each frozen protocol. Exact sign-flip tests enumerated sign assignments where feasible. The manuscript reports individual-direction consistency alongside means, confidence intervals and exact probabilities. Raw RSA magnitudes are not pooled across EEG, MEG and fMRI because their representational constructions and measurement scales differ.

For the post-confirmatory SMN4Lang MEG temporal-granularity family, familywise inference across the three frozen alternatives used the prespecified Bonferroni-adjusted one-sided alpha and corresponding bootstrap interval. No candidate passed.

Secondary AHBA molecular analyses used the frozen multiplicity-control and spatial-null procedures documented in the repository. Their confirmatory conclusion is null and they are not used to strengthen the main representational claim.

## Software and reproducibility

Custom analyses and manuscript figure generation are version controlled in `https://github.com/vafaei-ar/NeuroSem`. The repository records frozen protocols, exact-commit provenance, RunRelay execution metadata and presentation-only figure builders. The external multilingual model was `intfloat/multilingual-e5-large` at pinned revision `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3` for the frozen analyses. Dataset-specific library versions and execution details are recoverable from the exact commits and environment files associated with the reported runs.

## Data and code availability

All principal source datasets are public or were analyzed from de-identified releases under their source terms. The manuscript Data Availability section lists ChineseEEG, ZuCo 2.0, SMN4Lang, TMNRED, the directional-word EEG dataset, LanA and the Allen Human Brain Atlas. The Code Availability section points to the NeuroSem repository. A persistent archival release should be minted from the submission commit before publication.

## Ethics

This is secondary analysis of existing de-identified or public data. The manuscript records the original approval and consent basis for each participant-level dataset. NeuroSem obtained no new participant consent because it did not recruit participants or collect new human data.

## Items to confirm at submission

- Final author list and corresponding author.
- Funding sources and acknowledgements.
- Competing-interest declaration.
- Whether the current Nature Reporting Summary form asks for any field not represented above.
- Persistent DOI/version for the submission code archive if available at that stage.
