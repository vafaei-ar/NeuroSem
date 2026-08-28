# SMN4Lang MEG model-blind format and materialization probe

**Status:** frozen before any SMN4Lang MEG neural reliability or model outcome

**Date frozen:** 2026-08-28

## Purpose

The completed SMN4Lang fMRI arm established a positive prospective cross-modal transfer result. The original SMN4Lang prospective protocol specified a conditional secondary MEG arm only after the fMRI analysis was complete and scientifically informative. This document freezes the first MEG step before any MEG neural-geometry or model comparison is computed.

The immediate question is structural, not inferential:

> Which released preprocessed MEG derivative, channel structure, sampling/timebase, and story/run mapping can support one participant-comparable model-blind neural representation without outcome-driven choice?

## Guardrail

This probe must not compute MEG reliability, model RSA, neural-model correspondence, encoding performance, or any lambda=0.10 versus lambda=0 result. It must not load either NeuroSem adapter or any distributed BERT/GPT2/Word2Vec feature.

## Deterministic source selection

1. Use the existing pinned SMN4Lang/OpenNeuro `ds004078` checkout at `data/raw/smn4lang`.
2. Inventory every tracked preprocessed MEG file whose path is under `derivatives/`, contains `preprocessed`, contains `/meg/`, refers to `task-rdr`, and ends in `.fif` or `.tsv`.
3. Materialize exactly one representative preprocessed MEG `.fif`: the lexicographically first qualifying file in the tracked inventory. This rule is fixed before signal inspection and is unrelated to neural outcomes.
4. Materialize same-stem/same-run tracked TSV companions when present.

## Allowed inspection

For the representative FIF, open with MNE using `preload=False` and inspect metadata only:

- subject/run identity from path;
- sampling frequency;
- number of samples and duration;
- first/last sample indices;
- number of channels;
- channel names and MNE channel types;
- per-type channel counts;
- marked bad channels;
- high-pass/low-pass metadata;
- measurement date presence;
- annotations count and annotation description inventory;
- device/head-coordinate metadata availability where exposed without loading signal arrays.

For tracked TSV companions, inspect path, column names, row count, and a schema-safe type/sample summary sufficient to determine whether they contain channel/status or event/timing metadata. Do not use TSV values to select a neural representation by outcome.

## Full-inventory checks

Across all tracked qualifying preprocessed MEG files, report:

- subject IDs represented;
- run IDs represented;
- qualifying file counts by suffix/type;
- per-subject run/file counts;
- git-annex payload-size inventory where available;
- whether the expected 12 participants and 60 narrative runs are structurally represented.

## Decision after the probe

Only after this model-blind artifact is inspected may we freeze the MEG neural representation and reliability test. The representation must be chosen from acquisition structure and cross-participant comparability, not from observed model alignment.

The preferred scientific principle is to use one broad, minimally tuned sensor-space representation and one fixed language-event/time mapping. No latency, frequency-band, sensor-subset, source-localization, denoising, or representation search is allowed after MEG outcomes become visible.

If the released derivative cannot support a participant-comparable representation without substantial arbitrary choices, stop the MEG arm rather than optimize around the problem.

## Relationship to the final model test

If and only if the separately frozen MEG reliability gate passes, the sole confirmatory model contrast remains the already established ChineseEEG-trained multilingual-E5 `lambda=0.10` neural-guided adapter versus the matched `lambda=0` text-only adapter. No SMN4Lang model training or tuning is allowed.
