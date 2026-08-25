#!/usr/bin/env python3
"""Model-blind ZuCo 2.0 Task 1 NR stimulus/alignment probe.

Downloads only the seven shared word-boundary files, one representative preprocessed
EEG run (YDG NR1), and seven tiny public NR task-material CSVs. It never reads EEG
signal samples or computes EEG reliability/model alignment.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import h5py
from scipy.io import loadmat, whosmat

from probe_zuco2_nr_alignment import summarize_eeg, summarize_wordbounds

NODE = "2urht"
UA = "NeuroSem-ZuCo2-format-probe/1.8"
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
    out["whosmat"] = [{"name": n, "shape": list(s), "class": c} for n, s, c in whosmat(path)]
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
        return [r for r in csv.reader(f, delimiter=";", quotechar='"') if any(str(x).strip() for x in r)]


def word_count(text: str) -> int:
    # ZuCo wordbounds mark visually presented whitespace-delimited word units. This
    # count is used only for model-blind structural alignment, never as an outcome.
    return len(re.findall(r"\S+", str(text).strip()))


def summarize_material_csv(path: Path, expected_sentences: int):
    rows = load_material_rows(path)
    widths = Counter(len(r) for r in rows)
    standard = [r for r in rows if len(r) >= 3 and _intlike(r[0]) and _intlike(r[1])]
    flags = [str(r[3]).strip() if len(r) > 3 else "" for r in standard]
    id_pairs = [[int(str(r[0]).strip()), int(str(r[1]).strip())] for r in standard]
    texts = [str(r[2]).strip() for r in standard]
    return {
        "file": path.name,
        "delimiter": ";",
        "header_mode": "none",
        "n_rows": len(rows),
        "expected_eeg_sentences": expected_sentences,
        "row_minus_expected": len(rows) - expected_sentences,
        "row_width_counts": {str(k): v for k, v in sorted(widths.items())},
        "n_standard_rows_first_two_integer": len(standard),
        "n_unique_text_col2": len(set(texts)),
        "n_flagged_rows_col3": sum(bool(x) for x in flags),
        "flagged_row_indices_1based": [i + 1 for i, x in enumerate(flags) if x],
        "flag_values": sorted(set(x for x in flags if x)),
        "id_pairs_in_order": id_pairs,
        "material_word_counts": [word_count(t) for t in texts],
        "text_preview": texts[:5],
    }


def overlap_diagnostics(material_rows):
    out = []
    for i in range(len(material_rows) - 1):
        a, b = material_rows[i], material_rows[i + 1]
        amap = {(str(r[0]).strip(), str(r[1]).strip()): (j + 1, str(r[2]).strip()) for j, r in enumerate(a) if len(r) >= 3 and _intlike(r[0]) and _intlike(r[1])}
        bmap = {(str(r[0]).strip(), str(r[1]).strip()): (j + 1, str(r[2]).strip()) for j, r in enumerate(b) if len(r) >= 3 and _intlike(r[0]) and _intlike(r[1])}
        shared_ids = sorted(set(amap) & set(bmap), key=lambda x: (int(x[0]), int(x[1])))
        atexts = {str(r[2]).strip(): j + 1 for j, r in enumerate(a) if len(r) >= 3 and str(r[2]).strip()}
        btexts = {str(r[2]).strip(): j + 1 for j, r in enumerate(b) if len(r) >= 3 and str(r[2]).strip()}
        shared_text = sorted(set(atexts) & set(btexts))
        out.append({"run_a": f"NR{i+1}", "run_b": f"NR{i+2}", "n_shared_id_pairs": len(shared_ids), "n_shared_exact_texts": len(shared_text), "shared_text_row_pairs": [{"run_a_row_1based": atexts[t], "run_b_row_1based": btexts[t]} for t in shared_text]})
    return out


def monotonic_wordcount_alignment(eeg_counts, material_counts):
    """Select len(eeg_counts) material rows in order, allowing only material-row skips.

    Cost is absolute word-count difference. We also count optimal paths (capped at 2)
    so a zero-cost but ambiguous alignment is not silently treated as a freeze.
    """
    n, m = len(eeg_counts), len(material_counts)

    @lru_cache(maxsize=None)
    def solve(i, j):
        if i == n:
            return (0, 1, ())
        if j == m or m - j < n - i:
            return (10**9, 0, ())
        # match
        mc, mn, mp = solve(i + 1, j + 1)
        mc += abs(int(eeg_counts[i]) - int(material_counts[j]))
        # skip material row
        sc, sn, sp = solve(i, j + 1)
        best = min(mc, sc)
        paths = min(2, (mn if mc == best else 0) + (sn if sc == best else 0))
        if mc <= sc:
            path = (j,) + mp
        else:
            path = sp
        return best, paths, path

    cost, n_opt, path = solve(0, 0)
    selected = list(path)
    skipped = [j for j in range(m) if j not in set(selected)]
    diffs = [int(material_counts[j]) - int(eeg_counts[i]) for i, j in enumerate(selected)]
    return {
        "total_absolute_wordcount_cost": int(cost),
        "n_optimal_paths_capped_at_2": int(n_opt),
        "unique_optimum": bool(n_opt == 1),
        "selected_material_rows_1based": [j + 1 for j in selected],
        "skipped_material_rows_1based": [j + 1 for j in skipped],
        "n_exact_wordcount_matches": sum(d == 0 for d in diffs),
        "max_absolute_wordcount_difference": max((abs(d) for d in diffs), default=0),
        "wordcount_differences_material_minus_eeg": diffs,
        "freeze_ready": bool(cost == 0 and n_opt == 1 and len(skipped) == m - n),
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
    for t in TARGETS:
        p = root / t
        if not p.exists():
            download(idx[t], p)

    base = root / "task1 - NR" / "Preprocessed"
    word_alignment = [summarize_wordbounds(base / f"wordbounds_NR{i}.mat") for i in range(1, 8)]
    eeg_alignment = summarize_eeg(base / "YDG" / "gip_YDG_NR1_EEG.mat")
    counts = {f"NR{i+1}": row["n_sentences"] for i, row in enumerate(word_alignment)}
    material_paths = [root / f"task_materials/nr_{i}.csv" for i in range(1, 8)]
    raw_material = [load_material_rows(p) for p in material_paths]
    material = [summarize_material_csv(p, counts[f"NR{i}"]) for i, p in enumerate(material_paths, start=1)]

    mappings = []
    for i in range(7):
        eeg_wc = [int(s["wordbounds_shape"][0]) for s in word_alignment[i]["sentences"]]
        mat_wc = material[i]["material_word_counts"]
        rec = monotonic_wordcount_alignment(eeg_wc, mat_wc)
        rec.update({"run": f"NR{i+1}", "n_eeg_sentences": len(eeg_wc), "n_material_rows": len(mat_wc), "eeg_word_counts": eeg_wc})
        mappings.append(rec)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "model-blind task-material word-count mapping diagnostic; no EEG signal samples or model quantities read",
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
        "wordcount_mapping_diagnostics": mappings,
        "all_runs_freeze_ready": all(x["freeze_ready"] for x in mappings),
        "proposed_freeze_if_all_runs_ready": {
            "sentence_identity": "within-run EEG sentence order mapped to the unique zero-cost monotonic task-material row alignment",
            "nuisance_rdms": [
                "absolute within-run sentence-order difference",
                "word-count difference",
                "punctuation-count difference",
                "lowercased lexical-set Jaccard distance",
            ],
            "guardrail": "Adopt only if every run has a unique zero-cost structural mapping; otherwise do not infer or hand-pick rows.",
        },
        "guardrail": "No task-material row is selected using EEG values, model quantities, or outcome statistics. Wordbounds are screen-layout metadata only.",
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "all_runs_freeze_ready": summary["all_runs_freeze_ready"], "output_dir": str(outdir)}, indent=2))


if __name__ == "__main__":
    main()
