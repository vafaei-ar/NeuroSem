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


def norm(s: object) -> str:
    return str(s).strip().casefold()


def parse_optional_int(x: object) -> int | None:
    s = str(x).strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_fif_metadata_index_semantics/latest"))
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
            if md is None:
                raise RuntimeError(f"missing metadata in {fif}")
            if "word" not in md.columns:
                raise RuntimeError(f"missing word metadata in {fif}")

            inv = {int(code): label for label, code in ep.event_id.items()}
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

            metadata_word = [norm(x) for x in md["word"].tolist()]
            pandas_index = [int(x) for x in md.index.tolist()]
            ordinal0 = list(range(len(md)))
            ordinal1 = list(range(1, len(md) + 1))
            wordid_raw = md["WordID"].tolist() if "WordID" in md.columns else []
            wordid_parsed = [parse_optional_int(x) for x in wordid_raw] if wordid_raw else []
            n_blank_wordid = sum(str(x).strip() == "" for x in wordid_raw) if wordid_raw else len(md)
            n_numeric_wordid = sum(x is not None for x in wordid_parsed) if wordid_parsed else 0

            wordid_exact = bool(wordid_parsed) and all(x is not None for x in wordid_parsed) and event_index == [int(x) for x in wordid_parsed]
            pandas_exact = event_index == pandas_index
            ordinal0_exact = event_index == ordinal0
            ordinal1_exact = event_index == ordinal1

            rows.append({
                "subject": subject,
                "article": article,
                "n_epochs": len(ep),
                "metadata_columns": "|".join(str(c) for c in md.columns),
                "event_article_matches_folder": all(x == article for x in event_article),
                "event_word_matches_metadata_word": event_word == metadata_word,
                "event_suffix_matches_pandas_metadata_index": pandas_exact,
                "event_suffix_matches_retained_ordinal0": ordinal0_exact,
                "event_suffix_matches_retained_ordinal1": ordinal1_exact,
                "event_suffix_matches_numeric_WordID": wordid_exact,
                "n_blank_WordID": n_blank_wordid,
                "n_numeric_WordID": n_numeric_wordid,
                "first_event_suffix": event_index[0] if event_index else "",
                "last_event_suffix": event_index[-1] if event_index else "",
                "first_metadata_index": pandas_index[0] if pandas_index else "",
                "last_metadata_index": pandas_index[-1] if pandas_index else "",
            })

    fields = list(rows[0].keys()) if rows else []
    with (out / "file_diagnostic.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    n_files = len(rows)
    keys = [
        "event_article_matches_folder",
        "event_word_matches_metadata_word",
        "event_suffix_matches_pandas_metadata_index",
        "event_suffix_matches_retained_ordinal0",
        "event_suffix_matches_retained_ordinal1",
        "event_suffix_matches_numeric_WordID",
    ]
    counts = {k: sum(bool(r[k]) for r in rows) for k in keys}
    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "model-blind diagnostic of preserved FIF metadata index semantics",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_subjects": len(subjects),
        "n_files": n_files,
        "pass_counts": counts,
        "total_blank_WordID": sum(int(r["n_blank_WordID"]) for r in rows),
        "total_numeric_WordID": sum(int(r["n_numeric_WordID"]) for r in rows),
        "diagnostic_rule": (
            "Compare the event-label stimulus suffix against metadata DataFrame index, retained-row ordinals, and numeric nonblank WordID; "
            "independently require exact event-word versus metadata-word and article consistency. No EEG amplitudes are loaded."
        ),
        "guardrails": [
            "No reliability, RSA, embedding, transfer, participant selection, or outcome-driven exclusion is computed.",
            "WordID blanks are recorded rather than coerced or imputed.",
            "No fuzzy text matching is used."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
