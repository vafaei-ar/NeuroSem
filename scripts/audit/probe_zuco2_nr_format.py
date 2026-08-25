#!/usr/bin/env python3
"""Model-blind ZuCo 2.0 task1-NR format, alignment, and stimulus-material probe.

Downloads only the seven shared word-boundary files, one representative preprocessed
EEG run (YDG NR1), and the seven tiny public NR task-material CSV files. It inspects
structure/text metadata only. It never reads EEG signal samples or computes EEG
reliability/model alignment.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import h5py
from scipy.io import loadmat, whosmat

from probe_zuco2_nr_alignment import summarize_eeg, summarize_wordbounds

NODE = "2urht"
UA = "NeuroSem-ZuCo2-format-probe/1.6"
WORDBOUND_TARGETS = [f"task1 - NR/Preprocessed/wordbounds_NR{i}.mat" for i in range(1, 8)]
EEG_TARGET = "task1 - NR/Preprocessed/YDG/gip_YDG_NR1_EEG.mat"
MATERIAL_TARGETS = [f"task_materials/nr_{i}.csv" for i in range(1, 8)]
TARGETS = WORDBOUND_TARGETS + [EEG_TARGET] + MATERIAL_TARGETS


def get_json(url, retries=4):
    last = None
    for a in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.api+json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(2**a)
    raise RuntimeError(f"OSF request failed: {url}: {last}")


def paged(url):
    while url:
        o = get_json(url)
        yield from o.get("data", [])
        url = (o.get("links") or {}).get("next")


def child_url(row):
    rel = (((row.get("relationships") or {}).get("files") or {}).get("links") or {}).get("related")
    return rel.get("href") if isinstance(rel, dict) else rel


def walk_targets(url, prefix="", out=None):
    out = {} if out is None else out
    for row in paged(url):
        a = row.get("attributes") or {}
        name = str(a.get("name") or "")
        kind = str(a.get("kind") or "")
        p = f"{prefix}/{name}" if prefix else name
        if kind == "file":
            if p in TARGETS:
                out[p] = (row.get("links") or {}).get("download")
        elif kind == "folder" and any(t.startswith(p + "/") or t == p for t in TARGETS):
            u = child_url(row)
            if u:
                walk_targets(u, p, out)
    return out


def target_inventory():
    out = {}
    for prov in paged(f"https://api.osf.io/v2/nodes/{NODE}/files/"):
        u = child_url(prov)
        if u:
            walk_targets(u, "", out)
    return out


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, path.open("wb") as f:
        while True:
            b = r.read(1024 * 1024)
            if not b:
                break
            f.write(b)


def summarize_hdf5(path: Path):
    out = {"format": "matlab_v7.3_hdf5", "top_level": []}
    with h5py.File(path, "r") as f:
        for name, obj in f.items():
            rec = {"name": name, "kind": "dataset" if isinstance(obj, h5py.Dataset) else "group"}
            if isinstance(obj, h5py.Dataset):
                rec["shape"] = list(obj.shape)
                rec["dtype"] = str(obj.dtype)
            else:
                rec["n_children"] = len(obj.keys())
                rec["children_preview"] = list(obj.keys())[:25]
            out["top_level"].append(rec)
    return out


def summarize_mat(path, load_small=False):
    out = {"path": str(path), "size_bytes": path.stat().st_size}
    if h5py.is_hdf5(path):
        out.update(summarize_hdf5(path))
        return out
    out["format"] = "matlab_pre_v7.3"
    out["whosmat"] = []
    for name, shape, cls in whosmat(path):
        out["whosmat"].append({"name": name, "shape": list(shape), "class": cls})
    if load_small:
        d = loadmat(path, simplify_cells=True)
        out["keys"] = [k for k in d if not k.startswith("__")]
    return out


def ordered_unique(values):
    out = []
    seen = set()
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def summarize_material_csv(path: Path, expected_sentences: int):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys()) if rows else []
    stats = []
    for field in fields:
        vals = [str(r.get(field) or "").strip() for r in rows]
        nonempty = [v for v in vals if v]
        uniq = ordered_unique(nonempty)
        lengths = sorted(len(v) for v in nonempty)
        stats.append({
            "field": field,
            "n_nonempty": len(nonempty),
            "n_unique": len(set(nonempty)),
            "n_ordered_unique": len(uniq),
            "median_length": lengths[len(lengths)//2] if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "preview": nonempty[:3],
            "ordered_unique_preview": uniq[:3],
            "unique_count_matches_expected_sentences": len(uniq) == expected_sentences,
        })

    # These public CSVs can be word-level or fixation-oriented, so total row count need not
    # equal sentence count. A plausible sentence-text field should instead yield exactly the
    # frozen number of distinct sentence strings in first-occurrence order. Among such fields,
    # prefer longer strings. This remains a model-blind structural heuristic.
    eligible = [s for s in stats if s["n_ordered_unique"] == expected_sentences]
    candidate = max(eligible, key=lambda s: (s["median_length"], s["max_length"], s["n_nonempty"]), default=None)
    return {
        "file": path.name,
        "n_rows": len(rows),
        "expected_sentences": expected_sentences,
        "row_count_matches": len(rows) == expected_sentences,
        "row_count_interpretation": "diagnostic only; repeated rows are allowed because task-material CSVs may be word/fixation level",
        "fields": fields,
        "field_stats": stats,
        "candidate_sentence_text_field": candidate["field"] if candidate else None,
        "candidate_rule": "ordered distinct nonempty values equal frozen sentence count; prefer longest median string",
        "candidate_ordered_sentence_preview": candidate["ordered_unique_preview"] if candidate else [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_format_probe/latest"))
    args = ap.parse_args()

    idx = target_inventory()
    missing = [t for t in TARGETS if t not in idx or not idx[t]]
    if missing:
        raise SystemExit(f"missing OSF targets: {missing}")

    root = args.data_root.resolve()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    mats = []
    for t in TARGETS:
        p = root / t
        if not p.exists():
            download(idx[t], p)
        if p.suffix.lower() == ".mat":
            mats.append(summarize_mat(p, load_small="wordbounds_" in t))

    base = root / "task1 - NR" / "Preprocessed"
    word_alignment = [summarize_wordbounds(base / f"wordbounds_NR{i}.mat") for i in range(1, 8)]
    eeg_alignment = summarize_eeg(base / "YDG" / "gip_YDG_NR1_EEG.mat")
    counts = {f"NR{i+1}": row["n_sentences"] for i, row in enumerate(word_alignment)}
    material = [summarize_material_csv(root / f"task_materials/nr_{i}.csv", counts[f"NR{i}"]) for i in range(1, 8)]

    fields = [m["candidate_sentence_text_field"] for m in material]
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind format/alignment/stimulus-material diagnostic probe; no EEG signal samples or model quantities read",
        "release": "ZuCo 2.0",
        "osf_node": NODE,
        "task": "task1 - NR",
        "representative_subject": "YDG",
        "representative_run": "NR1",
        "sentence_counts_by_run": counts,
        "total_shared_sentences": int(sum(counts.values())),
        "wordbound_alignment_metadata": word_alignment,
        "representative_eeg_alignment_metadata": eeg_alignment,
        "task_materials": material,
        "candidate_text_fields_by_run": fields,
        "all_runs_have_candidate_text_field": all(fields),
        "intended_nuisance_freeze": [
            "absolute within-run sentence-order difference",
            "word-count difference from the frozen public NR sentence text",
            "punctuation-count difference from the frozen public NR sentence text",
            "lowercased lexical-set Jaccard distance from the frozen public NR sentence text"
        ],
        "guardrail": "Use only to identify public stimulus text and freeze nuisance RDM construction before EEG reliability. Row-count mismatch is diagnostic, not an exclusion criterion. No EEG sample values, model quantities, or outcome statistics are computed."
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "total_shared_sentences": summary["total_shared_sentences"],
        "candidate_text_fields_by_run": fields,
        "all_runs_have_candidate_text_field": summary["all_runs_have_candidate_text_field"],
        "output_dir": str(outdir)
    }, indent=2))


if __name__ == "__main__":
    main()
