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

---

## 2026-08-19: Use ChineseEEG as the primary discovery dataset

**Decision:** Use ChineseEEG as the first discovery dataset. Use SIGNAL as the first controlled validation dataset, ChineseEEG-2 as the cross-modal replication dataset, and the Russian-Spanish directional-word dataset as the cross-language concept-geometry validation dataset.

**Rationale:** ChineseEEG offers the best current combination of semantic richness, multiple participants, high-density EEG, naturalistic text, eye tracking, and word-level alignment. The complementary datasets answer distinct inferential questions rather than repeating the same benchmark.

**Alternatives considered:** Chisco as the discovery dataset; SIGNAL as the discovery dataset; starting with the six-concept directional dataset; beginning with multiple datasets in parallel.

**Consequences:** Engineering should focus first on downloading/auditing ChineseEEG and reproducing its published preprocessing/validation. We should not spend time adapting all candidate datasets before the first residual-semantic-geometry test is established.
