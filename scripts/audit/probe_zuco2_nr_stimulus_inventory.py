#!/usr/bin/env python3
"""Metadata-only ZuCo 2.0 Task 1 NR stimulus-file inventory.

Walk the public OSF file tree and report likely stimulus/text/material files by path,
size, and extension. No EEG, eye-tracking, stimulus payload, or model data are
downloaded or read. This is used only to choose a small public source for freezing
English nuisance RDMs before any ZuCo EEG reliability outcome is computed.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

NODE = "2urht"
UA = "NeuroSem-ZuCo2-stimulus-inventory/1.0"
TOKENS = (
    "sentence", "sentences", "stim", "stimulus", "stimuli", "text", "material",
    "task1", "task 1", "nr", "normal reading", "wordbound", "word_bound",
)
TEXT_EXTS = (".txt", ".csv", ".tsv", ".json", ".xlsx", ".xls", ".mat")


def get_json(url: str, retries: int = 4):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.api+json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"OSF API request failed after {retries} attempts: {url}: {last}")


def paged(url: str):
    while url:
        obj = get_json(url)
        yield from obj.get("data", [])
        url = (obj.get("links") or {}).get("next")


def related_files_url(row):
    rel = (((row.get("relationships") or {}).get("files") or {}).get("links") or {}).get("related")
    if isinstance(rel, dict):
        return rel.get("href")
    return rel if isinstance(rel, str) else None


def walk(url: str, prefix: str, rows: list[dict]):
    for row in paged(url):
        attrs = row.get("attributes") or {}
        name = str(attrs.get("name") or "")
        kind = str(attrs.get("kind") or "")
        path = f"{prefix}/{name}" if prefix else name
        if kind == "file":
            low = path.lower()
            ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
            token_hits = sorted({t for t in TOKENS if t in low})
            if token_hits or ext in TEXT_EXTS:
                rows.append({
                    "path": path,
                    "name": name,
                    "size_bytes": attrs.get("size"),
                    "extension": ext,
                    "token_hits": token_hits,
                    "download_url_present": bool((row.get("links") or {}).get("download")),
                })
        elif kind == "folder":
            child = related_files_url(row)
            if child:
                walk(child, path, rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_stimulus_inventory/latest"))
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    providers = list(paged(f"https://api.osf.io/v2/nodes/{NODE}/files/"))
    for provider in providers:
        child = related_files_url(provider)
        if child:
            walk(child, "", rows)

    # Prioritize small, text-like files and paths explicitly mentioning stimulus/material/sentence.
    def score(r):
        low = r["path"].lower()
        semantic = sum(tok in low for tok in ("sentence", "stim", "text", "material"))
        text_ext = int(r["extension"] in TEXT_EXTS)
        size = int(r["size_bytes"] or 10**18)
        return (-semantic, -text_ext, size, r["path"])

    rows.sort(key=score)
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind OSF metadata-only stimulus inventory; no file payloads downloaded",
        "release": "ZuCo 2.0",
        "osf_node": NODE,
        "task_focus": "Task 1 Normal Reading",
        "n_candidate_files": len(rows),
        "candidates": rows[:500],
        "guardrail": (
            "Use only to choose the smallest defensible public stimulus-text/material source before ZuCo EEG reliability. "
            "Do not inspect EEG values, eye-tracking values, model embeddings, or outcome statistics in this step."
        ),
    }
    (outdir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "n_candidate_files": len(rows), "output_dir": str(outdir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
