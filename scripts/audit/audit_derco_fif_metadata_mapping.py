#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import mne

ARTICLES = range(5)
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")


def norm(s: str) -> str:
    return str(s).strip().casefold()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_fif_metadata_mapping_audit/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    subjects = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name != "prediction")
    rows = []

    for subject in subjects:
        for article in ARTICLES:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            md = ep.metadata
            inv = {int(code): label for label, code in ep.event_id.items()}

            metadata_present = md is not None
            required_cols = {"index", "word"}
            columns = list(md.columns) if md is not None else []
            required_present = metadata_present and required_cols.issubset(set(columns))

            n_epochs = len(ep)
            n_rows = len(md) if md is not None else 0
            event_matches_metadata = False
            article_matches = False
            monotonic_unique_index = False
            event_word_matches_metadata = False
            min_index = None
            max_index = None

            if required_present and n_rows == n_epochs:
                meta_index = [int(x) for x in md["index"].tolist()]
                meta_word = [norm(x) for x in md["word"].tolist()]

                event_index = []
                event_word = []
                event_article = []
                for code in ep.events[:, 2].tolist():
                    label = inv[int(code)]
                    m = EVENT_RE.match(label)
                    if not m:
                        raise RuntimeError(f"unexpected event label {label!r} in {fif}")
                    event_index.append(int(m.group("stim_index")))
                    event_word.append(norm(m.group("word")))
                    event_article.append(int(m.group("article")))

                event_matches_metadata = event_index == meta_index
                article_matches = all(x == article for x in event_article)
                event_word_matches_metadata = event_word == meta_word
                monotonic_unique_index = len(set(meta_index)) == len(meta_index) and all(
                    b > a for a, b in zip(meta_index, meta_index[1:])
                )
                if meta_index:
                    min_index = min(meta_index)
                    max_index = max(meta_index)

            rows.append({
                "subject": subject,
                "article": article,
                "n_epochs": n_epochs,
                "metadata_present": metadata_present,
                "required_columns_present": required_present,
                "metadata_columns": "|".join(columns),
                "metadata_rows_match_epochs": n_rows == n_epochs,
                "event_suffix_matches_metadata_index": event_matches_metadata,
                "event_article_matches_folder": article_matches,
                "event_word_matches_metadata_word": event_word_matches_metadata,
                "metadata_index_strictly_monotonic_unique": monotonic_unique_index,
                "min_metadata_index": min_index,
                "max_metadata_index": max_index,
            })

    fields = list(rows[0].keys()) if rows else []
    with (out / "file_audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    n_files = len(rows)
    checks = [
        "metadata_present",
        "required_columns_present",
        "metadata_rows_match_epochs",
        "event_suffix_matches_metadata_index",
        "event_article_matches_folder",
        "event_word_matches_metadata_word",
        "metadata_index_strictly_monotonic_unique",
    ]
    counts = {k: sum(bool(r[k]) for r in rows) for k in checks}
    all_pass = all(counts[k] == n_files for k in checks)

    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "model-blind audit of authoritative preprocessed FIF metadata against DERCo event labels",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_subjects": len(subjects),
        "n_files": n_files,
        "pass_counts": counts,
        "all_files_pass_authoritative_mapping_gate": all_pass,
        "mapping_rule": (
            "Use preprocessed FIF metadata created by DERCo's own preprocessing pipeline. "
            "Require metadata columns index and word; one metadata row per retained epoch; "
            "event-label stimulus suffix exactly equals metadata index; event word exactly equals metadata word; "
            "article id matches folder; retained metadata indices are unique and strictly increasing."
        ),
        "guardrails": [
            "Uses only FIF event labels and attached metadata; EEG amplitudes are not loaded.",
            "No reconstruction from behavioural prediction tables is used for item identity.",
            "No participant selection, reliability, RSA, model embedding, or transfer outcome is computed.",
            "No fuzzy matching or outcome-driven exclusion is used."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
