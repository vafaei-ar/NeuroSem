# NeuroSem NMI v1.18.1 submission freeze

This document records the delivery-only freeze that follows the v1.18 scientific and provenance shipping audit. No scientific analysis, model training, model evaluation, neural analysis, dose selection or hypothesis testing is added by v1.18.1.

## Scientific provenance state

- Final v1.18 shipping audit: RunRelay job `K4R8M2V7`, completed with exit 0.
- Scientific claims: 129/129 verified.
- Source hashes: 23/23 verified.
- Unresolved lineages: 0.
- Blocking exceptions: 0.
- Shipping gate: PASS.
- Canonical Figure 1 provenance build: `M4V8K2R6`.
- Canonical Figure 1 source-manifest SHA-256: `42ece521c9f666d9b148cba9da3ecf24e4f2786800e43b91707818ff904201b6`.
- ChineseEEG reliability replay: `S0YJMCMF`, raw LOO `0.22000048082892687`, residual LOO `0.12049445312285981`, n=9.
- Fresh safe-derived provenance bundle SHA-256: `2d24156e75b5c52563ed94c34fe83cfaa5f6a63ff6393da5008216af7b09c3bc`.

## Public-code delivery fixes

The public repository now exposes the provenance-linked Figure 1 path used for the submission:

- `scripts/paper/build_nmi_figure1_provenance_v1.py` binds the reliability replay and frozen C-MTEB summaries to Figure 1 and records exact hashes.
- `scripts/paper/nmi_visualizations_v4/build_figure1_chineseeeg.py` loads reliability and semantic panel values from machine-readable artifacts in the non-demo path.
- `scripts/paper/build_nmi_main_figures_v3_4.py` pins canonical Figure 1 to the completed provenance artifact by exact source-manifest hash.
- `scripts/paper/build_figure1_chineseeeg.py` is a compatibility wrapper and no longer contains outcome-valued scientific literals.
- `paper/figure_data/chineseeeg_development_v1.json` records the independently replayed reliability provenance and cohort metadata.
- `docs/NMI_V118_PROVENANCE_LEDGER_SPEC.md` documents the submission ledger contract.

## v1.18.1 manuscript-only delivery edits

The v1.18.1 manuscript may differ from v1.18 only in delivery/provenance wording:

1. Figure 1b legend explicitly identifies the independently replayed whole-row temporal-mean correlation-distance RDM reliability analysis and distinguishes its n=9 cohort from historical n=10 run-07 summaries.
2. Code Availability points to the immutable public repository commit containing the submission code snapshot.
3. The accompanying provenance package includes the final claim-to-source ledger, source manifest, audit summary/report, empty exception table, and fresh safe-derived artifact bundle.

No reported scientific value, inference or interpretation is changed by these delivery edits.
