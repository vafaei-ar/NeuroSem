#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

SUB_RE = re.compile(r"sub-(\d+)")
RUN_RE = re.compile(r"run-0*(\d+)")


def run(cmd: list[str], cwd: Path | None = None, check: bool = False) -> dict:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    out = {
        "command": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip(),
    }
    if check and p.returncode != 0:
        raise RuntimeError(json.dumps(out, indent=2))
    return out


def git_files(root: Path) -> list[str]:
    p = subprocess.run(["git", "ls-files"], cwd=root, check=True, text=True, capture_output=True)
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


def safe_git_config(root: Path) -> dict:
    keys = [
        "remote.origin.url",
        "remote.origin.annex-ignore",
        "annex.uuid",
        "annex.version",
    ]
    out = {}
    for key in keys:
        p = subprocess.run(["git", "config", "--get-all", key], cwd=root, text=True, capture_output=True)
        vals = [x for x in p.stdout.splitlines() if x]
        out[key] = vals
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data/raw/smn4lang"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/smn4lang_meg_materialization_route_probe/latest"))
    args = ap.parse_args()

    root = args.data_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not (root / ".git").exists():
        raise RuntimeError(f"expected existing SMN4Lang git checkout: {root}")

    files = git_files(root)
    fif_files = sorted([p for p in files if qualifies_preproc_meg_fif(p)])
    if not fif_files:
        raise RuntimeError("no qualifying preprocessed task-rdr MEG FIF files found")
    chosen = fif_files[0]

    tool_names = ["git-annex", "datalad", "openneuro", "aws", "curl", "wget"]
    tools = {name: shutil.which(name) for name in tool_names}

    remote_v = run(["git", "remote", "-v"], cwd=root)
    annex_info = run(["git", "annex", "info"], cwd=root)
    annex_whereis = run(["git", "annex", "whereis", "--json", "--", chosen], cwd=root)
    annex_examinekey = run(["git", "annex", "examinekey", "--format=${key}\n", "--", chosen], cwd=root)
    annex_findref = run(["git", "annex", "findref", "HEAD", "--format=${key}\t${file}\n"], cwd=root)

    symlink_target = None
    path = root / chosen
    try:
        if path.is_symlink():
            symlink_target = os.readlink(path)
    except OSError:
        pass

    summary = {
        "schema_version": 1,
        "dataset": "SMN4Lang / OpenNeuro ds004078",
        "analysis_stage": "MEG model-blind materialization-route probe",
        "model_blind": True,
        "loads_neural_signal_arrays": False,
        "loads_model_embeddings": False,
        "computes_reliability": False,
        "deterministic_representative": {
            "selection_rule": "lexicographically first qualifying preprocessed task-rdr MEG FIF",
            "path": chosen,
            "subject": int(SUB_RE.search(chosen).group(1)) if SUB_RE.search(chosen) else None,
            "run": int(RUN_RE.search(chosen).group(1)) if RUN_RE.search(chosen) else None,
            "is_symlink": path.is_symlink(),
            "symlink_target": symlink_target,
        },
        "tool_availability": tools,
        "git_config_safe_subset": safe_git_config(root),
        "git_remote_v": remote_v,
        "git_annex_info": annex_info,
        "git_annex_whereis_representative": annex_whereis,
        "git_annex_examinekey_representative": annex_examinekey,
        "git_annex_findref_head": annex_findref,
        "failed_job_context": {
            "prior_job_id": "NEUROSEM-SMN4LANG-MEG-FORMAT-PROBE-0001",
            "prior_failure_class": "payload not available from any configured annex remote",
        },
        "next_decision": "choose a project-local public materialization route from observed checkout/tooling metadata only",
        "guardrails": {
            "no_payload_download_attempted": True,
            "no_signal_arrays_loaded": True,
            "no_model_outcomes": True,
            "no_latency_search": True,
            "no_sensor_search": True,
            "no_frequency_search": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
