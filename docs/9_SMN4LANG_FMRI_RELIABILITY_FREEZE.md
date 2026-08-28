# SMN4Lang fMRI reliability freeze

## Status

Prospective freeze written after the model-blind metadata, mapping, timebase, and LanA atlas audits and before any SMN4Lang neural reliability or model-alignment outcome is computed.

Dataset: SMN4Lang / OpenNeuro ds004078.

## Scientific question

Does independently measured cortical fMRI during naturalistic Mandarin comprehension contain a reproducible representational geometry within an independently defined high-level language network, after controlling obvious temporal and low-level auditory structure?

This stage is neural-only. It must not load or evaluate E5, BERT, any adapter, or any model-derived semantic representation.

## Cohort and runs

- All 12 SMN4Lang participants.
- All 60 shared story runs.
- No participant or story selection based on neural outcomes.
- The structural audit already verified 720/720 MNI/CIFTI runs, zero failures, identical within-story timepoint counts across participants, identical story onset and duration across participants, monotonic word timing, all words within the story event, and all story events within the scan.

## Spatial representation

Primary space is the independently released LanA SPM probabilistic language atlas from Lipkin et al. (Scientific Data 2022), file `SPM/LanA_n806.nii`.

Frozen atlas provenance:
- Figshare article DOI: `10.6084/m9.figshare.20425209.v1`
- archive MD5: `5e981df0866f2522e75a7899f69a00a5`
- atlas SHA256: `3d366a20d50a97ecabb4b9980359b2cc093e99ef7bd125bca26ed1c53babca3`
- atlas grid: 91 x 109 x 91, 2-mm isotropic MNI
- exact grid match to SMN4Lang MNI derivatives: true

Primary mask: atlas probability >= 0.20. This threshold is frozen because 0.20 is the atlas authors' published visualization threshold and was specified independently of SMN4Lang outcomes. No mask threshold search is allowed.

The fMRI feature vector for a TR is the vector of BOLD values across all voxels in this fixed mask.

## Temporal items

For each story, use the shared fMRI TR grid with TR = 0.71 s. Retain TRs from the story audio onset (10.65 s) through the end of the scan. This includes the post-stimulus BOLD tail without selecting a fitted lag.

No lag, temporal window, story subset, or participant subset may be selected using neural reliability.

## Neural RDM

For each participant and story separately:
1. extract the LanA-mask voxel pattern at every retained TR;
2. z-score every voxel across retained TRs using population SD (`ddof=0`);
3. compute correlation distance between every pair of retained TR patterns.

This produces one neural RDM per participant per story.

## Low-level nuisance controls

For every story, construct nuisance pairwise distances on the same retained TRs:

1. absolute temporal separation in seconds;
2. absolute difference in canonical-HRF-convolved word-onset density, using the released word timing annotations;
3. absolute difference in canonical-HRF-convolved acoustic RMS envelope, using the released story audio.

Use one fixed SPM-style canonical HRF implementation for both word-density and acoustic-envelope convolution. No HRF parameter search is allowed.

For the primary reliability coefficient, separately residualize the target participant RDM and the leave-one-participant-out reference RDM against the same nuisance design (intercept plus the three nuisance vectors), then compute Pearson correlation between the two residual vectors.

Raw, non-residualized RDM correlation is reported only as a sensitivity statistic.

## Leave-one-participant-out reference

For each target participant and story, the reference RDM is the elementwise mean of the other 11 participants' RDMs for that same story. Because the structural audit established identical within-story TR grids, no pairwise missingness estimator or item intersection search is required.

## Participant aggregation and inference

- Compute reliability separately for all 60 stories.
- Aggregate the 60 story coefficients within each participant using unweighted Fisher-z mean, then transform back with tanh.
- Participant is the inferential unit (n=12).
- Report mean, median, number positive, raw-sensitivity mean/median.
- Bootstrap the participant mean with 10,000 resamples, seed 20260827, percentile 95% CI.
- Report exact one-sided sign-flip p-value over the 12 participant aggregate coefficients.

Reliability gate passes only if both:
1. participant mean residual reliability > 0; and
2. bootstrap 95% CI lower bound > 0.

The sign-flip p-value is supportive and does not replace the gate.

## Guardrails

- No semantic/model embeddings are loaded in this stage.
- No ROI/mask threshold search.
- No lag/window/HRF search.
- No participant/story exclusion based on reliability.
- No voxel selection based on SMN4Lang responses.
- No alternate distance metrics after observing the result.
- No result-driven rescue analysis if the gate fails.

If the gate fails, stop the confirmatory SMN4Lang model-transfer path. If it passes, freeze the model-alignment analysis before exposing the existing ChineseEEG-trained E5 lambda=.10 versus text-only lambda=0 contrast.
