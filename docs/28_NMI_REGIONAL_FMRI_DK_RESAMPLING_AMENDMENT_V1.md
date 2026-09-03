# 28. Regional SMN4Lang DK-grid resampling amendment v1

**Status:** frozen technical amendment after the atlas-only preflight and before any regional SMN4Lang BOLD value, regional reliability, model-brain RSA, delta-RSA, or new fMRI-derived AHBA association was inspected.

## Reason for amendment

The completed atlas-only preflight established that the EvLab language parcels exactly match the SMN4Lang MNI derivative grid and that the frozen left-language labels are geometrically valid. The same preflight established that the standard volumetric Desikan-Killiany atlas returned by the pinned `abagen` environment does not have an identical voxel grid to the SMN4Lang MNI derivatives, although its 68 cortical parcel identities and the frozen AHBA metadata remain valid.

The original protocol required an exact grid match and therefore correctly blocked the DK stage before any neural or model outcome was read. This amendment freezes a deterministic, outcome-blind spatial harmonization rule so the already-prespecified DK68 phenotype can be represented on the fixed SMN4Lang grid.

This amendment does not change the Desikan-Killiany atlas, parcel identities, hemisphere assignments, AHBA expression preparation, 34-parcel left-hemisphere molecular domain, six language parcels, model contrast, nuisance model, reliability gate, 100-nonconstant-voxel threshold, inference, multiplicity correction, molecular families, nulls, or stopping rules in `docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md`.

## Frozen resampling rule

Use the standard volumetric Desikan-Killiany label image returned by `abagen.fetch_desikan_killiany(surface=False)` as the source atlas.

Resample that discrete label image into the representative SMN4Lang MNI grid defined by the first three dimensions and affine of:

`derivatives/preprocessed_data/sub-01/MNI/sub-01_task-RDR_run-1_bold.nii.gz`

The transformation is fixed as follows:

- implementation: `nibabel.processing.resample_from_to`;
- target: `(SMN4Lang_shape_xyz, SMN4Lang_affine)`;
- interpolation order: `0` (nearest-neighbor) because the image contains categorical integer parcel labels;
- outside-source fill value: `0`;
- no smoothing, dilation, erosion, interpolation-order search, thresholding, registration optimization or outcome-dependent adjustment;
- preserve the original integer parcel IDs exactly.

The source DK image and the resampled DK image must both be hashed and their shape/affine metadata recorded.

## Frozen atlas-integrity gates after resampling

Before any regional neural analysis, the preflight must verify all of the following:

1. the resampled DK image exactly matches the SMN4Lang target shape and affine;
2. every one of the 68 cortical parcel IDs in the frozen AHBA DK metadata is present in the resampled label image;
3. no cortical parcel ID is remapped or renamed;
4. the 68 metadata rows remain exactly 34 left and 34 right hemisphere parcels;
5. DK ID/name/hemisphere agreement with the frozen AHBA expression bundle remains exact;
6. every left-hemisphere DK parcel satisfies the already-frozen minimum atlas voxel-count gate of 100 voxels after resampling;
7. voxel counts and world-coordinate centroids before and after resampling are recorded for audit, but are not used to optimize the transformation.

If any of these gates fails, the DK stage remains blocked. No alternative atlas, resampling method or interpolation order may be selected after inspecting regional neural outcomes.

## Language-parcel status

The EvLab language parcels already exactly match the SMN4Lang grid and therefore are not resampled. Their label mapping and geometric checks remain exactly as frozen in `docs/27_NMI_REGIONAL_FMRI_ATLAS_PREFLIGHT_AMENDMENT_V1.md`.

## Evidential status

This is a technical amendment made in response to an atlas-grid incompatibility detected by an explicitly model-blind preflight. No regional BOLD value, reliability estimate, model-brain RSA, delta-RSA or new AHBA association was inspected before this rule was frozen. The regional extension remains post-confirmatory and outcome-blind with respect to all scientific regional results.
