# Garnett Dream Validation Protocol v1

**Frozen:** 2026-08-26

## Purpose

Test whether the reading-related neural geometry established in ChineseEEG *The Little Prince* generalizes to a different narrative, *Garnett Dream*, in the same participant/acquisition family.

This is a **same-participant / new-text validation**, not an independent-cohort replication.

## Prospective status

This protocol is frozen before examining Garnett Dream neural-reliability, neural-model RSA, or model-transfer outcomes.

Structural/file-format diagnostics are allowed only when they are model-blind and outcome-blind. They may determine how to locate, align, and segment the data, but they may not change the primary representation or inferential target based on observed effects.

## Primary EEG representation

Use the Little Prince primary representation unchanged:

- for each linguistic item, average EEG over time separately within each retained channel;
- do **not** average across channels;
- feature-wise z-score across items before constructing the neural RDM;
- use correlation distance to form the neural RDM.

This is `row_mean_all` in current NeuroSem terminology.

## Analysis unit

Use the most directly corresponding textual unit available from the Garnett Dream acquisition files, resolved model-blind from event/stimulus metadata.

The unit must be frozen before any neural-reliability or model-alignment outcome is computed. If the acquisition provides multiple plausible linguistic units, choose the one that most directly matches the Little Prince pipeline based on file semantics and event structure, not on outcome magnitude.

## Participant cohort

Start from the ChineseEEG participants who have the required Garnett Dream EEG and stimulus/event metadata.

Participant exclusions must be based only on prospective structural/signal-QC criteria needed to construct the frozen representation. Do not exclude participants because their reliability or neural-model RSA is unfavorable.

Because Garnett Dream uses the same participant pool as Little Prince, participant overlap must be stated explicitly in all manuscript text.

## Nuisance controls

Carry forward the Little Prince nuisance-control philosophy and use only predeclared, stimulus-derived nuisance structure available for the Garnett Dream analysis unit.

Primary nuisance family:

1. within-text item/order difference;
2. text-length difference appropriate to the frozen item unit;
3. punctuation-count difference;
4. lexical-overlap/Jaccard distance using deterministic tokenization appropriate to Chinese text.

If eye-tracking nuisance terms were part of the exact Little Prince analysis being replicated and are structurally available at the frozen Garnett Dream unit, retain them using the same definitions. If they are unavailable or not unit-compatible, document that difference before outcome analysis rather than replacing them post hoc.

### Model-blind reliability-stage clarification (frozen before Garnett EEG outcomes)

The completed Garnett structural/materialization audits established the presentation unit as the ordered `ROWS -> ROWE` pair within each chapter, but did **not** establish an exact mapping from every presentation row to its public novel text. This was learned before any Garnett EEG reliability or neural-model result was computed.

A direct check of the current Little Prince reliability implementation shows that its nuisance family is: run-position difference, duration difference, character-count difference, chapter-identity difference, character-set Jaccard distance, and punctuation-count difference. For the Garnett EEG-only reliability stage:

- analyze chapters separately, so chapter identity is constant within each analyzed unit and contributes no informative RDM;
- retain the two nuisance structures available exactly at the frozen Garnett unit without reconstructing missing text: within-chapter row/order difference and presentation-duration difference;
- do **not** invent or approximate text length, punctuation, or lexical-overlap terms from the novel after seeing EEG outcomes;
- report both raw and this reduced-nuisance residualized reliability;
- retain the residualized `row_mean_all` endpoint as the primary reliability gate;
- require an exact presentation-row text mapping to be frozen before any neural-model validation, at which point all applicable text-derived nuisance terms must be restored prospectively.

This clarification is a fidelity correction driven only by model-blind data structure. It does not change the primary EEG representation, participant cohort, item identity, chapter segmentation, or inferential unit.

## Primary validation endpoint

### EEG-only reproducibility

First test whether `row_mean_all` produces positive nuisance-residualized cross-subject neural-geometry reliability in Garnett Dream.

Use leave-one-subject-out reference geometry with participant as the inferential unit. Aggregate across runs/blocks with Fisher-z averaging if the text is split into multiple independently analyzed units.

Report:

- mean and median participant reliability;
- fraction positive;
- participant-bootstrap 95% CI;
- exact sign-flip inference when cohort size permits.

This EEG-only analysis must be completed before model-transfer interpretation.

## Neural-model validation

If the EEG-only geometry is structurally valid and reproducible, evaluate the previously frozen model(s) without Garnett Dream tuning.

The first model-level question is not model selection. It is whether the model representation already designated by the Little Prince/ChineseEEG program shows positive residual RSA with Garnett Dream EEG under the same nuisance-residualization logic.

Any neural-guided versus text-only comparison must reuse the already-trained adapters and predeclared lambda contrast. Garnett Dream may not be used to choose lambda, architecture, layer, pooling rule, text unit, EEG representation, sensor subset, or time window.

## Sensitivity analyses

The pre-existing `row_std_all` and `relative_8bin_all` families may be reported as secondary sensitivities only if they can be constructed without outcome-driven changes.

They must not replace `row_mean_all` as the primary Garnett Dream representation based on observed Garnett Dream results.

## Inference and multiplicity

The primary inferential unit is the participant.

Primary claims:

1. Garnett Dream EEG-only `row_mean_all` reliability;
2. if reliability passes the structural/reproducibility gate, the single prespecified neural-model validation corresponding to the current manuscript claim.

Secondary representations and any additional model arms are descriptive/sensitivity analyses unless separately preregistered before outcome access.

## Guardrails

- No Garnett Dream outcome-driven feature fishing.
- No participant/item exclusion based on favorable RSA or reliability.
- No post-hoc time-window or channel-group optimization.
- No lambda sweep.
- No architecture sweep.
- No claim that Garnett Dream is an independent participant replication.
- If the primary result is weak/null, narrow the text-generalization claim rather than searching for a favorable representation.

## Planned role in the manuscript

Garnett Dream is intended to answer one focused question:

> Does the Little Prince reading-related neural geometry generalize to a substantially different narrative in the same participants and acquisition family?

A positive result strengthens text generalization; a null result limits narrative generalization but does not erase the independent TMNRED and ZuCo evidence.
