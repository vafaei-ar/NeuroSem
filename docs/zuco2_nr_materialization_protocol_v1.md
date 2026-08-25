# ZuCo 2.0 Task 1 Normal Reading materialization protocol v1

Status: frozen after model-blind OSF inventory and representative-format/event probes, before full-cohort EEG reliability outcomes.

## Dataset and cohort target

Use ZuCo 2.0 OSF node `2urht`, Task 1 normal reading, preprocessed EEG files only. Target all participants with all seven NR runs available in the public preprocessed tree.

## Sentence extraction mapping

The representative YDG NR1 probe established a continuous EEGLAB recording at 500 Hz with 105 channels. Sentence events form exactly 50 ordered start/end pairs after excluding run-level and auxiliary triggers:

- ordinary sentence: type 10 start, type 11 end
- question-associated sentence: type 12 start, type 13 end

In YDG NR1 these yield 42 ordinary plus 8 question-associated sentences, matching the shared 50-sentence NR1 stimulus structure. Type 15 is treated as an auxiliary post-sentence/question trigger and is not a sentence boundary. Type 90 and 20 are run-level boundary triggers.

For each run, sentence order is the semantic item identity. Shared expected sentence counts are frozen as NR1=50, NR2=50, NR3=51, NR4=50, NR5=50, NR6=49, NR7=49, total 349.

## Materialization/QC rules

The full-cohort materialization step may inspect file structure, metadata, and event trigger values/latencies but must not compute EEG representational reliability, model embeddings, or neural-model RSA.

A run is structurally ready only if:

1. the preprocessed EEG file is a readable MATLAB v7.3/HDF5 EEGLAB file;
2. the EEG data array is continuous (2-D) and metadata provide positive sampling rate, channel count, and point count;
3. event records can be decoded deterministically;
4. after retaining sentence-boundary triggers only, the sequence decomposes entirely into ordered 10/11 or 12/13 pairs;
5. the number of sentence pairs equals the frozen run-specific shared sentence count;
6. sentence starts and ends are strictly ordered, in bounds, and each start precedes its matching end.

The primary reliability cohort will require all seven runs to pass these structural rules. No participant may be excluded based on EEG reliability magnitude or any language-model quantity.

## Guardrail

This protocol freezes only materialization, event mapping, sentence identity, and cohort readiness. EEG representation choice, preprocessing of signal values, nuisance control, and reliability inference will be frozen separately before examining reliability outcomes.
