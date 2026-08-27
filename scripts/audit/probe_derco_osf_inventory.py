#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

OSF_NODE = "rkqbu"
OSF_API = f"https://api.osf.io/v2/nodes/{OSF_NODE}/files/"
USER_AGENT = "NeuroSem-DERCo-audit/1.1"


def get_json(url: str, max_attempts: int = 8) -> dict:
    for attempt in range(max_attempts):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.loads(r.read().decode("utf-8"))
            time.sleep(0.75)
            return payload
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == max_attempts - 1:
                raise
            retry = e.headers.get("Retry-After")
            try:
                wait = max(1.0, float(retry)) if retry is not None else min(60.0, 5.0 * (attempt + 1))
            except ValueError:
                wait = min(60.0, 5.0 * (attempt + 1))
            time.sleep(wait)
    raise RuntimeError("unreachable")


def iter_pages(url: str, max_pages: int = 20):
    page = 0
    while url:
        page += 1
        if page > max_pages:
            raise RuntimeError(f"pagination exceeded safe cap of {max_pages} pages for {url}")
        payload = get_json(url)
        for item in payload.get("data", []):
            yield item
        nxt = payload.get("links", {}).get("next")
        if isinstance(nxt, dict):
            url = nxt.get("href")
        else:
            url = nxt


def related_files_url(item: dict) -> str | None:
    rel = item.get("relationships", {}).get("files", {}).get("links", {}).get("related")
    if isinstance(rel, dict):
        return rel.get("href")
    if isinstance(rel, str):
        return rel
    return None


def item_name(item: dict) -> str:
    return str(item.get("attributes", {}).get("name") or "")


def item_kind(item: dict) -> str:
    return str(item.get("attributes", {}).get("kind") or "")


def row_for(item: dict, prefix: str) -> dict:
    attrs = item.get("attributes", {})
    links = item.get("links", {})
    name = item_name(item)
    kind = item_kind(item)
    return {
        "path": f"{prefix}/{name}" if prefix else name,
        "kind": kind,
        "size_bytes": attrs.get("size"),
        "modified": attrs.get("date_modified"),
        "provider": attrs.get("provider"),
        "download_url": links.get("download") if kind == "file" else "",
    }


def list_children(folder_item: dict, prefix: str, rows: list[dict]) -> list[dict]:
    url = related_files_url(folder_item)
    if not url:
        return []
    items = list(iter_pages(url))
    rows.extend(row_for(x, prefix) for x in items)
    return items


def find_folder(items: list[dict], required_tokens: tuple[str, ...]) -> dict | None:
    for item in items:
        if item_kind(item) != "folder":
            continue
        name = item_name(item).lower().replace("-", "_").replace(" ", "_")
        if all(tok in name for tok in required_tokens):
            return item
    return None


def first_folder(items: list[dict]) -> dict | None:
    return next((x for x in items if item_kind(x) == "folder"), None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_osf_inventory/latest"))
    args = ap.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    providers = list(iter_pages(OSF_API, max_pages=5))
    if not providers:
        raise RuntimeError("OSF node returned no storage providers")
    storage = providers[0]
    storage_name = item_name(storage) or str(storage.get("attributes", {}).get("provider") or "storage")
    root = list_children(storage, storage_name, rows)
    if not root:
        raise RuntimeError("DERCo OSF storage root is empty")

    eeg_exp = find_folder(root, ("eeg", "reading"))
    beh_exp = find_folder(root, ("behaviour",)) or find_folder(root, ("behavior",))

    eeg_children: list[dict] = []
    eeg_data_children: list[dict] = []
    preproc_subjects: list[dict] = []
    representative_article_items: list[dict] = []
    behavioral_children: list[dict] = []
    prediction_files: list[dict] = []

    if eeg_exp:
        eeg_prefix = f"{storage_name}/{item_name(eeg_exp)}"
        eeg_children = list_children(eeg_exp, eeg_prefix, rows)
        eeg_data = find_folder(eeg_children, ("eeg", "data"))
        if eeg_data:
            data_prefix = f"{eeg_prefix}/{item_name(eeg_data)}"
            eeg_data_children = list_children(eeg_data, data_prefix, rows)
            preproc = find_folder(eeg_data_children, ("preprocessed",)) or find_folder(eeg_data_children, ("preprocess",))
            if preproc:
                preproc_prefix = f"{data_prefix}/{item_name(preproc)}"
                preproc_subjects = list_children(preproc, preproc_prefix, rows)
                subject = first_folder(preproc_subjects)
                if subject:
                    subject_prefix = f"{preproc_prefix}/{item_name(subject)}"
                    articles = list_children(subject, subject_prefix, rows)
                    article = first_folder(articles)
                    if article:
                        article_prefix = f"{subject_prefix}/{item_name(article)}"
                        representative_article_items = list_children(article, article_prefix, rows)

    if beh_exp:
        beh_prefix = f"{storage_name}/{item_name(beh_exp)}"
        behavioral_children = list_children(beh_exp, beh_prefix, rows)
        pred = find_folder(behavioral_children, ("prediction",))
        if pred:
            pred_prefix = f"{beh_prefix}/{item_name(pred)}"
            prediction_files = list_children(pred, pred_prefix, rows)

    fif_rows = [r for r in rows if r["kind"] == "file" and r["path"].lower().endswith(".fif")]
    text_like = [r for r in rows if r["kind"] == "file" and r["path"].lower().endswith((".txt", ".csv", ".tsv", ".xlsx", ".docx"))]
    preproc_fif = [r for r in fif_rows if "preprocess" in r["path"].lower()]
    prediction_csv = [r for r in rows if "prediction" in r["path"].lower() and r["path"].lower().endswith(".csv")]

    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "kind", "size_bytes", "modified", "provider", "download_url"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "osf_node": OSF_NODE,
        "osf_doi": "10.17605/OSF.IO/RKQBU",
        "analysis": "prospective targeted metadata-only OSF inventory",
        "model_blind": True,
        "downloads_eeg_payloads": False,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "rate_limit_strategy": "targeted traversal only; 0.75 s pacing; Retry-After-aware exponential fallback for HTTP 429",
        "n_inventory_entries": len(rows),
        "root_entries": [item_name(x) for x in root],
        "eeg_experiment_folder_found": eeg_exp is not None,
        "behavioral_experiment_folder_found": beh_exp is not None,
        "n_preprocessed_subject_folders_seen": sum(item_kind(x) == "folder" for x in preproc_subjects),
        "representative_article_entries": [item_name(x) for x in representative_article_items],
        "n_representative_preprocessed_fif_files": len(preproc_fif),
        "n_prediction_csv_files_seen": len(prediction_csv),
        "preprocessed_fif_examples": [r["path"] for r in preproc_fif[:10]],
        "prediction_csv_examples": [r["path"] for r in prediction_csv[:10]],
        "text_or_table_examples": [r["path"] for r in text_like[:20]],
        "ready_for_targeted_derco_materialization_probe": bool(preproc_fif and prediction_csv),
        "guardrails": [
            "This step inventories public OSF metadata only.",
            "The traversal is deliberately targeted and samples one preprocessed participant/article rather than recursively enumerating all EEG files.",
            "No EEG file is downloaded or opened.",
            "No NeuroSem model, embedding, RSA, reliability, participant selection, or transfer outcome is computed.",
            "If the public structure cannot support a comparable frozen linguistic item mapping, DERCo will be recorded as infeasible rather than changing the scientific target post hoc."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "n_entries": len(rows),
        "preprocessed_subject_folders_seen": summary["n_preprocessed_subject_folders_seen"],
        "representative_fif": len(preproc_fif),
        "prediction_csv": len(prediction_csv),
        "ready": summary["ready_for_targeted_derco_materialization_probe"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
