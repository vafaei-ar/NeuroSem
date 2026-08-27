#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import mne

ARTICLES = range(5)
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<event_id>-?\d+)$")


def norm(s: str) -> str:
    return str(s).strip().casefold()


def load_canonical(path: Path) -> list[str]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(norm(row["correct_word"]))
    return rows


def event_words(path: Path, article: int) -> list[str]:
    ep = mne.read_epochs(path, preload=False, verbose="ERROR")
    inv = {int(code): label for label, code in ep.event_id.items()}
    out = []
    for code in ep.events[:, 2].tolist():
        label = inv[int(code)]
        m = EVENT_RE.match(label)
        if not m:
            raise RuntimeError(f"unexpected label {label!r}")
        if int(m.group("article")) != article:
            raise RuntimeError(f"article mismatch in {label!r}")
        out.append(norm(m.group("word")))
    return out


def leftmost_embedding(obs: list[str], canon: list[str]) -> list[int] | None:
    idxs = []
    j = 0
    for w in obs:
        while j < len(canon) and canon[j] != w:
            j += 1
        if j >= len(canon):
            return None
        idxs.append(j)
        j += 1
    return idxs


def rightmost_embedding(obs: list[str], canon: list[str]) -> list[int] | None:
    idxs = [None] * len(obs)
    j = len(canon) - 1
    for i in range(len(obs) - 1, -1, -1):
        w = obs[i]
        while j >= 0 and canon[j] != w:
            j -= 1
        if j < 0:
            return None
        idxs[i] = j
        j -= 1
    return [int(x) for x in idxs]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_monotonic_word_alignment_diagnostic/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    canon = {a: load_canonical(root / "prediction" / f"human_prediction_article_{a}.csv") for a in ARTICLES}
    subjects = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name != "prediction")
    rows = []
    for subject in subjects:
        for article in ARTICLES:
            fif = root / subject / f"article_{article}" / "preprocessed_epoch.fif"
            obs = event_words(fif, article)
            left = leftmost_embedding(obs, canon[article])
            right = rightmost_embedding(obs, canon[article])
            full = left is not None and right is not None
            unique = bool(full and left == right)
            n_ambig = ""
            max_width = ""
            first_idx = ""
            last_idx = ""
            if full:
                widths = [r - l for l, r in zip(left, right)]
                n_ambig = sum(w > 0 for w in widths)
                max_width = max(widths) if widths else 0
                first_idx = left[0] + 1 if left else ""
                last_idx = left[-1] + 1 if left else ""
            rows.append({
                "subject": subject,
                "article": article,
                "n_epochs": len(obs),
                "n_canonical_words": len(canon[article]),
                "full_monotonic_subsequence": full,
                "unique_monotonic_mapping": unique,
                "n_ambiguous_positions": n_ambig,
                "max_index_uncertainty": max_width,
                "first_canonical_index_1based": first_idx,
                "last_canonical_index_1based": last_idx,
            })

    fields = list(rows[0].keys()) if rows else []
    with (out / "alignment_diagnostic.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    n_files = len(rows)
    n_full = sum(r["full_monotonic_subsequence"] for r in rows)
    n_unique = sum(r["unique_monotonic_mapping"] for r in rows)
    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "model-blind monotonic alignment of retained FIF event-word sequence to published article word sequence",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_files": n_files,
        "n_full_monotonic_subsequence_files": n_full,
        "n_unique_monotonic_mapping_files": n_unique,
        "all_files_full_monotonic_subsequence": n_full == n_files,
        "all_files_unique_monotonic_mapping": n_unique == n_files,
        "mapping_rule": "Event words must appear in published article order. Leftmost and rightmost greedy subsequence embeddings are compared; equality gives a unique exact monotonic item mapping without using EEG amplitudes or model outcomes.",
        "guardrails": [
            "Uses only event labels and published text tables; EEG amplitudes are not loaded.",
            "No participant selection, reliability, RSA, model embedding, or transfer outcome is computed.",
            "No approximate/fuzzy word matching is used."
        ]
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
