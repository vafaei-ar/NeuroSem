#!/usr/bin/env python3
"""Model-blind ZuCo 2.0 task1-NR format, alignment, and stimulus-text probe.

Downloads the seven shared word-boundary files, one representative preprocessed EEG
run (YDG NR1), and the seven small corrected eye-tracking files for YDG. It inspects
MATLAB/EEGLAB metadata and string-valued stimulus fields only. It never reads EEG
signal samples and does not compute EEG reliability or model alignment.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from scipy.io import loadmat, whosmat

from probe_zuco2_nr_alignment import summarize_eeg, summarize_wordbounds

NODE = "2urht"
UA = "NeuroSem-ZuCo2-format-probe/1.3"
WORDBOUND_TARGETS = [f"task1 - NR/Preprocessed/wordbounds_NR{i}.mat" for i in range(1, 8)]
EEG_TARGET = "task1 - NR/Preprocessed/YDG/gip_YDG_NR1_EEG.mat"
ET_TARGETS = [f"task1 - NR/Preprocessed/YDG/YDG_NR{i}_corrected_ET.mat" for i in range(1, 8)]
TARGETS = WORDBOUND_TARGETS + [EEG_TARGET] + ET_TARGETS


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


def walk(url, prefix="", out=None):
    out = {} if out is None else out
    for row in paged(url):
        a = row.get("attributes") or {}
        name = str(a.get("name") or "")
        kind = str(a.get("kind") or "")
        p = f"{prefix}/{name}" if prefix else name
        if kind == "file":
            out[p] = (row.get("links") or {}).get("download")
        elif kind == "folder" and any(t.startswith(p + "/") or t == p for t in TARGETS):
            u = child_url(row)
            if u:
                walk(u, p, out)
    return out


def inventory():
    out = {}
    for prov in paged(f"https://api.osf.io/v2/nodes/{NODE}/files/"):
        u = child_url(prov)
        if u:
            walk(u, "", out)
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
        for k in out["keys"]:
            v = d[k]
            out.setdefault("value_types", {})[k] = type(v).__name__
            if hasattr(v, "shape"):
                out.setdefault("value_shapes", {})[k] = list(v.shape)
    return out


def _collect_strings(value, path, out, depth=0):
    """Collect string leaves only; numeric arrays are never serialized or inspected elementwise."""
    if depth > 12:
        return
    if isinstance(value, str):
        s = value.strip()
        if s:
            out[path].append(s)
        return
    if isinstance(value, bytes):
        try:
            s = value.decode("utf-8").strip()
        except Exception:
            return
        if s:
            out[path].append(s)
        return
    if isinstance(value, dict):
        for k, v in value.items():
            _collect_strings(v, f"{path}.{k}" if path else str(k), out, depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _collect_strings(v, f"{path}[{i}]", out, depth + 1)
        return
    if isinstance(value, np.ndarray):
        if value.dtype.kind in "US":
            for i, v in enumerate(value.ravel()):
                _collect_strings(str(v), f"{path}[{i}]", out, depth + 1)
        elif value.dtype == object and value.size <= 20000:
            for i, v in enumerate(value.ravel()):
                _collect_strings(v, f"{path}[{i}]", out, depth + 1)


def summarize_stimulus_strings(path: Path):
    if h5py.is_hdf5(path):
        return {
            "file": path.name,
            "format": "matlab_v7.3_hdf5",
            "status": "not_loaded_for_string_probe",
            "candidate_groups": [],
        }
    d = loadmat(path, simplify_cells=True)
    grouped = defaultdict(list)
    for k, v in d.items():
        if not k.startswith("__"):
            _collect_strings(v, k, grouped)

    # Collapse indexed leaf paths to a stable structural path so repeated sentence/word
    # fields can be recognized without relying on one exact MATLAB nesting layout.
    collapsed = defaultdict(list)
    for p, vals in grouped.items():
        base = p
        while "[" in base:
            left = base.find("[")
            right = base.find("]", left)
            if right < 0:
                break
            base = base[:left] + "[]" + base[right + 1 :]
        collapsed[base].extend(vals)

    rows = []
    for p, vals in collapsed.items():
        unique = []
        seen = set()
        for s in vals:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        rows.append({
            "path": p,
            "n_strings": len(vals),
            "n_unique": len(unique),
            "max_length": max((len(s) for s in unique), default=0),
            "preview": unique[:12],
        })
    rows.sort(key=lambda r: (-r["n_strings"], -r["max_length"], r["path"]))
    return {
        "file": path.name,
        "format": "matlab_pre_v7.3",
        "status": "string_fields_only",
        "candidate_groups": rows[:100],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_format_probe/latest"))
    args = ap.parse_args()

    idx = inventory()
    missing = [t for t in TARGETS if t not in idx or not idx[t]]
    if missing:
        raise SystemExit(f"missing OSF targets: {missing}")

    root = args.data_root.resolve()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    mats = []
    local_paths = {}
    for t in TARGETS:
        p = root / t
        if not p.exists():
            download(idx[t], p)
        local_paths[t] = p
        mats.append(summarize_mat(p, load_small="wordbounds_" in t))

    base = root / "task1 - NR" / "Preprocessed"
    word_alignment = [summarize_wordbounds(base / f"wordbounds_NR{i}.mat") for i in range(1, 8)]
    eeg_alignment = summarize_eeg(base / "YDG" / "gip_YDG_NR1_EEG.mat")
    counts = {f"NR{i+1}": row["n_sentences"] for i, row in enumerate(word_alignment)}
    stimulus_probe = [summarize_stimulus_strings(base / "YDG" / f"YDG_NR{i}_corrected_ET.mat") for i in range(1, 8)]

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind format/alignment/stimulus-text metadata probe; no EEG signal samples or model quantities read",
        "release": "ZuCo 2.0",
        "osf_node": NODE,
        "task": "task1 - NR",
        "representative_subject": "YDG",
        "representative_run": "NR1",
        "targets": mats,
        "sentence_counts_by_run": counts,
        "total_shared_sentences": int(sum(counts.values())),
        "wordbound_alignment_metadata": word_alignment,
        "representative_eeg_alignment_metadata": eeg_alignment,
        "stimulus_text_string_probe": stimulus_probe,
        "intended_nuisance_freeze": [
            "absolute within-run sentence-order difference",
            "word-count difference",
            "punctuation-count difference",
            "lowercased lexical-set Jaccard distance",
        ],
        "guardrail": (
            "Use only to identify the public stimulus-text field and freeze English nuisance RDM construction before any EEG reliability. "
            "No EEG sample values are read; no candidate EEG representation, time window, or language-model condition is selected here."
        ),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "total_shared_sentences": summary["total_shared_sentences"], "output_dir": str(outdir)}, indent=2))


if __name__ == "__main__":
    main()
