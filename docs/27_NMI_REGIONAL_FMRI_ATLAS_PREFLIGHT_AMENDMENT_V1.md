# 27. Regional SMN4Lang atlas-preflight amendment v1

**Status:** frozen operational amendment before any regional SMN4Lang BOLD value, regional reliability, model-brain RSA, delta-RSA, or new fMRI-derived AHBA association was inspected.

## Reason for amendment

The original regional-extension protocol required the EvLab `allParcels-language-SN220` NIfTI and a linked ROI-index text file to establish the integer-label mapping. The atlas-only preflight showed that the downloaded text endpoint did not provide a parseable integer-label-to-region mapping. The failure occurred before any neural or model outcome was loaded or computed.

This amendment changes only the atlas metadata source. It does not change the six prespecified language regions, their scientific interpretation, the SMN4Lang pipeline, the model contrast, the reliability rule, the 100-nonconstant-voxel structural threshold, inference, multiplicity correction, DK68 phenotype, AHBA domain, molecular families, nulls, or stopping rules in `docs/26_NMI_REGIONAL_FMRI_AHBA_EXTENSION_V1.md`.

## Frozen EvLab parcel resource and label mapping

Use the public EvLab/Fedorenko group language-parcel image distributed as:

`https://evlab.squarespace.com/s/allParcels-language-SN220.nii`

Freeze the left-hemisphere integer labels exactly as independently documented in the analysis code accompanying Ryskina et al., *Language models align with brain regions that represent concepts across modalities* (COLM 2025), repository commit `c3c331432887fbbae28c250f4852407cd678ccdf`:

| Integer label | Frozen region name |
| ---: | --- |
| 1 | IFGorb |
| 2 | IFG |
| 3 | MFG |
| 4 | AntTemp |
| 5 | PostTemp |
| 6 | AngG |

The preflight must additionally verify from the atlas geometry itself that labels 1-6 have left-hemisphere world-coordinate centroids. If labels 7-12 are present, it must record their centroids and verify that they occupy the right hemisphere. This geometric check is atlas-only and cannot use SMN4Lang BOLD values.

The six-region scientific family therefore remains exactly the same as originally frozen: IFG, IFGorb, MFG, AntTemp, PostTemp and AngG. No region is added, removed, merged, split or redefined.

## Preflight behavior

The corrected atlas-only preflight must:

1. download the public EvLab parcel NIfTI fresh and record its resolved URL and SHA-256;
2. verify that labels 1-6 are present and have left-hemisphere centroids;
3. record all positive integer labels and their voxel counts and world-coordinate centroids;
4. compare only NIfTI shape and affine against a representative SMN4Lang derivative header, without reading BOLD values;
5. verify the volumetric Desikan-Killiany atlas against the already-frozen AHBA DK68 metadata;
6. stop before regional neural outcomes if any frozen atlas/grid/metadata gate fails.

No resampling, interpolation, threshold search, mask optimization or outcome-driven rescue is permitted.

## Evidential status

This is a pre-outcome operational correction to a metadata assumption, not a scientific result and not a change made in response to regional NeuroSem outcomes. The original post-confirmatory status of the regional extension is unchanged.
