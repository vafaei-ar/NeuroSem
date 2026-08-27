#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import mne

ARTICLES = list(range(5))
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<event_index>-?\d+)$")
OFFSETS = list(range(-3, 4))


def load_word_maps(pred_root: Path) -> dict[int, dict[int, str]]:
    maps: dict[int, dict[int, str]] = {}
    pat = re.compile(r"^topic-(?P<article>\d+)-(?P<idx>\d+)$")
    for article in ARTICLES:
        p = pred_root / f"human_prediction_article_{article}.csv"
        out: dict[int, str] = {}
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                wid = str(row["word_id"]).strip()
                word = str(row["correct_word"]).strip()
                m = pat.match(wid)
                if not m or int(m.group("article")) != article:
                    raise RuntimeError(f"unexpected word_id {wid!r} in article {article}")
                idx = int(m.group("idx"))
                prior = out.get(idx)
                if prior is not None and prior.casefold() != word.casefold():
                    raise RuntimeError(f"inconsistent word for {wid}")
                out[idx] = word
        maps[article] = out
    return maps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_event_index_offset_diagnostic/latest"))
    args = ap.parse_args()
    root = args.data_root.resolve()
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    maps = load_word_maps(root / "prediction")

    rows = []
    files = sorted(root.glob("*/article_*/preprocessed_epoch.fif"))
    if len(files) != 110:
        raise RuntimeError(f"expected 110 already-materialized FIFs, found {len(files)}")

    exact_files = 0
    ambiguous_files = 0
    for p in files:
        subject = p.parent.parent.name
        article = int(p.parent.name.split("_")[-1])
        epochs = mne.read_epochs(p, preload=False, verbose="ERROR")
        inv_event = {int(code): label for label, code in epochs.event_id.items()}
        parsed = []
        for code in epochs.events[:, 2].tolist():
            label = inv_event[int(code)]
            m = EVENT_RE.match(label)
            if not m:
                raise RuntimeError(f"unexpected label {label!r}")
            if int(m.group("article")) != article:
                raise RuntimeError(f"article mismatch {label!r}")
            parsed.append((m.group("word"), int(m.group("event_index"))))

        candidates = []
        for offset in OFFSETS:
            invalid = 0; mismatch = 0; matched = 0
            for word, event_idx in parsed:
                canonical_idx = event_idx + offset
                canonical = maps[article].get(canonical_idx)
                if canonical is None:
                    invalid += 1
                elif canonical.casefold() != word.casefold():
                    mismatch += 1
                else:
                    matched += 1
            candidates.append((invalid, mismatch, -matched, offset, matched))
        candidates.sort()
        best = candidates[0]
        exact_offsets = [c[3] for c in candidates if c[0] == 0 and c[1] == 0]
        exact = len(exact_offsets) == 1
        if exact: exact_files += 1
        if len(exact_offsets) > 1: ambiguous_files += 1
        rows.append({
            "subject": subject,
            "article": article,
            "n_epochs": len(parsed),
            "best_offset": best[3],
            "best_invalid": best[0],
            "best_mismatches": best[1],
            "best_matches": best[4],
            "exact_offsets": "|".join(str(x) for x in exact_offsets),
            "unique_exact_alignment": exact,
        })

    with (out / "offset_diagnostic.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["subject","article","n_epochs","best_offset","best_invalid","best_mismatches","best_matches","exact_offsets","unique_exact_alignment"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

    from collections import Counter
    exact_counter = Counter(str(r["best_offset"]) for r in rows if r["unique_exact_alignment"])
    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "model-blind diagnostic of constant event-index offsets against published article word sequence",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_files": len(rows),
        "offsets_tested": OFFSETS,
        "n_unique_exact_alignment_files": exact_files,
        "n_ambiguous_exact_alignment_files": ambiguous_files,
        "exact_offset_counts": dict(exact_counter),
        "all_files_unique_exact": exact_files == 110,
        "guardrails": [
            "Uses event labels and published text only; EEG amplitudes are not loaded.",
            "Tests only small constant integer offsets prospectively motivated by observed boundary failures.",
            "No participant, representation, model, RSA, reliability, or transfer outcome is evaluated."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
