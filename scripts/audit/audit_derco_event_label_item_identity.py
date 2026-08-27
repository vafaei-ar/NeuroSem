#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import mne

ARTICLES = range(5)
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<stim_index>-?\d+)$")


def norm(s: str) -> str:
    return str(s).strip().casefold()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_event_label_item_identity/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    subjects = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name != "prediction")
    rows = []
    words_by_key: dict[tuple[int, int], set[str]] = defaultdict(set)
    subjects_by_key: dict[tuple[int, int], set[str]] = defaultdict(set)

    for subject in subjects:
        for article in ARTICLES:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            ep = mne.read_epochs(fif, preload=False, verbose="ERROR")
            inv = {int(code): label for label, code in ep.event_id.items()}

            indices = []
            words = []
            article_ok = True
            labels_ok = True
            for code in ep.events[:, 2].tolist():
                label = inv[int(code)]
                m = EVENT_RE.match(label)
                if not m:
                    labels_ok = False
                    continue
                a = int(m.group("article"))
                idx = int(m.group("stim_index"))
                word = norm(m.group("word"))
                article_ok = article_ok and (a == article)
                indices.append(idx)
                words.append(word)
                words_by_key[(a, idx)].add(word)
                subjects_by_key[(a, idx)].add(subject)

            unique = len(indices) == len(set(indices))
            strictly_increasing = all(b > a for a, b in zip(indices, indices[1:]))
            rows.append({
                "subject": subject,
                "article": article,
                "n_epochs": len(ep),
                "all_labels_parse": labels_ok and len(indices) == len(ep),
                "article_matches_folder": article_ok,
                "stimulus_indices_unique": unique,
                "stimulus_indices_strictly_increasing": strictly_increasing,
                "first_stimulus_index": min(indices) if indices else "",
                "last_stimulus_index": max(indices) if indices else "",
            })

    with (out / "file_audit.csv").open("w", encoding="utf-8", newline="") as f:
        fields = list(rows[0].keys()) if rows else []
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    key_rows = []
    for (article, idx), wordset in sorted(words_by_key.items()):
        key_rows.append({
            "article": article,
            "stimulus_index": idx,
            "n_distinct_words": len(wordset),
            "word": sorted(wordset)[0] if len(wordset) == 1 else "|".join(sorted(wordset)),
            "n_subjects_retaining_item": len(subjects_by_key[(article, idx)]),
        })
    with (out / "item_key_audit.csv").open("w", encoding="utf-8", newline="") as f:
        fields = list(key_rows[0].keys()) if key_rows else []
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(key_rows)

    n_files = len(rows)
    all_parse = sum(bool(r["all_labels_parse"]) for r in rows)
    article_match = sum(bool(r["article_matches_folder"]) for r in rows)
    unique = sum(bool(r["stimulus_indices_unique"]) for r in rows)
    increasing = sum(bool(r["stimulus_indices_strictly_increasing"]) for r in rows)
    n_conflicting_keys = sum(len(v) != 1 for v in words_by_key.values())
    gate = (
        all_parse == n_files
        and article_match == n_files
        and unique == n_files
        and increasing == n_files
        and n_conflicting_keys == 0
    )

    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "model-blind audit of event-label-defined participant-independent item identity",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_subjects": len(subjects),
        "n_files": n_files,
        "n_unique_article_stimulus_keys": len(words_by_key),
        "pass_counts": {
            "all_labels_parse": all_parse,
            "article_matches_folder": article_match,
            "stimulus_indices_unique": unique,
            "stimulus_indices_strictly_increasing": increasing,
        },
        "n_conflicting_article_stimulus_word_keys": n_conflicting_keys,
        "all_files_pass_event_label_item_identity_gate": gate,
        "mapping_rule": (
            "Use the retained MNE event label itself as the authoritative item key: "
            "<word>_<article>_<stimulus_index>. Require every label to parse, article id to match the file folder, "
            "stimulus indices to be unique and strictly increasing within each participant/article file, and the same "
            "(article, stimulus_index) key to carry exactly one normalized word across all participants."
        ),
        "guardrails": [
            "Uses only event labels; EEG amplitudes are not loaded.",
            "Attached FIF feature metadata and behavioural prediction tables are not used to define item identity.",
            "No participant selection, reliability, RSA, embedding, transfer outcome, fuzzy matching, or outcome-driven exclusion is computed."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
