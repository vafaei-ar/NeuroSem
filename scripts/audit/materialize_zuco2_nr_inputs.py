#!/usr/bin/env python3
"""Materialize and structurally QC the full ZuCo 2.0 Task 1 normal-reading cohort.

This step is model-blind. It downloads the public preprocessed EEG files, inspects
HDF5/EEGLAB metadata and trigger structure, and freezes structural readiness. It does
not compute EEG reliability or model alignment.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

NODE = "2urht"
UA = "NeuroSem-ZuCo2-materialize/1.1"
EXPECTED = {1: 50, 2: 50, 3: 51, 4: 50, 5: 50, 6: 49, 7: 49}
EEG_NAME_RE = re.compile(r"(?P<prefix>[A-Za-z]+)_(?P<subject>[A-Za-z0-9]+)_NR(?P<run>[1-7])_EEG\.mat$")


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


def collect_files(url, prefix="", out=None):
    out = {} if out is None else out
    for row in paged(url):
        a = row.get("attributes") or {}
        name = str(a.get("name") or "")
        kind = str(a.get("kind") or "")
        p = f"{prefix}/{name}" if prefix else name
        if kind == "file":
            out[p] = {"download": (row.get("links") or {}).get("download"), "size": a.get("size")}
        elif kind == "folder":
            u = child_url(row)
            if u:
                collect_files(u, p, out)
    return out


def osf_inventory():
    out = {}
    for prov in paged(f"https://api.osf.io/v2/nodes/{NODE}/files/"):
        u = child_url(prov)
        if u:
            collect_files(u, "", out)
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


def decode_text_dataset(f, ds):
    arr = np.asarray(ds[()])
    if h5py.check_dtype(ref=ds.dtype) is not None:
        vals = []
        for ref in arr.ravel():
            obj = f[ref]
            x = np.asarray(obj[()])
            if x.dtype.kind in "uifb" and x.size > 1:
                try:
                    vals.append("".join(chr(int(v)) for v in x.ravel() if int(v) != 0))
                except Exception:
                    vals.append(str(x.ravel()[0]))
            elif x.size:
                vals.append(str(x.ravel()[0]))
            else:
                vals.append("")
        return vals
    return [str(x) for x in arr.ravel()]


def decode_numeric_refs(f, ds):
    arr = np.asarray(ds[()])
    if h5py.check_dtype(ref=ds.dtype) is not None:
        vals = []
        for ref in arr.ravel():
            obj = f[ref]
            x = np.asarray(obj[()]).ravel()
            vals.append(float(x[0]) if x.size else np.nan)
        return vals
    return [float(x) for x in arr.ravel()]


def inspect_run(path: Path, expected_sentences: int):
    rec = {"path": str(path), "ready": False, "errors": []}
    try:
        if not h5py.is_hdf5(path):
            rec["errors"].append("not_hdf5_mat_v7_3")
            return rec
        with h5py.File(path, "r") as f:
            if "EEG" not in f:
                rec["errors"].append("missing_EEG")
                return rec
            eeg = f["EEG"]
            data = eeg.get("data")
            rec["data_shape"] = list(data.shape) if isinstance(data, h5py.Dataset) else None
            rec["continuous_2d"] = isinstance(data, h5py.Dataset) and len(data.shape) == 2
            for k in ("srate", "nbchan", "pnts", "trials"):
                obj = eeg.get(k)
                if isinstance(obj, h5py.Dataset):
                    arr = np.asarray(obj[()]).ravel()
                    rec[k] = float(arr[0]) if arr.size else None
                else:
                    rec[k] = None
            if not rec["continuous_2d"]:
                rec["errors"].append("data_not_continuous_2d")
            ev = eeg.get("event")
            if not isinstance(ev, h5py.Group) or not all(k in ev for k in ("type", "latency")):
                rec["errors"].append("missing_event_type_latency")
                return rec
            types = [str(x).strip() for x in decode_text_dataset(f, ev["type"])]
            lats = decode_numeric_refs(f, ev["latency"])
            rec["n_events"] = len(types)
            core = [(t, lat) for t, lat in zip(types, lats) if t in {"10", "11", "12", "13"}]
            rec["core_event_count"] = len(core)
            pairs = []
            ok_pairs = len(core) % 2 == 0
            if ok_pairs:
                for i in range(0, len(core), 2):
                    a, b = core[i], core[i + 1]
                    if (a[0], b[0]) not in {("10", "11"), ("12", "13")}:
                        ok_pairs = False
                        break
                    pairs.append((a, b))
            rec["sentence_pairs"] = len(pairs) if ok_pairs else None
            rec["ordinary_pairs"] = sum(1 for a, b in pairs if (a[0], b[0]) == ("10", "11")) if ok_pairs else None
            rec["question_pairs"] = sum(1 for a, b in pairs if (a[0], b[0]) == ("12", "13")) if ok_pairs else None
            rec["pair_pattern_valid"] = bool(ok_pairs)
            if not ok_pairs:
                rec["errors"].append("invalid_sentence_event_pair_sequence")
            if ok_pairs and len(pairs) != expected_sentences:
                rec["errors"].append(f"sentence_count_{len(pairs)}_expected_{expected_sentences}")
            pnts = rec.get("pnts") or 0
            bounds_ok = True
            if ok_pairs:
                prev = -np.inf
                for a, b in pairs:
                    if not (a[1] < b[1] and a[1] > prev and b[1] <= pnts):
                        bounds_ok = False
                        break
                    prev = b[1]
            rec["latency_order_bounds_valid"] = bool(bounds_ok)
            if not bounds_ok:
                rec["errors"].append("invalid_sentence_latency_order_or_bounds")
            rec["ready"] = not rec["errors"]
            return rec
    except Exception as e:
        rec["errors"].append(f"exception:{type(e).__name__}:{e}")
        return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_nr"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_input_materialization/latest"))
    args = ap.parse_args()

    inv = osf_inventory()
    prefix = "task1 - NR/Preprocessed/"
    candidates = {}
    filename_prefix_counts = Counter()
    ignored_eeg_paths = []
    for p, meta in inv.items():
        if not p.startswith(prefix) or not p.endswith("_EEG.mat"):
            continue
        rel = p[len(prefix):]
        parts = rel.split("/")
        if len(parts) != 2:
            ignored_eeg_paths.append(p)
            continue
        subj_folder, fname = parts
        m = EEG_NAME_RE.fullmatch(fname)
        if m is None or m.group("subject") != subj_folder:
            ignored_eeg_paths.append(p)
            continue
        run = int(m.group("run"))
        key = (subj_folder, run)
        if key in candidates:
            raise SystemExit(f"ambiguous duplicate EEG files for {key}: {candidates[key][0]} and {p}")
        file_prefix = m.group("prefix")
        filename_prefix_counts[file_prefix] += 1
        candidates[key] = (p, meta, file_prefix)

    subjects = sorted({s for s, _ in candidates})
    root = args.data_root.resolve()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for subj in subjects:
        for run in range(1, 8):
            key = (subj, run)
            row = {"subject": subj, "run": run, "expected_sentences": EXPECTED[run]}
            if key not in candidates:
                row.update({"present_on_osf": False, "ready": False, "errors": "missing_osf_file"})
                rows.append(row)
                continue
            p, meta, file_prefix = candidates[key]
            local = root / p
            if not local.exists():
                download(meta["download"], local)
            qc = inspect_run(local, EXPECTED[run])
            row.update({
                "present_on_osf": True,
                "osf_path": p,
                "filename_prefix": file_prefix,
                "size_bytes": local.stat().st_size,
                **qc,
            })
            row["errors"] = ";".join(qc.get("errors", []))
            rows.append(row)

    by_subj = defaultdict(list)
    for r in rows:
        by_subj[r["subject"]].append(r)
    ready_subjects = sorted(s for s, rs in by_subj.items() if len(rs) == 7 and all(bool(r.get("ready")) for r in rs))

    csv_path = outdir / "session_inventory.csv"
    fields = sorted({k for r in rows for k in r.keys()})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind full-cohort materialization and structural QC; no EEG reliability or model analysis",
        "release": "ZuCo 2.0",
        "osf_node": NODE,
        "task": "task1 - NR",
        "expected_sentence_counts": {f"NR{k}": v for k, v in EXPECTED.items()},
        "n_subjects_discovered": len(subjects),
        "subjects_discovered": subjects,
        "n_run_files_expected": len(subjects) * 7,
        "n_run_files_present": sum(bool(r.get("present_on_osf")) for r in rows),
        "n_runs_ready": sum(bool(r.get("ready")) for r in rows),
        "n_ready_subjects_all_7_runs": len(ready_subjects),
        "ready_subjects_all_7_runs": ready_subjects,
        "published_filename_prefix_counts": dict(sorted(filename_prefix_counts.items())),
        "n_ignored_eeg_paths": len(ignored_eeg_paths),
        "ignored_eeg_paths": ignored_eeg_paths,
        "cohort_rule": "primary reliability cohort requires all seven runs to pass structural QC; no outcome-based exclusions",
        "guardrail": "No EEG representational reliability or language-model quantities are computed in this step.",
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
