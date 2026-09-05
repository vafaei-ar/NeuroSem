# 5. Current Roadmap

**Last updated:** 2026-09-04

NeuroSem is in a **completed evidence / publication-production phase** for the current Nature Machine Intelligence manuscript. The prospective evidential chain is complete. The planned post-confirmatory specificity, participant-by-stimulus, model-space, reverse-direction, dose, model-family, regional fMRI and AHBA analyses are also complete. No outcome-bearing analysis is currently active.

## Current manuscript position

The current author-review master is `NeuroSem_Nature_Manuscript_v1.11_NMI_native_vector_figures.docx`, with `NeuroSem_NMI_Supplementary_Technical_Tables_v1.11_NMI_native_vector_figures.docx` as Supplementary Information. Exact fingerprints are recorded in `paper/CURRENT_MANUSCRIPT.md`.

Current title:

> **External transfer of brain-derived relational constraints depends on dose, target and model backbone**

The primary paper remains centered on the frozen ChineseEEG -> ZuCo -> SMN4Lang chain. Later analyses define scope and limits; they do not alter the historical status of the two primary external tests.

## Locked primary evidence

1. **ChineseEEG development:** reproducible natural-reading EEG geometry and sealed run-07 learnability.
2. **ZuCo EEG:** fresh external test of `lambda=0.10` versus matched `lambda=0`; mean participant delta-RSA **+0.0016637**, **17/17** positive.
3. **SMN4Lang fMRI:** prospectively designated cross-modal target after a model-blind reliability gate; mean participant delta-RSA **+0.0008525**, **12/12** positive.

These results remain the primary evidential chain.

## Completed post-confirmatory scope analyses

### Neural-specificity control

Across three fixed E5 seeds, genuine-neural training outperformed the matched destroyed-item-correspondence shuffled-neural control on both ZuCo and SMN4Lang fMRI. ZuCo shuffled-minus-text was inconsistent around zero; fMRI showed a small positive shuffled-minus-text component. The supported claim is therefore specificity to preserved neural item correspondence relative to this matched destroyed-correspondence objective, not uniqueness relative to every possible structured non-neural target.

### Participant x stimulus robustness

A 10,000-replicate two-factor bootstrap was positive in every replicate for both primary external targets. Reported 95% intervals were approximately **[+0.000996,+0.002476]** for ZuCo and **[+0.000653,+0.001068]** for SMN4Lang fMRI. This is a sensitivity over the observed participants and stimulus units, not unrestricted inference to arbitrary linguistic stimuli.

### Forward ChineseEEG -> external dose characterization

The complete already-trained E5 grid was evaluated after the primary `lambda=0.10` tests under a frozen post-confirmatory protocol.

- ZuCo mean delta-RSA: `+0.000211`, `+0.000477`, `+0.001664`, `+0.008739`, `+0.027599` at `lambda=0.01,0.03,0.10,0.30,1.0`.
- SMN4Lang fMRI mean delta-RSA: `+0.000107`, `+0.000283`, `+0.000852`, `+0.003038`, `-0.000991` over the same doses.
- ZuCo remains positive through `lambda=1.0`; fMRI peaks at `lambda=0.30` and reverses at `lambda=1.0`.
- The already-observed generic STS decrement increases with dose, reaching approximately `-0.03453` at `lambda=1.0`.

Interpretation:

> External transfer magnitude is dose-sensitive and target-dependent. The data do not define one universal target-independent optimum.

### Model-space perturbation

At the prospective `lambda=0.10` dose, E5 remains very close to the text-only representation: corresponding-item cosine `0.99839`, RDM Pearson `0.99792`, RDM Spearman `0.99745`, centered CKA `0.99932`, k=10 neighborhood Jaccard `0.9276`.

At post-confirmatory `lambda=1.0`, restructuring is much larger: corresponding-item cosine `0.94221`, RDM Pearson `0.79653`, RDM Spearman `0.77887`, CKA `0.93766`, k=10 Jaccard `0.5794`.

### Reverse fMRI -> ZuCo transfer

The source-selected primary reverse candidate remains `lambda=0.01`. Its frozen ZuCo result is positive but small. Three additional prespecified optimization seeds also produced positive mean deltas. The full reverse dose curve is subsequent characterization and does not replace the source-selected primary reverse test.

### Six-model common-protocol panel

All 36 model x seed x direction units completed and were retained.

- **E5-large:** 3/3 positive in both directions.
- **E5-base:** 3/3 positive in both directions.
- **MPNet:** 3/3 positive EEG -> fMRI; mixed/approximately null reverse.
- **MiniLM:** 3/3 positive EEG -> fMRI; 3/3 negative reverse.
- **XLM-R:** heterogeneous in both directions.
- **mBERT:** 3/3 positive EEG -> fMRI; 3/3 negative reverse.

The panel establishes model- and direction-dependent portability under one common fixed protocol. It does not isolate an architecture mechanism and does not establish E5 uniqueness.

### Regional SMN4Lang fMRI characterization

All six predefined language parcels passed the model-blind reliability gate and showed positive `lambda=0.10` minus `lambda=0` effects in **12/12** participants; all six survived the frozen six-region max-stat FWER correction.

However, the complete DK68 analysis also showed **positive mean delta-RSA in all 68 parcels with 12/12 positive participants**. The correct interpretation is therefore:

> The displacement is cortex-wide in direction. The predefined language parcels establish within-network effects but do not establish language-network specificity.

Superior temporal parcels are among the larger descriptive effects, but no temporal-versus-nontemporal or language-versus-control contrast was prespecified.

### AHBA mechanistic extension

The prespecified GABAergic, serotonergic and pathway gene-set tests are null under the frozen participant-level and multiplicity-corrected framework. Exploratory whole-transcriptome and hemispheric/mirroring sensitivities do not revise those null conclusions. No specific transcriptomic mechanism is established.

## Boundary evidence that must remain visible

- **TMNRED:** weak reliability, transfer null.
- **Garnett Dream:** modest reliability, transfer inconclusive.
- **Directional inner speech:** out-of-task negative boundary.
- **SMN4Lang MEG:** prospectively frozen representation failed the model-blind reliability gate; no model evaluation was opened.
- **Generic semantic benchmark:** no stable neural-specific advantage.

## Current stopping rules

- Do not reopen the original ZuCo or SMN4Lang target-side model/representation choices.
- Do not promote any target-observed dose to prospective status.
- Do not perform model-specific rescue searches after the completed six-model panel.
- Do not add more model families or neural datasets merely to improve the narrative.
- Do not rescue TMNRED or Garnett.
- Do not evaluate E5 on failed MEG targets or expand the MEG representation family.
- Do not reinterpret the regional result as language-network specificity.
- Do not add gene sets, pathways, parcel subsets or transcriptomic follow-ups from observed AHBA outcomes.
- Preserve all nulls, negative effects, heterogeneous seeds and reliability failures.
- No additional outcome-bearing analysis is required for the current manuscript unless a reviewer/editor asks a clearly specified question.

## Current production tasks

1. Maintain the v1.11 Word manuscript and Supplementary Information as the external author-review masters.
2. Keep `paper/CURRENT_MANUSCRIPT.md` synchronized with each external binary revision using filename + SHA-256.
3. Complete author order/affiliations, contributions, funding/acknowledgements and competing interests.
4. Complete the Nature reporting summary and final citation-manager refresh.
5. Perform a final figure/table/manuscript consistency check without reopening analysis choices.
6. Archive the final code snapshot and reproducibility entry points with a persistent DOI at submission/acceptance as appropriate.

## Key current documents

- `paper/CURRENT_MANUSCRIPT.md`
- `paper/README.md`
- `docs/31_NMI_FORWARD_EXTERNAL_DOSE_CHARACTERIZATION_V1.md`
- `docs/32_NMI_LAMBDA1_MODEL_SPACE_CHARACTERIZATION_V1.md`
- `docs/30_NMI_FMRI_TO_ZUCO_LAMBDA001_MULTISEED_ROBUSTNESS_V1.md`
- `docs/29_NMI_REGIONAL_FMRI_TRANSFER_RESULT_V1.md`
- `docs/25_NMI_REVIEWER_SPECIFICITY_AND_ROBUSTNESS_V1.md`
- `docs/23_NMI_BIDIRECTIONAL_MODEL_FAMILY_PANEL_RESULT.md`
- `paper/FIGURE_GENERATION.md`

The primary scientific work is complete. The opportunity cost of new exploratory analysis now exceeds its expected value for this paper.
