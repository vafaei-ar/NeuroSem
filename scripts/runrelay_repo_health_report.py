#!/usr/bin/env python3
"""Create a small safe derived health report from the public NeuroSem RunRelay config."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".runrelay" / "project.yaml"
AGENTS = ROOT / "AGENTS.md"
OUTPUT_DIR = ROOT / "outputs" / "runrelay_repo_health" / "latest"

REPORTING_INPUTS = [
    "outputs/zuco2_nr_e5_transfer_v1/latest/subject_results.csv",
    "outputs/smn4lang_fmri_e5_transfer_v1/latest/participant_results.csv",
    "outputs/smn4lang_fmri_e5_transfer/latest/participant_results.csv",
    "outputs/nmi_reviewer_response_consolidated_v1/latest/summary.json",
    "outputs/nmi_reviewer_response_scientific_v1/latest/summary.json",
    "outputs/nmi_fmri_to_zuco_lambda001_multiseed_v1/latest/summary.json",
]
for seed in [20260829, 20260830, 20260831]:
    for dataset, csv_name in [("zuco", "subject_results.csv"), ("smn4lang_fmri", "participant_results.csv")]:
        for comparison in ["shuffled_minus_text", "genuine_minus_shuffled"]:
            REPORTING_INPUTS.append(
                f"outputs/nmi_reviewer_response_scientific_v1/latest/seed_{seed}/{dataset}/{comparison}/{csv_name}"
            )


def inspect_reporting_input(rel: str) -> dict:
    p = ROOT / rel
    item = {"path": rel, "exists": p.exists(), "is_file": p.is_file()}
    if not p.is_file():
        return item
    item["size_bytes"] = p.stat().st_size
    if p.suffix.lower() == ".csv":
        try:
            with p.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                item["header"] = next(reader, [])
                item["n_rows"] = sum(1 for _ in reader)
        except Exception as e:
            item["read_error"] = type(e).__name__ + ": " + str(e)
    elif p.suffix.lower() == ".json":
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            item["top_level_keys"] = sorted(obj.keys()) if isinstance(obj, dict) else []
        except Exception as e:
            item["read_error"] = type(e).__name__ + ": " + str(e)
    return item


def main() -> None:
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    agents_text = AGENTS.read_text(encoding="utf-8")

    task_names = re.findall(r"^  ([A-Za-z0-9_]+):\s*$", manifest_text, flags=re.MULTILINE)
    machine_match = re.search(r"^  machine_id:\s*([^\s#]+)", manifest_text, flags=re.MULTILINE)
    project_match = re.search(r"^  id:\s*([^\s#]+)", manifest_text, flags=re.MULTILINE)
    script_paths = sorted(set(re.findall(r"^\s+-\s+(scripts/[A-Za-z0-9_./-]+\.py)\s*$", manifest_text, flags=re.MULTILINE)))

    script_checks = [
        {"path": rel, "exists": (ROOT / rel).is_file()}
        for rel in script_paths
    ]
    missing_scripts = [item["path"] for item in script_checks if not item["exists"]]

    payload = {
        "schema_version": 1,
        "report": "neurosem_runrelay_repo_health",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": project_match.group(1) if project_match else None,
        "machine_id": machine_match.group(1) if machine_match else None,
        "task_count": len(task_names),
        "tasks": task_names,
        "referenced_python_script_count": len(script_checks),
        "missing_referenced_scripts": missing_scripts,
        "agents_declares_runrelay": "RunRelay" in agents_text,
        "reporting_input_diagnostic": {
            "scope": "existence, CSV headers/row counts, and JSON top-level keys only; no outcome values",
            "items": [inspect_reporting_input(rel) for rel in REPORTING_INPUTS],
        },
        "status": "ok" if not missing_scripts and task_names else "attention",
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "health.txt").write_text(
        "\n".join(
            [
                "NeuroSem RunRelay repository health report",
                f"Status: {payload['status']}",
                f"Project: {payload['project_id']}",
                f"Machine: {payload['machine_id']}",
                f"Registered tasks: {payload['task_count']}",
                f"Referenced Python scripts checked: {payload['referenced_python_script_count']}",
                f"Missing referenced scripts: {len(missing_scripts)}",
                "Reporting input diagnostic: included in health.json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
