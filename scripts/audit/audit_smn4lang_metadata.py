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

DATASET_REPO = "https://github.com/OpenNeuroDatasets/ds004078.git"
SUB_RE = re.compile(r"sub-(\d+)")
RUN_RE = re.compile(r"run-0*(\d+)")
STORY_RE = re.compile(r"story[_-]0*(\d+)", re.I)
ANNEX_SIZE_RE = re.compile(r"-s(\d+)--")


def run(cmd: list[str], cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)
    return p.stdout.strip()


def ensure_checkout(root: Path, repo_url: str) -> None:
    if (root / ".git").exists():
        return
    if root.exists() and any(root.iterdir()):
        raise RuntimeError(f"data root exists but is not a git checkout: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--filter=blob:none", "--depth=1", repo_url, str(root)])


def git_files(root: Path) -> list[str]:
    out = run(["git", "ls-files"], cwd=root)
    return [x for x in out.splitlines() if x]


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
        pass
    return None


def materialized(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink() and path.stat().st_size > 0
    except OSError:
        return False


def category(rel: str) -> str | None:
    low = rel.lower()
    if "/func/" in low and "task-rdr" in low and low.endswith("_bold.nii.gz") and not low.startswith("derivatives/"):
        return "raw_fmri_bold"
    if "/meg/" in low and "task-rdr" in low and low.endswith("_meg.fif") and not low.startswith("derivatives/"):
        return "raw_meg_fif"
    if low.startswith("derivatives/") and "preprocessed" in low and "cifti" in low and "task-rdr" in low and low.endswith(".dtseries.nii"):
        return "preproc_fmri_cifti"
    if low.startswith("derivatives/") and "preprocessed" in low and "/mni/" in low and "task-rdr" in low and low.endswith("_bold.nii.gz"):
        return "preproc_fmri_mni"
    if low.startswith("derivatives/") and "preprocessed" in low and "/meg/" in low and "task-rdr" in low and (low.endswith(".fif") or low.endswith(".tsv")):
        return "preproc_meg"
    if low.startswith("derivatives/annotations/"):
        if "/scripts/" in low and low.endswith(".txt"):
            return "annotation_story_text"
        if "time_align" in low and "word" in low:
            return "annotation_word_timing"
        if "time_align" in low and "char" in low:
            return "annotation_char_timing"
        if "syntactic" in low or "constitu" in low or "dependency" in low or "part_of_speech" in low:
            return "annotation_syntax"
    return None


def ids_from(paths: list[str], regex: re.Pattern[str]) -> list[int]:
    vals = []
    for p in paths:
        m = regex.search(p)
        if m:
            vals.append(int(m.group(1)))
    return sorted(set(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_metadata_audit/latest"))
    ap.add_argument("--repo-url", default=DATASET_REPO)
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ensure_checkout(root, args.repo_url)

    commit = run(["git", "rev-parse", "HEAD"], cwd=root)
    files = git_files(root)
    relevant = [(p, category(p)) for p in files]
    relevant = [(p, c) for p, c in relevant if c is not None]

    by_cat: dict[str, list[str]] = defaultdict(list)
    inv_rows = []
    for rel, cat in relevant:
        by_cat[cat].append(rel)
        path = root / rel
        size = annex_pointer_size(path)
        inv_rows.append({
            "category": cat,
            "path": rel,
            "subject": (f"sub-{int(SUB_RE.search(rel).group(1)):02d}" if SUB_RE.search(rel) else ""),
            "run": (int(RUN_RE.search(rel).group(1)) if RUN_RE.search(rel) else ""),
            "story": (int(STORY_RE.search(rel).group(1)) if STORY_RE.search(rel) else ""),
            "annex_payload_bytes": "" if size is None else size,
            "materialized_in_metadata_checkout": materialized(path),
        })

    raw_fmri_subjects = ids_from(by_cat.get("raw_fmri_bold", []), SUB_RE)
    raw_meg_subjects = ids_from(by_cat.get("raw_meg_fif", []), SUB_RE)
    raw_fmri_runs = ids_from(by_cat.get("raw_fmri_bold", []), RUN_RE)
    raw_meg_runs = ids_from(by_cat.get("raw_meg_fif", []), RUN_RE)
    cifti_subjects = ids_from(by_cat.get("preproc_fmri_cifti", []), SUB_RE)
    cifti_runs = ids_from(by_cat.get("preproc_fmri_cifti", []), RUN_RE)
    mni_subjects = ids_from(by_cat.get("preproc_fmri_mni", []), SUB_RE)
    mni_runs = ids_from(by_cat.get("preproc_fmri_mni", []), RUN_RE)
    text_stories = ids_from(by_cat.get("annotation_story_text", []), STORY_RE)
    word_timing_stories = ids_from(by_cat.get("annotation_word_timing", []), STORY_RE)

    per_subject_fmri = Counter()
    per_subject_meg = Counter()
    per_subject_cifti = Counter()
    for p in by_cat.get("raw_fmri_bold", []):
        m = SUB_RE.search(p)
        if m: per_subject_fmri[int(m.group(1))] += 1
    for p in by_cat.get("raw_meg_fif", []):
        m = SUB_RE.search(p)
        if m: per_subject_meg[int(m.group(1))] += 1
    for p in by_cat.get("preproc_fmri_cifti", []):
        m = SUB_RE.search(p)
        if m: per_subject_cifti[int(m.group(1))] += 1

    payload_sizes = {}
    for cat, paths in by_cat.items():
        vals = [annex_pointer_size(root / p) for p in paths]
        known = [v for v in vals if v is not None]
        payload_sizes[cat] = {
            "n_files": len(paths),
            "n_with_annex_size": len(known),
            "known_payload_bytes": int(sum(known)),
        }

    expected_subjects = set(range(1, 13))
    expected_runs = set(range(1, 61))
    all_subjects = set(raw_fmri_subjects) == expected_subjects and set(raw_meg_subjects) == expected_subjects
    all_runs = set(raw_fmri_runs) == expected_runs and set(raw_meg_runs) == expected_runs
    preproc_fmri_complete = set(cifti_subjects) == expected_subjects and set(cifti_runs) == expected_runs
    text_complete = set(text_stories) == expected_runs
    word_timing_complete = set(word_timing_stories) == expected_runs

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "dataset_git_repo": args.repo_url,
        "dataset_git_commit": commit,
        "metadata_only": True,
        "n_git_tracked_files": len(files),
        "category_counts": {k: len(v) for k, v in sorted(by_cat.items())},
        "raw_fmri_subject_ids": raw_fmri_subjects,
        "raw_meg_subject_ids": raw_meg_subjects,
        "raw_fmri_run_ids": raw_fmri_runs,
        "raw_meg_run_ids": raw_meg_runs,
        "preproc_cifti_subject_ids": cifti_subjects,
        "preproc_cifti_run_ids": cifti_runs,
        "preproc_mni_subject_ids": mni_subjects,
        "preproc_mni_run_ids": mni_runs,
        "story_text_ids": text_stories,
        "word_timing_story_ids": word_timing_stories,
        "per_subject_raw_fmri_run_counts": {str(k): v for k, v in sorted(per_subject_fmri.items())},
        "per_subject_raw_meg_run_counts": {str(k): v for k, v in sorted(per_subject_meg.items())},
        "per_subject_preproc_cifti_run_counts": {str(k): v for k, v in sorted(per_subject_cifti.items())},
        "payload_size_inventory": payload_sizes,
        "structural_checks": {
            "raw_modalities_have_exact_12_subjects": all_subjects,
            "raw_modalities_have_exact_60_runs": all_runs,
            "preprocessed_cifti_has_exact_12_subjects_60_runs": preproc_fmri_complete,
            "story_text_has_exact_60_story_ids": text_complete,
            "word_timing_has_exact_60_story_ids": word_timing_complete,
        },
        "ready_for_targeted_materialization_probe": bool(all_subjects and all_runs and preproc_fmri_complete and text_complete and word_timing_complete),
        "guardrails": [
            "This job performs metadata-only Git/OpenNeuro inventory and does not load fMRI or MEG signal arrays.",
            "No NeuroSem model, embedding checkpoint, RSA, encoding model, or model comparison is computed.",
            "Distributed BERT/GPT2/Word2Vec annotations are not inspected for outcome selection.",
            "No semantic unit, HRF lag/window, cortical mask, or MEG representation is selected from neural outcomes.",
        ],
    }

    with (out / "file_inventory.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["category", "path", "subject", "run", "story", "annex_payload_bytes", "materialized_in_metadata_checkout"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(inv_rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
