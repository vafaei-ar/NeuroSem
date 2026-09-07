# NeuroSem NMI v1.18 bidirectional provenance ledger specification

## Purpose

The v1.18 provenance ledger is a submission gate, not a narrative audit. It must make every manuscript-relevant empirical claim traceable from manuscript to exact computational evidence and every manuscript-relevant computational output traceable back to an explicit manuscript disposition.

The ledger must distinguish original execution evidence, later reproducibility replays, superseded outputs, recovery jobs, failed jobs, presentation-only rebuilds and unresolved provenance. A claim is not verified merely because a displayed literal currently matches a value found elsewhere.

## Scope

The ledger covers:

1. empirical numerical claims in the abstract, Results, Discussion, figure legends and Extended Data;
2. cohort counts, exclusion rules and reliability gates that condition interpretation of those claims;
3. figure and table values used to support the empirical claims;
4. post-confirmatory robustness, dose, model-family, reverse-transfer, specificity, boundary, regional and spatial results;
5. manuscript-relevant model/protocol identity when two runs use the same model name but different revisions or objectives;
6. every completed or partially completed output family that is scientifically relevant to the manuscript, whether included, omitted, superseded or excluded.

Bibliographic years/page numbers and external-dataset DOI metadata are outside the scientific-result ledger, but analysis parameters that materially define an empirical result must be linked to the corresponding committed protocol/code.

## Claim-to-source ledger

One row per atomic empirical claim/value. Required fields:

- `claim_id`
- `manuscript_version`
- `manuscript_location` (section, paragraph/table/figure)
- `claim_label`
- `reported_value`
- `units_or_scale`
- `inferential_role` (primary, post-confirmatory, sensitivity, boundary, descriptive)
- `source_job_id`
- `source_job_status`
- `source_project_commit`
- `artifact_path`
- `artifact_sha256`
- `field_selector` (exact JSON path or CSV row/column selector)
- `observed_value`
- `comparison_tolerance`
- `cohort_or_item_set`
- `model_or_adapter_identity` where applicable
- `provenance_class`
- `verification_status`
- `notes`

Allowed `provenance_class` values:

- `original_execution`
- `recovery_reusing_verified_outputs`
- `reproducibility_replay`
- `presentation_only_rebuild`
- `legacy_literal_with_verified_source`
- `superseded`

Allowed `verification_status` values:

- `verified`
- `incorrect`
- `unresolved`
- `missing`
- `not_applicable`

## Output-to-manuscript ledger

One row per manuscript-relevant output family or job. Required fields:

- `output_id`
- `job_id`
- `job_status`
- `project_commit`
- `task`
- `artifact_path`
- `artifact_sha256`
- `scientific_role`
- `cohort_or_item_set`
- `model_or_adapter_identity` where applicable
- `manuscript_disposition` (main text, figure, Extended Data, supplement, omitted with reason, superseded)
- `superseded_by` where applicable
- `notes`

## Verification rules

1. **Failed jobs do not support a manuscript claim by status alone.** A value generated before a later implementation failure may be used only if its exact output was preserved, independently hash-identified and explicitly reconciled by a successful recovery or audit. The ledger must state that lineage.
2. **`latest` is not provenance.** A `latest` path may be shown for convenience only when the ledger also records the exact artifact SHA256 and, where available, the timestamped producing path.
3. **Replays are not original runs.** A successful replay may verify a historical value, but the ledger must label it `reproducibility_replay` and must not imply that the replay was the historical producing execution.
4. **Figure literals are insufficient.** Scientific values in a non-demo figure path must be loaded from hash-pinned machine-readable sources or explicitly documented as legacy literals with verified source lineage. The preferred fix is source loading followed by a provenance-linked rebuild.
5. **Cohort identity is part of the claim.** A value is not verified if the numerical value matches but the participant/item cohort differs.
6. **Adapter/model identity is part of the claim.** Model id alone is insufficient. Immutable model revision, training objective/pooling protocol and adapter path/hash must be recorded when materially relevant.
7. **Optimization seeds are descriptive robustness evidence unless a seed-level population analysis was prespecified.** Participant-level inference and seed-level robustness must remain distinct.
8. **Recovery jobs must distinguish reused outputs from newly computed outputs.** No recovery may silently recompute completed endpoints unless the ledger says so.
9. **Every manuscript-relevant output receives a disposition.** Completed negative or boundary results cannot disappear simply because they complicate the story.
10. **A fresh artifact bundle is mandatory.** The submission bundle must contain the ledger and all hash-pinned safe artifacts needed to verify it. A stale historical bundle fails the shipping gate even if the live workstation contains the missing evidence.

## Required reconciliation cases for v1.18

The ledger must explicitly resolve at least the following known cases:

- ChineseEEG raw/residual LOO values 0.220/0.121: historical literal lineage plus `S0YJMCMF` reproducibility replay, exact script hash, nine-subject cohort and input hashes.
- Figure 1 STS values: both frozen task-level C-MTEB summaries, exact eight-task means, builder source path and regenerated Figure 1 hashes.
- Figure 1 terminology and builder lineage: `reserved`, not `sealed`; identify the actual submission builder used.
- Primary ZuCo and SMN4Lang transfer results and their target-reliability gates.
- Forward E5 optimization-seed robustness, including original and three additional seeds.
- DERCo high-reliability negative-transfer boundary.
- MPNet structured non-neural alternative-signal materialization, all surrogate trainings, recovery lineage and six external evaluations.
- MPNet model-space displacement diagnostic relative to seed-matched text-only and genuine-neural arms.
- Shuffled-neural specificity controls.
- The two mBERT protocol families, including immutable revisions, objective/pooling differences and the fact that the common model-family panel does not test ChineseEEG-to-ZuCo.
- Forward dose characterization and generic STS cost.
- Lambda=0.10 and lambda=1.0 model-space perturbation/compression diagnostics.
- Reverse fMRI-to-ZuCo transfer, with wording calibrated to its small magnitude relative to run-to-run variation.
- ZuCo discovery/QC cohort, including structural exclusion of YTL and no outcome-based exclusion.
- Run-07 historical reissues/cohort changes and the final manuscript-dispositioned development evidence.
- Any bit-identical reported deltas arising from different adapter paths, including whether the paths resolve to the same effective weights or to duplicated outputs.
- Any manuscript value previously associated with a failed job.
- Regional and final spatial-validation outputs used in Figure 5, Extended Data figures/tables or the main text.
- Secondary AHBA analyses where they are retained in the manuscript.

## Shipping gate

A v1.18 manuscript may be labeled numerically/provenance verified only when:

- every primary and main-text empirical claim is `verified`;
- no `incorrect`, `unresolved` or `missing` row remains for a claim used to support the paper's central conclusions;
- all Figure 1 scientific values are source-loaded and hash-pinned in the provenance rebuild;
- the MPNet displacement diagnostic has a completed disposition;
- failed/superseded/recovery lineages are explicit;
- the output-to-manuscript reverse ledger has no scientifically relevant output without a disposition;
- the generative-AI disclosure does not claim independent verification beyond what this ledger actually establishes; and
- the distributed artifact bundle is regenerated from the final ledger state rather than reused from an earlier manuscript version.
