# 17. NMI bidirectional fMRI-source freeze v1

**Status:** frozen model-blind source-target construction for the post-confirmatory bidirectional cross-modal transfer experiment.

## Scientific question

Does a relational constraint derived from SMN4Lang fMRI induce a multilingual-E5 representational perturbation that transfers to independent EEG data?

This experiment is secondary and post-confirmatory. It does not alter the historical status of the primary ChineseEEG -> ZuCo -> SMN4Lang prospective chain.

## Stage B1 purpose

Before loading or training any language model, freeze the fMRI source supervision object and the source-only train/validation split. No EEG outcome is read in this stage.

## Frozen fMRI source representation

- Dataset: SMN4Lang / OpenNeuro ds004078.
- Participants: the same 12 participants used in the frozen fMRI reliability and transfer analyses.
- Stories: the same 60 stories.
- Spatial representation: the same LanA probabilistic language-network mask thresholded at 0.20.
- Temporal representation: the same retained within-story fMRI timepoints used in the frozen reliability/transfer pipeline.
- Neural RDM: correlation distance across LanA-mask multivoxel patterns at retained timepoints.
- Nuisance adjustment: the same three frozen within-story nuisance vectors: absolute temporal separation, absolute difference in canonical-HRF-convolved word-onset density, and absolute difference in canonical-HRF-convolved acoustic RMS envelope.
- No new ROI, mask threshold, HRF, lag, temporal unit, participant, story, or nuisance search is permitted.

## Group relational target

For each story independently:

1. Compute the participant-specific neural correlation-distance RDM over the frozen retained timepoints.
2. Residualize the RDM using the frozen three-column nuisance design from the existing SMN4Lang pipeline.
3. Convert the residualized edge vector to average ranks and z-standardize it within participant.
4. Average the 12 participant rank-z vectors edgewise.
5. Z-standardize the resulting group vector to mean 0 and population SD 1.

The resulting standardized group edge vector is the sole fMRI relational-supervision target for that story.

This aggregation is fixed before model training and is chosen to match the rank-based RSA logic used in the frozen fMRI evaluation while producing a stable differentiable Pearson-style relational target.

## Frozen source split

The 60 stories were ordered by SHA256 of the literal string `smn4lang-story-XX`, where `XX` is the zero-padded story number. The lowest 48 hashes are training stories and the remaining 12 are source-validation stories.

Training stories:

`[1, 3, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24, 25, 27, 28, 29, 30, 31, 32, 33, 35, 36, 39, 40, 42, 43, 44, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]`

Validation stories:

`[2, 7, 11, 16, 22, 26, 34, 37, 38, 41, 45, 50]`

The split is outcome-independent, committed before any fMRI-guided model training, and must not be changed after source-validation or EEG outcomes are observed.

## Stage B1 outputs

- one aggregate source target file per story under `outputs/nmi_bidirectional_fmri_source_v1/latest/targets/`;
- `split.json` containing the exact train/validation lists;
- `summary.json` containing only aggregate, non-sensitive source-target dimensions and checks.

Only `summary.json` and `split.json` are declared as RunRelay artifacts. The per-story derived targets remain project-local for the subsequent training stage.

## Guardrails

- No language model is loaded in Stage B1.
- No ZuCo, ChineseEEG, TMNRED, Garnett, MEG, or other external neural target is read.
- No target-side or source-side representation search is allowed.
- A failure of this construction is a technical/source-target failure and is not to be rescued by changing the representation family.
- Stage B2 model training must use exactly these committed split and aggregation rules.
