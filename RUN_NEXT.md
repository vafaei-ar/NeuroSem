# Run Next: ChineseEEG Download and Structural Audit

This is the immediate NeuroSem execution step. Do not start model training yet.

## 1. Clone and enter the repository

```bash
git clone https://github.com/vafaei-ar/NeuroSem.git
cd NeuroSem
git pull
```

## 2. Download ChineseEEG

The repository includes `scripts/download/download_chineseeeg.sh`.

```bash
bash scripts/download/download_chineseeeg.sh
```

Default destination:

```text
data/raw/chineseeeg
```

If OpenNeuro/DataLad initially retrieves only annex metadata, enter the dataset and retrieve the content needed for the first audit. For the complete local copy:

```bash
cd data/raw/chineseeeg
datalad get -r .
cd ../../..
```

If the full dataset is too large for the available disk, stop before selectively retrieving files and report the output of:

```bash
du -sh data/raw/chineseeeg
find data/raw/chineseeeg -maxdepth 3 -type f | head -100
```

We will then define a minimal retrieval subset instead of guessing.

## 3. Run the structural/metadata audit

No additional Python package is required for this first audit.

```bash
python scripts/audit/audit_chineseeeg.py \
  data/raw/chineseeeg \
  --output-dir outputs/chineseeeg_audit \
  --make-zip
```

Do **not** add `--hash-large-files` on the first run. It is unnecessary and may take substantial time.

The script does not load EEG samples. It inventories the BIDS tree and produces small metadata summaries.

## 4. Return the audit archive

The command prints a path similar to:

```text
outputs/chineseeeg_audit/YYYYMMDD_HHMMSS.zip
```

Upload that ZIP to the project conversation. It should contain only:

- `manifest.json`
- `file_inventory.csv`
- `events_summary.json`
- `channels_summary.json`
- `eeg_json_summary.json`
- `participants_copy.tsv` if present
- `report.md`

No raw EEG samples are included.

## 5. What happens after the audit

The audit determines the real subject/run/event structure and exact stimulus columns in the local data. Based on those outputs, the next commit will define:

1. the exact analysis unit (character, word, phrase, or sentence event);
2. discovery subjects/runs and exclusions;
3. temporal epoch definitions;
4. stimulus-to-text mapping;
5. nuisance RDM construction;
6. a preprocessing reproduction script tied to the actual files;
7. the first frozen Phase-1 analysis configuration.

The dataset documentation is not a substitute for this local audit. We need to verify the files actually downloaded before writing analysis code around assumed BIDS paths or event fields.
