#!/usr/bin/env python3
"""Model-blind inventory of public ZuCo 1.0 and ZuCo 2.0 OSF file trees.

This probe intentionally does not download EEG payloads or compute any signal/model
quantities. It inventories the public OSF storage trees so we can choose a feasible,
prospectively defined normal-reading signal source before materialization.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NODES = {
    "zuco1": {"osf_node": "q3zws", "label": "ZuCo 1.0"},
    "zuco2": {"osf_node": "2urht", "label": "ZuCo 2.0"},
}
USER_AGENT = "NeuroSem-ZuCo-inventory/1.0"


def get_json(url: str, retries: int = 4) -> dict[str, Any]:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.api+json"})
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
        for row in obj.get("data", []):
            yield row
        url = (obj.get("links") or {}).get("next")


def related_files_url(row: dict[str, Any]) -> str | None:
    rel = (((row.get("relationships") or {}).get("files") or {}).get("links") or {}).get("related")
    if isinstance(rel, dict):
        return rel.get("href")
    if isinstance(rel, str):
        return rel
    return None


def walk_listing(url: str, release: str, provider: str, prefix: str, out: list[dict[str, Any]]):
    for row in paged(url):
        attrs = row.get("attributes") or {}
        name = str(attrs.get("name") or "")
        kind = str(attrs.get("kind") or "")
        path = f"{prefix}/{name}" if prefix else name
        links = row.get("links") or {}
        extra = attrs.get("extra") or {}
        hashes = extra.get("hashes") or {}
        rec = {
            "release": release,
            "provider": provider,
            "kind": kind,
            "path": path,
            "name": name,
            "size_bytes": attrs.get("size") if kind == "file" else None,
            "date_modified": attrs.get("date_modified"),
            "download_url": links.get("download") if kind == "file" else None,
            "md5": hashes.get("md5"),
            "sha256": hashes.get("sha256"),
        }
        out.append(rec)
        if kind == "folder":
            child = related_files_url(row)
            if child:
                walk_listing(child, release, provider, path, out)


def inventory_release(key: str, node: str) -> list[dict[str, Any]]:
    providers_url = f"https://api.osf.io/v2/nodes/{node}/files/"
    rows: list[dict[str, Any]] = []
    providers = list(paged(providers_url))
    if not providers:
        raise RuntimeError(f"No public storage providers returned for {key} ({node})")
    for p in providers:
        attrs = p.get("attributes") or {}
        provider = str(attrs.get("name") or p.get("id") or "provider")
        child = related_files_url(p)
        if not child:
            continue
        walk_listing(child, key, provider, "", rows)
    return rows


def lower_path(r):
    return str(r.get("path") or "").lower()


def summarize_release(rows: list[dict[str, Any]]) -> dict[str, Any]:
    files = [r for r in rows if r["kind"] == "file"]
    total = sum(int(r["size_bytes"] or 0) for r in files)
    by_ext: dict[str, dict[str, int]] = {}
    for r in files:
        name = r["name"].lower()
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else "[none]"
        d = by_ext.setdefault(ext, {"n_files": 0, "size_bytes": 0})
        d["n_files"] += 1
        d["size_bytes"] += int(r["size_bytes"] or 0)

    tokens = ["task1-nr", "task2-nr", "normal reading", "matlab", "preprocessed", "eeg"]
    matched = {}
    for token in tokens:
        subset = [r for r in files if token in lower_path(r)]
        matched[token] = {
            "n_files": len(subset),
            "size_bytes": sum(int(r["size_bytes"] or 0) for r in subset),
            "examples": [r["path"] for r in subset[:20]],
        }
    large = sorted(files, key=lambda r: int(r["size_bytes"] or 0), reverse=True)[:20]
    return {
        "n_entries": len(rows),
        "n_files": len(files),
        "total_size_bytes": total,
        "extensions": dict(sorted(by_ext.items())),
        "path_token_matches": matched,
        "largest_files": [
            {"path": r["path"], "size_bytes": int(r["size_bytes"] or 0), "download_url_present": bool(r["download_url"])}
            for r in large
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco_osf_inventory/latest"))
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind public metadata inventory; no EEG payloads loaded",
        "sources": {},
    }
    for key, spec in NODES.items():
        rows = inventory_release(key, spec["osf_node"])
        all_rows.extend(rows)
        summary["sources"][key] = {
            "label": spec["label"],
            "osf_node": spec["osf_node"],
            "public_url": f"https://osf.io/{spec['osf_node']}/",
            **summarize_release(rows),
        }

    csv_path = outdir / "inventory.csv"
    fields = ["release", "provider", "kind", "path", "name", "size_bytes", "date_modified", "download_url", "md5", "sha256"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    summary["decision_guardrail"] = (
        "Use this inventory only to choose a feasible normal-reading release/task and signal file source. "
        "Do not inspect EEG values, representation reliability, or model alignment before freezing that choice."
    )
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "n_entries": len(all_rows), "output_dir": str(outdir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
