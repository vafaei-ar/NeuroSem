# ChineseEEG local audit: 2026-08-19

This note records the first verified local inspection of the OpenNeuro ChineseEEG checkout used by NeuroSem.

## Provenance

- OpenNeuro accession: `ds004952`
- Local git/DataLad commit: `cb575fd94f58e8566541573a9a34d6c782efaf81`
- Git describe: `1.2.2`
- Subjects present: `sub-04`, `sub-05`, `sub-06`, `sub-07`, `sub-08`, `sub-09`, `sub-10`, `sub-13`, `sub-14`, `sub-15`
- Structural audit only. No EEG samples were loaded.

## Local checkout state

The OpenNeuro CLI checkout contains the complete repository structure and annex metadata, but no annexed signal objects were materialized locally at the time of audit.

Observed repository state:

- 10 subject directories
- 6,010 metadata/filesystem entries inventoried by the Python audit
- 4,844 annexed files in the working tree
- approximately 748.05 GB logical annexed size
- zero local annex keys
- approximately 91 MB actual local disk use for the OpenNeuro checkout before materializing data objects

This confirms that full recursive retrieval would be wasteful for the first NeuroSem experiment.

## BIDS/event structure

The metadata audit found:

- 1,196 `*_events.tsv` files
- 1,196 `*_channels.tsv` files
- 1,196 `*_eeg.json` files
- raw EEG metadata at 1,000 Hz for 245 runs
- derivative EEG metadata at 256 Hz for 951 run/derivative combinations

The raw-run counts differ slightly among participants, so analyses must use the actual BIDS inventory rather than assume a perfectly rectangular subject-by-run structure.

The event TSV files expose only:

`onset, duration, trial_type, value, sample`

For the filtered derivatives, common trial types include `ROWS`, `ROWE`, `CALE`, `CH01`, and `EYEE`. In a typical GarnettDream run, `ROWS` and `ROWE` dominate and occur as start/end marker pairs. The event table itself does **not** contain semantic text, word, sentence, or stimulus strings.

This is an important design finding: semantic alignment cannot be built from `events.tsv` alone. We must explicitly join the timing markers to the dataset's segmented text/stimulus files or author alignment outputs.

## EEG metadata

The derivative metadata confirm:

- 128 EEG channels
- 256 Hz sampling for the filtered/preprocessed derivatives
- 50 Hz power-line frequency

The raw BIDS EEG metadata report 1,000 Hz acquisition.

## Immediate implications for NeuroSem

1. Do not retrieve all 748 GB.
2. Begin with one subject, one session, and one run to verify signal loading, event timing, text alignment, and preprocessing semantics.
3. Prefer the distributed 0.5-30 Hz derivative for the first computational pilot, because it is already downsampled to 256 Hz and is sufficient for initial time-domain/RSA pipeline validation.
4. Retrieve the corresponding raw run only after the derivative pipeline is verified, for preprocessing reproducibility checks.
5. Before semantic RSA, identify the exact text/stimulus mapping files and define how `ROWS`/`ROWE` events map to highlighted text units.
6. Eye-tracking data should be added after basic EEG/text alignment is verified, then incorporated as nuisance structure rather than ignored.

## Pilot choice

Use `sub-04`, `ses-LittlePrince`, `run-01` as the engineering pilot unless local annex inspection reveals a missing or atypical signal object.

This choice is arbitrary with respect to semantic results. It is intended only to validate I/O and alignment before expanding to all subjects.

## Next checkpoint

Retrieve only the annexed objects matching the selected filtered derivative run and inspect:

- exact annex file names and total byte size;
- MNE readability;
- channel count and sampling frequency;
- recording duration;
- event-marker timing relative to the signal;
- availability and structure of corresponding text/alignment files.

Only after this succeeds should we define the first multi-subject retrieval set.
