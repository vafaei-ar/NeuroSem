#!/usr/bin/env python3
"""Model-blind ZuCo 2.0 Task 1 NR alignment metadata probe.

Uses only already-materialized shared word-boundary files and one representative
preprocessed EEG run. It does not read EEG signal samples or compute reliability/model
alignment. The purpose is to establish whether sentence/run timing and EEGLAB metadata
support a deterministic sentence-level analysis plan.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from scipy.io import loadmat


def _numeric_summary(x):
    try:
        a = np.asarray(x, dtype=float).ravel()
    except Exception:
        return {"dtype": str(getattr(np.asarray(x), "dtype", "unknown")), "n": int(np.size(x))}
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size),
        "min": float(np.min(a)),
        "max": float(np.max(a)),
        "first": float(a[0]),
        "last": float(a[-1]),
    }


def summarize_wordbounds(path: Path):
    d = loadmat(path, simplify_cells=True)
    wb = np.asarray(d["wordbounds"], dtype=object).ravel()
    tb = np.asarray(d["textbounds"], dtype=object).ravel()
    rows = []
    for i, (w, t) in enumerate(zip(wb, tb), start=1):
        wa = np.asarray(w)
        ta = np.asarray(t)
        rows.append({
            "sentence_index": i,
            "wordbounds_shape": list(wa.shape),
            "wordbounds_numeric": _numeric_summary(wa),
            "textbounds_shape": list(ta.shape),
            "textbounds_numeric": _numeric_summary(ta),
        })
    return {
        "file": path.name,
        "n_sentences": len(rows),
        "sentences": rows,
        "interpretation": "screen/text spatial bounds only; not used as EEG temporal boundaries",
    }


def h5_meta(obj):
    rec = {"name": obj.name.split("/")[-1] or "/"}
    if isinstance(obj, h5py.Dataset):
        rec.update({"kind": "dataset", "shape": list(obj.shape), "dtype": str(obj.dtype)})
        if obj.size <= 16 and obj.dtype.kind in "biuf":
            vals = np.asarray(obj[()]).ravel()
            rec["small_numeric_values"] = [float(v) for v in vals]
        if h5py.check_dtype(ref=obj.dtype) is not None:
            rec["is_reference_dataset"] = True
    else:
        rec.update({"kind": "group", "n_children": len(obj.keys()), "children": list(obj.keys())[:100]})
    return rec


def _decode_matlab_value(f: h5py.File, ref):
    if not ref:
        return None
    obj = f[ref]
    if not isinstance(obj, h5py.Dataset):
        return {"kind": "group", "path": obj.name}
    a = np.asarray(obj[()])
    if a.size == 0:
        return None
    # MATLAB char arrays in v7.3 files are commonly uint16 code points.
    if a.dtype.kind in "ui" and a.ndim <= 2:
        vals = a.ravel(order="F")
        if vals.size and np.all((vals == 0) | ((vals >= 9) & (vals <= 0x10FFFF))):
            nonzero = [int(v) for v in vals if int(v) != 0]
            if nonzero and sum(32 <= v <= 126 for v in nonzero) / len(nonzero) >= 0.7:
                try:
                    return "".join(chr(v) for v in nonzero)
                except ValueError:
                    pass
    if a.size == 1 and a.dtype.kind in "biuf":
        return float(a.ravel()[0])
    if a.size <= 16 and a.dtype.kind in "biuf":
        return [float(v) for v in a.ravel()]
    return {"shape": list(a.shape), "dtype": str(a.dtype)}


def summarize_events(f: h5py.File, eeg: h5py.Group):
    ev = eeg.get("event")
    if not isinstance(ev, h5py.Group):
        return {"available": False}
    fields = [k for k in ("type", "value", "latency", "duration", "urevent") if k in ev]
    n = min(int(ev[k].size) for k in fields) if fields else 0
    rows = []
    for i in range(n):
        row = {"event_index": i + 1}
        for k in fields:
            ds = ev[k]
            flat = np.asarray(ds[()]).ravel(order="F")
            row[k] = _decode_matlab_value(f, flat[i])
        rows.append(row)
    type_counts = Counter(str(r.get("type")) for r in rows)
    value_counts = Counter(str(r.get("value")) for r in rows)
    latencies = [r.get("latency") for r in rows if isinstance(r.get("latency"), (int, float))]
    return {
        "available": True,
        "n_events": n,
        "fields": fields,
        "type_counts": dict(type_counts),
        "value_counts": dict(value_counts),
        "latency_samples_summary": _numeric_summary(latencies) if latencies else {"n": 0},
        "records": rows,
        "signal_samples_read": False,
    }


def summarize_eeg(path: Path):
    out = {"file": path.name, "size_bytes": path.stat().st_size}
    with h5py.File(path, "r") as f:
        eeg = f["EEG"]
        fields = [
            "data", "srate", "nbchan", "pnts", "trials", "xmin", "xmax", "times",
            "event", "epoch", "chanlocs", "urevent", "condition", "setname",
        ]
        out["eeg_fields"] = {}
        for name in fields:
            if name in eeg:
                obj = eeg[name]
                out["eeg_fields"][name] = h5_meta(obj)
                if isinstance(obj, h5py.Group):
                    out["eeg_fields"][name]["child_metadata"] = {
                        k: h5_meta(obj[k]) for k in list(obj.keys())[:100]
                    }
        out["data_values_read"] = False
        data = eeg.get("data")
        if isinstance(data, h5py.Dataset):
            shape = list(data.shape)
            out["data_shape"] = shape
            out["data_dtype"] = str(data.dtype)
            out["data_dimensionality"] = len(shape)
            out["likely_epoched"] = len(shape) >= 3 and min(shape) > 1
        else:
            out["data_shape"] = None
            out["likely_epoched"] = None
        out["event_records"] = summarize_events(f, eeg)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/zuco2_probe"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/zuco2_nr_alignment_probe/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    base = root / "task1 - NR" / "Preprocessed"
    word_files = [base / f"wordbounds_NR{i}.mat" for i in range(1, 8)]
    eeg_file = base / "YDG" / "gip_YDG_NR1_EEG.mat"
    missing = [str(p) for p in [*word_files, eeg_file] if not p.exists()]
    if missing:
        raise SystemExit(f"missing previously materialized probe inputs: {missing}")

    runs = [summarize_wordbounds(p) for p in word_files]
    eeg = summarize_eeg(eeg_file)
    total_sentences = sum(r["n_sentences"] for r in runs)

    out = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind alignment metadata probe; no EEG signal samples or model quantities read",
        "release": "ZuCo 2.0",
        "task": "task1 - NR",
        "representative_subject": "YDG",
        "representative_run": "NR1",
        "n_runs": 7,
        "sentence_counts_by_run": {f"NR{i+1}": r["n_sentences"] for i, r in enumerate(runs)},
        "total_shared_sentences": total_sentences,
        "wordbound_metadata": runs,
        "representative_eeg_metadata": eeg,
        "decision_guardrail": (
            "Use only to determine whether a deterministic sentence-level timing/alignment scheme can be frozen. "
            "Do not use this probe to select EEG representations, time windows, or model conditions."
        ),
    }
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "summary.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "total_shared_sentences": total_sentences, "output_dir": str(outdir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
