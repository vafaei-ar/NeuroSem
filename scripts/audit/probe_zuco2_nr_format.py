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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import h5py
from scipy.io import loadmat, whosmat

from probe_zuco2_nr_alignment import summarize_eeg, summarize_wordbounds

NODE = "2urht"
UA = "NeuroSem-ZuCo2-format-probe/1.7"
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


def _intlike(s):
    try:
        int(str(s).strip())
        return True
    except Exception:
        return False


def load_material_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f, delimiter=";", quotechar='"') if any(str(x).strip() for x in r)]
    return rows


def summarize_material_csv(path: Path, expected_sentences: int):
    rows = load_material_rows(path)
    widths = Counter(len(r) for r in rows)
    previews = [r[:5] for r in rows[:5]]
    maxw = max((len(r) for r in rows), default=0)
    col_stats = []
    for j in range(maxw):
        vals = [str(r[j]).strip() if j < len(r) else "" for r in rows]
        nonempty = [v for v in vals if v]
        col_stats.append({
            "column_index": j,
            "n_nonempty": len(nonempty),
            "n_unique": len(set(nonempty)),
            "all_nonempty_intlike": bool(nonempty) and all(_intlike(v) for v in nonempty),
            "median_length": sorted(len(v) for v in nonempty)[len(nonempty)//2] if nonempty else 0,
            "max_length": max((len(v) for v in nonempty), default=0),
            "preview": nonempty[:5],
        })

    standard_rows = [r for r in rows if len(r) >= 3 and _intlike(r[0]) and _intlike(r[1])]
    text_values = [str(r[2]).strip() for r in standard_rows]
    control_flags = [str(r[3]).strip() if len(r) > 3 else "" for r in standard_rows]
    control_idx = [i + 1 for i, x in enumerate(control_flags) if x]
    id_pairs = [[int(str(r[0]).strip()), int(str(r[1]).strip())] for r in standard_rows]

    return {
        "file": path.name,
        "delimiter": ";",
        "header_mode": "none",
        "n_rows": len(rows),
        "expected_eeg_sentences": expected_sentences,
        "row_minus_expected": len(rows) - expected_sentences,
        "row_width_counts": {str(k): v for k, v in sorted(widths.items())},
        "row_preview": previews,
        "column_stats": col_stats,
        "n_standard_rows_first_two_integer": len(standard_rows),
        "n_nonempty_text_col2": sum(bool(x) for x in text_values),
        "n_unique_text_col2": len(set(x for x in text_values if x)),
        "n_flagged_rows_col3": len(control_idx),
        "flagged_row_indices_1based": control_idx,
        "flag_values": sorted(set(x for x in control_flags if x)),
        "id_pairs_in_order": id_pairs,
        "first_five_id_pairs": id_pairs[:5],
        "last_five_id_pairs": id_pairs[-5:],
        "text_preview": text_values[:5],
        "diagnostic_interpretation": (
            "Compare the semicolon-parsed material rows and identifiers with the already frozen EEG sentence count. "
            "Do not drop rows or select a mapping in this probe."
        ),
    }


def overlap_diagnostics(material_rows):
    out = []
    for i in range(len(material_rows) - 1):
        a = material_rows[i]
        b = material_rows[i + 1]
        amap = {(str(r[0]).strip(), str(r[1]).strip()): (j + 1, str(r[2]).strip())
                for j, r in enumerate(a) if len(r) >= 3 and _intlike(r[0]) and _intlike(r[1])}
        bmap = {(str(r[0]).strip(), str(r[1]).strip()): (j + 1, str(r[2]).strip())
                for j, r in enumerate(b) if len(r) >= 3 and _intlike(r[0]) and _intlike(r[1])}
        shared_ids = sorted(set(amap) & set(bmap), key=lambda x: (int(x[0]), int(x[1])))
        exact = []
        for key in shared_ids:
            ai, at = amap[key]
            bi, bt = bmap[key]
            exact.append({
                "id_pair": [int(key[0]), int(key[1])],
                "run_a_row_1based": ai,
                "run_b_row_1based": bi,
                "text_exact_match": at == bt,
            })
        atexts = {str(r[2]).strip(): j + 1 for j, r in enumerate(a) if len(r) >= 3 and str(r[2]).strip()}
        btexts = {str(r[2]).strip(): j + 1 for j, r in enumerate(b) if len(r) >= 3 and str(r[2]).strip()}
        shared_text = sorted(set(atexts) & set(btexts))
        out.append({
            "run_a": f"NR{i+1}",
            "run_b": f"NR{i+2}",
            "n_shared_id_pairs": len(shared_ids),
            "shared_id_pairs": exact,
            "n_shared_exact_texts": len(shared_text),
            "shared_text_row_pairs": [
                {"run_a_row_1based": atexts[t], "run_b_row_1based": btexts[t]}
                for t in shared_text
            ],
        })
    return out


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
    material_paths = [root / f"task_materials/nr_{i}.csv" for i in range(1, 8)]
    raw_material = [load_material_rows(p) for p in material_paths]
    material = [summarize_material_csv(p, counts[f"NR{i}"]) for i, p in enumerate(material_paths, start=1)]

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind task-material identifier/overlap diagnostic; no EEG signal samples or model quantities read",
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
        "adjacent_run_overlap_diagnostics": overlap_diagnostics(raw_material),
        "guardrail": (
            "Use this probe only to determine the deterministic relationship between public NR task-material rows and frozen EEG sentence identities. "
            "No task-material row is excluded here; no EEG sample values, model quantities, or outcome statistics are computed."
        ),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "total_shared_sentences": summary["total_shared_sentences"], "output_dir": str(outdir)}, indent=2))


if __name__ == "__main__":
    main()
