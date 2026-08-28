#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import mne

SUB_RE = re.compile(r"sub-(\d+)")
RUN_RE = re.compile(r"run-0*(\d+)")
ANNEX_SIZE_RE = re.compile(r"-s(\d+)--")


def run(cmd: list[str], cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)
    return p.stdout.strip()


def git_files(root: Path) -> list[str]:
    out = run(["git", "ls-files"], cwd=root)
    return [x for x in out.splitlines() if x]


def qualifies_preproc_meg(rel: str) -> bool:
    low = rel.lower()
    return (
        low.startswith("derivatives/")
        and "preprocessed" in low
        and "/meg/" in low
        and "task-rdr" in low
        and (low.endswith(".fif") or low.endswith(".tsv"))
    )


def annex_pointer_size(path: Path) -> int | None:
    try:
        if path.is_symlink():
            target = os.readlink(path)
            m = ANNEX_SIZE_RE.search(target)
            return int(m.group(1)) if m else None
        if path.is_file() and path.stat().st_size < 4096:
            txt = path.read_text(encoding="utf-8", errors="ignore")
            m = ANNEX_SIZE_RE.search(txt)
            return int(m.group(1)) if m else None
    except OSError:
        return None
    return None


def materialized(path: Path) -> bool:
    try:
        if path.is_symlink():
            return path.exists() and path.resolve().is_file() and path.resolve().stat().st_size > 0
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def annex_get(root: Path, rel: str) -> None:
    path = root / rel
    if materialized(path):
        return
    subprocess.run(["git", "annex", "get", "--", rel], cwd=root, check=True)
    if not materialized(path):
        raise RuntimeError(f"failed to materialize {rel}")


def ids(paths: list[str], regex: re.Pattern[str]) -> list[int]:
    out = []
    for p in paths:
        m = regex.search(p)
        if m:
            out.append(int(m.group(1)))
    return sorted(set(out))


def inspect_tsv(path: Path) -> dict:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)
    header = rows[0] if rows else []
    n_rows = max(0, len(rows) - 1)
    sample = rows[1][: len(header)] if len(rows) > 1 else []
    return {
        "path": str(path),
        "columns": header,
        "n_rows": n_rows,
        "first_data_row_as_strings": sample,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_meg_format_probe/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not (root / ".git").exists():
        raise RuntimeError(f"expected existing SMN4Lang git checkout: {root}")

    dataset_commit = run(["git", "rev-parse", "HEAD"], cwd=root)
    files = git_files(root)
    candidates = sorted([p for p in files if qualifies_preproc_meg(p)])
    fif_files = [p for p in candidates if p.lower().endswith(".fif")]
    tsv_files = [p for p in candidates if p.lower().endswith(".tsv")]
    if not fif_files:
        raise RuntimeError("no qualifying preprocessed task-rdr MEG FIF files found")

    chosen = fif_files[0]
    chosen_sub = SUB_RE.search(chosen)
    chosen_run = RUN_RE.search(chosen)
    chosen_sub_id = int(chosen_sub.group(1)) if chosen_sub else None
    chosen_run_id = int(chosen_run.group(1)) if chosen_run else None

    same_run_tsv = []
    for rel in tsv_files:
        sm = SUB_RE.search(rel)
        rm = RUN_RE.search(rel)
        if sm and rm and int(sm.group(1)) == chosen_sub_id and int(rm.group(1)) == chosen_run_id:
            same_run_tsv.append(rel)

    materialize_targets = [chosen] + same_run_tsv
    for rel in materialize_targets:
        annex_get(root, rel)

    raw = mne.io.read_raw_fif(root / chosen, preload=False, verbose="ERROR")
    type_counts = Counter(raw.get_channel_types())
    annotations = Counter(str(x) for x in raw.annotations.description)
    ch_rows = []
    for name, ctype in zip(raw.ch_names, raw.get_channel_types(), strict=True):
        ch_rows.append({"channel": name, "mne_type": ctype, "is_bad": name in raw.info.get("bads", [])})

    inventory_rows = []
    per_subject_fif = Counter()
    per_subject_tsv = Counter()
    per_subject_runs: dict[int, set[int]] = defaultdict(set)
    for rel in candidates:
        sm = SUB_RE.search(rel)
        rm = RUN_RE.search(rel)
        sid = int(sm.group(1)) if sm else None
        rid = int(rm.group(1)) if rm else None
        suffix = "fif" if rel.lower().endswith(".fif") else "tsv"
        if sid is not None:
            if suffix == "fif":
                per_subject_fif[sid] += 1
            else:
                per_subject_tsv[sid] += 1
            if rid is not None:
                per_subject_runs[sid].add(rid)
        size = annex_pointer_size(root / rel)
        inventory_rows.append({
            "path": rel,
            "suffix": suffix,
            "subject": "" if sid is None else f"sub-{sid:02d}",
            "run": "" if rid is None else rid,
            "annex_payload_bytes": "" if size is None else size,
            "materialized": materialized(root / rel),
        })

    tsv_summaries = [inspect_tsv(root / rel) for rel in same_run_tsv]
    expected_subjects = set(range(1, 13))
    expected_runs = set(range(1, 61))
    fif_subjects = ids(fif_files, SUB_RE)
    fif_runs = ids(fif_files, RUN_RE)

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "MEG model-blind format/materialization probe",
        "dataset_git_commit": dataset_commit,
        "model_blind": True,
        "computes_neural_reliability": False,
        "computes_model_outcomes": False,
        "qualifying_inventory": {
            "n_files": len(candidates),
            "n_fif": len(fif_files),
            "n_tsv": len(tsv_files),
            "subject_ids_in_fif": fif_subjects,
            "run_ids_in_fif": fif_runs,
            "per_subject_fif_counts": {str(k): v for k, v in sorted(per_subject_fif.items())},
            "per_subject_tsv_counts": {str(k): v for k, v in sorted(per_subject_tsv.items())},
            "per_subject_unique_run_counts": {str(k): len(v) for k, v in sorted(per_subject_runs.items())},
            "has_exact_12_subjects_in_fif": set(fif_subjects) == expected_subjects,
            "has_exact_60_run_ids_in_fif": set(fif_runs) == expected_runs,
        },
        "deterministic_representative": {
            "selection_rule": "lexicographically first qualifying preprocessed task-rdr MEG FIF",
            "path": chosen,
            "subject": chosen_sub_id,
            "run": chosen_run_id,
            "same_run_tsv_paths": same_run_tsv,
        },
        "representative_fif_metadata": {
            "sfreq_hz": float(raw.info["sfreq"]),
            "n_times": int(raw.n_times),
            "first_samp": int(raw.first_samp),
            "last_samp": int(raw.last_samp),
            "duration_seconds": float(raw.n_times / raw.info["sfreq"]),
            "n_channels": len(raw.ch_names),
            "channel_type_counts": dict(sorted(type_counts.items())),
            "bad_channels": list(raw.info.get("bads", [])),
            "highpass_hz": float(raw.info.get("highpass", 0.0)),
            "lowpass_hz": float(raw.info.get("lowpass", 0.0)),
            "measurement_date_present": raw.info.get("meas_date") is not None,
            "n_annotations": len(raw.annotations),
            "annotation_description_counts": dict(sorted(annotations.items())),
            "dev_head_t_present": raw.info.get("dev_head_t") is not None,
        },
        "representative_tsv_metadata": tsv_summaries,
        "next_decision": "freeze one MEG representation and reliability gate from structural/acquisition information only",
        "guardrails": {
            "preload_false": True,
            "no_signal_arrays_loaded": True,
            "no_model_embeddings_loaded": True,
            "no_reliability_computed": True,
            "no_latency_search": True,
            "no_frequency_search": True,
            "no_sensor_subset_search": True,
            "no_source_localization_search": True,
            "no_result_driven_rescue": True,
        },
    }

    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["path", "suffix", "subject", "run", "annex_payload_bytes", "materialized"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(inventory_rows)

    with (out / "channel_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["channel", "mne_type", "is_bad"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(ch_rows)

    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
