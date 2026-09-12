# NMI redesign v2 figure data

These files are safe, de-identified figure-source snapshots committed so the redesigned manuscript figures can be regenerated from a fresh clone.

For Figure 1:

- `figure1_reliability_source.csv` contains sequential-participant residual reliability values for ZuCo and SMN4Lang.
- `figure1_transfer_source.csv` contains sequential-participant text-only, neural-guided, and paired-delta residual RSA values.
- `figure1_seed_source.csv` contains the frozen primary and added optimization-run mean deltas and positive-participant counts.
- `figure1_source_snapshot_manifest.json` records exact RunRelay provenance, the original safe artifact SHA-256 values, original upstream output hashes, frozen headline summaries, and evidential status.

The snapshots originate from completed RunRelay job `4N8R2K7C`, task `build_nmi_figure2_redesign_v1`, exact source commit `0ff001b37f17d91600035cab6c523676d3823d81`.

These files are presentation inputs, not a new analysis dataset. Participant identifiers are not included; indices are sequential only. Do not replace values manually. If a scientific upstream result changes, regenerate and re-provenance the snapshot rather than editing a plotted number.
