#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import mne

S3_BUCKET = "openneuro.org"
S3_BASE = f"https://s3.amazonaws.com/{S3_BUCKET}/"
DATASET_PREFIX = "ds004078/"
SUB_RE = re.compile(r"sub-(\d+)")
RUN_RE = re.compile(r"run-0*(\d+)")
ANNEX_RE = re.compile(r"MD5E-s(\d+)--([0-9a-fA-F]{32})\.fif")
EXPECTED_SUBJECTS = list(range(1, 13))
EXPECTED_N_RUNS = 60
EXPECTED_SFREQ = 1000.0
EXPECTED_HIGHPASS = 1.0
EXPECTED_LOWPASS = 40.0
EXPECTED_MEG_COUNTS = {"grad": 204, "mag": 102}


def git_files(root: Path) -> list[str]:
    p = __import__("subprocess").run(
        ["git", "ls-files"], cwd=root, check=True, text=True, capture_output=True
    )
    return [x for x in p.stdout.splitlines() if x]


def qualifies_preproc_meg_fif(rel: str) -> bool:
    low = rel.lower()
    return (
        low.startswith("derivatives/")
        and "preprocessed" in low
        and "/meg/" in low
        and "task-rdr" in low
        and low.endswith(".fif")
    )


def parse_sub_run(rel: str) -> tuple[int, int]:
    sm = SUB_RE.search(rel)
    rm = RUN_RE.search(rel)
    if not sm or not rm:
        raise RuntimeError(f"cannot parse subject/run from {rel}")
    return int(sm.group(1)), int(rm.group(1))


def annex_meta(path: Path) -> tuple[int, str]:
    if not path.is_symlink():
        raise RuntimeError(f"expected git-annex symlink: {path}")
    target = os.readlink(path)
    m = ANNEX_RE.search(target)
    if not m:
        raise RuntimeError(f"cannot parse MD5E annex key from symlink: {path} -> {target}")
    return int(m.group(1)), m.group(2).lower()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def head_object(url: str) -> tuple[int, str | None]:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "NeuroSem-SMN4Lang-MEG-format-probe/2"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        size = int(r.headers.get("Content-Length", "0"))
        etag = r.headers.get("ETag")
    return size, etag.strip('"') if etag else None


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "NeuroSem-SMN4Lang-MEG-format-probe/2"},
    )
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as f:
        while True:
            chunk = r.read(8 * 1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dst)


def channel_name_hash(names: list[str]) -> str:
    joined = "\n".join(names).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_meg_format_probe/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cache_root = root.parent / "smn4lang_meg_probe_cache"

    if not (root / ".git").exists():
        raise RuntimeError(f"expected existing SMN4Lang git checkout: {root}")

    all_fif = sorted(p for p in git_files(root) if qualifies_preproc_meg_fif(p))
    if not all_fif:
        raise RuntimeError("no qualifying preprocessed task-RDR MEG FIF files found")

    by_sub: dict[int, list[tuple[int, str]]] = defaultdict(list)
    inventory_rows: list[dict] = []
    for rel in all_fif:
        sub, run = parse_sub_run(rel)
        size, md5 = annex_meta(root / rel)
        by_sub[sub].append((run, rel))
        inventory_rows.append(
            {
                "subject": sub,
                "run": run,
                "relative_path": rel,
                "annex_size_bytes": size,
                "annex_md5": md5,
                "representative": False,
            }
        )

    subjects = sorted(by_sub)
    run_sets = {sub: sorted(run for run, _ in by_sub[sub]) for sub in subjects}
    common_runs = sorted(set.intersection(*(set(v) for v in run_sets.values()))) if run_sets else []
    identical_run_sets = len({tuple(v) for v in run_sets.values()}) == 1

    representatives: dict[int, str] = {}
    for sub in subjects:
        representatives[sub] = sorted(rel for _, rel in by_sub[sub])[0]
    rep_set = set(representatives.values())
    for row in inventory_rows:
        row["representative"] = row["relative_path"] in rep_set

    rep_rows: list[dict] = []
    channel_rows: list[dict] = []
    channel_hashes: list[str] = []
    metadata_signatures: list[tuple] = []

    for sub in subjects:
        rel = representatives[sub]
        _, run = parse_sub_run(rel)
        expected_size, expected_md5 = annex_meta(root / rel)
        key = DATASET_PREFIX + rel
        url = S3_BASE + urllib.parse.quote(key, safe="/")
        s3_size, etag = head_object(url)
        if s3_size != expected_size:
            raise RuntimeError(
                f"S3 size mismatch for {rel}: annex={expected_size}, s3={s3_size}"
            )

        cache = cache_root / rel
        if not cache.exists() or cache.stat().st_size != expected_size:
            download(url, cache)
        observed_md5 = md5_file(cache)
        if observed_md5 != expected_md5:
            raise RuntimeError(
                f"MD5 mismatch for {rel}: annex={expected_md5}, observed={observed_md5}"
            )

        raw = mne.io.read_raw_fif(cache, preload=False, verbose="ERROR")
        types = raw.get_channel_types()
        counts = Counter(types)
        meg_counts = {"grad": counts.get("grad", 0), "mag": counts.get("mag", 0)}
        ch_hash = channel_name_hash(list(raw.ch_names))
        channel_hashes.append(ch_hash)
        signature = (
            float(raw.info["sfreq"]),
            float(raw.info.get("highpass", 0.0)),
            float(raw.info.get("lowpass", 0.0)),
            meg_counts["grad"],
            meg_counts["mag"],
        )
        metadata_signatures.append(signature)

        rep_rows.append(
            {
                "subject": sub,
                "run": run,
                "relative_path": rel,
                "object_url": url,
                "size_bytes": expected_size,
                "expected_md5": expected_md5,
                "observed_md5": observed_md5,
                "s3_etag": etag,
                "integrity_verified": observed_md5 == expected_md5,
                "sfreq_hz": float(raw.info["sfreq"]),
                "n_times": int(raw.n_times),
                "duration_seconds": float(raw.n_times / raw.info["sfreq"]),
                "n_channels": len(raw.ch_names),
                "n_grad": meg_counts["grad"],
                "n_mag": meg_counts["mag"],
                "n_bads": len(raw.info.get("bads", [])),
                "highpass_hz": float(raw.info.get("highpass", 0.0)),
                "lowpass_hz": float(raw.info.get("lowpass", 0.0)),
                "n_annotations": len(raw.annotations),
                "dev_head_t_present": raw.info.get("dev_head_t") is not None,
                "channel_name_sha256": ch_hash,
                "preload": False,
            }
        )
        for idx, (name, typ) in enumerate(zip(raw.ch_names, types)):
            channel_rows.append(
                {
                    "subject": sub,
                    "representative_run": run,
                    "channel_index": idx,
                    "channel_name": name,
                    "channel_type": typ,
                    "is_bad": name in raw.info.get("bads", []),
                }
            )

    expected_subjects_ok = subjects == EXPECTED_SUBJECTS
    exactly_60_each = all(len(v) == EXPECTED_N_RUNS for v in run_sets.values())
    reps_integrity_ok = all(r["integrity_verified"] for r in rep_rows)
    expected_meg_counts_ok = all(
        r["n_grad"] == EXPECTED_MEG_COUNTS["grad"]
        and r["n_mag"] == EXPECTED_MEG_COUNTS["mag"]
        for r in rep_rows
    )
    expected_preproc_ok = all(
        r["sfreq_hz"] == EXPECTED_SFREQ
        and r["highpass_hz"] == EXPECTED_HIGHPASS
        and r["lowpass_hz"] == EXPECTED_LOWPASS
        for r in rep_rows
    )
    dev_head_t_all = all(r["dev_head_t_present"] for r in rep_rows)
    channel_names_identical = len(set(channel_hashes)) == 1
    metadata_signature_identical = len(set(metadata_signatures)) == 1

    structural_ready = all(
        [
            expected_subjects_ok,
            exactly_60_each,
            identical_run_sets,
            len(common_runs) == EXPECTED_N_RUNS,
            reps_integrity_ok,
            expected_meg_counts_ok,
            expected_preproc_ok,
            dev_head_t_all,
            metadata_signature_identical,
        ]
    )

    with (out / "file_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(inventory_rows[0].keys()))
        w.writeheader()
        w.writerows(inventory_rows)

    with (out / "channel_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(channel_rows[0].keys()))
        w.writeheader()
        w.writerows(channel_rows)

    summary = {
        "schema_version": 2,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "MEG model-blind cross-participant format/materialization probe",
        "model_blind": True,
        "computes_reliability": False,
        "loads_neural_signal_arrays": False,
        "loads_model_embeddings": False,
        "representation_freeze": "docs/13_SMN4LANG_MEG_REPRESENTATION_FREEZE.md",
        "public_materialization_route": {
            "source": "OpenNeuro public AWS S3 mirror",
            "bucket": S3_BUCKET,
            "endpoint_style": "path-style HTTPS",
            "tls_verification_disabled": False,
        },
        "full_inventory": {
            "n_fif": len(all_fif),
            "subjects": subjects,
            "n_subjects": len(subjects),
            "runs_per_subject": {str(k): len(v) for k, v in run_sets.items()},
            "common_run_ids": common_runs,
            "n_common_runs": len(common_runs),
            "identical_run_sets": identical_run_sets,
        },
        "representative_rule": "lexicographically first qualifying preprocessed task-RDR MEG FIF independently within each subject",
        "n_representatives_materialized": len(rep_rows),
        "representatives": rep_rows,
        "cross_participant_checks": {
            "expected_subjects_1_to_12": expected_subjects_ok,
            "exactly_60_runs_each": exactly_60_each,
            "same_60_run_ids_all_subjects": identical_run_sets and len(common_runs) == EXPECTED_N_RUNS,
            "all_representative_md5_verified": reps_integrity_ok,
            "all_representatives_204_grad_102_mag": expected_meg_counts_ok,
            "all_representatives_1000hz_1to40hz": expected_preproc_ok,
            "all_dev_head_t_present": dev_head_t_all,
            "channel_names_identical_across_representatives": channel_names_identical,
            "metadata_signature_identical_across_representatives": metadata_signature_identical,
        },
        "structural_ready_for_frozen_reliability": structural_ready,
        "next_decision": (
            "run the already-frozen model-blind MEG reliability analysis"
            if structural_ready
            else "stop and resolve structural incompatibility without model outcomes"
        ),
        "guardrails": {
            "one_deterministic_representative_per_participant_only": True,
            "no_meg_sample_arrays_loaded": True,
            "no_reliability_computed": True,
            "no_model_outcomes": True,
            "no_latency_search": True,
            "no_frequency_search": True,
            "no_sensor_subset_search": True,
            "no_source_localization_search": True,
        },
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if structural_ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
