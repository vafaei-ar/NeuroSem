# Project Plan

## Milestone 1. Go/No-Go: Residual Neural Semantic Geometry

Objective: establish whether neural responses contain reproducible semantic relational structure after nuisance control.

Work packages:

1. Verify and rank candidate datasets.
2. Select one primary dataset and reproduce published preprocessing/validation.
3. Extract neural and language representations.
4. Construct semantic and nuisance RDMs.
5. Run partial RSA / variance partitioning.
6. Run permutation and temporal-confound controls.
7. Test leave-one-subject-out generalization.
8. Decide whether the evidence supports moving to model tuning.

Deliverables:

- audited dataset card;
- reproducible preprocessing pipeline;
- first neural/model geometry figures;
- residual-semantic-effect table;
- written go/no-go decision.

## Milestone 2. Cross-dataset and cross-language replication

Objective: determine whether the signal generalizes beyond the discovery dataset.

Priority analyses:

- controlled semantic validation using SIGNAL or comparable data;
- cross-language validation using Russian-Spanish matched concepts;
- dense imagined-speech replication using Chisco;
- cross-modality replication where paired reading/listening data exist.

## Milestone 3. Neural-guided language-model tuning

Objective: test whether biological residual geometry provides useful supervision beyond language-only targets.

Requirements before starting:

- Milestone 1 passes;
- at least one meaningful replication from Milestone 2;
- tuning controls and evaluation benchmarks frozen in advance.

Initial model strategy:

- open model in approximately the 1B-8B parameter range;
- LoRA/adapters before full fine-tuning;
- several geometry-alignment objectives benchmarked under equal compute budgets.

## Milestone 4. External semantic and neural evaluation

Objective: determine whether tuning generalizes to stimuli and data not used for neural supervision.

Evaluation axes:

- unseen text;
- held-out semantic domains;
- cross-language semantic retrieval;
- unseen participants;
- independent neural dataset;
- independent neural modality where feasible.

## Milestone 5. Manuscript and public release

Deliverables:

- frozen analysis repository/tag;
- reproducible figure-generation scripts;
- manuscript;
- dataset provenance and licensing table;
- model/configuration cards;
- reusable semantic-geometry evaluation toolkit if justified by results.

## Collaboration workflow

Use issues for discrete scientific/technical tasks and pull requests for analysis changes. Major methodological decisions should be documented in `docs/decisions.md` with date, rationale, alternatives considered, and consequences.

Do not commit raw neural datasets or large checkpoints. Store only scripts, configurations, provenance metadata, small derived summaries, and publication-ready outputs that licenses permit.
