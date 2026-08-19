# Scientific and Technical Decisions

Record consequential decisions here so that changes in the analysis are explicit rather than hidden in code history.

For each decision, use:

## YYYY-MM-DD: Decision title

**Decision:** What was chosen.

**Rationale:** Scientific or technical reason.

**Alternatives considered:** Serious alternatives that were rejected.

**Consequences:** What analyses, interpretation, or reproducibility this affects.

---

## 2026-08-19: Require evidence of residual neural semantic geometry before LLM tuning

**Decision:** Treat residual neural semantic geometry and cross-subject generalization as go/no-go criteria before substantive LLM fine-tuning.

**Rationale:** Raw brain-model alignment can reflect shared stimulus, lexical, positional, or temporal structure. Fine-tuning before establishing a brain-specific semantic component would risk optimizing to a confounded target.

**Alternatives considered:** Begin with direct EEG-to-embedding alignment or end-to-end EEG-to-text generation.

**Consequences:** Milestone 1 prioritizes dataset audit, reproducible preprocessing, nuisance-controlled RSA, permutation testing, and generalization. LLM tuning is deferred to a later milestone.
