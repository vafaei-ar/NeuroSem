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

---

## 2026-08-19: Use displayed rows as the first ChineseEEG alignment unit and exclude chapter-number rows from semantic tests

**Decision:** Treat the run workbook rows as the canonical temporal alignment sequence, preserving one-to-one indices with `ROWS`-`ROWE` EEG segments and the author embedding array. Numeric chapter rows remain in the alignment table but are flagged as structural and excluded from semantic RSA/geometry tests.

**Rationale:** In the validated LittlePrince run-01 pilot, the workbook contains 395 non-empty rows, the BIDS event stream contains 395 well-formed `ROWS`-`ROWE` segments, and the author embedding array contains 395 rows. The four numeric workbook rows are chapter numbers 1-4, matching the four BIDS chapter markers `CH01`-`CH04` in the same order. The first numeric row aligns to a very short 0.367 s row segment, consistent with a one-character displayed item under the experiment's highlighted-character presentation logic. The authors' embedding code also embeds every workbook row from row 2 onward, including numeric chapter rows. Dropping those rows before alignment would shift all subsequent indices and corrupt the mapping.

**Alternatives considered:** Remove chapter rows before alignment; align only text-only rows; infer a separate offset at each chapter boundary; move immediately to character-level alignment.

**Consequences:** The Phase-1 representation table must preserve all workbook/EEG/embedding indices, include an `is_chapter_row`/`semantic_eligible` flag, and exclude chapter rows only at the analysis stage. The first reproducible semantic unit is the displayed row/presentation unit. Character- or word-level analyses require additional timing/eye-tracking justification and will be treated as later sensitivity analyses rather than assumed ground truth.
