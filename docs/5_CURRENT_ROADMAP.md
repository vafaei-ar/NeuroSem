# 5. Current Roadmap

**Last updated:** 2026-09-08

NeuroSem is in a completed-evidence, submission-production phase for the current Nature Machine Intelligence manuscript. The prospective evidential chain and the planned post-confirmatory specificity, robustness, dose, reverse-transfer, model-family, model-space, boundary, regional, and spatial analyses are complete. No outcome-bearing analysis is currently active.

## Current manuscript

The author-review package is **v1.18.2**. Exact external Word filenames, SHA-256 fingerprints, rendered page counts and submission-length checks are recorded in `paper/CURRENT_MANUSCRIPT.md`.

Current title:

> **External transfer of brain-derived relational constraints depends on dose, target and model backbone**

The primary paper remains centered on the frozen ChineseEEG to ZuCo to SMN4Lang chain. Later analyses define scope and limits and do not alter the historical status of the two primary external tests.

## Locked primary evidence

1. ChineseEEG development establishes reproducible natural-reading EEG geometry and model learnability.
2. ZuCo EEG is the first fresh external test of the frozen multilingual-E5 contrast; 17/17 retained participants show positive neural-guided minus text-only transfer.
3. SMN4Lang fMRI is the prospective cross-modal test after a model-blind reliability gate; 12/12 participants show positive transfer.

## Completed scope analyses

The manuscript now includes or dispositions the following post-confirmatory evidence:

- preserved neural item correspondence versus shuffled-neural training;
- a structured non-neural MPNet surrogate, together with the model-space magnitude-mismatch diagnostic;
- participant-by-stimulus sensitivity;
- forward dose characterization and generic STS cost;
- lambda=0.10 and lambda=1 model-space characterization;
- reverse fMRI-to-ZuCo transfer and added optimization seeds;
- a six-model common-protocol panel plus the separately documented legacy mBERT protocol;
- DERCo as a higher-reliability negative-transfer boundary;
- regional and final spatial-validation analyses in SMN4Lang fMRI;
- the failed SMN4Lang MEG reliability gate;
- prespecified AHBA molecular nulls and bounded exploratory sensitivities.

These analyses remain secondary or post-confirmatory exactly as described in the manuscript and provenance records.

## Provenance and shipping state

The final claim-to-source audit verifies the scientifically locked v1.18 evidence against hash-pinned derived artifacts, including the independently replayed ChineseEEG reliability values used in Figure 1 and the structured-surrogate diagnostic. The v1.18.2 manuscript no longer states that a provenance ledger physically accompanies the journal upload. Instead, its AI disclosure points to the versioned provenance-ledger specification and final shipping-audit workflow available through the immutable code snapshot identified under Code availability.

The current provenance contract is `docs/NMI_V118_PROVENANCE_LEDGER_SPEC.md`. The final shipping code is `scripts/audit/audit_nmi_v118_final_shipping_v1.py`, with the safe derived evidence bundle assembled by `scripts/audit/build_nmi_v118_shipping_bundle_v1.py`.

## Stopping rules

- Do not reopen the original ZuCo or SMN4Lang target-side model or representation choices.
- Do not promote a target-observed dose to prospective status.
- Do not perform model-specific rescue searches after the completed model-family panel.
- Do not add datasets, model families, gene sets, parcel subsets, or transcriptomic follow-ups merely to improve the narrative.
- Do not reinterpret the regional result as language-network specificity.
- Preserve nulls, negative effects, heterogeneous seeds, and reliability failures.
- Do not open another outcome-bearing analysis unless an editor or reviewer asks a clearly specified question that requires it.

## Remaining production work

Only submission administration and archival production remain: author order and affiliations, contributions, funding and acknowledgements, competing interests, reporting-summary completion, citation-manager refresh if needed, a final native Microsoft Word save of the submission files if document-property normalization is desired, and final archival release preparation.
