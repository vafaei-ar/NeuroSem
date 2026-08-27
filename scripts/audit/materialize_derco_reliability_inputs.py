#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import mne

OSF_NODE = "rkqbu"
OSF_API = f"https://api.osf.io/v2/nodes/{OSF_NODE}/files/"
ARTICLES = list(range(5))
EVENT_RE = re.compile(r"^(?P<word>.+)_(?P<article>\d+)_(?P<word_id>\d+)$")


def get_json(url: str, max_attempts: int = 8) -> dict:
    delay = 1.0
    for attempt in range(max_attempts):
        req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem-DERCo-materialize/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                payload = json.loads(r.read().decode("utf-8"))
            time.sleep(0.5)
            return payload
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt + 1 >= max_attempts:
                raise
            retry_after = e.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else delay
            except Exception:
                wait = delay
            time.sleep(max(wait, delay))
            delay = min(delay * 2.0, 60.0)
    raise RuntimeError("unreachable")


def iter_pages(url: str):
    while url:
        payload = get_json(url)
        for item in payload.get("data", []):
            yield item
        nxt = payload.get("links", {}).get("next")
        url = nxt.get("href") if isinstance(nxt, dict) else nxt


def related_files_url(item: dict) -> str | None:
    rel = item.get("relationships", {}).get("files", {}).get("links", {}).get("related")
    if isinstance(rel, dict):
        return rel.get("href")
    return rel if isinstance(rel, str) else None


def find_named(url: str, name: str) -> dict:
    for item in iter_pages(url):
        if str(item.get("attributes", {}).get("name")) == name:
            return item
    raise FileNotFoundError(name)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem-DERCo-materialize/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, tmp.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def file_download_url(item: dict) -> str:
    url = item.get("links", {}).get("download")
    if not url:
        raise RuntimeError("OSF file missing download URL")
    return str(url)


def canonical_word_map(path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "word_id" not in reader.fieldnames or "correct_word" not in reader.fieldnames:
            raise RuntimeError(f"missing word_id/correct_word in {path}")
        for row in reader:
            wid = int(row["word_id"])
            word = str(row["correct_word"]).strip()
            if not word:
                raise RuntimeError(f"empty correct_word for word_id={wid} in {path}")
            prior = out.get(wid)
            if prior is not None and prior != word:
                raise RuntimeError(f"inconsistent correct_word for article file {path}, word_id={wid}: {prior!r} vs {word!r}")
            out[wid] = word
    if not out:
        raise RuntimeError(f"no canonical words in {path}")
    return out


def parse_event_label(label: str) -> tuple[str, int, int]:
    m = EVENT_RE.match(label)
    if not m:
        raise RuntimeError(f"unexpected DERCo event label: {label}")
    return m.group("word"), int(m.group("article")), int(m.group("word_id"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/derco"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_reliability_input_materialization/latest"))
    args = ap.parse_args()

    data_root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    providers = list(iter_pages(OSF_API))
    osfstorage = None
    for p in providers:
        if str(p.get("attributes", {}).get("provider")) == "osfstorage" or str(p.get("attributes", {}).get("name")) == "osfstorage":
            osfstorage = p
            break
    if osfstorage is None:
        raise RuntimeError("osfstorage provider not found")
    root_url = related_files_url(osfstorage)
    if not root_url:
        raise RuntimeError("osfstorage root missing files URL")

    eeg_exp = find_named(root_url, "EEG-based Reading Experiment")
    beh_exp = find_named(root_url, "Behavioural Word-Prediction Experiment")
    eeg_url = related_files_url(eeg_exp)
    beh_url = related_files_url(beh_exp)
    if not eeg_url or not beh_url:
        raise RuntimeError("DERCo experiment folders malformed")

    eeg_data = find_named(eeg_url, "EEG_data")
    preproc = find_named(related_files_url(eeg_data), "preprocessed")
    preproc_url = related_files_url(preproc)
    pred = find_named(beh_url, "prediction")
    pred_url = related_files_url(pred)
    if not preproc_url or not pred_url:
        raise RuntimeError("DERCo preprocessed/prediction folder malformed")

    word_maps: dict[int, dict[int, str]] = {}
    prediction_files = {}
    for article in ARTICLES:
        name = f"human_prediction_article_{article}.csv"
        item = find_named(pred_url, name)
        path = data_root / "prediction" / name
        download(file_download_url(item), path)
        word_maps[article] = canonical_word_map(path)
        prediction_files[article] = str(path.relative_to(Path.cwd())) if path.is_relative_to(Path.cwd()) else str(path)

    subjects = []
    for item in iter_pages(preproc_url):
        if str(item.get("attributes", {}).get("kind")) == "folder":
            subjects.append((str(item.get("attributes", {}).get("name")), related_files_url(item)))
    subjects = sorted((s, u) for s, u in subjects if s and u)
    if len(subjects) != 22:
        raise RuntimeError(f"expected 22 DERCo preprocessed subjects, found {len(subjects)}")

    inventory_rows = []
    ready_subjects = []
    blockers = []
    for subject, subject_url in subjects:
        subject_ok = True
        for article in ARTICLES:
            try:
                article_item = find_named(subject_url, f"article_{article}")
                article_url = related_files_url(article_item)
                if not article_url:
                    raise RuntimeError("article folder missing files URL")
                fif_item = find_named(article_url, "preprocessed_epoch.fif")
                fif_path = data_root / subject / f"article_{article}" / "preprocessed_epoch.fif"
                download(file_download_url(fif_item), fif_path)
                epochs = mne.read_epochs(fif_path, preload=False, verbose="ERROR")
                if len(epochs.ch_names) != 32 or any(t != "eeg" for t in epochs.get_channel_types()):
                    raise RuntimeError(f"unexpected channel structure for {subject} article {article}")
                if abs(float(epochs.info["sfreq"]) - 1000.0) > 1e-6:
                    raise RuntimeError(f"unexpected sfreq for {subject} article {article}: {epochs.info['sfreq']}")
                if abs(float(epochs.tmin) - (-0.2)) > 1e-6 or abs(float(epochs.tmax) - 1.0) > 1e-6:
                    raise RuntimeError(f"unexpected epoch window for {subject} article {article}: {epochs.tmin}, {epochs.tmax}")
                inv_event = {int(code): label for label, code in epochs.event_id.items()}
                seen_ids = []
                mismatch = 0
                for code in epochs.events[:, 2].tolist():
                    label = inv_event[int(code)]
                    word, art_from_label, wid = parse_event_label(label)
                    if art_from_label != article:
                        raise RuntimeError(f"article mismatch in event label {label}")
                    canonical = word_maps[article].get(wid)
                    if canonical is None:
                        raise RuntimeError(f"word_id {wid} missing from article {article} prediction table")
                    if canonical.casefold() != word.casefold():
                        mismatch += 1
                    seen_ids.append(wid)
                if mismatch:
                    raise RuntimeError(f"{mismatch} event/text word mismatches for {subject} article {article}")
                if len(seen_ids) != len(epochs):
                    raise RuntimeError("epoch/event count mismatch")
                inventory_rows.append({
                    "subject": subject,
                    "article": article,
                    "n_epochs": len(epochs),
                    "n_unique_word_ids": len(set(seen_ids)),
                    "min_word_id": min(seen_ids) if seen_ids else "",
                    "max_word_id": max(seen_ids) if seen_ids else "",
                    "n_channels": len(epochs.ch_names),
                    "sfreq_hz": float(epochs.info["sfreq"]),
                    "tmin_s": float(epochs.tmin),
                    "tmax_s": float(epochs.tmax),
                    "fif_size_bytes": fif_path.stat().st_size,
                    "exact_event_text_match": True,
                })
            except Exception as e:
                subject_ok = False
                blockers.append({"subject": subject, "article": article, "error": f"{type(e).__name__}: {e}"})
        if subject_ok:
            ready_subjects.append(subject)

    with (out / "session_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["subject", "article", "n_epochs", "n_unique_word_ids", "min_word_id", "max_word_id", "n_channels", "sfreq_hz", "tmin_s", "tmax_s", "fif_size_bytes", "exact_event_text_match"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(inventory_rows)

    word_rows = []
    for article, mapping in sorted(word_maps.items()):
        for wid, word in sorted(mapping.items()):
            word_rows.append({"article": article, "word_id": wid, "correct_word": word})
    with (out / "canonical_word_map.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["article", "word_id", "correct_word"])
        w.writeheader(); w.writerows(word_rows)

    ready = len(ready_subjects) == 22 and len(inventory_rows) == 110 and not blockers
    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "analysis": "prospective full preprocessed-input materialization and exact retained-epoch text identity freeze",
        "model_blind": True,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_expected_subjects": 22,
        "n_ready_subjects": len(ready_subjects),
        "ready_subjects": ready_subjects,
        "n_expected_subject_article_files": 110,
        "n_validated_subject_article_files": len(inventory_rows),
        "n_articles": 5,
        "n_channels_expected": 32,
        "sfreq_hz_expected": 1000.0,
        "epoch_window_s": [-0.2, 1.0],
        "item_identity_rule": "parse retained epoch event label as <word>_<article>_<word_id>; require article and word_id/correct_word agreement with frozen public article prediction table",
        "canonical_word_counts": {str(a): len(m) for a, m in word_maps.items()},
        "blockers": blockers,
        "ready_for_frozen_derco_reliability": ready,
        "guardrails": [
            "This stage materializes public preprocessed DERCo EEG only and validates exact retained-epoch linguistic identity.",
            "No EEG reliability, RSA, semantic-model quantity, model embedding, or transfer outcome is computed.",
            "The cohort is structural: all 22 public preprocessed participants must pass all five article checks; no participant is selected based on NeuroSem outcomes.",
            "The primary downstream representation remains the already-selected all-channel temporal mean; this stage does not compare EEG representations."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok" if ready else "blocked", "ready_subjects": len(ready_subjects), "validated_files": len(inventory_rows), "blockers": len(blockers), "ready_for_frozen_derco_reliability": ready}, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
