# Manuscript figure generation v1

This stage turns already-locked NeuroSem outputs into manuscript-facing figures and compact tables. It does not rerun scientific analyses or introduce new hypothesis tests.

## Builder

`scripts/paper/build_manuscript_figures_v1.py`

The builder currently generates:

- `fig2_reading_reliability.png` and `.pdf`: participant-level residual LOO neural-geometry reliability for Little Prince, TMNRED, ZuCo 2.0, and Garnett Dream. External-dataset intervals are the already-frozen participant-bootstrap intervals. The historical Little Prince checkpoint is shown without inventing a new confidence interval.
- `fig4_ahba_frozen_molecular_nulls.png` and `.pdf`: all seven prespecified GABA/serotonin/pathway sets and all seven specificity-control cell-type sets, with participant sign-flip p, within-family BH q, and size-matched random-set p shown for every set.
- `table2_reliability_summary.csv`: normalized reliability summary used by Figure 2.
- `table3_ahba_gene_sets.csv`: normalized frozen AHBA gene-set table used by Figure 4.
- `source_manifest.json`: exact local locked-output paths consumed by the builder plus guardrails.

Default output directory:

`outputs/manuscript_figures_v1/latest/`

## Scientific guardrails

The builder must remain presentation-only. It must not select participants, representations, datasets, genes, gene sets, or plotting subsets from manuscript outcomes. It must fail if required locked artifacts are absent rather than silently substituting documentation values.

Little Prince is a historical development checkpoint with no newly created inferential interval. TMNRED, ZuCo, and Garnett intervals come directly from their frozen reliability summaries.

For AHBA, both the primary mechanistic family and the specificity-control family must be shown in full. The figure title and caption must preserve the frozen null conclusion.

## Next figure tranche

After this builder is executed and visually inspected, extend the same source-manifest pattern to:

1. frozen E5 external transfer effects across TMNRED, ZuCo, Garnett, and Nature;
2. exploratory whole-transcriptome PLS/spatial-null visualization and published Wong language panels;
3. the post-hoc mirroring diagnostic as an Extended Data figure unless manuscript space justifies otherwise;
4. provenance and dataset-design tables.
