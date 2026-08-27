#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path

OSF_NODE = "rkqbu"
OSF_API = f"https://api.osf.io/v2/nodes/{OSF_NODE}/files/"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "NeuroSem-DERCo-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def iter_pages(url: str):
    while url:
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


def walk_listing(url: str, prefix: str, rows: list[dict]) -> None:
    for item in iter_pages(url):
        attrs = item.get("attributes", {})
        links = item.get("links", {})
        name = str(attrs.get("name") or "")
        kind = str(attrs.get("kind") or "")
        path = f"{prefix}/{name}" if prefix else name
        row = {
            "path": path,
            "kind": kind,
            "size_bytes": attrs.get("size"),
            "modified": attrs.get("date_modified"),
            "provider": attrs.get("provider"),
            "download_url": links.get("download") if kind == "file" else "",
        }
        rows.append(row)
        child = related_files_url(item)
        if kind == "folder" and child:
            walk_listing(child, path, rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/derco_osf_inventory/latest"))
    args = ap.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    providers = list(iter_pages(OSF_API))
    for provider in providers:
        attrs = provider.get("attributes", {})
        name = str(attrs.get("name") or attrs.get("provider") or "provider")
        child = related_files_url(provider)
        if child:
            walk_listing(child, name, rows)

    if not rows:
        raise RuntimeError("OSF inventory returned no files/folders")

    eeg_rows = [r for r in rows if "eeg" in r["path"].lower()]
    fif_rows = [r for r in rows if r["kind"] == "file" and r["path"].lower().endswith(".fif")]
    text_like = [r for r in rows if r["kind"] == "file" and r["path"].lower().endswith((".txt", ".csv", ".tsv", ".xlsx", ".docx"))]
    preproc_fif = [r for r in fif_rows if "preprocess" in r["path"].lower() or "preprocessed" in r["path"].lower()]

    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "kind", "size_bytes", "modified", "provider", "download_url"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    summary = {
        "schema_version": 1,
        "dataset": "DERCo",
        "osf_node": OSF_NODE,
        "osf_doi": "10.17605/OSF.IO/RKQBU",
        "analysis": "prospective metadata-only OSF inventory",
        "model_blind": True,
        "downloads_eeg_payloads": False,
        "computes_neural_outcomes": False,
        "computes_model_outcomes": False,
        "n_inventory_entries": len(rows),
        "n_files": sum(r["kind"] == "file" for r in rows),
        "n_folders": sum(r["kind"] == "folder" for r in rows),
        "n_paths_containing_eeg": len(eeg_rows),
        "n_fif_files": len(fif_rows),
        "n_preprocessed_fif_files": len(preproc_fif),
        "n_text_or_table_files": len(text_like),
        "preprocessed_fif_examples": [r["path"] for r in preproc_fif[:20]],
        "text_or_table_examples": [r["path"] for r in text_like[:30]],
        "ready_for_targeted_derco_materialization_probe": bool(preproc_fif and text_like),
        "guardrails": [
            "This step inventories public OSF metadata only.",
            "No EEG file is downloaded or opened.",
            "No NeuroSem model, embedding, RSA, reliability, participant selection, or transfer outcome is computed.",
            "If the public structure cannot support a comparable frozen linguistic item mapping, DERCo will be recorded as infeasible rather than changing the scientific target post hoc."
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "n_entries": len(rows), "n_fif": len(fif_rows), "n_preprocessed_fif": len(preproc_fif), "ready": summary["ready_for_targeted_derco_materialization_probe"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
