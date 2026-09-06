# NMI Remaining Regional Ideas v1

Status: frozen before execution. Analysis stage: post-confirmatory extension.

## Purpose

Test the four remaining reviewer-facing ideas using only already-trained adapters and previously frozen SMN4Lang, ZuCo and STS pipelines:

1. dose x cortical-system interaction,
2. language enrichment across the fixed six-model backbone panel,
3. cross-condition EEG-fMRI coupling,
4. semantic-cost versus cortical-specificity trade-off.

No new model training, dose search, ROI search, target-side tuning, rescue analysis or subject exclusion is permitted.

## Frozen regional systems

Functional language: IFG, IFGorb, MFG, AntTemp, PostTemp, AngG.

Left sensorimotor controls: precentral, postcentral, paracentral.

Left visual controls: pericalcarine, cuneus, lingual, lateraloccipital.

Pooled control is the unweighted mean across the seven fixed sensorimotor and visual parcels. Language specificity for participant s and condition c is

`mean_delta(language) - mean_delta(pooled control)`.

Temporal language is AntTemp + PostTemp. Frontal language is IFG + IFGorb + MFG. AngG remains outside the temporal-frontal contrast.

## Dose analysis

Use the already-trained ChineseEEG multilingual-E5 grid lambda = 0.01, 0.03, 0.10, 0.30, 1.00. Reuse the existing lambda=.10 regional result exactly; evaluate only the four missing nonzero doses on the same selected regions.

For each dose report participant-level mean delta RSA for language, sensorimotor and visual systems, plus language specificity. The five dose-specific language-specificity tests form one exact max-|mean| sign-flip family. Bootstrap 95% CIs use 10,000 participant resamples with seed 20260906.

The focal dose-interaction test is the participant-level difference in language specificity between lambda=1.00 and lambda=0.10. This is two-sided exact sign-flip inference and is interpreted as a post-confirmatory interaction, not a prospective dose optimum test.

## Backbone analysis

Use the fixed panel and seeds from the completed bidirectional model-family experiment:

- e5_large
- e5_base
- multilingual_mpnet
- multilingual_minilm
- xlmr_base
- mbert

Seeds: 20260829, 20260830, 20260831.

Use only the already-trained EEG-to-fMRI text and neural arms at lambda=.10. For each model x seed, evaluate the same 13 selected SMN4Lang regions and also evaluate the same adapters on the frozen independent ZuCo EEG target. Do not retrain any arm.

For each model, average language specificity across the three fixed seeds. For participant-level inference, first average each participant's language-specificity contrast across the three seeds, then test the six fixed model contrasts in one exact max-|mean| family. Model-class summaries remain descriptive because the six backbones are a fixed panel rather than a random sample from an architecture population.

## Cross-modal coupling

Dose coupling: across the five nonzero E5 doses, compute descriptive Spearman correlations between independent ZuCo mean delta RSA and fMRI language specificity. No p-value is used because n=5 fixed dose conditions.

Backbone coupling: average each model over the three fixed seeds, then compute descriptive Spearman correlations across the six models between ZuCo mean delta RSA and (a) fMRI language mean delta and (b) fMRI language specificity. These are condition-level descriptive associations, not subject-level inference.

## Semantic-cost versus specificity

Across the five fixed nonzero E5 doses, correlate the already-observed STS change versus lambda=0 with fMRI language specificity using descriptive Spearman rho. Plot the full five-point trajectory. No new semantic dataset or semantic tuning is allowed.

## Multiplicity and interpretation

- Five dose-specific language-specificity tests share one exact max-stat family.
- Six model-specific participant-averaged language-specificity tests share one exact max-stat family.
- The lambda=1 versus lambda=.10 difference-in-differences is the single focal dose-interaction test.
- Condition-level Spearman analyses are explicitly descriptive.
- All results are post-confirmatory and must be reported whether positive, null or directionally opposite.

## Required outputs

- summary.json
- report.txt
- regional_participant_results.csv
- participant_system_results.csv
- dose_system_summary.csv
- model_seed_enrichment_summary.csv
- model_backbone_enrichment_summary.csv
- model_family_zuco_participant_results.csv
- dose/system figure
- backbone-enrichment figure
- cross-modal coupling figure
- semantic-cost/specificity figure
