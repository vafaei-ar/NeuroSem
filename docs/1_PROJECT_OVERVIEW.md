# 1. NeuroSem Project Overview

**Last updated:** 2026-08-30

NeuroSem asks whether reproducible human neural representational geometry can constrain language-model learning in a way that transfers to independent neural measurements.

## Current scientific conclusion

The strongest defensible primary conclusion remains:

> Human language-related neural geometry can provide a transferable relational constraint on language representations. A constraint learned from Chinese natural-reading EEG improves alignment to independent English-reading EEG and prospectively to language-network fMRI in different participants during naturalistic auditory comprehension, but transfer is selective rather than universal and should only be evaluated when the target neural geometry is itself reproducible.

Post-confirmatory work now adds two important qualifications:

1. **Source-modality bidirectionality:** an fMRI-derived relational constraint can transfer back to independent ZuCo EEG within multilingual E5.
2. **Model-family scope:** stable bidirectional transfer is reproduced across multilingual E5-large and E5-base under a common adaptation protocol, but is not universal across MPNet, MiniLM, XLM-R or mBERT.

Thus, the current model-level interpretation is:

> Neural relational supervision is architecture- and direction-dependent. Bidirectional external neural transfer is reproducible within the tested multilingual E5 family, while other multilingual encoders show direction-specific, seed-dependent or negative reverse-transfer effects.

These architecture analyses are post-confirmatory and do not alter the historical status of the original prospective chain.

## Empirical stages

The project separates four empirical questions that must not be conflated:

1. **Target reliability:** does a reproducible neural geometry exist?
2. **Learnability:** can model training move representations toward that geometry?
3. **External transfer:** does the learned perturbation remain detectable in independent neural contexts?
4. **Scope:** across which source modalities, targets and model families does that transfer remain stable?

A separate transcriptomic mechanism question remains unsupported.

## Primary locked positive evidence

- **ChineseEEG Little Prince:** nuisance-residualized cross-participant reliability approximately **0.121** and sealed neural-guided learnability.
- **ZuCo 2.0 normal reading:** reliability **0.06742**, 95% CI **[0.05831,0.07687]**, **17/17** positive. Frozen E5 lambda=.10 minus lambda=0 transfer **+0.0016637**, 95% CI **[+0.0012294,+0.0021452]**, **17/17** positive, one-sided exact sign-flip **p = 7.63e-06**.
- **SMN4Lang fMRI:** model-blind language-network reliability **0.65327**, 95% CI **[0.63945,0.66843]**, **12/12** positive. Frozen E5 transfer **+0.00085250**, 95% CI **[+0.00078966,+0.00091398]**, **12/12** positive, exact one-sided sign-flip **p = 0.00024414**.

## Primary boundaries

- **TMNRED:** weakly reproducible geometry but frozen E5 transfer null, p=.402.
- **Garnett Dream:** reliable same-participant/new-text geometry but transfer null/inconclusive, p=.1016.
- **Directional inner speech:** out-of-task negative/null boundary, delta approximately -0.001786.
- **SMN4Lang MEG:** frozen sensor-level target failed model-blind reliability; no model evaluation was performed.
- **Generic semantic benchmarks:** no stable neural-specific improvement.
- **AHBA:** no confirmatory molecular mechanism.

## Post-confirmatory reverse-direction evidence

The frozen SMN4Lang fMRI-source calibration selected lambda=.01 using source-only validation before any EEG target was read. On independent ZuCo EEG:

- mean delta RSA **+0.00001671**;
- **14/17** positive;
- bootstrap 95% CI approximately **[+0.00001108,+0.00002200]**;
- exact one-sided **p = 0.0001068**.

This supports source-modality bidirectionality within E5. The secondary ChineseEEG run-07 lambda=.01 check was directionally positive but inconclusive.

A post-confirmatory dose-response characterization on ZuCo showed progressively larger effects from lambda=.01 through lambda=1.0. A three-seed ChineseEEG robustness analysis showed that low/intermediate doses are not stable across optimization trajectories; lambda=1.0 alone had positive seed-level mean delta in all three new seeds. See `24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`.

## Post-confirmatory model-family evidence

A common-protocol panel evaluated six multilingual encoders, three seeds and both neural-source directions. All 36 units completed.

### EEG -> fMRI

E5-large, E5-base, multilingual MPNet and multilingual MiniLM were positive in all three seed-level means. mBERT was also positive in all three but smaller. XLM-R was heterogeneous.

### fMRI -> EEG

Only E5-large and E5-base were positive in all three seed-level means. MPNet was approximately null/mixed, MiniLM negative in all three, XLM-R heterogeneous and mBERT negative in all three.

This supports a narrower claim than “sentence embedding models work”:

> Robust bidirectional portability is reproducible across the two tested multilingual E5 variants, whereas other tested multilingual encoders do not reproduce the same bidirectional pattern under the common protocol.

Full exact revisions, seed-level effects, participant counts, confidence intervals and p-values are in `23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`.

## Publication state

The primary paper is now best treated as **evidence-locked with completed post-confirmatory scope analyses**. The next work should be manuscript integration, figure/legend updates, provenance checks and submission readiness, not outcome-driven model or dataset search.

Recommended scientific presentation:

1. ChineseEEG reproducible geometry and learnability.
2. ZuCo independent cross-language EEG transfer.
3. SMN4Lang prospective cross-modal fMRI transfer as the primary capstone.
4. Post-confirmatory E5 source-modality bidirectionality.
5. Post-confirmatory six-model architecture/scope panel.
6. Explicit transfer and reliability boundaries.
7. Generic semantic dissociation and AHBA mechanistic nulls.

## Stopping rules

- Preserve the original prospective chain unchanged.
- Do not promote target-observed lambda choices to prospective status.
- Do not rescue non-E5 architectures with model-specific lambda/layer/pooling searches after the common-protocol panel.
- Do not reopen ZuCo or SMN4Lang fMRI target-side representation/model choices.
- Do not rescue TMNRED or Garnett.
- Do not evaluate models on failed SMN4Lang MEG representations.
- Do not expand MEG or AHBA searches for significance.
- Preserve all nulls, negative effects, heterogeneous seeds and failed reliability gates.

## Read next

- [`3_RESULTS_AND_COMPARISONS.md`](3_RESULTS_AND_COMPARISONS.md)
- [`5_CURRENT_ROADMAP.md`](5_CURRENT_ROADMAP.md)
- [`23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`](23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md)
- [`24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md`](24_NMI_FMRI_TO_CHINESEEEG_MULTISEED_DOSE_RESULT.md)
- [`4_EXPERIMENT_LEDGER.md`](4_EXPERIMENT_LEDGER.md)
