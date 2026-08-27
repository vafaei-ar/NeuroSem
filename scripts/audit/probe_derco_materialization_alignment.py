#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

REP_FIF_URL = "https://osf.io/download/65d78b5d47a5b700534100fe/"
PREDICTION_URLS = {
    0: "https://osf.io/download/9yaqp/",
    1: "https://osf.io/download/bfv75/",
    2: "https://osf.io/download/nv2g7/",
    3: "https://osf.io/download/298st/",
    4: "https://osf.io/download/d5k83/",
}
REP_SUBJECT = "RRO98"
REP_ARTICLE = 4


def download(url: str, path: Path, max_attempts: int = 6) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem-DERCo-probe/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r, path.open("wb") as f:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == max_attempts - 1:
                raise
            retry_after = e.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(30.0, 2.0 ** attempt)
            time.sleep(delay)
    raise RuntimeError(f"failed to download {url}")


def csv_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"empty CSV: {path}")
    header = [str(x) for x in rows[0]]
    widths = sorted({len(r) for r in rows[1:]})
    preview_nonempty_counts = []
    for r in rows[1:11]:
        preview_nonempty_counts.append(sum(bool(str(x).strip()) for x in r))
    return {
        "file": path.name,
        "n_rows_including_header": len(rows),
        "n_data_rows": max(0, len(rows) - 1),
        "n_columns_header": len(header),
        "header": header,
        "observed_data_row_widths": widths,
        "first10_nonempty_cell_counts": preview_nonempty_counts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_materialization_alignment_probe/latest"))
    args = ap.parse_args()

    data_root = args.data_root.resolve()
    out = args.output_dir.resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    fif = data_root / REP_SUBJECT / f"article_{REP_ARTICLE}" / "preprocessed_epoch.fif"
    download(REP_FIF_URL, fif)

    prediction_paths = {}
    for article, url in PREDICTION_URLS.items():
        p = data_root / "prediction" / f"human_prediction_article_{article}.csv"
        download(url, p)
        prediction_paths[article] = p
        time.sleep(0.5)

    import mne

    epochs = mne.read_epochs(fif, preload=False, verbose="ERROR")
    metadata_cols = [] if epochs.metadata is None else [str(c) for c in epochs.metadata.columns]
    event_id = {str(k): int(v) for k, v in epochs.event_id.items()}
    n_epochs = len(epochs)
    n_channels = len(epochs.ch_names)
    sfreq = float(epochs.info["sfreq"])
    ch_types = epochs.get_channel_types(unique=False)

    prediction = {str(article): csv_schema(path) for article, path in sorted(prediction_paths.items())}

    likely_token_columns = {}
    for article, rec in prediction.items():
        candidates = []
        for col in rec["header"]:
            low = col.strip().lower()
            if any(key in low for key in ("word", "token", "text", "sentence", "target", "item")):
                candidates.append(col)
        likely_token_columns[article] = candidates

    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "prospective targeted materialization and alignment-format probe",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "representative_subject": REP_SUBJECT,
        "representative_article": REP_ARTICLE,
        "representative_fif": {
            "local_relative_path": str(fif.relative_to(Path.cwd())) if Path.cwd() in fif.parents else str(fif),
            "size_bytes": fif.stat().st_size,
            "n_epochs": n_epochs,
            "n_channels": n_channels,
            "sfreq_hz": sfreq,
            "tmin_s": float(epochs.tmin),
            "tmax_s": float(epochs.tmax),
            "channel_names": [str(x) for x in epochs.ch_names],
            "channel_types": ch_types,
            "event_id": event_id,
            "metadata_columns": metadata_cols,
            "selection_length": int(len(epochs.selection)),
            "drop_log_length": int(len(epochs.drop_log)),
        },
        "prediction_csvs": prediction,
        "likely_linguistic_item_columns": likely_token_columns,
        "ready_for_exact_item_mapping_freeze": bool(n_epochs > 0 and n_channels >= 16 and any(likely_token_columns.values())),
        "guardrails": [
            "Only one representative public preprocessed EEG FIF is downloaded and structurally inspected.",
            "All five public prediction CSVs are downloaded only to inspect schema and row counts.",
            "No EEG samples are analyzed for reliability, semantic alignment, or model transfer.",
            "No participant, article, time window, channel set, linguistic column, or model is selected from NeuroSem outcomes.",
            "If exact linguistic item identity cannot be frozen from public metadata, DERCo will be declared infeasible for the planned transfer test rather than redefining the target post hoc."
        ],
    }

    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with (out / "prediction_schema.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["article", "n_data_rows", "n_columns", "header", "likely_item_columns"])
        w.writeheader()
        for article, rec in prediction.items():
            w.writerow({
                "article": article,
                "n_data_rows": rec["n_data_rows"],
                "n_columns": rec["n_columns_header"],
                "header": " | ".join(rec["header"]),
                "likely_item_columns": " | ".join(likely_token_columns[article]),
            })

    print(json.dumps({
        "status": "ok",
        "n_epochs": n_epochs,
        "n_channels": n_channels,
        "sfreq_hz": sfreq,
        "metadata_columns": metadata_cols,
        "ready_for_exact_item_mapping_freeze": summary["ready_for_exact_item_mapping_freeze"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
